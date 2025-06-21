# -*- coding: utf-8 -*-
# 本檔案負責查詢即時天氣資訊，來自 OpenWeatherMap API，若無金鑰則顯示預設訊息

import os
import requests

def get_weather_by_location(text: str) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "🌦️ 天氣查詢功能還在努力中～稍後就能使用囉！"

    location = text.replace("天氣", "").replace("的", "").strip()

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&lang=zh_tw&units=metric"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            return f"❌ 找不到 {location} 的天氣資訊"

        name = data["name"]
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]

        return f"📍 {name} 現在天氣：{desc}，氣溫 {temp}°C，濕度 {humidity}%"

    except Exception:
        return "⚠️ 天氣查詢失敗，請稍後再試或確認地點是否正確"
