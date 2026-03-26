"""
여론 분석 서비스 — FastAPI 웹 서버
실행: uvicorn main:app --reload --port 8000
접속: http://localhost:8000
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import json

from collector import collect_all
from analyzer import analyze

app = FastAPI(title="여론 분석 서비스")


# ── 대시보드 HTML (인라인) ─────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>여론 분석 서비스</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; color: #1a1a2e; }
  header { background: #16213e; color: #fff; padding: 20px 40px; display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 22px; font-weight: 700; }
  header span { font-size: 13px; opacity: 0.6; }
  .search-bar { background: #fff; padding: 24px 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .search-bar form { display: flex; gap: 12px; max-width: 600px; }
  .search-bar input {
    flex: 1; padding: 12px 18px; border: 2px solid #e0e0e0;
    border-radius: 8px; font-size: 16px; outline: none;
    transition: border-color .2s;
  }
  .search-bar input:focus { border-color: #3b82f6; }
  .search-bar button {
    padding: 12px 28px; background: #3b82f6; color: #fff;
    border: none; border-radius: 8px; font-size: 15px; font-weight: 600;
    cursor: pointer; transition: background .2s;
  }
  .search-bar button:hover { background: #2563eb; }
  .container { max-width: 1100px; margin: 32px auto; padding: 0 24px; }
  .loading { text-align: center; padding: 60px; font-size: 18px; color: #64748b; display: none; }
  .results { display: none; }

  /* 카드 그리드 */
  .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
  .card {
    background: #fff; border-radius: 12px; padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }
  .card .label { font-size: 13px; color: #64748b; margin-bottom: 8px; font-weight: 500; }
  .card .value { font-size: 32px; font-weight: 800; color: #1e293b; }
  .card .sub { font-size: 12px; color: #94a3b8; margin-top: 4px; }

  /* 2열 레이아웃 */
  .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
  .panel {
    background: #fff; border-radius: 12px; padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }
  .panel h3 { font-size: 15px; font-weight: 700; margin-bottom: 16px; color: #1e293b; }

  /* 감성 바 */
  .sentiment-bar { display: flex; height: 24px; border-radius: 12px; overflow: hidden; margin-bottom: 12px; }
  .sentiment-bar .pos { background: #22c55e; }
  .sentiment-bar .neg { background: #ef4444; }
  .sentiment-bar .neu { background: #94a3b8; }
  .sentiment-legend { display: flex; gap: 16px; font-size: 13px; }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; }

  /* 키워드 태그 */
  .keyword-cloud { display: flex; flex-wrap: wrap; gap: 8px; }
  .keyword-tag {
    padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;
    background: #eff6ff; color: #2563eb; cursor: default;
  }

  /* 트렌드 차트 */
  .trend-chart { width: 100%; height: 120px; position: relative; }
  canvas { width: 100% !important; }

  /* 최신 뉴스 */
  .news-list { list-style: none; }
  .news-list li {
    padding: 12px 0; border-bottom: 1px solid #f1f5f9;
    display: flex; flex-direction: column; gap: 4px;
  }
  .news-list li:last-child { border-bottom: none; }
  .news-list a { font-size: 14px; font-weight: 600; color: #1e40af; text-decoration: none; }
  .news-list a:hover { text-decoration: underline; }
  .news-list .desc { font-size: 12px; color: #64748b; }
  .news-list .date { font-size: 11px; color: #94a3b8; }

  /* 전체 너비 패널 */
  .full { margin-bottom: 24px; }

  .empty { text-align: center; padding: 80px 0; color: #94a3b8; }
  .empty .emoji { font-size: 48px; margin-bottom: 16px; }
  .empty p { font-size: 16px; }
</style>
</head>
<body>

<header>
  <h1>📊 여론 분석 서비스</h1>
  <span>네이버 뉴스 · 블로그 · 카페 · DataLab 기반</span>
</header>

<div class="search-bar">
  <form onsubmit="analyze(event)">
    <input type="text" id="candidateInput" placeholder="후보자 이름 입력 (예: 홍길동)" />
    <button type="submit">분석 시작</button>
  </form>
</div>

<div class="container">
  <div class="loading" id="loading">⏳ 데이터를 수집하고 분석 중입니다...</div>

  <div class="results" id="results">
    <div class="cards" id="mentionCards"></div>
    <div class="row2">
      <div class="panel" id="sentimentPanel">
        <h3>😊 감성 분석</h3>
        <div id="sentimentContent"></div>
      </div>
      <div class="panel" id="keywordPanel">
        <h3>🔑 연관 키워드 TOP 15</h3>
        <div id="keywordContent"></div>
      </div>
    </div>
    <div class="panel full" id="trendPanel">
      <h3>📈 검색량 트렌드 (최근 30일)</h3>
      <div id="trendContent"></div>
    </div>
    <div class="panel full" id="newsPanel">
      <h3>📰 최신 뉴스</h3>
      <ul class="news-list" id="newsList"></ul>
    </div>
  </div>

  <div class="empty" id="emptyState">
    <div class="emoji">🔍</div>
    <p>후보자 이름을 입력하면 여론 데이터를 분석해드립니다</p>
  </div>
</div>

<script>
async function analyze(e) {
  e.preventDefault();
  const name = document.getElementById('candidateInput').value.trim();
  if (!name) return;

  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('results').style.display = 'none';
  document.getElementById('loading').style.display = 'block';

  try {
    const res = await fetch('/analyze?candidate=' + encodeURIComponent(name));
    const data = await res.json();

    if (data.error) {
      alert('오류: ' + data.error);
      return;
    }

    renderResults(data);
    document.getElementById('results').style.display = 'block';
  } catch (err) {
    alert('서버 오류가 발생했습니다.');
    console.error(err);
  } finally {
    document.getElementById('loading').style.display = 'none';
  }
}

function renderResults(data) {
  const m = data.mention_count;
  document.getElementById('mentionCards').innerHTML = `
    <div class="card">
      <div class="label">총 언급량</div>
      <div class="value">${m.total.toLocaleString()}</div>
      <div class="sub">건</div>
    </div>
    <div class="card">
      <div class="label">📰 뉴스</div>
      <div class="value">${m.news.toLocaleString()}</div>
      <div class="sub">건</div>
    </div>
    <div class="card">
      <div class="label">✍️ 블로그</div>
      <div class="value">${m.blog.toLocaleString()}</div>
      <div class="sub">건</div>
    </div>
    <div class="card">
      <div class="label">☕ 카페</div>
      <div class="value">${m.cafe.toLocaleString()}</div>
      <div class="sub">건</div>
    </div>
  `;

  const s = data.sentiment_ratio;
  document.getElementById('sentimentContent').innerHTML = `
    <div class="sentiment-bar">
      <div class="pos" style="width:${s.positive}%"></div>
      <div class="neg" style="width:${s.negative}%"></div>
      <div class="neu" style="width:${s.neutral}%"></div>
    </div>
    <div class="sentiment-legend">
      <div class="legend-item"><div class="dot" style="background:#22c55e"></div> 긍정 ${s.positive}%</div>
      <div class="legend-item"><div class="dot" style="background:#ef4444"></div> 부정 ${s.negative}%</div>
      <div class="legend-item"><div class="dot" style="background:#94a3b8"></div> 중립 ${s.neutral}%</div>
    </div>
  `;

  const kwHtml = data.keywords.map(k =>
    `<span class="keyword-tag">${k.word} <small style="opacity:.6">${k.count}</small></span>`
  ).join('');
  document.getElementById('keywordContent').innerHTML = `<div class="keyword-cloud">${kwHtml}</div>`;

  if (data.trend && data.trend.length > 0) {
    renderTrendChart(data.trend);
  } else {
    document.getElementById('trendContent').innerHTML = '<p style="color:#94a3b8;font-size:13px">트렌드 데이터 없음</p>';
  }

  const newsHtml = data.recent_news.map(n => `
    <li>
      <a href="${n.link}" target="_blank">${n.title}</a>
      <span class="desc">${n.description}</span>
      <span class="date">${n.pubDate}</span>
    </li>
  `).join('');
  document.getElementById('newsList').innerHTML = newsHtml || '<li style="color:#94a3b8">뉴스 없음</li>';
}

function renderTrendChart(trendData) {
  const container = document.getElementById('trendContent');
  container.innerHTML = '<canvas id="trendCanvas" height="120"></canvas>';
  const canvas = document.getElementById('trendCanvas');
  const ctx = canvas.getContext('2d');

  canvas.width = container.offsetWidth || 600;
  canvas.height = 120;

  const values = trendData.map(d => d.ratio);
  const labels = trendData.map(d => d.date.slice(5)); // MM-DD
  const max = Math.max(...values) || 1;
  const w = canvas.width;
  const h = canvas.height;
  const pad = { l: 40, r: 10, t: 10, b: 30 };
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;
  const step = innerW / (values.length - 1 || 1);

  ctx.clearRect(0, 0, w, h);

  // 그리드 라인
  ctx.strokeStyle = '#f1f5f9';
  ctx.lineWidth = 1;
  [0, 0.5, 1].forEach(r => {
    const y = pad.t + innerH * (1 - r);
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
    ctx.fillStyle = '#94a3b8'; ctx.font = '10px sans-serif'; ctx.textAlign = 'right';
    ctx.fillText(Math.round(max * r), pad.l - 4, y + 4);
  });

  // 채우기
  const gradient = ctx.createLinearGradient(0, pad.t, 0, pad.t + innerH);
  gradient.addColorStop(0, 'rgba(59,130,246,0.3)');
  gradient.addColorStop(1, 'rgba(59,130,246,0)');

  ctx.beginPath();
  values.forEach((v, i) => {
    const x = pad.l + i * step;
    const y = pad.t + innerH * (1 - v / max);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.lineTo(pad.l + (values.length - 1) * step, pad.t + innerH);
  ctx.lineTo(pad.l, pad.t + innerH);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // 선
  ctx.beginPath();
  ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2;
  values.forEach((v, i) => {
    const x = pad.l + i * step;
    const y = pad.t + innerH * (1 - v / max);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();

  // x축 레이블 (7일 간격)
  ctx.fillStyle = '#94a3b8'; ctx.font = '10px sans-serif'; ctx.textAlign = 'center';
  labels.forEach((label, i) => {
    if (i % 7 === 0 || i === labels.length - 1) {
      const x = pad.l + i * step;
      ctx.fillText(label, x, h - 6);
    }
  });
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


@app.get("/analyze")
async def analyze_candidate(candidate: str):
    if not candidate or len(candidate.strip()) < 1:
        return {"error": "후보자 이름을 입력해주세요."}

    try:
        raw_data = collect_all(candidate.strip())
        result = analyze(raw_data)
        return result
    except Exception as e:
        return {"error": str(e)}
