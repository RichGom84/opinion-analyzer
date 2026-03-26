"""
네이버 API 데이터 수집 모듈
- Search API: 뉴스, 블로그, 카페
- DataLab API: 검색어 트렌드
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

HEADERS = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET,
}


def search_naver(query: str, source: str, display: int = 100) -> list[dict]:
    """
    네이버 검색 API 호출
    source: news | blog | cafearticle
    """
    url = f"https://openapi.naver.com/v1/search/{source}.json"
    params = {
        "query": query,
        "display": display,
        "start": 1,
        "sort": "date",  # 최신순
    }

    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get("items", [])
        # 출처 태깅
        for item in items:
            item["source_type"] = source
        return items
    except Exception as e:
        print(f"[{source}] 검색 오류: {e}")
        return []


def get_trend(keyword: str, period_days: int = 30) -> dict:
    """
    네이버 DataLab 검색어 트렌드 API 호출
    최근 N일간 일별 검색량 비율 반환
    """
    url = "https://openapi.naver.com/v1/datalab/search"

    end_date = datetime.today()
    start_date = end_date - timedelta(days=period_days)

    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": "date",  # 일별
        "keywordGroups": [
            {
                "groupName": keyword,
                "keywords": [keyword],
            }
        ],
    }

    try:
        res = requests.post(
            url,
            headers={**HEADERS, "Content-Type": "application/json"},
            json=body,
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()
        results = data.get("results", [])
        if results:
            return {
                "keyword": keyword,
                "data": results[0].get("data", []),  # [{period, ratio}]
            }
        return {"keyword": keyword, "data": []}
    except Exception as e:
        print(f"[DataLab] 트렌드 오류: {e}")
        return {"keyword": keyword, "data": []}


def collect_all(candidate_name: str) -> dict:
    """
    후보자 이름으로 전체 데이터 수집
    """
    print(f"[수집 시작] '{candidate_name}' 검색 중...")

    news = search_naver(candidate_name, "news", display=100)
    blogs = search_naver(candidate_name, "blog", display=50)
    cafes = search_naver(candidate_name, "cafearticle", display=50)
    trend = get_trend(candidate_name, period_days=30)

    print(f"  뉴스: {len(news)}건 / 블로그: {len(blogs)}건 / 카페: {len(cafes)}건")

    return {
        "candidate": candidate_name,
        "collected_at": datetime.now().isoformat(),
        "news": news,
        "blogs": blogs,
        "cafes": cafes,
        "trend": trend,
    }
