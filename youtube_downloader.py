# -*- coding: utf-8 -*-
# 本檔案負責處理 YouTube 影片與音訊連結擷取，僅回傳可下載的 direct URL（不下載、不儲存）

from linebot.models import TextSendMessage
from yt_dlp import YoutubeDL

def handle_youtube_download(event, line_bot_api, media_type="video"):
    text = event.message.text.strip()
    url = text.replace("下載影片", "").replace("下載音訊", "").replace("下載音樂", "").strip()

    if not url.startswith("http"):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請提供正確的 YouTube 連結網址。")
        )
        return

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forceurl': True,
    }

    if media_type == "audio":
        ydl_opts["format"] = "bestaudio/best"
    else:
        ydl_opts["format"] = "best[ext=mp4]"

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info["url"]
            title = info.get("title", "影片")

        reply_text = f"✅ 以下是 {title} 的 direct 下載連結：\n請用電腦瀏覽器下載另存：\n{download_url}"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

    except Exception as e:
        print("[YT Download Error]", e)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 抱歉，無法擷取該影片的下載連結。")
        )
