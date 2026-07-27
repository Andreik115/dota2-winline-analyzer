@app.get("/recommendations", response_class=HTMLResponse)
async def recommendations():
    import sqlite3
    conn = sqlite3.connect("data/dota2.db")
    rows = conn.execute(
        "SELECT team1, team2, tournament, odds1, odds2, ai_verdict, created FROM ai_recommendations ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()
    
    if not rows:
        return "<h1>Нет рекомендаций</h1><a href='/'>Назад</a>"
    
    html = ""
    for r in rows:
        verdict = r[5].replace('\n', '<br>')[:400]
        html += f"""
        <div class="card" style="margin:15px 0;">
            <h3>{r[0]} ({r[3]}) VS {r[1]} ({r[4]})</h3>
            <div style="color:#94a3b8;">🏆 {r[2]}</div>
            <div style="background:linear-gradient(135deg,#1e1b4b,#1e293b);padding:15px;border-radius:8px;margin-top:10px;color:#cbd5e1;line-height:1.6;">
                🤖 {verdict}
            </div>
            <div style="color:#64748b;font-size:12px;margin-top:5px;">{r[6]}</div>
        </div>
        """
    
    return f"""
    <!DOCTYPE html><html lang="ru">
    <head><meta charset="UTF-8"><title>AI Рекомендации</title>
    <link href="/static/css/style.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    </head>
    <body>
    <header><div class="container"><a href="/" class="logo">🎮 Dota2 Analyzer</a></div></header>
    <main class="container">
    <a href="/" style="color:#3b82f6;">← Назад</a>
    <h1 style="margin:20px 0;">🤖 AI-РЕКОМЕНДАЦИИ</h1>
    {html}
    </main></body></html>
    """
