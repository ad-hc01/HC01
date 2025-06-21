# -*- coding: utf-8 -*-
# 本檔案為地圖查詢模組，使用 Google Maps 靜態圖 API 回傳地圖圖片，供 LINE 使用者查詢地點或附近資訊

import os
import urllib.parse
from linebot.models import ImageSendMessage

# Google Maps 靜態圖 API base（注意須設 GOOGLE_MAPS_API_KEY）
GOOGLE_MAPS_STATIC_URL = "https://maps.googleapis.com/maps/api/staticmap"

def generate_map_image(query_text):
    """
    傳回 LINE 可用的 ImageSendMessage，根據地點名稱生成地圖圖片。
    query_text: 使用者輸入的地點關鍵詞
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return None  # 未設定 API 金鑰

    params = {
        "center": query_text,
        "zoom": 15,
        "size": "640x480",
        "maptype": "roadmap",
        "markers": f"color:red|label:X|{query_text}",
        "key": api_key
    }

    query_string = urllib.parse.urlencode(params)
    image_url = f"{GOOGLE_MAPS_STATIC_URL}?{query_string}"

    return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
