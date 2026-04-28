import requests
from typing import Optional

ITS_BASE_URL = "https://openapi.its.go.kr:9443"

class ITSApiService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_cctv_list(
            self,
            type: str = "ex",
            cctvType: str = "1",   # ← 추가 (1=HLS, 2=mp4, 4=HLS HTTPS, 5=mp4 HTTPS)
            min_x: float = 126.7,
            min_y: float = 37.4,
            max_x: float = 127.2,
            max_y: float = 37.7,
        ) -> list:
        """
        ITS CCTV 목록 조회
        Returns: { "response": { "data": [ { "cctvname", "cctvurl", "coordx", "coordy", ... } ] } }
        """
        url = f"{ITS_BASE_URL}/cctvInfo"
        params = {
            "apiKey": self.api_key,
            "type": type,
            "cctvType": "1",   # ← 추가! 1=실시간 HLS 스트리밍
            "minX": min_x,
            "minY": min_y,
            "maxX": max_x,
            "maxY": max_y,
            "getType": "json",
            # limit 제거 (공식 파라미터 아님)
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        raw_list = data.get("response", {}).get("data", [])

        return [
            {
                "name": item.get("cctvname", "이름없음"),
                "url":  item.get("cctvurl", ""),
                "lat":  item.get("coordy"),
                "lng":  item.get("coordx"),
                "road": item.get("roadsectionid", ""),
            }
            for item in raw_list
            if item.get("cctvurl")
        ]

    def get_cctv_stream_url(self, cctv_url: str) -> str:
        """
        cctvurl 그대로 반환 (HLS/RTSP URL)
        필요시 여기서 전처리 가능
        """
        return cctv_url