# -*- coding: utf-8 -*-
# 本檔案為主控程式，整合 GPT 導師 + 多模組 + 使用者命名記憶 + 翻譯 + YouTube 下載連結功能 + 地圖/抽卡/天氣 + 圖片風格生成

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, AudioMessage, TextSendMessage, ImageSendMessage

from utils import (
    extract_user_name, extract_ai_name, extract_user_style,
    extract_user_fact, is_clear_facts,
    is_image_request, is_video_request, is_transport_request,
    is_map_request, is_translate_request,
    is_draw_request, is_weather_request, is_stylegen_request
)
from gpt_handler import generate_gpt_reply
from image_generator import generate_image_message
from image_analyzer import analyze_image_with_gpt
from image_generator_style import generate_stylized_image
from youtube_handler import search_youtube_card
from youtube_downloader import handle_youtube_download
from transport import get_thsr_schedule
from search_web import search_web_fallback
from translate_handler import translate_text
from draw_handler import draw_fortune, draw_tarot, draw_custom
from weather_handler import get_weather_by_location

from extended_modules.map_handler import generate_map_image
from extended_modules.tts_handler import generate_tts_audio
from extended_modules.stt_handler import transcribe_audio_from_line

from collections import defaultdict, deque

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

user_data = defaultdict(lambda: {
    "name": None,
    "display_name": None,
    "ai_name": "HC",
    "style": "正式風",
    "history": deque(maxlen=20),
    "facts": [],
    "translate_pending": None
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

    try:
        profile = line_bot_api.get_profile(user_id)
        memory["display_name"] = profile.display_name
    except:
        pass

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

    # 翻譯處理
    if memory["translate_pending"]:
        original = memory["translate_pending"]
        target_lang = text.strip()
        translated = translate_text(original, target_lang)
        memory["translate_pending"] = None
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"翻譯成「{target_lang}」結果如下：\n{original} → {translated}")
        )
        return
    if is_translate_request(text):
        original_text = text.replace("翻譯", "").strip()
        memory["translate_pending"] = original_text
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="你想翻譯成哪一種語言呢？例如英文、日文、韓文、法文...")
        )
        return

    # YouTube 下載
    if text.startswith("下載影片"):
        handle_youtube_download(event, line_bot_api, media_type="video")
        return
    if text.startswith("下載音訊") or text.startswith("下載音樂"):
        handle_youtube_download(event, line_bot_api, media_type="audio")
        return

    # 名稱與歡迎語
    ai_name = memory["ai_name"] or "HC"
    user_name = memory["display_name"] or memory["name"] or "朋友"

    if text in ["你叫什麼名字", "你是誰", "你的名字是？", "你現在叫什麼"]:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"我叫做 {ai_name} 😄"))
        return

    if ai_name.lower() not in text.lower():
        return

    if memory["history"] == deque(maxlen=20):
        welcome = (
            f"嗨～你可以幫我改名喔，我就是你專屬的小助理了 ❤️\n"
            f"我會記住你說過的 20 句話～但我記憶力有限喔！\n"
            f"{ai_name} 不能陪妳太久真難過~~"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome))
        return

    # 模組邏輯
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
    if is_draw_request(text):
        if "運勢" in text:
            reply = draw_fortune()
        elif "塔羅" in text or "tarot" in text.lower():
            reply = draw_tarot()
        elif "自訂" in text and "抽" in text:
            pool = text.split("抽")[-1].strip().split("、")
            reply = draw_custom(pool)
        else:
            reply = "請指定要抽的類型，例如「抽運勢」、「抽塔羅」、「抽蘋果、香蕉、葡萄」"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    if is_map_request(text):
        reply = generate_map_image(text)
        line_bot_api.reply_message(event.reply_token, reply or TextSendMessage(text="❌ 找不到地圖，請確認地點或 API 金鑰設定"))
        return
    if is_weather_request(text):
        reply = get_weather_by_location(text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # GPT 回答
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
        reply += f"\n\n{search_web_fallback(text)}"

    memory["history"].append({"role": "user", "content": text})
    memory["history"].append({"role": "assistant", "content": reply})

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{user_name}～{reply}"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    memory = user_data[user_id]
    if not memory["ai_name"]:
        return

    message_id = event.message.id
    image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    text = getattr(event.message, "text", "")

    if is_stylegen_request(text) and memory["ai_name"].lower() in text.lower():
        style = text.replace("幫我生成", "").replace("風格", "").strip()
        styled_url = generate_stylized_image(image_url, style)
        if styled_url:
            line_bot_api.reply_message(
                event.reply_token,
                ImageSendMessage(original_content_url=styled_url, preview_image_url=styled_url)
            )
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 圖片風格生成失敗"))
        return

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
