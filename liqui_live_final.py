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
    
    # Получаем весь текст
    text = soup.get_text()
    
    # Разбиваем на строки
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    i = 0
    while i < len(lines) - 2:
        # Ищем "LIVE" в трёх соседних строках
        segment = ' '.join(lines[i:i+6]) if i+6 <= len(lines) else ' '.join(lines[i:])
        
        if 'LIVE' in segment and 'vs' in segment.lower():
            # Нашли блок с LIVE-матчем
            block = lines[i:i+8]
            block_text = ' | '.join(block)
            
            # Ищем команды
            vs_idx = -1
            for j, l in enumerate(block):
                if l.lower() == 'vs':
                    vs_idx = j
                    break
            
            if vs_idx >= 1 and vs_idx < len(block) - 1:
                team1 = block[vs_idx - 1]
                team2 = block[vs_idx + 1]
                
                # Ищем турнир (самая длинная строка рядом)
                tournament = ""
                for l in block:
                    if len(l) > len(tournament) and l not in [team1, team2, 'LIVE', 'vs']:
                        tournament = l
                
                # Ищем время матча
                time_str = ""
                for l in block:
                    tm = re.search(r'(\d+m\s*\d*s|\d+m|\d+:\d+)', l)
                    if tm:
                        time_str = tm.group(1)
                
                matches.append({
                    'team1': team1[:60],
                    'team2': team2[:60],
                    'tournament': tournament[:100] or "Неизвестный турнир",
                    'time': time_str
                })
                i += 8
                continue
        i += 1
    
    return matches

def main():
    conn = create_table()
    
    while True:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        matches = parse_live()
        
        print(f"\n{'='*50}")
        print(f"[{now}] 🔴 LIVE-МАТЧЕЙ: {len(matches)}")
        print(f"{'='*50}")
        
        for m in matches:
            print(f"\n🏆 {m['tournament']}")
            print(f"   {m['team1']} VS {m['team2']}")
            if m['time']:
                print(f"   ⏱️ {m['time']}")
            
            conn.execute(
                "INSERT INTO live_matches (team1, team2, tournament, status, match_time, updated) VALUES (?, ?, ?, 'LIVE', ?, ?)",
                (m['team1'], m['team2'], m['tournament'], m['time'], now)
            )
        
        if not matches:
            print("   Нет активных матчей")
        
        conn.commit()
        print(f"\n⏳ Обновление через 30 сек...")
        time.sleep(30)

if __name__ == "__main__":
    main()
