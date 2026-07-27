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
            odds_total REAL, odds_total_over REAL, odds_total_under REAL,
            odds_fora1 REAL, odds_fora2 REAL,
            ai_verdict TEXT, confidence TEXT,
            updated TEXT
        )
    """)
    # Таблица для полных коэффициентов Winline
    conn.execute("""
        CREATE TABLE IF NOT EXISTS winline_odds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT, team2 TEXT,
            odds_p1 REAL, odds_x REAL, odds_p2 REAL,
            odds_total REAL, odds_total_over REAL, odds_total_under REAL,
            odds_fora REAL, odds_fora1 REAL, odds_fora2 REAL,
            match_time TEXT, updated TEXT
        )
    """)
    conn.commit()
    return conn

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")
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

def parse_winline_full():
    """Собирает все коэффициенты Winline: исход, тотал, фора"""
    driver = get_driver()
    driver.get("https://winline.ru/stavki/sport/kibersport/dota_2")
    time.sleep(5)
    
    events = driver.find_elements(By.CSS_SELECTOR, ".event-card")
    print(f"   Найдено событий Winline: {len(events)}")
    
    all_odds = []
    for event in events:
        try:
            text = event.text
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            team1, team2 = "", ""
            odds_p1 = odds_x = odds_p2 = None
            total = total_over = total_under = None
            fora = fora1 = fora2 = None
            
            for i, line in enumerate(lines):
                # Ищем команды (первая и вторая строка с буквами)
                if not team1 and re.match(r'^[A-Z]', line) and not re.match(r'^\d', line):
                    team1 = line
                elif team1 and not team2 and re.match(r'^[A-Z]', line) and line != team1:
                    team2 = line
                
                # Коэффициенты на исход
                nums = re.findall(r'^(\d+\.\d{2})$', line)
                if nums and not odds_p1:
                    odds_p1 = float(nums[0])
                elif nums and odds_p1 and not odds_x:
                    odds_x = float(nums[0])
                elif nums and odds_x and not odds_p2:
                    odds_p2 = float(nums[0])
            
            if team1 and team2 and odds_p1:
                all_odds.append({
                    'team1': team1, 'team2': team2,
                    'odds_p1': odds_p1, 'odds_x': odds_x,
                    'odds_p2': odds_p2,
                    'total': total, 'total_over': total_over, 'total_under': total_under,
                    'fora': fora, 'fora1': fora1, 'fora2': fora2
                })
        except:
            pass
    
    driver.quit()
    return all_odds

def find_odds(team1, team2, conn):
    """Ищет коэффициенты в winline_odds"""
    for table in ['winline_odds', 'matches']:
        cols = "odds_p1, odds_x, odds_p2, odds_total, odds_total_over, odds_total_under, odds_fora, odds_fora1, odds_fora2" if table == 'winline_odds' else "team1_odds, NULL, team2_odds, NULL, NULL, NULL, NULL, NULL, NULL"
        
        row = conn.execute(
            f"SELECT {cols} FROM {table} WHERE team1_name LIKE ? AND team2_name LIKE ? LIMIT 1",
            (f"%{team1}%", f"%{team2}%")
        ).fetchone()
        
        if not row:
            row = conn.execute(
                f"SELECT {cols} FROM {table} WHERE team1_name LIKE ? AND team2_name LIKE ? LIMIT 1",
                (f"%{team2}%", f"%{team1}%")
            ).fetchone()
        
        if row and row[0]:
            return row
    
    return (None,) * 9

def analyze_with_ai(match, odds):
    """Отправляет матч в GigaChat с полными коэффициентами"""
    odds_text = f"П1={odds[0]}"
    if odds[1]:
        odds_text += f", X={odds[1]}"
    if odds[2]:
        odds_text += f", П2={odds[2]}"
    if odds[4]:
        odds_text += f" | Тотал: ТБ={odds[4]}, ТМ={odds[5]}"
    if odds[7]:
        odds_text += f" | Фора: Ф1={odds[7]}, Ф2={odds[8]}"
    
    try:
        return analyzer.analyze_match(
            match['team1'], match['team2'],
            odds[0], odds[2],
            match['tournament']
        )
    except:
        return None

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
            liqui_matches = parse_liquipedia()
        except:
            liqui_matches = []
        
        live = [m for m in liqui_matches if m['status'] == 'LIVE']
        upcoming = [m for m in liqui_matches if m['status'] == 'UPCOMING']
        
        print(f"   🔴 LIVE: {len(live)} | ⏳ Upcoming: {len(upcoming)}")
        
        # 2. Парсим Winline (полные кэфы)
        print("\n💰 Winline...")
        try:
            winline_odds = parse_winline_full()
        except:
            winline_odds = []
        
        # Сохраняем в базу
        for w in winline_odds:
            conn.execute("""
                INSERT OR REPLACE INTO winline_odds 
                (team1, team2, odds_p1, odds_x, odds_p2, odds_total, odds_total_over, odds_total_under, odds_fora, odds_fora1, odds_fora2, match_time, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                w['team1'], w['team2'],
                w['odds_p1'], w['odds_x'], w['odds_p2'],
                w['total'], w['total_over'], w['total_under'],
                w['fora'], w['fora1'], w['fora2'],
                '', now
            ))
        conn.commit()
        
        print(f"   Обновлено: {len(winline_odds)} матчей")
        
        # 3. Анализируем LIVE
        if live:
            print(f"\n{'─'*60}")
            print("🔴 LIVE-МАТЧИ:")
            print(f"{'─'*60}")
            
            for m in live[:8]:
                odds = find_odds(m['team1'], m['team2'], conn)
                odds_str = ""
                if odds[0]:
                    odds_str = f"💰 П1={odds[0]}"
                    if odds[1]:
                        odds_str += f" X={odds[1]}"
                    odds_str += f" П2={odds[2]}"
                    if odds[4]:
                        odds_str += f" | ТБ={odds[4]} ТМ={odds[5]}"
                    if odds[7]:
                        odds_str += f" | Ф1={odds[7]} Ф2={odds[8]}"
                else:
                    odds_str = "⚪ Нет кэфов"
                
                print(f"\n   {m['team1']} VS {m['team2']} | ⏱️ {m['time']}")
                print(f"   🏆 {m['tournament']}")
                print(f"   {odds_str}")
        
        # 4. Анализируем предстоящие с кэфами + AI
        print(f"\n{'─'*60}")
        print("🎯 РЕКОМЕНДАЦИИ (предстоящие с кэфами):")
        print(f"{'─'*60}")
        
        count = 0
        for m in upcoming:
            odds = find_odds(m['team1'], m['team2'], conn)
            if not odds[0]:
                continue
            
            count += 1
            print(f"\n   ═══ МАТЧ #{count} ═══")
            print(f"   {m['team1']} VS {m['team2']}")
            print(f"   🏆 {m['tournament']} | ⏰ {m['time']}")
            print(f"   💰 Исход: П1={odds[0]} | X={odds[1]} | П2={odds[2]}")
            
            if odds[4]:
                print(f"   📊 Тотал: ТБ={odds[4]} | ТМ={odds[5]}")
            if odds[7]:
                print(f"   📊 Фора: Ф1={odds[7]} | Ф2={odds[8]}")
            
            # AI-анализ
            verdict = analyze_with_ai(m, odds)
            if verdict:
                print(f"   🤖 AI: {verdict[:300]}")
                conn.execute(
                    "INSERT INTO live_bets (team1, team2, tournament, status, match_time, odds1, odds2, odds_total, odds_total_over, odds_total_under, odds_fora1, odds_fora2, ai_verdict, confidence, updated) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (m['team1'], m['team2'], m['tournament'], m['status'], m['time'],
                     odds[0], odds[2], odds[3], odds[4], odds[5], odds[7], odds[8],
                     verdict, 'СРЕДНЯЯ', now)
                )
            
            if count >= 5:
                break
        
        conn.commit()
        
        total_recs = conn.execute("SELECT COUNT(*) FROM live_bets").fetchone()[0]
        print(f"\n📊 Всего рекомендаций в базе: {total_recs}")
        print(f"⏳ Обновление через 120 сек...")
        time.sleep(120)

if __name__ == "__main__":
    main()
