# -*- coding: utf-8 -*-
# 本檔案為主控程式，整合 GPT 導師 + 搜尋補充 + 圖片分析 + 多人記憶管理 + 地圖/語音/卡片模組 + 安靜喚醒模式

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, AudioMessage, TextSendMessage

from utils import (
    extract_user_name, extract_ai_name, extract_user_style,
    extract_user_fact, is_clear_facts,
    is_image_request, is_video_request, is_transport_request,
    is_map_request
)
from gpt_handler import generate_gpt_reply
from image_generator import generate_image_message
from image_analyzer import analyze_image_with_gpt
from youtube_handler import search_youtube_card
from transport import get_thsr_schedule
from search_web import search_web_fallback

from extended_modules.map_handler import generate_map_image
from extended_modules.tts_handler import generate_tts_audio
from extended_modules.stt_handler import transcribe_audio_from_line
from extended_modules.flex_template import create_video_card

from collections import defaultdict, deque

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# ✅ 使用者資料快取，預設 ai_name 為 HC，並限制記憶最多 20 句
user_data = defaultdict(lambda: {
    "name": None,
    "ai_name": "HC",        # ✅ 預設名稱
    "style": "正式風",
    "history": deque(maxlen=20),
    "facts": []
})

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    memory = user_data[user_id]

    # --- 記憶控制區 ---
    if is_clear_facts(text):
        memory["facts"] = []
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🧹 已清除你的個人知識。"))
        return
    if (fact := extract_user_fact(text)):
        memory["facts"].append(fact)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"📌 已記住：「{fact}」"))
        return
    if (new_name := extract_user_name(text)):
        memory["name"] = new_name
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"好的，我會叫你 {new_name}！"))
        return
    if (new_ai_name := extract_ai_name(text)):
        memory["ai_name"] = new_ai_name
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"從現在起，我就叫 {new_ai_name} 囉！"))
        return
    if (new_style := extract_user_style(text)):
        memory["style"] = new_style
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"已切換為「{new_style}」風格。"))
        return

    ai_name = memory["ai_name"] or "HC"

    # ✅ 查詢 AI 名字
    if text in ["你叫什麼名字", "你是誰", "你的名字是？", "你現在叫什麼"]:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text=f"我叫做 {ai_name} 😄" if ai_name else "你還沒幫我取名字呢～"
        ))
        return

    # 🔇 安靜模式：若輸入未提到 AI 名稱則不處理
    if ai_name.lower() not in text.lower():
        return

    # 🗣️ 第一次提到 AI（或非命令式開場），給出提示與情感語句
    if memory["history"] == deque(maxlen=20):
        welcome = (
            f"嗨～你可以幫我改名喔，我就是你專屬的小助理了 ❤️\n"
            f"我會記住你說過的 20 句話～但我記憶力有限喔！\n"
            f"{ai_name} 不能陪妳太久真難過~~"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessag
