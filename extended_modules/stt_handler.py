# -*- coding: utf-8 -*-
# 本檔案為語音輸入模組（STT），將 LINE 使用者語音訊息轉為文字並回傳給 GPT 使用

import os
import tempfile
import requests
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_audio_from_line(message_id, line_bot_api):
    """
    從 LINE 語音訊息下載音檔，送交 OpenAI Whisper 模型轉成文字
    :param message_id: LINE 的語音訊息 ID
    :param line_bot_api: 已初始化的 LINE Bot API 實例
    :return: str 辨識後的文字（若錯誤則回傳 None）
    """
    try:
        # 從 LINE 下載音檔（音訊格式為 m4a）
        audio_content = line_bot_api.get_message_content(message_id).content

        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_audio:
            temp_audio.write(audio_content)
            temp_audio.flush()

            # 使用 OpenAI Whisper 轉文字
            with open(temp_audio.name, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)

            return transcript["text"]
    except Exception as e:
        print(f"[STT Error] {e}")
        return None
