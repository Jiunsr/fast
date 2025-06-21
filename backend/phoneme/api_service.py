from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
from phonemizer import phonemize
from phonemizer.separator import Separator
import pyphen
from arpa2ipa import arpa_to_ipa
from syllabify import syllabify, pprint
from g2p_en import G2p
import nltk
from nltk.corpus import cmudict
from google.cloud import texttospeech
import os
import uuid
import tempfile

app = FastAPI(title="Text-to-Speech API", version="1.0.0")

# 初始化组件
dic = pyphen.Pyphen(lang="en_US")
g2p = G2p()
client = texttospeech.TextToSpeechClient()

class TextToSpeechRequest(BaseModel):
    text: str
    language_code: str = "en-US"
    voice_gender: str = "NEUTRAL"  # NEUTRAL, MALE, FEMALE

class TextToPhonemeRequest(BaseModel):
    text: str

@app.post("/convert-text-to-phoneme")
async def convert_text_to_phoneme(request: TextToPhonemeRequest):
    """将文本转换为音素"""
    try:
        text = [request.text]
        
        # 使用phonemizer进行音素转换
        phn = phonemize(
            text,
            language='en-us',
            backend='espeak',
        )
        
        # 使用g2p进行音素转换
        phones = g2p(request.text)
        
        # 音节划分
        syllab = syllabify(phones)
        syllabifyd = pprint(syllab)
        
        # 处理音节格式
        if syllabifyd.startswith('-'):
            syllabifyd = syllabifyd[1:]
        
        # 转换为IPA
        phonesJoin = syllabifyd.split('.')
        phonesJoin = [phone.replace('-', ' ') for phone in phonesJoin]
        phonesRes = []
        for phone in phonesJoin:
            phonesRes.append(arpa_to_ipa(phone.strip()))
        
        return {
            "success": True,
            "original_text": request.text,
            "phonemes": phones,
            "syllables": syllabifyd,
            "ipa_phonemes": phonesRes,
            "phonemizer_result": phn[0] if phn else ""
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音素转换失败: {str(e)}")

@app.post("/synthesize-speech")
async def synthesize_speech(request: TextToSpeechRequest):
    """合成语音并返回音频文件"""
    try:
        # 首先转换为音素
        phoneme_request = TextToPhonemeRequest(text=request.text)
        phoneme_result = await convert_text_to_phoneme(phoneme_request)
        
        # 构建SSML
        ipa_phonemes = phoneme_result["ipa_phonemes"]
        if ipa_phonemes:
            # 使用IPA音素构建SSML
            ipa_text = "".join(ipa_phonemes)
            ssml_text = f"""
<speak>
  <phoneme alphabet="ipa" ph="{ipa_text}">{request.text}</phoneme>
</speak>
"""
        else:
            # 如果没有IPA音素，使用普通文本
            ssml_text = f"<speak>{request.text}</speak>"
        
        # 设置语音参数
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
        
        # 设置语音性别
        gender_map = {
            "NEUTRAL": texttospeech.SsmlVoiceGender.NEUTRAL,
            "MALE": texttospeech.SsmlVoiceGender.MALE,
            "FEMALE": texttospeech.SsmlVoiceGender.FEMALE
        }
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=request.language_code,
            ssml_gender=gender_map.get(request.voice_gender, texttospeech.SsmlVoiceGender.NEUTRAL)
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # 合成语音
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # 保存音频文件
        filename = f"output_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        with open(filepath, "wb") as out:
            out.write(response.audio_content)
        
        return {
            "success": True,
            "audio_file": filename,
            "file_path": filepath,
            "phoneme_info": phoneme_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")

@app.get("/download-audio/{filename}")
async def download_audio(filename: str):
    """下载音频文件"""
    try:
        filepath = os.path.join(tempfile.gettempdir(), filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="audio/mpeg"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "text-to-speech-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 