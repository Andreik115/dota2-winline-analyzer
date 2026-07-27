# liqui_live_final.py
import requests, sqlite3, time, re
from datetime import datetime
from bs4 import BeautifulSoup

DB = "data/dota2.db"
URL = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def create_table():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT, team2 TEXT,
            tournament TEXT, status TEXT,
            match_time TEXT, updated TEXT
        )
    """)
    conn.commit()
    return conn

def parse_live():
    r = requests.get(URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, 'lxml')
    matches = []
    
    # Ищем текст страницы
    text = soup.get_text()
    lines = text.split('\n')
    
    i = 0
    while i < len(lines) - 3:
        line = lines[i].strip()
        next_lines = [lines[i+j].strip() for j in range(1, 5)]
        combined = ' '.join([line] + next_lines)
        
        # Ищем паттерн "Команда1 vs Команда2" рядом с LIVE
        if 'LIVE' in combined and 'vs' in combined.lower():
            # Ищем команды до и после vs
            parts = combined.split('vs')
            if len(parts) >= 2:
                team1 = parts[0].strip().split('\n')[-1].strip()
                team2 = parts[1].strip().split('\n')[0].strip()
                
                # Ищем турнир
                tournament = ""
                for nl in next_lines + lines[i+3:i+8]:
                    if len(nl) > 10 and not nl.startswith('LIVE') and 'vs' not in nl.lower():
                        tournament = nl.strip()
                        break
                
                # Время матча
                time_str = ""
                time_match = re.search(r'(\d+m\s*\d+s|\d+m)', combined)
                if time_match:
                    time_str = time_match.group(1)
                
                matches.append({
                    'team1': team1[:50],
                    'team2': team2[:50],
                    'tournament': tournament[:100],
                    'time': time_str
                })
                i += 5
                continue
        i += 1
    
    return matches

def main():
    conn = create_table()
    
    while True:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        matches = parse_live()
        
        print(f"\n{'='*50}")
        print(f"[{now}] 🔴 LIVE-МАТЧИ: {len(matches)}")
        print(f"{'='*50}")
        
        if matches:
            for m in matches:
                print(f"\n🏆 {m['tournament']}")
                print(f"   {m['team1']} vs {m['team2']}")
                if m['time']:
                    print(f"   ⏱️ {m['time']}")
                
                # Сохраняем в базу
                conn.execute(
                    "INSERT INTO live_matches (team1, team2, tournament, status, match_time, updated) VALUES (?, ?, ?, 'LIVE', ?, ?)",
                    (m['team1'], m['team2'], m['tournament'], m['time'], now)
                )
                conn.commit()
        else:
            print("   Нет активных матчей")
        
        print(f"\n⏳ Обновление через 30 сек...")
        time.sleep(30)

if __name__ == "__main__":
    main()
