# -*- coding: utf-8 -*-
# 本檔案為指令解析模組，處理命名、風格切換、知識記憶等行為

import re

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
