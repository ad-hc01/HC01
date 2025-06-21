# -*- coding: utf-8 -*-
# 本檔案為語音輸出模組（TTS），將 GPT 回覆轉為語音檔並傳回 LINE 音訊訊息

import os
import openai
import tempfile
from linebot.models import AudioSendMessage

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_tts_audio(text, user_id):
    """
    將文字轉為語音，回傳 LINE 可用的 AudioSendMessage（使用 OpenAI TTS）
    """
    try:
        # 使用 OpenAI TTS 模型（支持 mp3 輸出）
        response = openai.audio.speech.create(
            model="tts-1",
            voice="nova",  # 可改為 alloy / echo / fable / onyx / shimmer
            input=text
        )

        # 儲存語音為 mp3 暫存檔
        tmp_path = f"/tmp/{user_id}_tts.mp3"
        with open(tmp_path, "wb") as f:
            f.write(response.content)

        file_url = upload_to_temp_url(tmp_path)  # 需實作檔案上傳 (CDN 或靜態公開路徑)

        return AudioSendMessage(
            original_content_url=file_url,
            duration=8000  # 可自動偵測長度（此為範例 8 秒）
        )
    except Exception as e:
        print(f"[TTS Error] {e}")
        return None

def upload_to_temp_url(filepath):
    """
    模擬上傳檔案到靜態網址，實務上應使用雲端儲存服務 (例如 Imgur / S3 / Render public file)
    """
    # FIXME: 請依你部署環境修改此上傳方式
    filename = os.path.basename(filepath)
    static_url = f"https://your-public-cdn.com/audio/{filename}"  # 假設你有公開資料夾
    return static_url
