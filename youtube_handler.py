# -*- coding: utf-8 -*-
# 本檔案負責處理使用者的音樂、MV、影片搜尋需求，並用卡片方式在 LINE 中顯示 YouTube 結果。

from linebot.models import TemplateSendMessage, ButtonsTemplate, URITemplateAction
from urllib.parse import quote

def search_youtube_card(query: str) -> TemplateSendMessage:
    """
    接收影片名稱關鍵字 query，構造 YouTube 搜尋結果卡片（模擬版）。
    未使用 API key，使用第一筆預測網址與封面。
    """
    # 模擬搜尋網址與封面（實務可接 YouTube API）
    search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
    video_url = f"https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 模擬用影片
    thumbnail_url = "https://img.youtube.com/vi/dQw4w9WgXcQ/0.jpg"  # 示意封面圖

    return TemplateSendMessage(
        alt_text="這是你要的影片",
        template=ButtonsTemplate(
            thumbnail_image_url=thumbnail_url,
            title="找到的影片",
            text=f"與「{query}」相關的影片：",
            actions=[
                URITemplateAction(label="▶ 播放影片", uri=video_url)
            ]
        )
    )
