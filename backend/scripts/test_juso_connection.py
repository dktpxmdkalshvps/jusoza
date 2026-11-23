"""Juso official address-search API connection smoke test.

Usage:
  pip install httpx
  set JUSO_API_KEY=YOUR_KEY           # Windows CMD
  python scripts/test_juso_connection.py --address "서울특별시 종로구 세종대로 209"
"""
import argparse
import json
import os
import sys
import time

import httpx

URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"


def probe(address: str, timeout: float) -> int:
    key = os.environ.get("JUSO_API_KEY", "").strip()
    if not key:
        print("CONFIG_ERROR: JUSO_API_KEY 환경변수가 비어 있습니다.")
        return 2

    params = {
        "confmKey": key,
        "currentPage": 1,
        "countPerPage": 5,
        "keyword": address,
        "resultType": "json",
    }
    print(f"조회 주소: {address}")
    print(f"요청 URL: {URL} (승인키 비공개)")
    start = time.perf_counter()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            response = client.get(URL, params=params)
    except httpx.ConnectTimeout:
        print("CONNECT_TIMEOUT: 서버 연결 제한시간 초과. 네트워크/방화벽을 확인하세요.")
        return 3
    except httpx.ReadTimeout:
        print("READ_TIMEOUT: 연결 후 응답 지연. 잠시 후 재시도하세요.")
        return 3
    except httpx.ConnectError as exc:
        print(f"CONNECT_ERROR: DNS/TLS/프록시/방화벽 문제 가능성 ({type(exc).__name__})")
        return 3
    except httpx.RequestError as exc:
        print(f"NETWORK_ERROR: {type(exc).__name__}")
        return 3

    print(f"HTTP 상태: {response.status_code}")
    print(f"응답 시간: {time.perf_counter() - start:.2f}초")
    if response.status_code != 200:
        print("HTTP_ERROR: 429=호출 제한, 5xx=서버/게이트웨이 장애 가능성.")
        return 4
    try:
        payload = response.json()
        results = payload["results"]
        common = results["common"]
    except (ValueError, KeyError, TypeError):
        print("FORMAT_ERROR: JSON 응답 또는 results.common 구조를 확인할 수 없습니다.")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        return 5

    error_code = str(common.get("errorCode", ""))
    print(f"API 오류 코드: {error_code}")
    if error_code != "0":
        print(f"API_ERROR: {common.get('errorMessage', '상세 메시지 없음')}")
        print("승인키 종류/사용 가능 여부 및 검색어를 확인하세요.")
        return 6

    candidates = results.get("juso") or []
    print(f"총 검색 건수: {common.get('totalCount', 'unknown')}")
    print(f"현재 페이지 결과: {len(candidates)}건")
    for i, item in enumerate(candidates, 1):
        print(json.dumps({
            "순번": i,
            "도로명주소": item.get("roadAddrPart1") or item.get("roadAddr"),
            "지번주소": item.get("jibunAddr"),
            "우편번호": item.get("zipNo"),
            "건물관리번호": item.get("bdMgtSn"),
        }, ensure_ascii=False, indent=2))
    print("SUCCESS: 행안부 주소 검색 API 호출 및 응답 파싱 성공")
    if not candidates:
        print("참고: API 연결은 정상이나 해당 검색어로 조회된 주소는 없습니다.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="행안부 도로명주소 API 연결 진단")
    parser.add_argument("--address", default="서울특별시 종로구 세종대로 209")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    if not args.address.strip() or args.timeout <= 0:
        parser.error("주소와 양수 timeout이 필요합니다.")
    return probe(args.address.strip(), args.timeout)


if __name__ == "__main__":
    sys.exit(main())
