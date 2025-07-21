from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import uuid

app = FastAPI(title="Text-to-Speech API", version="1.0.0")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "text-to-speech-api"}


# amazon 文本转语音
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import sys
from typing import Optional

session = Session(profile_name="default")
polly = session.client("polly")


class IpaToSpeechRequest(BaseModel):
    ipa: Optional[str] = None
    text: Optional[str] = None

@app.post("/speech")
async def speech(request: IpaToSpeechRequest):
    try:
        # 如果是ipa，则直接使用ipa；如果是英语句子，则直接使用英语句子
        if request.ipa:
            print(f"IPA===: {request.ipa}")
            text = f"""
                <speak>
                    <phoneme alphabet="ipa" ph="{request.ipa}"></phoneme>
                </speak>
            """
        else:
            # 如果是英语句子，则直接使用英语句子
            text = request.text

        # response = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId="Joanna", TextType="ssml", Engine="neural")
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId="Joanna",
            # 传ipa时需要使用SSML，英语句子使用text格式
            TextType="ssml" if request.ipa else "text",
            Engine="neural"
        )
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)

        # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            
            try:
                # 返回文件二进制流
                return return_audio(stream)

            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                sys.exit(-1)

    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        sys.exit(-1)
        

from io import BytesIO
# 假设你已经得到了第三方的 stream（是一个类文件对象）
def return_audio(stream):
    # 把文件内容读进内存
    audio_bytes = BytesIO(stream.read())
    audio_bytes.seek(0)  # 确保从头开始读取

    # 使用 StreamingResponse 返回给前端
    return StreamingResponse(
        audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{uuid.uuid4().hex}.mp3"'
        }
    )


# 查询单词
from wordfreq import word_frequency
from fuzzywuzzy import fuzz

# 准备前置条件
english_words = set(open('words_alpha.txt').read().split())

# 单词包含关键字的单词查询
def ranked_suggestions(query, words, limit=10):
    try:
        candidates = [word for word in words if query in word]
        scored = []

        for word in candidates:
            freq = word_frequency(word, 'en')
            sim = fuzz.partial_ratio(query, word) / 100
            score = freq * sim
            scored.append((word, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [word for word, score in scored[:limit]]
    except Exception as e:
        print(f"Error during ranked suggestions: {e}")
        return []


# 单词前缀查询
def ranked_prefix_suggestions(query, words, limit=10):
    try:
        candidates = [word for word in words if word.startswith(query)]
        scored = []

        for word in candidates:
            freq = word_frequency(word, 'en')
            sim = fuzz.partial_ratio(query, word) / 100
            score = freq * sim
            scored.append((word, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [word for word, score in scored[:limit]]
    except Exception as e:
        print(f"Error during ranked prefix suggestions: {e}")
        return []


class QueryWordRequest(BaseModel):
    word: Optional[str] = None
    type: Optional[int] = None

# 用单词关键字母查询单词
@app.post("/query-word")
async def query_word(request: QueryWordRequest):

    if not request.word:
        raise HTTPException(status_code=400, detail="Word query is required")
    
    # 监测报错，报错返回[]
    try:
        if request.type == 0:
            # 前缀查询
            suggestions = ranked_prefix_suggestions(request.word, english_words)

        else:
            # 包含关键字查询
            suggestions = ranked_suggestions(request.word, english_words)

    except Exception as e:
        print(f"Error during word query: {e}")
        suggestions = []

    return {"suggestions": suggestions}