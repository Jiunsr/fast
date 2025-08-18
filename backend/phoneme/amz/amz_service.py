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
            Engine="neural",
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
        },
    )


# 查询单词候选词
from wordfreq import word_frequency
from rapidfuzz.fuzz import partial_ratio
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# 加载词表
with open("words_alpha.txt") as f:
    english_words = set(f.read().split())

@lru_cache(maxsize=10000)
def cached_word_frequency(word):
    return word_frequency(word, "en")

def score_word(word, query):
    freq = cached_word_frequency(word)
    sim = partial_ratio(query, word) / 100
    return (word, freq * sim)

def ranked_suggestions(query, words, limit=10, max_word_length=20, min_freq=1e-6):
    try:
        # 生成器方式，提前筛选词长和最小频率
        candidates = (
            word for word in words
            if query in word and len(word) <= max_word_length and cached_word_frequency(word) >= min_freq
        )

        with ThreadPoolExecutor() as executor:
            scored = list(executor.map(lambda w: score_word(w, query), candidates))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [word for word, score in scored[:limit]]

    except Exception as e:
        print(f"Error during ranked suggestions: {e}")
        return []


# 单词前缀查询
def ranked_prefix_suggestions(query, words, limit=10, max_word_length=20, min_freq=1e-6):
    try:
        # 筛选：以 query 为前缀、长度符合、频率足够
        candidates = (
            word for word in words
            if word.startswith(query) and len(word) <= max_word_length and cached_word_frequency(word) >= min_freq
        )

        with ThreadPoolExecutor() as executor:
            scored = list(executor.map(lambda w: score_word(w, query), candidates))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [word for word, score in scored[:limit]]

    except Exception as e:
        print(f"Error during ranked prefix suggestions: {e}")
        return []


class QueryWordRequest(BaseModel):
    word: Optional[str] = None
    type: Optional[int] = None


# 执行耗时
import time


# 用单词关键字母查询单词
@app.post("/query-word")
async def query_word(request: QueryWordRequest):

    if not request.word:
        raise HTTPException(status_code=400, detail="Word query is required")

    _time_start = time.time()

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

    _time_end = time.time()
    print(f"耗时毫秒: {(_time_end - _time_start) * 1000:.2f}ms")

    return {"suggestions": suggestions, "time": (_time_end - _time_start) * 1000}


from httpx import AsyncClient

@app.get("/weixin-link")
async def weixin_link(url: str):
    """获取微信公众号 H5 页面跳转到微信的真实链接"""
    print(f"Received URL: {url}")

    # 检查 URL 参数是否存在
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")

    # 用http库调用 https://mp.weixin.qq.com/mp/jumptoweixin Content-Type = text/plain
    # 传入body内容 link=https://mp.weixin.qq.com/s/xXf3zL5FI3s5LOT2Fk7Uqw
    # 返回link

    async with AsyncClient() as client:
        try:
            response = await client.post(
                "https://mp.weixin.qq.com/mp/jumptoweixin",
                data={"link": url},
                headers={"Content-Type": "text/plain"}
            )
            response.raise_for_status()  # 检查请求是否成功
            data = response.json()
            link = data.get("url")
        except Exception as e:
            # 如果错误，则返回原始 URL
            link = url
            print(f"Error fetching Weixin link: {e}")

    # 返回跳转后的链接
    if link:
        return {"link": link}
    
    # link为空返回原始 URL
    return {"link": url}