"""
여론 분석 모듈
- 언급량 집계 (네이버 + 유튜브)
- 긍/부정 감성 분석
- 연관 키워드 추출
"""

import re
from collections import Counter

POSITIVE_WORDS = [
    "지지", "응원", "훌륭", "탁월", "기대", "신뢰", "믿음", "최고", "잘한다",
    "좋다", "좋아", "훌륭하다", "성공", "업적", "공약", "실천", "추진", "개혁",
    "희망", "긍정", "강력", "능력", "전문", "경험", "리더십", "비전", "올바른",
    "공정", "정의", "투명", "청렴", "당선", "압도", "압승", "우세",
]

NEGATIVE_WORDS = [
    "반대", "비판", "실망", "우려", "문제", "논란", "의혹", "비리", "부패",
    "거짓", "실패", "무능", "낙선", "사퇴", "사과", "해명", "논쟁", "갈등",
    "불신", "위기", "추락", "불법", "탈세", "도덕", "막말", "혐오", "분열",
    "실언", "망언", "악화", "퇴행", "적폐", "역풍", "열세",
]

STOPWORDS = {
    "있다", "없다", "하다", "이다", "것이다", "되다", "이", "그", "저",
    "및", "또", "등", "또한", "그리고", "하지만", "그러나", "그래서",
    "기자", "뉴스", "기사", "제공", "저작권", "무단", "전재", "배포", "금지",
    "nbsp", "quot", "amp", "lt", "gt",
}


def clean_text(html_text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = re.sub(r"[^\w\s가-힣]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(texts: list[str], top_n: int = 20) -> list[dict]:
    all_words = []
    for text in texts:
        cleaned = clean_text(text)
        words = re.findall(r"[가-힣]{2,6}", cleaned)
        all_words.extend([w for w in words if w not in STOPWORDS])
    counter = Counter(all_words)
    return [{"word": w, "count": c} for w, c in counter.most_common(top_n)]


def score_sentiment(text: str) -> str:
    cleaned = clean_text(text)
    pos = sum(1 for w in POSITIVE_WORDS if w in cleaned)
    neg = sum(1 for w in NEGATIVE_WORDS if w in cleaned)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    else:
        return "neutral"


def analyze(raw_data: dict) -> dict:
    candidate = raw_data["candidate"]
    news = raw_data.get("news", [])
    blogs = raw_data.get("blogs", [])
    cafes = raw_data.get("cafes", [])
    trend = raw_data.get("trend", {})
    youtube = raw_data.get("youtube", {})

    all_naver = news + blogs + cafes
    yt_comments = youtube.get("all_comments", [])

    # ── 1. 언급량 ────────────────────────────────────────────────────
    mention_count = {
        "news": len(news),
        "blog": len(blogs),
        "cafe": len(cafes),
        "youtube_video": youtube.get("video_count", 0),
        "youtube_comment": youtube.get("comment_count", 0),
        "total": len(all_naver) + youtube.get("comment_count", 0),
    }

    # ── 2. 감성 분석 (네이버 + 유튜브 댓글 통합) ─────────────────────
    sentiment_counts = Counter()

    for item in all_naver:
        text = item.get("title", "") + " " + item.get("description", "")
        sentiment_counts[score_sentiment(text)] += 1

    for comment in yt_comments:
        sentiment_counts[score_sentiment(comment.get("text", ""))] += 1

    total = sum(sentiment_counts.values()) or 1
    sentiment_ratio = {
        "positive": round(sentiment_counts["positive"] / total * 100, 1),
        "negative": round(sentiment_counts["negative"] / total * 100, 1),
        "neutral": round(sentiment_counts["neutral"] / total * 100, 1),
    }

    # ── 3. 연관 키워드 (네이버 + 유튜브 댓글) ────────────────────────
    texts = []
    for item in all_naver:
        texts.append(item.get("title", "") + " " + item.get("description", ""))
    for comment in yt_comments:
        texts.append(comment.get("text", ""))

    keywords = extract_keywords(texts, top_n=20)
    keywords = [k for k in keywords if candidate not in k["word"]][:15]

    # ── 4. 트렌드 ────────────────────────────────────────────────────
    trend_data = [
        {"date": d["period"], "ratio": d["ratio"]}
        for d in trend.get("data", [])
    ]

    # ── 5. 최신 뉴스 5건 ──────────────────────────────────────────────
    recent_news = [
        {
            "title": clean_text(item.get("title", "")),
            "link": item.get("link", ""),
            "pubDate": item.get("pubDate", ""),
            "description": clean_text(item.get("description", ""))[:100],
        }
        for item in news[:5]
    ]

    # ── 6. 유튜브 영상 (썸네일 포함) ─────────────────────────────────
    yt_videos = [
        {
            "title": v.get("title", ""),
            "channel": v.get("channel", ""),
            "published_at": v.get("published_at", ""),
            "url": v.get("url", ""),
            "thumbnail": v.get("thumbnail", ""),
            "comment_count": len(v.get("comments", [])),
        }
        for v in youtube.get("videos", [])
    ]

    # ── 7. 유튜브 인기 댓글 TOP 5 ────────────────────────────────────
    all_comments_sorted = sorted(
        yt_comments, key=lambda x: x.get("like_count", 0), reverse=True
    )
    top_comments = [
        {
            "text": clean_text(c.get("text", ""))[:120],
            "like_count": c.get("like_count", 0),
            "sentiment": score_sentiment(c.get("text", "")),
        }
        for c in all_comments_sorted[:5]
    ]

    return {
        "candidate": candidate,
        "collected_at": raw_data.get("collected_at", ""),
        "mention_count": mention_count,
        "sentiment_ratio": sentiment_ratio,
        "keywords": keywords,
        "trend": trend_data,
        "recent_news": recent_news,
        "youtube_videos": yt_videos,
        "top_comments": top_comments,
    }
