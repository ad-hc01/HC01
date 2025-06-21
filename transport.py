# -*- coding: utf-8 -*-
# 本檔案負責查詢 PTX 運輸資料（高鐵、台鐵、航班），並以 LINE 卡片方式顯示結果。

import os
import requests
import datetime
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, URITemplateAction

# 從環境變數讀取 PTX App ID / Key
TDX_APP_ID = os.getenv("TDX_APP_ID")
TDX_APP_KEY = os.getenv("TDX_APP_KEY")


def get_tdx_headers():
    """
    回傳 PTX API 所需標頭（含 AppID/Key）
    """
    return {
        "accept": "application/json",
        "x-ptx-app-id": TDX_APP_ID,
        "x-ptx-app-key": TDX_APP_KEY
    }


def get_thsr_schedule(origin="Taipei", destination="Taichung", date=None):
    """
    查詢高鐵班次（PTX API 實作版）目前支援台灣站名英文。
    回傳 LINE CarouselTemplate 格式。
    """
    try:
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d")

        url = (
            f"https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/DailyTimetable/OD/"
            f"{origin}/to/{destination}/{date}?$format=JSON"
        )
        response = requests.get(url, headers=get_tdx_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return TemplateSendMessage(
                alt_text="目前查無高鐵班次",
                template=CarouselTemplate(columns=[
                    CarouselColumn(
                        thumbnail_image_url="https://www.thsrc.com.tw/Content/Images/logo.png",
                        title="查無資料",
                        text="今天沒有查到班次，請稍後再試。",
                        actions=[URITemplateAction(label="前往高鐵官網", uri="https://www.thsrc.com.tw")]
                    )
                ])
            )

        # 取前 5 筆班次
        columns = []
        for entry in data[:5]:
            train_no = entry["DailyTrainInfo"]["TrainNo"]
            dep_time = entry["OriginStopTime"]["DepartureTime"]
            arr_time = entry["DestinationStopTime"]["ArrivalTime"]

            columns.append(CarouselColumn(
                thumbnail_image_url="https://www.thsrc.com.tw/Content/Images/logo.png",
                title=f"高鐵班次 {train_no}",
                text=f"{origin} 出發：{dep_time}\n{destination} 抵達：{arr_time}",
                actions=[URITemplateAction(label="查看高鐵時刻", uri="https://www.thsrc.com.tw")]
            ))

        return TemplateSendMessage(
            alt_text="高鐵班次查詢結果",
            template=CarouselTemplate(columns=columns)
        )

    except Exception as e:
        print(f"[PTX ERROR] {e}")
        return TemplateSendMessage(
            alt_text="查詢失敗",
            template=CarouselTemplate(columns=[
                CarouselColumn(
                    thumbnail_image_url="https://www.thsrc.com.tw/Content/Images/logo.png",
                    title="查詢失敗",
                    text="無法查詢高鐵資訊，請稍後再試。",
                    actions=[URITemplateAction(label="高鐵官網", uri="https://www.thsrc.com.tw")]
                )
            ])
        )
