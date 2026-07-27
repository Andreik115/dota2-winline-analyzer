# final_analyzer.py
import sqlite3, time, re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from src.ai.gigachat_analyzer import analyzer

DB = "data/dota2.db"
LIQUI_URL = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT, team2 TEXT, tournament TEXT,
            status TEXT, match_time TEXT,
            odds1 REAL, odds2 REAL,
            ai_verdict TEXT, confidence TEXT,
            updated TEXT
        )
    """)
    conn.commit()
    return conn

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def parse_liquipedia():
    """Собирает live и upcoming матчи"""
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

def find_odds(team1, team2, conn):
    """Ищет коэффициенты Winline в базе"""
    # Прямое совпадение
    row = conn.execute(
        "SELECT team1_odds, team2_odds FROM matches WHERE team1_name LIKE ? AND team2_name LIKE ? AND team1_odds IS NOT NULL",
        (f"%{team1}%", f"%{team2}%")
    ).fetchone()
    if row:
        return row[0], row[1]
    
    # Обратное совпадение
    row = conn.execute(
        "SELECT team2_odds, team1_odds FROM matches WHERE team1_name LIKE ? AND team2_name LIKE ? AND team1_odds IS NOT NULL",
        (f"%{team2}%", f"%{team1}%")
    ).fetchone()
    if row:
        return row[0], row[1]
    
    return None, None

def main():
    conn = init_db()
    
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n{'='*60}")
        print(f"[{now}] 🔄 ПОЛНЫЙ АНАЛИЗ")
        print(f"{'='*60}")
        
        # 1. Парсим Liquipedia
        print("\n📡 Liquipedia...")
        try:
            matches = parse_liquipedia()
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(30)
            continue
        
        live = [m for m in matches if m['status'] == 'LIVE']
        upcoming = [m for m in matches if m['status'] == 'UPCOMING']
        
        print(f"   🔴 LIVE: {len(live)} | ⏳ Upcoming: {len(upcoming)}")
        
        # 2. Анализируем LIVE-матчи
        if live:
            print(f"\n{'─'*60}")
            print("🔴 LIVE-АНАЛИЗ:")
            print(f"{'─'*60}")
            
            for m in live[:5]:  # Топ-5 live
                odds1, odds2 = find_odds(m['team1'], m['team2'], conn)
                
                print(f"\n   {m['team1']} VS {m['team2']}")
                print(f"   🏆 {m['tournament']} | ⏱️ {m['time']}")
                
                if odds1 and odds2:
                    print(f"   💰 Winline: П1={odds1}, П2={odds2}")
                    
                    # AI-анализ
                    try:
                        verdict = analyzer.analyze_match(
                            m['team1'], m['team2'], odds1, odds2, m['tournament']
                        )
                        # Извлекаем вердикт
                        if 'СТАВИТЬ' in verdict.upper():
                            conf = "ВЫСОКАЯ" if 'ВЫСОКАЯ' in verdict.upper() else "СРЕДНЯЯ"
                            conn.execute(
                                "INSERT INTO live_bets (team1, team2, tournament, status, match_time, odds1, odds2, ai_verdict, confidence, updated) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (m['team1'], m['team2'], m['tournament'], 'LIVE', m['time'], odds1, odds2, verdict, conf, now)
                            )
                        print(f"   🤖 AI: {verdict[:200]}...")
                    except Exception as e:
                        print(f"   🤖 AI: ошибка - {e}")
                else:
                    print(f"   ⚠️ Нет коэффициентов Winline")
        
        # 3. Показываем предстоящие с кэфами
        with_odds = [(m, *find_odds(m['team1'], m['team2'], conn)) for m in upcoming if find_odds(m['team1'], m['team2'], conn)[0]]
        
        if with_odds:
            print(f"\n{'─'*60}")
            print(f"💰 ПРЕДСТОЯЩИЕ С КЭФАМИ ({len(with_odds)}):")
            print(f"{'─'*60}")
            
            for m, o1, o2 in with_odds[:5]:
                print(f"   {m['team1']} ({o1}) VS {m['team2']} ({o2}) | {m['tournament']} | ⏰ {m['time']}")
        
        conn.commit()
        
        # Статистика
        total = conn.execute("SELECT COUNT(*) FROM live_bets").fetchone()[0]
        today = conn.execute("SELECT COUNT(*) FROM live_bets WHERE updated LIKE ?", (datetime.now().strftime('%Y-%m-%d') + '%',)).fetchone()[0]
        print(f"\n📊 В базе: {total} рекомендаций (сегодня: {today})")
        print(f"⏳ Обновление через 60 сек...")
        
        time.sleep(60)

if __name__ == "__main__":
    main()
