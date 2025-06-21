# -*- coding: utf-8 -*-
# 本檔案負責處理使用者圖片生成請求，透過 DALL·E 並將圖像直接傳至 LINE 視窗

import os
import openai
from linebot.models import ImageSendMessage, TextSendMessage

openai.api_key = os.getenv("OPENAI_API_KEY")

# 敏感詞過濾（簡化版）
SENSITIVE_KEYWORDS = ["裸體", "色情", "暴力", "血腥", "自殺", "仇恨"]

def is_sensitive(prompt):
    return any(kw in prompt for kw in SENSITIVE_KEYWORDS)

def handle_image_generation(event, line_bot_api, user_info):
    prompt = event.message.text.strip()
    user_id = event.source.user_id

    if is_sensitive(prompt):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="這類圖片無法提供，請嘗試其他主題～")
        )
        return

    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            response_format="url"
        )
        image_url = response.data[0].url

        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
        )
    except Exception as e:
        print(f"[Image Generation Error] {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="目前無法生成圖片，請稍後再試。")
        )
