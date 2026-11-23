import os
import httpx

API_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"

class JusoError(Exception):
    pass

class JusoClient:
    def __init__(self, key=None, client=None):
        self.key = key or os.environ.get("JUSO_API_KEY")
        if not self.key:
            raise ValueError("JUSO_API_KEY is required")
        self.client = client

    async def search(self, keyword: str, page: int = 1, count: int = 20):
        params = {"confmKey": self.key, "keyword": keyword,
                  "currentPage": page, "countPerPage": count,
                  "resultType": "json", "hstryYn": "Y"}
        if self.client is not None:
            response = await self.client.get(API_URL, params=params)
        else:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(API_URL, params=params)
        response.raise_for_status()
        payload = response.json()["results"]
        common = payload["common"]
        if str(common.get("errorCode")) != "0":
            raise JusoError(str(common.get("errorMessage", "Juso API error")))
        return {"total": int(common.get("totalCount", 0)),
                "candidates": payload.get("juso") or []}
