# -*- coding: utf-8 -*-
# 本檔案為指令解析模組，處理命名、風格切換、知識記憶等行為

import re

def is_stylegen_request(text: str) -> bool:
    return "幫我生成" in text and "風格" in text

def is_translate_request(text):
    return text.startswith("翻譯 ")

def extract_user_name(text):
    """提取使用者自訂名稱"""
    match = re.match(r"(你)?要叫我[:：]?(.+)", text)
    return match.group(2).strip() if match else None

def extract_ai_name(text):
    """提取使用者給 AI 命名"""
    match = re.match(r"(你)?叫做[:：]?(.+)", text)
    return match.group(2).strip() if match else None

def extract_user_style(text):
    """提取風格切換"""
    match = re.match(r"(切換風格|風格)[:：]?(.+)", text)
    return match.group(2).strip() if match else None

def extract_user_fact(text):
    """提取使用者知識指令（記住：...）"""
    match = re.match(r"(記住|我想讓你知道)[:：]?(.+)", text)
    return match.group(2).strip() if match else None

def is_clear_facts(text):
    return text in ["清空知識", "忘掉我剛剛說的", "忘記知識", "重置記憶"]

def is_image_request(text):
    return any(keyword in text for keyword in ["畫", "生成圖片", "幫我畫", "想像圖"])

def is_video_request(text):
    return any(keyword in text for keyword in ["播放", "MV", "YouTube", "推薦影片", "影片"])

def is_transport_request(text):
    return any(keyword in text for keyword in ["高鐵", "台鐵", "航班", "班次", "車次"])

def is_map_request(text):
    """判斷是否為地圖查詢請求"""
    keywords = ["地圖", "在哪", "怎麼走", "地址", "地點", "map", "location"]
    return any(keyword in text.lower() for keyword in keywords)

def is_draw_request(text):
    return any(keyword in text for keyword in ["抽卡", "抽塔羅", "塔羅牌", "抽運勢", "今日運勢"])

def is_weather_request(text):
    return "天氣" in text
