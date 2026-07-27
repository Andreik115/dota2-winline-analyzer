# deep_analyzer.py
import sqlite3, time, re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from src.ai.gigachat_analyzer import analyzer
from gigachat.models import Chat, Messages, MessagesRole

DB = "data/dota2.db"
LIQUI_URL = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def parse_liquipedia():
    driver = get_driver()
    driver.get(LIQUI_URL)
    time.sleep(5)
    lines = [l.strip() for l in driver.find_element(By.TAG_NAME, "body").text.split('\n') if l.strip()]
    driver.quit()
    
    matches = []
    i = 18
    while i < len(lines) - 5:
        if lines[i+1] == 'vs' and lines[i+2].startswith('(Bo'):
            team1, team2 = lines[i], lines[i+3]
            tournament = lines[i+4]
            status_line = lines[i+5]
            
            status = "LIVE" if status_line == 'LIVE' or re.match(r'\d+m', status_line) else "UPCOMING"
            time_str = status_line if re.match(r'\d+m', status_line) else ""
            if not time_str and i+6 < len(lines) and re.match(r'\d+m', lines[i+6]):
                time_str = lines[i+6]
            
            matches.append({
                'team1': team1, 'team2': team2,
                'tournament': tournament,
                'status': status, 'time': time_str
            })
            i += 6
        else:
            i += 1
    return matches

def get_team_recent_form(team_name, conn):
    rows = conn.execute(
        "SELECT opponent, result, score, tournament FROM team_results WHERE team_name LIKE ? LIMIT 5",
        (f"%{team_name}%",)
    ).fetchall()
    if rows:
        wins = sum(1 for r in rows if r[1] == 'W')
        return rows, wins
    return [], 0

def find_head_to_head(team1, team2, conn):
    rows = conn.execute(
        "SELECT team1, team2, score1, score2, winner FROM match_results WHERE (team1 LIKE ? AND team2 LIKE ?) OR (team1 LIKE ? AND team2 LIKE ?) LIMIT 10",
        (f"%{team1}%", f"%{team2}%", f"%{team2}%", f"%{team1}%")
    ).fetchall()
    return rows

def get_odds(team1, team2, conn):
    row = conn.execute(
        "SELECT team1_odds, team2_odds FROM matches WHERE team1_name LIKE ? AND team2_name LIKE ? AND team1_odds IS NOT NULL",
        (f"%{team1}%", f"%{team2}%")
    ).fetchone()
    if row:
        return row
    row = conn.execute(
        "SELECT team2_odds, team1_odds FROM matches WHERE team1_name LIKE ? AND team2_name LIKE ? AND team1_odds IS NOT NULL",
        (f"%{team2}%", f"%{team1}%")
    ).fetchone()
    return row

def deep_analysis(match, conn):
    team1, team2 = match['team1'], match['team2']
    
    odds = get_odds(team1, team2, conn)
    h2h = find_head_to_head(team1, team2, conn)
    form1, wins1 = get_team_recent_form(team1, conn)
    form2, wins2 = get_team_recent_form(team2, conn)
    
    context = f"""
=== ИСТОРИЯ ЛИЧНЫХ ВСТРЕЧ ===
{chr(10).join([f'{r[0]} {r[2]}:{r[3]} {r[1]} | {r[4]}' for r in h2h]) if h2h else 'Нет данных'}

=== ФОРМА {team1} ===
Последние матчи: {wins1}/{len(form1)} побед
{chr(10).join([f'  {r[1]} vs {r[0]} ({r[2]}) | {r[3]}' for r in form1]) if form1 else 'Нет данных'}

=== ФОРМА {team2} ===
Последние матчи: {wins2}/{len(form2)} побед
{chr(10).join([f'  {r[1]} vs {r[0]} ({r[2]}) | {r[3]}' for r in form2]) if form2 else 'Нет данных'}

=== КОЭФФИЦИЕНТЫ ===
П1={odds[0] if odds else '?'}, П2={odds[1] if odds else '?'}
"""
    
    prompt = f"""Ты — профессиональный аналитик Dota 2. Проведи глубокий анализ матча.

=== МАТЧ ===
{team1} vs {team2}
Турнир: {match['tournament']}
Формат: Bo3 (возможна ничья в группе)

{context}

=== ЗАДАНИЕ ===
Дай структурированный анализ:

📊 ИСТОРИЯ H2H: Кто чаще побеждал в личных встречах?
📈 ФОРМА: У кого лучше форма сейчас?
💰 ЛИНИЯ: Оценка коэффициентов. Есть ли value?
🎯 ПРОГНОЗ: 
- Исход: П1/Ничья/П2 с вероятностью (%)
- Тотал: больше/меньше 2.5 карт
- Фора: по картам

⚡ ИТОГ: Финальная рекомендация + уровень уверенности.

УЧТИ: в Bo3 может быть ничья в групповом этапе! Если фаворит не очевиден — укажи ничью как возможный исход."""

    try:
        return analyzer.client.chat(
            Chat(messages=[Messages(role=MessagesRole.USER, content=prompt)]),
            temperature=0.2, max_tokens=800
        ).choices[0].message.content
    except:
        return "AI недоступен"

def main():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deep_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT, team2 TEXT, tournament TEXT,
            analysis TEXT, created TEXT
        )
    """)
    conn.commit()
    
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n{'='*60}")
        print(f"[{now}] 🔬 ГЛУБОКИЙ АНАЛИЗ")
        print(f"{'='*60}")
        
        matches = parse_liquipedia()
        upcoming = [m for m in matches if m['status'] == 'UPCOMING']
        
        analyzed = 0
        for m in upcoming[:10]:
            exist = conn.execute(
                "SELECT id FROM deep_analysis WHERE team1=? AND team2=? AND created LIKE ?",
                (m['team1'], m['team2'], datetime.now().strftime('%Y-%m-%d') + '%')
            ).fetchone()
            if exist:
                continue
            
            print(f"\n🔬 {m['team1']} VS {m['team2']} | {m['tournament']}")
            analysis = deep_analysis(m, conn)
            print(f"🤖 {analysis[:300]}...")
            
            conn.execute(
                "INSERT INTO deep_analysis (team1, team2, tournament, analysis, created) VALUES (?,?,?,?,?)",
                (m['team1'], m['team2'], m['tournament'], analysis, now)
            )
            conn.commit()
            analyzed += 1
        
        print(f"\n✅ Проанализировано: {analyzed}")
        time.sleep(300)

if __name__ == "__main__":
    main()
