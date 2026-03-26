"""
여론 분석 서비스 — FastAPI 웹 서버
실행: uvicorn main:app --reload --port 8000
접속: http://localhost:8000
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from collector import collect_all
from analyzer import analyze
from pledge_generator import generate_pledges

app = FastAPI(title="여론 분석 서비스")


class PledgeRequest(BaseModel):
    candidate: str
    region: str = ""
    persona: str = "전체 유권자"

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
    border-radius: 8px; font-size: 16px; outline: none; transition: border-color .2s;
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
  .cards { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 24px; }
  .card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
  .card .label { font-size: 12px; color: #64748b; margin-bottom: 6px; font-weight: 500; }
  .card .value { font-size: 28px; font-weight: 800; color: #1e293b; }
  .card .sub { font-size: 11px; color: #94a3b8; margin-top: 2px; }
  .card.yt { background: #fff8f8; }

  /* 2열 */
  .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
  .panel { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
  .panel h3 { font-size: 15px; font-weight: 700; margin-bottom: 16px; color: #1e293b; }

  /* 감성 바 */
  .sentiment-bar { display: flex; height: 24px; border-radius: 12px; overflow: hidden; margin-bottom: 12px; }
  .sentiment-bar .pos { background: #22c55e; }
  .sentiment-bar .neg { background: #ef4444; }
  .sentiment-bar .neu { background: #94a3b8; }
  .sentiment-legend { display: flex; gap: 16px; font-size: 13px; }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; }

  /* 키워드 */
  .keyword-cloud { display: flex; flex-wrap: wrap; gap: 8px; }
  .keyword-tag { padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; background: #eff6ff; color: #2563eb; }

  /* 트렌드 */
  .full { margin-bottom: 24px; }

  /* 뉴스 */
  .news-list { list-style: none; }
  .news-list li { padding: 12px 0; border-bottom: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 4px; }
  .news-list li:last-child { border-bottom: none; }
  .news-list a { font-size: 14px; font-weight: 600; color: #1e40af; text-decoration: none; }
  .news-list a:hover { text-decoration: underline; }
  .news-list .desc { font-size: 12px; color: #64748b; }
  .news-list .date { font-size: 11px; color: #94a3b8; }

  /* 유튜브 영상 그리드 */
  .yt-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
  .yt-card { border-radius: 8px; overflow: hidden; background: #f8fafc; }
  .yt-card img { width: 100%; aspect-ratio: 16/9; object-fit: cover; }
  .yt-card .yt-info { padding: 10px; }
  .yt-card .yt-title { font-size: 12px; font-weight: 600; color: #1e293b; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .yt-card .yt-channel { font-size: 11px; color: #64748b; }
  .yt-card .yt-meta { font-size: 11px; color: #94a3b8; margin-top: 4px; }
  .yt-card a { text-decoration: none; }

  /* 유튜브 댓글 */
  .comment-list { list-style: none; }
  .comment-list li { padding: 12px; border-radius: 8px; background: #f8fafc; margin-bottom: 8px; }
  .comment-list .c-text { font-size: 13px; color: #1e293b; margin-bottom: 6px; line-height: 1.5; }
  .comment-list .c-meta { display: flex; gap: 12px; font-size: 11px; color: #94a3b8; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
  .badge.pos { background: #dcfce7; color: #16a34a; }
  .badge.neg { background: #fee2e2; color: #dc2626; }
  .badge.neu { background: #f1f5f9; color: #64748b; }

  .empty { text-align: center; padding: 80px 0; color: #94a3b8; }
  .empty .emoji { font-size: 48px; margin-bottom: 16px; }

  /* 푸터 */
  footer {
    background: #16213e; color: #fff;
    padding: 40px;
    margin-top: 48px;
  }
  .footer-inner {
    max-width: 1100px; margin: 0 auto;
    display: flex; justify-content: space-between; align-items: center;
    gap: 24px; flex-wrap: wrap;
  }
  .footer-info .name {
    font-size: 18px; font-weight: 700; margin-bottom: 4px;
  }
  .footer-info .role {
    font-size: 13px; opacity: 0.6; margin-bottom: 12px;
  }
  .footer-info .email a {
    font-size: 13px; color: #93c5fd; text-decoration: none;
  }
  .footer-info .email a:hover { text-decoration: underline; }
  .footer-links {
    display: flex; gap: 12px; flex-wrap: wrap;
  }
  .footer-links a {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 18px; border-radius: 8px;
    font-size: 13px; font-weight: 600; text-decoration: none;
    transition: opacity .2s;
  }
  .footer-links a:hover { opacity: 0.85; }
  .footer-links .btn-yt   { background: #ff0000; color: #fff; }
  .footer-links .btn-home { background: #3b82f6; color: #fff; }
  .footer-links .btn-ai   { background: #7c3aed; color: #fff; }
  .footer-copy {
    max-width: 1100px; margin: 24px auto 0;
    font-size: 11px; opacity: 0.35; text-align: center;
  }
</style>
</head>
<body>

<header>
  <h1>📊 여론 분석 서비스</h1>
  <span>네이버 뉴스·블로그·카페·DataLab + YouTube 기반</span>
</header>

<div class="search-bar">
  <form onsubmit="analyze(event)">
    <input type="text" id="candidateInput" placeholder="후보자 이름 입력 (예: 홍길동)" />
    <button type="submit">분석 시작</button>
  </form>
</div>

<div class="container">
  <div class="loading" id="loading">⏳ 네이버 + YouTube 데이터를 수집하고 분석 중입니다...</div>

  <div class="results" id="results">
    <div class="cards" id="mentionCards"></div>
    <div class="row2">
      <div class="panel">
        <h3>😊 감성 분석</h3>
        <div id="sentimentContent"></div>
      </div>
      <div class="panel">
        <h3>🔑 연관 키워드 TOP 15</h3>
        <div id="keywordContent"></div>
      </div>
    </div>
    <div class="panel full">
      <h3>📈 검색량 트렌드 (최근 30일)</h3>
      <div id="trendContent"></div>
    </div>
    <div class="row2">
      <div class="panel">
        <h3>📰 최신 뉴스</h3>
        <ul class="news-list" id="newsList"></ul>
      </div>
      <div class="panel">
        <h3>💬 YouTube 인기 댓글 TOP 5</h3>
        <ul class="comment-list" id="commentList"></ul>
      </div>
    </div>
    <div class="panel full">
      <h3>▶️ YouTube 관련 영상</h3>
      <div class="yt-grid" id="ytGrid"></div>
    </div>
    <div id="pledgeBanner" style="display:none;margin-bottom:24px;"></div>
  </div>

  <div class="empty" id="emptyState">
    <div class="emoji">🔍</div>
    <p>후보자 이름을 입력하면 여론 데이터를 분석해드립니다</p>
  </div>
</div>

</div><!-- /container -->

<footer>
  <div class="footer-inner">
    <div class="footer-info">
      <div class="name">권혁용 연구위원</div>
      <div class="role">AI선거전략연구소 연구위원</div>
      <div class="email">✉️ <a href="mailto:hukyoung84@naver.com">hukyoung84@naver.com</a></div>
    </div>
    <div class="footer-links">
      <a href="https://www.youtube.com/@KwonT_AI" target="_blank" class="btn-yt">
        ▶ YouTube
      </a>
      <a href="https://litt.ly/levelupai" target="_blank" class="btn-home">
        🏠 홈페이지
      </a>
      <a href="https://win-ai.kr/" target="_blank" class="btn-ai">
        🏆 AI선거전략연구소
      </a>
    </div>
  </div>
  <div class="footer-copy">© 2026 권혁용 연구위원 · 여론 분석 서비스 · AI선거전략연구소</div>
</footer>

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
    if (data.error) { alert('오류: ' + data.error); return; }
    renderResults(data);
    document.getElementById('results').style.display = 'block';
  } catch (err) {
    alert('서버 오류가 발생했습니다.');
  } finally {
    document.getElementById('loading').style.display = 'none';
  }
}

function renderResults(data) {
  const m = data.mention_count;
  document.getElementById('mentionCards').innerHTML = `
    <div class="card"><div class="label">총 언급량</div><div class="value">${m.total.toLocaleString()}</div><div class="sub">건</div></div>
    <div class="card"><div class="label">📰 뉴스</div><div class="value">${m.news.toLocaleString()}</div><div class="sub">건</div></div>
    <div class="card"><div class="label">✍️ 블로그</div><div class="value">${m.blog.toLocaleString()}</div><div class="sub">건</div></div>
    <div class="card"><div class="label">☕ 카페</div><div class="value">${m.cafe.toLocaleString()}</div><div class="sub">건</div></div>
    <div class="card yt"><div class="label">▶️ YT 영상</div><div class="value">${m.youtube_video}</div><div class="sub">개</div></div>
    <div class="card yt"><div class="label">💬 YT 댓글</div><div class="value">${m.youtube_comment.toLocaleString()}</div><div class="sub">개</div></div>
  `;

  const s = data.sentiment_ratio;
  document.getElementById('sentimentContent').innerHTML = `
    <div class="sentiment-bar">
      <div class="pos" style="width:${s.positive}%"></div>
      <div class="neg" style="width:${s.negative}%"></div>
      <div class="neu" style="width:${s.neutral}%"></div>
    </div>
    <div class="sentiment-legend">
      <div class="legend-item"><div class="dot" style="background:#22c55e"></div>긍정 ${s.positive}%</div>
      <div class="legend-item"><div class="dot" style="background:#ef4444"></div>부정 ${s.negative}%</div>
      <div class="legend-item"><div class="dot" style="background:#94a3b8"></div>중립 ${s.neutral}%</div>
    </div>
  `;

  document.getElementById('keywordContent').innerHTML = `
    <div class="keyword-cloud">
      ${data.keywords.map(k => `<span class="keyword-tag">${k.word} <small style="opacity:.6">${k.count}</small></span>`).join('')}
    </div>`;

  if (data.trend && data.trend.length > 0) renderTrendChart(data.trend);
  else document.getElementById('trendContent').innerHTML = '<p style="color:#94a3b8;font-size:13px">트렌드 데이터 없음</p>';

  document.getElementById('newsList').innerHTML = data.recent_news.map(n => `
    <li>
      <a href="${n.link}" target="_blank">${n.title}</a>
      <span class="desc">${n.description}</span>
      <span class="date">${n.pubDate}</span>
    </li>`).join('') || '<li style="color:#94a3b8">뉴스 없음</li>';

  const sentimentBadge = s => {
    if (s === 'positive') return '<span class="badge pos">긍정</span>';
    if (s === 'negative') return '<span class="badge neg">부정</span>';
    return '<span class="badge neu">중립</span>';
  };

  document.getElementById('commentList').innerHTML = data.top_comments.length
    ? data.top_comments.map(c => `
      <li>
        <div class="c-text">${c.text}</div>
        <div class="c-meta">
          ${sentimentBadge(c.sentiment)}
          <span>👍 ${c.like_count.toLocaleString()}</span>
        </div>
      </li>`).join('')
    : '<li style="color:#94a3b8;font-size:13px">댓글 없음</li>';

  document.getElementById('ytGrid').innerHTML = data.youtube_videos.length
    ? data.youtube_videos.map(v => `
      <div class="yt-card">
        <a href="${v.url}" target="_blank">
          <img src="${v.thumbnail}" alt="${v.title}" onerror="this.style.display='none'">
          <div class="yt-info">
            <div class="yt-title">${v.title}</div>
            <div class="yt-channel">${v.channel}</div>
            <div class="yt-meta">💬 ${v.comment_count}개 · ${v.published_at}</div>
          </div>
        </a>
      </div>`).join('')
    : '<p style="color:#94a3b8;font-size:13px">영상 없음</p>';

  // 공약 생성기 연결 버튼
  const name = document.getElementById('candidateInput').value.trim();
  const pledgeBanner = document.getElementById('pledgeBanner');
  pledgeBanner.innerHTML = `
    <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:16px;padding:28px 32px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;">
      <div>
        <div style="color:#fff;font-size:18px;font-weight:700;margin-bottom:6px;">🗳️ 이 여론 데이터로 맞춤형 공약을 만들어보세요</div>
        <div style="color:rgba(255,255,255,0.8);font-size:14px;">GPT가 심각성·확산성·시급성 기준으로 최우선 이슈 3가지와 5W1H 공약·슬로건·스토리텔링을 자동 생성합니다</div>
      </div>
      <a href="/pledge?candidate=${encodeURIComponent(name)}" style="background:#fff;color:#6366f1;padding:13px 28px;border-radius:10px;font-size:15px;font-weight:700;text-decoration:none;white-space:nowrap;flex-shrink:0;">
        ✨ 공약 자동 생성하기 →
      </a>
    </div>
  `;
  pledgeBanner.style.display = 'block';
}

function renderTrendChart(trendData) {
  const container = document.getElementById('trendContent');
  container.innerHTML = '<canvas id="trendCanvas" height="120"></canvas>';
  const canvas = document.getElementById('trendCanvas');
  const ctx = canvas.getContext('2d');
  canvas.width = container.offsetWidth || 600;
  canvas.height = 120;

  const values = trendData.map(d => d.ratio);
  const labels = trendData.map(d => d.date.slice(5));
  const max = Math.max(...values) || 1;
  const w = canvas.width, h = canvas.height;
  const pad = { l: 40, r: 10, t: 10, b: 30 };
  const innerW = w - pad.l - pad.r, innerH = h - pad.t - pad.b;
  const step = innerW / (values.length - 1 || 1);

  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = '#f1f5f9'; ctx.lineWidth = 1;
  [0, 0.5, 1].forEach(r => {
    const y = pad.t + innerH * (1 - r);
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
    ctx.fillStyle = '#94a3b8'; ctx.font = '10px sans-serif'; ctx.textAlign = 'right';
    ctx.fillText(Math.round(max * r), pad.l - 4, y + 4);
  });

  const gradient = ctx.createLinearGradient(0, pad.t, 0, pad.t + innerH);
  gradient.addColorStop(0, 'rgba(59,130,246,0.3)');
  gradient.addColorStop(1, 'rgba(59,130,246,0)');

  ctx.beginPath();
  values.forEach((v, i) => {
    const x = pad.l + i * step, y = pad.t + innerH * (1 - v / max);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.lineTo(pad.l + (values.length - 1) * step, pad.t + innerH);
  ctx.lineTo(pad.l, pad.t + innerH);
  ctx.closePath();
  ctx.fillStyle = gradient; ctx.fill();

  ctx.beginPath(); ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2;
  values.forEach((v, i) => {
    const x = pad.l + i * step, y = pad.t + innerH * (1 - v / max);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = '#94a3b8'; ctx.font = '10px sans-serif'; ctx.textAlign = 'center';
  labels.forEach((label, i) => {
    if (i % 7 === 0 || i === labels.length - 1)
      ctx.fillText(label, pad.l + i * step, h - 6);
  });
}
</script>
</body>
</html>"""


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


@app.get("/pledge", response_class=HTMLResponse)
async def pledge_page():
    return PLEDGE_HTML


@app.post("/generate-pledge")
async def generate_pledge_endpoint(body: PledgeRequest):
    if not body.candidate or len(body.candidate.strip()) < 1:
        return {"error": "후보자 이름을 입력해주세요."}
    try:
        raw_data = collect_all(body.candidate.strip())
        opinion_data = analyze(raw_data)
        pledges = generate_pledges(opinion_data, body.region, body.persona)
        return {"opinion": opinion_data, "pledges": pledges}
    except Exception as e:
        return {"error": str(e)}


PLEDGE_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>맞춤형 공약 생성기</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; color: #1a1a2e; }

  header { background: #16213e; color: #fff; padding: 20px 40px; display: flex; align-items: center; gap: 16px; justify-content: space-between; }
  header .logo { display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 22px; font-weight: 700; }
  header span { font-size: 13px; opacity: 0.6; }
  header a.back { color: #93c5fd; font-size: 13px; text-decoration: none; }
  header a.back:hover { text-decoration: underline; }

  .container { max-width: 900px; margin: 40px auto; padding: 0 24px; }

  /* 입력 폼 */
  .form-card {
    background: #fff; border-radius: 16px; padding: 36px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 32px;
  }
  .form-card h2 { font-size: 20px; font-weight: 700; margin-bottom: 8px; color: #1e293b; }
  .form-card .subtitle { font-size: 14px; color: #64748b; margin-bottom: 28px; line-height: 1.6; }

  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group.full { grid-column: 1 / -1; }
  .form-group label { font-size: 13px; font-weight: 600; color: #374151; }
  .form-group input, .form-group select {
    padding: 11px 14px; border: 2px solid #e5e7eb; border-radius: 8px;
    font-size: 15px; outline: none; transition: border-color .2s; background: #fff;
  }
  .form-group input:focus, .form-group select:focus { border-color: #6366f1; }

  .persona-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  .persona-btn {
    padding: 10px; border: 2px solid #e5e7eb; border-radius: 10px;
    background: #fff; cursor: pointer; font-size: 13px; font-weight: 600;
    color: #64748b; text-align: center; transition: all .2s;
  }
  .persona-btn:hover { border-color: #6366f1; color: #6366f1; }
  .persona-btn.active { border-color: #6366f1; background: #eef2ff; color: #6366f1; }
  .persona-btn .emoji { display: block; font-size: 22px; margin-bottom: 4px; }

  .generate-btn {
    width: 100%; padding: 15px; background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff; border: none; border-radius: 10px; font-size: 16px; font-weight: 700;
    cursor: pointer; margin-top: 20px; transition: opacity .2s; letter-spacing: -0.3px;
  }
  .generate-btn:hover { opacity: 0.92; }
  .generate-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* 로딩 */
  .loading-card {
    background: #fff; border-radius: 16px; padding: 48px 36px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; display: none;
  }
  .spinner {
    width: 48px; height: 48px; border: 4px solid #e5e7eb;
    border-top-color: #6366f1; border-radius: 50%;
    animation: spin 0.8s linear infinite; margin: 0 auto 20px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-steps { display: flex; flex-direction: column; gap: 10px; margin-top: 20px; }
  .step-item { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #94a3b8; }
  .step-item.active { color: #6366f1; font-weight: 600; }
  .step-item.done { color: #22c55e; }
  .step-dot { width: 8px; height: 8px; border-radius: 50%; background: #e5e7eb; flex-shrink: 0; }
  .step-item.active .step-dot { background: #6366f1; }
  .step-item.done .step-dot { background: #22c55e; }

  /* 요약 카드 */
  .summary-card {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff; border-radius: 16px; padding: 28px 32px;
    margin-bottom: 24px; box-shadow: 0 4px 20px rgba(99,102,241,0.3);
  }
  .summary-card .label { font-size: 12px; font-weight: 600; opacity: 0.75; margin-bottom: 8px; letter-spacing: 0.5px; text-transform: uppercase; }
  .summary-card p { font-size: 15px; line-height: 1.7; opacity: 0.95; }
  .summary-meta { display: flex; gap: 20px; margin-top: 16px; flex-wrap: wrap; }
  .summary-meta .meta-item { font-size: 13px; opacity: 0.8; }
  .summary-meta .meta-item strong { opacity: 1; font-weight: 700; }

  /* 이슈 카드 */
  .issue-cards { display: flex; flex-direction: column; gap: 20px; }
  .issue-card {
    background: #fff; border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.07); overflow: hidden;
  }
  .issue-header {
    padding: 20px 28px; display: flex; align-items: center;
    justify-content: space-between; gap: 16px;
    border-bottom: 1px solid #f1f5f9; cursor: pointer;
  }
  .issue-rank {
    width: 40px; height: 40px; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff; font-size: 16px; font-weight: 800;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .issue-title { flex: 1; }
  .issue-title h3 { font-size: 17px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
  .issue-title .evidence { font-size: 12px; color: #64748b; }
  .score-bars { display: flex; gap: 12px; }
  .score-item { text-align: center; }
  .score-item .score-label { font-size: 10px; color: #94a3b8; font-weight: 600; margin-bottom: 4px; }
  .score-item .score-val { font-size: 18px; font-weight: 800; }
  .score-item.severity .score-val { color: #ef4444; }
  .score-item.spread .score-val { color: #f59e0b; }
  .score-item.urgency .score-val { color: #6366f1; }
  .score-total { text-align: center; padding: 0 8px; border-left: 1px solid #e5e7eb; }
  .score-total .score-label { font-size: 10px; color: #94a3b8; font-weight: 600; margin-bottom: 4px; }
  .score-total .score-val { font-size: 22px; font-weight: 800; color: #1e293b; }
  .toggle-icon { font-size: 18px; color: #94a3b8; transition: transform .3s; }
  .issue-card.open .toggle-icon { transform: rotate(180deg); }

  /* 탭 */
  .issue-body { display: none; padding: 0 28px 28px; }
  .issue-card.open .issue-body { display: block; }
  .tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 2px solid #f1f5f9; }
  .tab-btn {
    padding: 10px 18px; border: none; background: none; cursor: pointer;
    font-size: 14px; font-weight: 600; color: #94a3b8; border-bottom: 2px solid transparent;
    margin-bottom: -2px; transition: all .2s;
  }
  .tab-btn.active { color: #6366f1; border-bottom-color: #6366f1; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }

  /* 5W1H */
  .fivewh-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .fivewh-item { background: #f8fafc; border-radius: 10px; padding: 14px 16px; }
  .fivewh-item .wh-label {
    font-size: 11px; font-weight: 700; color: #6366f1; margin-bottom: 6px;
    text-transform: uppercase; letter-spacing: 0.5px;
  }
  .fivewh-item .wh-value { font-size: 14px; color: #1e293b; line-height: 1.5; }

  /* 네이밍/슬로건 */
  .naming-box { text-align: center; padding: 28px; }
  .naming-box .pledge-name {
    font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 12px;
  }
  .naming-box .slogan {
    display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff; padding: 8px 24px; border-radius: 20px;
    font-size: 16px; font-weight: 700;
  }

  /* 스토리텔링 */
  .story-box {
    background: #f8fafc; border-radius: 12px; padding: 24px;
    font-size: 14px; color: #374151; line-height: 1.85;
    white-space: pre-wrap;
  }

  /* 에러 */
  .error-card {
    background: #fef2f2; border-radius: 12px; padding: 20px 24px;
    color: #dc2626; font-size: 14px; display: none; margin-top: 16px;
  }

  /* 결과 숨김 */
  #results { display: none; }

  footer {
    background: #16213e; color: #fff;
    padding: 40px; margin-top: 48px;
  }
  .footer-inner {
    max-width: 900px; margin: 0 auto;
    display: flex; justify-content: space-between; align-items: center;
    gap: 24px; flex-wrap: wrap;
  }
  .footer-info .name { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
  .footer-info .role { font-size: 13px; opacity: 0.6; margin-bottom: 12px; }
  .footer-info .email a { font-size: 13px; color: #93c5fd; text-decoration: none; }
  .footer-links { display: flex; gap: 12px; flex-wrap: wrap; }
  .footer-links a {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 18px; border-radius: 8px;
    font-size: 13px; font-weight: 600; text-decoration: none; transition: opacity .2s;
  }
  .footer-links a:hover { opacity: 0.85; }
  .footer-links .btn-yt   { background: #ff0000; color: #fff; }
  .footer-links .btn-home { background: #3b82f6; color: #fff; }
  .footer-links .btn-ai   { background: #7c3aed; color: #fff; }
  .footer-copy { max-width: 900px; margin: 24px auto 0; font-size: 11px; opacity: 0.35; text-align: center; }
</style>
</head>
<body>

<header>
  <div class="logo">
    <h1>🗳️ 맞춤형 공약 생성기</h1>
    <span>여론 분석 → GPT 기반 공약 자동 생성</span>
  </div>
  <a href="/" class="back">← 여론 분석으로 돌아가기</a>
</header>

<div class="container">

  <!-- 입력 폼 -->
  <div class="form-card" id="formCard">
    <h2>🎯 공약 생성 설정</h2>
    <p class="subtitle">후보자 이름을 입력하면 여론 데이터를 자동 수집하고,<br>GPT가 심각성·확산성·시급성 기준으로 최우선 이슈 3가지와 맞춤형 공약을 생성합니다.</p>

    <div class="form-grid">
      <div class="form-group">
        <label>👤 후보자 이름 *</label>
        <input type="text" id="candidateInput" placeholder="예: 홍길동" />
      </div>
      <div class="form-group">
        <label>📍 지역구 (선택)</label>
        <input type="text" id="regionInput" placeholder="예: 서울 노원구" />
      </div>
    </div>

    <div class="form-group">
      <label>🎯 타겟 유권자 페르소나</label>
      <div class="persona-grid" id="personaGrid">
        <button class="persona-btn active" data-value="전체 유권자" onclick="selectPersona(this)">
          <span class="emoji">🧑‍🤝‍🧑</span>전체 유권자
        </button>
        <button class="persona-btn" data-value="청년층 (20-30대)" onclick="selectPersona(this)">
          <span class="emoji">🧑‍💻</span>청년층 (20-30대)
        </button>
        <button class="persona-btn" data-value="중장년층 (40-50대)" onclick="selectPersona(this)">
          <span class="emoji">👨‍👩‍👧</span>중장년층 (40-50대)
        </button>
        <button class="persona-btn" data-value="노년층 (60대+)" onclick="selectPersona(this)">
          <span class="emoji">👴</span>노년층 (60대+)
        </button>
      </div>
    </div>

    <button class="generate-btn" id="generateBtn" onclick="generatePledge()">
      ✨ 공약 자동 생성하기
    </button>
    <div class="error-card" id="errorCard"></div>
  </div>

  <!-- 로딩 -->
  <div class="loading-card" id="loadingCard">
    <div class="spinner"></div>
    <div style="font-size:16px;font-weight:700;color:#1e293b">공약을 생성하고 있습니다...</div>
    <div style="font-size:13px;color:#64748b;margin-top:6px">네이버·YouTube 데이터 수집 후 GPT가 분석합니다 (약 30초)</div>
    <div class="loading-steps" id="loadingSteps">
      <div class="step-item active" id="step1"><div class="step-dot"></div>네이버 뉴스·블로그·카페 데이터 수집 중</div>
      <div class="step-item" id="step2"><div class="step-dot"></div>YouTube 영상·댓글 수집 중</div>
      <div class="step-item" id="step3"><div class="step-dot"></div>여론 데이터 분석 중</div>
      <div class="step-item" id="step4"><div class="step-dot"></div>GPT로 이슈 우선순위 산정 및 공약 생성 중</div>
    </div>
  </div>

  <!-- 결과 -->
  <div id="results">

    <!-- 요약 -->
    <div class="summary-card" id="summaryCard"></div>

    <!-- 이슈 카드들 -->
    <div class="issue-cards" id="issueCards"></div>

  </div>
</div>

<footer>
  <div class="footer-inner">
    <div class="footer-info">
      <div class="name">권혁용 연구위원</div>
      <div class="role">AI선거전략연구소 연구위원</div>
      <div class="email">✉️ <a href="mailto:hukyoung84@naver.com">hukyoung84@naver.com</a></div>
    </div>
    <div class="footer-links">
      <a href="https://www.youtube.com/@KwonT_AI" target="_blank" class="btn-yt">▶ YouTube</a>
      <a href="https://litt.ly/levelupai" target="_blank" class="btn-home">🏠 홈페이지</a>
      <a href="https://win-ai.kr/" target="_blank" class="btn-ai">🏆 AI선거전략연구소</a>
    </div>
  </div>
  <div class="footer-copy">© 2026 권혁용 연구위원 · 맞춤형 공약 생성기 · AI선거전략연구소</div>
</footer>

<script>
let selectedPersona = '전체 유권자';
let stepTimer = null;

// URL 파라미터에서 후보자 이름 자동 입력
window.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const candidate = params.get('candidate');
  if (candidate) {
    document.getElementById('candidateInput').value = candidate;
  }
});

function selectPersona(btn) {
  document.querySelectorAll('.persona-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedPersona = btn.dataset.value;
}

function animateSteps() {
  const steps = ['step1','step2','step3','step4'];
  let i = 0;
  stepTimer = setInterval(() => {
    if (i > 0) {
      document.getElementById(steps[i-1]).classList.remove('active');
      document.getElementById(steps[i-1]).classList.add('done');
    }
    if (i < steps.length) {
      document.getElementById(steps[i]).classList.add('active');
      i++;
    } else {
      clearInterval(stepTimer);
    }
  }, 7000);
}

async function generatePledge() {
  const candidate = document.getElementById('candidateInput').value.trim();
  if (!candidate) {
    showError('후보자 이름을 입력해주세요.');
    return;
  }

  const region = document.getElementById('regionInput').value.trim();

  document.getElementById('errorCard').style.display = 'none';
  document.getElementById('formCard').style.display = 'none';
  document.getElementById('loadingCard').style.display = 'block';
  document.getElementById('results').style.display = 'none';

  // 스텝 애니메이션 초기화
  ['step1','step2','step3','step4'].forEach((id, i) => {
    const el = document.getElementById(id);
    el.classList.remove('active','done');
    if (i === 0) el.classList.add('active');
  });
  animateSteps();

  try {
    const res = await fetch('/generate-pledge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate, region, persona: selectedPersona })
    });
    const data = await res.json();

    clearInterval(stepTimer);

    if (data.error) { showError('오류: ' + data.error); return; }
    renderResults(data, candidate, region);

  } catch (err) {
    clearInterval(stepTimer);
    showError('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
  }
}

function showError(msg) {
  document.getElementById('loadingCard').style.display = 'none';
  document.getElementById('formCard').style.display = 'block';
  const el = document.getElementById('errorCard');
  el.textContent = '⚠️ ' + msg;
  el.style.display = 'block';
}

function renderResults(data, candidate, region) {
  document.getElementById('loadingCard').style.display = 'none';
  document.getElementById('results').style.display = 'block';

  const opinion = data.opinion;
  const pledges = data.pledges;
  const s = opinion.sentiment_ratio;
  const m = opinion.mention_count;

  // 요약 카드
  document.getElementById('summaryCard').innerHTML = `
    <div class="label">📊 여론 분석 요약 — ${candidate}${region ? ' · ' + region : ''} · ${selectedPersona}</div>
    <p>${pledges.summary}</p>
    <div class="summary-meta">
      <div class="meta-item">총 언급량 <strong>${m.total.toLocaleString()}건</strong></div>
      <div class="meta-item">긍정 <strong>${s.positive}%</strong></div>
      <div class="meta-item">부정 <strong>${s.negative}%</strong></div>
      <div class="meta-item">중립 <strong>${s.neutral}%</strong></div>
      <div class="meta-item">키워드 <strong>${(opinion.keywords||[]).slice(0,5).map(k=>k.word).join(', ')}</strong></div>
    </div>
  `;

  // 이슈 카드
  const container = document.getElementById('issueCards');
  container.innerHTML = '';

  (pledges.priority_issues || []).forEach((issue, idx) => {
    const sc = issue.score || {};
    const pl = issue.pledge || {};
    const wh = pl['5w1h'] || {};
    const evidence = (issue.evidence || []).join(' · ');

    container.innerHTML += `
    <div class="issue-card" id="issue-${idx}">
      <div class="issue-header" onclick="toggleIssue(${idx})">
        <div class="issue-rank">${idx + 1}</div>
        <div class="issue-title">
          <h3>${issue.issue}</h3>
          <div class="evidence">근거: ${evidence}</div>
        </div>
        <div class="score-bars">
          <div class="score-item severity">
            <div class="score-label">심각성</div>
            <div class="score-val">${sc.severity}</div>
          </div>
          <div class="score-item spread">
            <div class="score-label">확산성</div>
            <div class="score-val">${sc.spread}</div>
          </div>
          <div class="score-item urgency">
            <div class="score-label">시급성</div>
            <div class="score-val">${sc.urgency}</div>
          </div>
          <div class="score-total">
            <div class="score-label">합계</div>
            <div class="score-val">${sc.total}</div>
          </div>
        </div>
        <div class="toggle-icon">▼</div>
      </div>

      <div class="issue-body">
        <div class="tabs">
          <button class="tab-btn active" onclick="switchTab(${idx}, 'fivewh', this)">📋 5W1H 공약</button>
          <button class="tab-btn" onclick="switchTab(${idx}, 'naming', this)">🏷️ 네이밍·슬로건</button>
          <button class="tab-btn" onclick="switchTab(${idx}, 'story', this)">📖 스토리텔링</button>
        </div>

        <div class="tab-content active" id="tab-${idx}-fivewh">
          <div class="fivewh-grid">
            <div class="fivewh-item"><div class="wh-label">Who — 누가</div><div class="wh-value">${wh.who||'-'}</div></div>
            <div class="fivewh-item"><div class="wh-label">What — 무엇을</div><div class="wh-value">${wh.what||'-'}</div></div>
            <div class="fivewh-item"><div class="wh-label">When — 언제까지</div><div class="wh-value">${wh.when||'-'}</div></div>
            <div class="fivewh-item"><div class="wh-label">Where — 어디서</div><div class="wh-value">${wh.where||'-'}</div></div>
            <div class="fivewh-item"><div class="wh-label">Why — 왜</div><div class="wh-value">${wh.why||'-'}</div></div>
            <div class="fivewh-item"><div class="wh-label">How — 어떻게</div><div class="wh-value">${wh.how||'-'}</div></div>
          </div>
        </div>

        <div class="tab-content" id="tab-${idx}-naming">
          <div class="naming-box">
            <div class="pledge-name">${pl.naming||'공약명'}</div>
            <div class="slogan">${pl.slogan||'슬로건'}</div>
          </div>
        </div>

        <div class="tab-content" id="tab-${idx}-story">
          <div class="story-box">${pl.storytelling||'스토리텔링 내용'}</div>
        </div>
      </div>
    </div>
    `;

    // 첫 번째 카드 자동 펼침
    if (idx === 0) {
      setTimeout(() => toggleIssue(0), 100);
    }
  });

  // 하단에 다시 생성 버튼 추가
  container.innerHTML += `
    <div style="text-align:center;margin-top:8px">
      <button onclick="resetForm()" style="padding:12px 32px;background:#f1f5f9;border:none;border-radius:10px;font-size:14px;font-weight:600;color:#374151;cursor:pointer;">
        ↩ 다시 생성하기
      </button>
    </div>
  `;
}

function toggleIssue(idx) {
  document.getElementById('issue-' + idx).classList.toggle('open');
}

function switchTab(issueIdx, tabName, btn) {
  const card = document.getElementById('issue-' + issueIdx);
  card.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  card.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-' + issueIdx + '-' + tabName).classList.add('active');
}

function resetForm() {
  document.getElementById('results').style.display = 'none';
  document.getElementById('formCard').style.display = 'block';
  document.getElementById('candidateInput').value = '';
  document.getElementById('regionInput').value = '';
}
</script>
</body>
</html>"""
