"""
데이터 수집 모듈
- 네이버 Search API: 뉴스, 블로그, 카페
- 네이버 DataLab API: 검색어 트렌드
- YouTube Data API v3: 영상 검색 + 댓글
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

NAVER_HEADERS = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET,
}


# ── 네이버 Search API ─────────────────────────────────────────────────

def search_naver(query: str, source: str, display: int = 100) -> list[dict]:
    """source: news | blog | cafearticle"""
    url = f"https://openapi.naver.com/v1/search/{source}.json"
    params = {"query": query, "display": display, "start": 1, "sort": "date"}
    try:
        res = requests.get(url, headers=NAVER_HEADERS, params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get("items", [])
        for item in items:
            item["source_type"] = source
        return items
    except Exception as e:
        print(f"[{source}] 오류: {e}")
        return []


# ── 네이버 DataLab API ────────────────────────────────────────────────

def get_trend(keyword: str, period_days: int = 30) -> dict:
    """최근 N일간 일별 검색량 비율"""
    url = "https://openapi.naver.com/v1/datalab/search"
    end_date = datetime.today()
    start_date = end_date - timedelta(days=period_days)
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": "date",
        "keywordGroups": [{"groupName": keyword, "keywords": [keyword]}],
    }
    try:
        res = requests.post(
            url,
            headers={**NAVER_HEADERS, "Content-Type": "application/json"},
            json=body,
            timeout=10,
        )
        res.raise_for_status()
        results = res.json().get("results", [])
        if results:
            return {"keyword": keyword, "data": results[0].get("data", [])}
        return {"keyword": keyword, "data": []}
    except Exception as e:
        print(f"[DataLab] 오류: {e}")
        return {"keyword": keyword, "data": []}


# ── YouTube Data API v3 ───────────────────────────────────────────────

def search_youtube_videos(query: str, max_results: int = 10) -> list[dict]:
    """후보자 관련 유튜브 영상 검색"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance",
        "regionCode": "KR",
        "relevanceLanguage": "ko",
        "key": YOUTUBE_API_KEY,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get("items", [])
        videos = []
        for item in items:
            snippet = item.get("snippet", {})
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", "")[:10],
                "description": snippet.get("description", "")[:200],
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            })
        return videos
    except Exception as e:
        print(f"[YouTube 검색] 오류: {e}")
        return []


def get_youtube_comments(video_id: str, max_results: int = 100) -> list[dict]:
    """영상 댓글 수집"""
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": max_results,
        "order": "relevance",
        "key": YOUTUBE_API_KEY,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get("items", [])
        comments = []
        for item in items:
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": top.get("textDisplay", ""),
                "like_count": top.get("likeCount", 0),
                "published_at": top.get("publishedAt", "")[:10],
            })
        return comments
    except Exception as e:
        print(f"[YouTube 댓글 {video_id}] 오류: {e}")
        return []


def collect_youtube(query: str, video_limit: int = 5) -> dict:
    """유튜브 영상 + 댓글 통합 수집"""
    videos = search_youtube_videos(query, max_results=video_limit)
    all_comments = []
    for video in videos:
        comments = get_youtube_comments(video["video_id"], max_results=50)
        video["comments"] = comments
        all_comments.extend(comments)

    print(f"  유튜브: 영상 {len(videos)}개 / 댓글 {len(all_comments)}개")
    return {
        "videos": videos,
        "all_comments": all_comments,
        "video_count": len(videos),
        "comment_count": len(all_comments),
    }


# ── 전체 수집 ─────────────────────────────────────────────────────────

def collect_all(candidate_name: str) -> dict:
    print(f"[수집 시작] '{candidate_name}' 검색 중...")

    news = search_naver(candidate_name, "news", display=100)
    blogs = search_naver(candidate_name, "blog", display=50)
    cafes = search_naver(candidate_name, "cafearticle", display=50)
    trend = get_trend(candidate_name, period_days=30)
    youtube = collect_youtube(candidate_name, video_limit=5)

    print(f"  뉴스: {len(news)}건 / 블로그: {len(blogs)}건 / 카페: {len(cafes)}건")

    return {
        "candidate": candidate_name,
        "collected_at": datetime.now().isoformat(),
        "news": news,
        "blogs": blogs,
        "cafes": cafes,
        "trend": trend,
        "youtube": youtube,
    }
