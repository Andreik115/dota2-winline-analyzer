from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.database import get_session, Match
from src.ai.gigachat_analyzer import analyzer

app = FastAPI(title="Dota 2 Winline Analyzer", version="0.1.0")

static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    session = get_session()
    matches = session.query(Match).order_by(Match.id.desc()).limit(50).all()
    session.close()
    
    matches_html = ""
    if matches:
        for m in matches:
            odds_display = ""
            if m.team1_odds and m.team2_odds:
                odds_display = f"""
                <div style="display:flex;gap:10px;justify-content:center;margin-top:10px;">
                    <span style="background:#334155;padding:5px 15px;border-radius:8px;">К1: {m.team1_odds}</span>
                    <span style="background:#334155;padding:5px 15px;border-radius:8px;">К2: {m.team2_odds}</span>
                </div>"""
            
            matches_html += f"""
            <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;margin:10px 0;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-weight:600;font-size:18px;">{m.team1_name}</span>
                    <span style="font-weight:700;color:#64748b;">VS</span>
                    <span style="font-weight:600;font-size:18px;">{m.team2_name}</span>
                </div>
                {odds_display}
                <div style="color:#64748b;font-size:13px;text-align:center;margin-top:5px;">{m.tournament or ''}</div>
                <a href="/match/{m.id}" style="display:block;margin-top:12px;padding:10px;background:#3b82f6;color:white;text-align:center;text-decoration:none;border-radius:8px;">🤖 AI-анализ →</a>
            </div>
            """
    else:
        matches_html = """
        <div style="background:#1e293b;border-radius:12px;padding:48px;text-align:center;">
            <div style="font-size:48px;">📭</div>
            <p style="color:#94a3b8;font-size:18px;">Матчей пока нет</p>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dota 2 Winline Analyzer</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <header>
            <div class="container">
                <a href="/" class="logo">🎮 Dota2 Analyzer</a>
                <nav class="nav-links">
                    <a href="/">Матчи</a>
                    <a href="/recommendations">🤖 AI Рекомендации</a>
                    <a href="/live">🔴 LIVE</a>
                </nav>
            </div>
        </header>
        <main class="container">
            <h1 style="font-size:32px;margin-bottom:8px;">🎮 Анализ матчей Dota 2</h1>
            <p style="color:#94a3b8;margin-bottom:32px;">AI-прогнозы от GigaChat с коэффициентами Winline</p>
            <h2 style="font-size:24px;margin-bottom:16px;">📊 Матчи</h2>
            {matches_html}
        </main>
        <footer>
            <p>Dota 2 Winline Analyzer | AI: GigaChat | Данные: Winline, Liquipedia</p>
        </footer>
    </body>
    </html>
    """

@app.get("/match/{match_id}", response_class=HTMLResponse)
async def match_detail(match_id: int):
    session = get_session()
    match = session.query(Match).filter(Match.id == match_id).first()
    session.close()
    
    if not match:
        return "<h1>Матч не найден</h1><a href='/'>Назад</a>"
    
    odds_display = ""
    if match.team1_odds and match.team2_odds:
        odds_display = f"""
        <div style="display:flex;gap:20px;justify-content:center;margin-top:10px;">
            <span style="background:#334155;padding:8px 20px;border-radius:8px;font-size:18px;font-weight:600;">П1: {match.team1_odds}</span>
            <span style="background:#334155;padding:8px 20px;border-radius:8px;font-size:18px;font-weight:600;">П2: {match.team2_odds}</span>
        </div>"""
    
    ai_text = analyzer.analyze_match(
        match.team1_name,
        match.team2_name,
        match.team1_odds,
        match.team2_odds,
        match.tournament or ""
    )
    ai_text = ai_text.replace('\n', '<br>')
    
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{match.team1_name} vs {match.team2_name}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <header>
            <div class="container">
                <a href="/" class="logo">🎮 Dota2 Analyzer</a>
                <nav class="nav-links">
                    <a href="/">Матчи</a>
                    <a href="/recommendations">🤖 AI Рекомендации</a>
                    <a href="/live">🔴 LIVE</a>
                </nav>
            </div>
        </header>
        <main class="container">
            <a href="/" style="color:#3b82f6;text-decoration:none;">← Назад к матчам</a>
            
            <div class="card" style="margin:20px 0;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="text-align:center;flex:1;">
                        <div style="font-size:24px;font-weight:700;">{match.team1_name}</div>
                    </div>
                    <div style="font-size:24px;font-weight:700;color:#64748b;">VS</div>
                    <div style="text-align:center;flex:1;">
                        <div style="font-size:24px;font-weight:700;">{match.team2_name}</div>
                    </div>
                </div>
                {odds_display}
                <div style="text-align:center;color:#64748b;margin-top:8px;">{match.tournament or ''}</div>
            </div>
            
            <div class="card" style="background:linear-gradient(135deg,#1e1b4b,#1e293b);">
                <h3 style="margin-bottom:16px;">🤖 AI-анализ от GigaChat</h3>
                <div style="color:#cbd5e1;line-height:1.8;font-size:15px;">{ai_text}</div>
            </div>
        </main>
        <footer>
            <p>Dota 2 Winline Analyzer | AI: GigaChat</p>
        </footer>
    </body>
    </html>
    """

@app.get("/recommendations", response_class=HTMLResponse)
async def recommendations():
    conn = sqlite3.connect("data/dota2.db")
    rows = conn.execute(
        "SELECT team1, team2, tournament, odds1, odds2, ai_verdict, created FROM ai_recommendations ORDER BY id DESC LIMIT 30"
    ).fetchall()
    conn.close()
    
    if not rows:
        return """
        <!DOCTYPE html><html lang="ru">
        <head><meta charset="UTF-8"><title>AI Рекомендации</title>
        <link href="/static/css/style.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        </head>
        <body>
        <header><div class="container"><a href="/" class="logo">🎮 Dota2 Analyzer</a>
        <nav class="nav-links"><a href="/">Матчи</a><a href="/recommendations">🤖 AI Рекомендации</a><a href="/live">🔴 LIVE</a></nav>
        </div></header>
        <main class="container">
        <a href="/" style="color:#3b82f6;">← Назад</a>
        <div class="card" style="text-align:center;padding:48px;margin-top:20px;">
            <div style="font-size:48px;">🤖</div>
            <p style="color:#94a3b8;font-size:18px;">Рекомендаций пока нет</p>
            <p style="color:#64748b;">Запустите ai_recommend.py для генерации</p>
        </div>
        </main></body></html>"""
    
    html = ""
    for r in rows:
        verdict = r[5].replace('\n', '<br>')[:500]
        html += f"""
        <div class="card" style="margin:15px 0;">
            <h3 style="margin-bottom:5px;">{r[0]} ({r[3]}) VS {r[1]} ({r[4]})</h3>
            <div style="color:#94a3b8;font-size:14px;">🏆 {r[2]}</div>
            <div style="background:linear-gradient(135deg,#1e1b4b,#1e293b);padding:15px;border-radius:8px;margin-top:10px;color:#cbd5e1;line-height:1.6;font-size:14px;">
                🤖 {verdict}
            </div>
            <div style="color:#64748b;font-size:11px;margin-top:5px;">🕐 {r[6]}</div>
        </div>"""
    
    return f"""
    <!DOCTYPE html><html lang="ru">
    <head><meta charset="UTF-8"><title>AI Рекомендации</title>
    <link href="/static/css/style.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    </head>
    <body>
    <header><div class="container"><a href="/" class="logo">🎮 Dota2 Analyzer</a>
    <nav class="nav-links"><a href="/">Матчи</a><a href="/recommendations">🤖 AI Рекомендации</a><a href="/live">🔴 LIVE</a></nav>
    </div></header>
    <main class="container">
    <a href="/" style="color:#3b82f6;">← Назад</a>
    <h1 style="margin:20px 0;">🤖 AI-РЕКОМЕНДАЦИИ</h1>
    <p style="color:#94a3b8;">Анализ от GigaChat на основе коэффициентов Winline</p>
    {html}
    </main></body></html>"""

@app.get("/live", response_class=HTMLResponse)
async def live_page():
    conn = sqlite3.connect("data/dota2.db")
    live = conn.execute(
        "SELECT DISTINCT team1, team2, tournament, match_time FROM live_matches WHERE status='LIVE' ORDER BY id DESC LIMIT 20"
    ).fetchall()
    
    # Статистика
    total_live = conn.execute("SELECT COUNT(DISTINCT team1||team2) FROM live_matches WHERE status='LIVE'").fetchone()[0]
    total_recs = conn.execute("SELECT COUNT(*) FROM ai_recommendations").fetchone()[0]
    conn.close()
    
    live_html = ""
    if live:
        for m in live:
            live_html += f"""
            <div class="card" style="margin:10px 0;border-left:3px solid #ef4444;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">
                    <span style="color:#ef4444;font-weight:700;">🔴 LIVE</span>
                    <span style="color:#94a3b8;font-size:13px;">⏱️ {m[3] or 'Идёт'}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-weight:600;font-size:16px;">{m[0]}</span>
                    <span style="font-weight:700;color:#64748b;">VS</span>
                    <span style="font-weight:600;font-size:16px;">{m[1]}</span>
                </div>
                <div style="color:#94a3b8;font-size:13px;margin-top:5px;">🏆 {m[2]}</div>
            </div>"""
    else:
        live_html = """
        <div class="card" style="text-align:center;padding:48px;">
            <div style="font-size:48px;">😴</div>
            <p style="color:#94a3b8;">Нет активных матчей</p>
        </div>"""
    
    return f"""
    <!DOCTYPE html><html lang="ru">
    <head><meta charset="UTF-8"><title>LIVE Матчи</title>
    <link href="/static/css/style.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <meta http-equiv="refresh" content="60">
    </head>
    <body>
    <header><div class="container"><a href="/" class="logo">🎮 Dota2 Analyzer</a>
    <nav class="nav-links"><a href="/">Матчи</a><a href="/recommendations">🤖 AI Рекомендации</a><a href="/live">🔴 LIVE</a></nav>
    </div></header>
    <main class="container">
    <a href="/" style="color:#3b82f6;">← Назад</a>
    <h1 style="margin:20px 0;">🔴 LIVE МАТЧИ</h1>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:30px;">
        <div class="card"><div style="font-size:28px;font-weight:700;">{total_live}</div><div style="color:#94a3b8;">Активных матчей</div></div>
        <div class="card"><div style="font-size:28px;font-weight:700;">{total_recs}</div><div style="color:#94a3b8;">AI-рекомендаций</div></div>
        <div class="card"><div style="font-size:28px;font-weight:700;color:#22c55e;">Winline</div><div style="color:#94a3b8;">Коэффициенты</div></div>
    </div>
    {live_html}
    <p style="color:#64748b;text-align:center;font-size:12px;">Автообновление каждые 60 секунд</p>
    </main></body></html>"""

@app.get("/api/health")
async def health():
    return {"status": "ok"}
