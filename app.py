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

    # 🗣️ 第一次提到 AI（歡迎提示）
    if memory["history"] == deque(maxlen=20):
        welcome = (
            f"嗨～你可以幫我改名喔，我就是你專屬的小助理了 ❤️\n"
            f"我會記住你說過的 20 句話～但我記憶力有限喔！\n"
            f"{ai_name} 不能陪妳太久真難過~~"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome))
        return

    # --- 功能判斷區 ---
    if is_image_request(text):
        reply = generate_image_message(text)
        line_bot_api.reply_message(event.reply_token, reply)
        return
    if is_video_request(text):
        reply = search_youtube_card(text)
        line_bot_api.reply_message(event.reply_token, reply)
        return
    if is_transport_request(text):
        reply = get_thsr_schedule()
        line_bot_api.reply_message(event.reply_token, reply)
        return
    if is_map_request(text):
        reply = generate_map_image(text)
        if reply:
            line_bot_api.reply_message(event.reply_token, reply)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 找不到地圖，請確認地點或 API 金鑰設定"))
        return

    # --- GPT 對話區 ---
    reply = generate_gpt_reply(
        user_id=user_id,
        user_msg=text,
        history=memory["history"],
        user_name=memory["name"],
        ai_name=memory["ai_name"],
        style=memory["style"],
        facts=memory["facts"]
    )

    if "我不知道" in reply or "無法提供" in reply:
        fallback = search_web_fallback(text)
        reply += f"\n\n{fallback}"

    memory["history"].append({"role": "user", "content": text})
    memory["history"].append({"role": "assistant", "content": reply})

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    memory = user_data[user_id]
    if not memory["ai_name"]:
        return
    message_id = event.message.id
    image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    reply = analyze_image_with_gpt(image_url, memory["name"], memory["ai_name"], memory["style"])
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):
    user_id = event.source.user_id
    memory = user_data[user_id]
    if not memory["ai_name"]:
        return
    message_id = event.message.id
    text = transcribe_audio_from_line(message_id, line_bot_api)
    if text:
        event.message.text = text
        handle_text(event)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
