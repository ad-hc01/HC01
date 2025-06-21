# -*- coding: utf-8 -*-
# 本檔案負責圖片分析功能，使用 GPT-4o 的多模態能力處理 LINE 傳來的圖片內容。

import openai

def analyze_image_with_gpt(image_url: str, user_name: str = None, ai_name: str = "AI", style: str = "正式風") -> str:
    """
    使用 GPT-4o Vision 分析圖片內容，並根據風格與命名回應。
    """
    try:
        system_prompt = "你是一位圖像分析導師，請幫助使用者詳細描述圖片內容，並提供延伸觀察。"
        style_prefix = {
            "可愛風": "嗨嗨～這是我看到的唷：",
            "正式風": "您好，這是您圖片的分析結果：",
            "搞笑風": "哇～這張圖也太有趣了吧，我來說說："
        }.get(style, "")

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "請分析這張圖片，說明內容並給予觀察建議"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
        )

        answer = response.choices[0].message.content.strip()

        if user_name:
            answer = f"{user_name}您好，我是{ai_name}。\n{style_prefix}{answer}"
        else:
            answer = f"{style_prefix}{answer}"

        return answer

    except Exception:
        return "這張圖片無法分析，可能格式錯誤或內容不清晰唷。"
