"""
맞춤형 공약 자동생성기 — GPT API 연동 모듈

흐름:
  1. 여론 분석 데이터(opinion_data) 수신
  2. 키워드·뉴스·댓글 기반으로 이슈 우선순위 산정 (심각성·확산성·시급성)
  3. 상위 3개 이슈에 대해 5W1H 공약 + 네이밍/슬로건 + 스토리텔링 생성
"""

import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_pledges(opinion_data: dict, region: str = "", persona: str = "전체 유권자") -> dict:
    candidate = opinion_data.get("candidate", "후보자")
    keywords = [k["word"] for k in opinion_data.get("keywords", [])[:12]]
    sentiment = opinion_data.get("sentiment_ratio", {})
    news_titles = [n["title"] for n in opinion_data.get("recent_news", [])]
    comments = [c["text"] for c in opinion_data.get("top_comments", [])]
    mention = opinion_data.get("mention_count", {})

    region_text = f"지역구: {region}" if region else "지역구: 미입력 (전국/일반)"

    news_str = "\n".join(f"  - {t}" for t in news_titles) if news_titles else "  - 없음"
    comment_str = "\n".join(f"  - {c}" for c in comments) if comments else "  - 없음"

    prompt = f"""당신은 대한민국 선거 전략 전문가입니다.
아래 여론 분석 데이터를 바탕으로 **{candidate}** 후보의 맞춤형 공약을 생성해주세요.

---
## 여론 분석 데이터
- 후보자: {candidate}
- {region_text}
- 타겟 유권자: {persona}
- 총 언급량: {mention.get("total", 0)}건 (뉴스 {mention.get("news", 0)} / 블로그 {mention.get("blog", 0)} / 카페 {mention.get("cafe", 0)} / YT댓글 {mention.get("youtube_comment", 0)})
- 감성 분석: 긍정 {sentiment.get("positive", 0)}% / 부정 {sentiment.get("negative", 0)}% / 중립 {sentiment.get("neutral", 0)}%
- 연관 키워드 TOP 12: {", ".join(keywords)}
- 최신 뉴스 헤드라인:
{news_str}
- YouTube 인기 댓글:
{comment_str}

---
## 지시사항
1. 위 데이터에서 유권자가 실제로 관심 갖는 **이슈 3개**를 식별하세요.
2. 각 이슈를 **심각성(1-10)·확산성(1-10)·시급성(1-10)**으로 평가하세요.
3. 각 이슈에 대해 **구체적인 공약**을 다음 형식으로 작성하세요:
   - 5W1H: Who(누가) / What(무엇을) / When(언제까지) / Where(어디서) / Why(왜) / How(어떻게)
   - 공약 네이밍: 짧고 인상적인 이름 (15자 이내)
   - 슬로건: 핵심 메시지 (10자 이내)
   - 스토리텔링: {persona} 관점에서 감성적으로 작성한 2-3문단 초안

아래 JSON 형식으로만 응답하세요 (JSON 외 텍스트 금지):
{{
  "summary": "전체 여론 분석 요약 2-3문장",
  "priority_issues": [
    {{
      "issue": "이슈명",
      "score": {{
        "severity": 8,
        "spread": 7,
        "urgency": 9,
        "total": 24
      }},
      "evidence": ["근거가 된 키워드나 뉴스/댓글 내용 2-3개"],
      "pledge": {{
        "5w1h": {{
          "who": "누가 (주체)",
          "what": "무엇을 (정책 내용)",
          "when": "언제까지 (기한)",
          "where": "어디서 (대상 지역/범위)",
          "why": "왜 (필요성/목적)",
          "how": "어떻게 (구체적 방법)"
        }},
        "naming": "공약 이름",
        "slogan": "슬로건",
        "storytelling": "스토리텔링 초안 (2-3문단)"
      }}
    }}
  ]
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=3000,
    )

    return json.loads(response.choices[0].message.content)
