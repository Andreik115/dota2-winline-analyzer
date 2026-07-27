import sqlite3, time, re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

DB = "data/dota2.db"
URL = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"

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
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    driver.get(URL)
    time.sleep(5)
    
    body = driver.find_element(By.TAG_NAME, "body").text
    driver.quit()
    
    matches = []
    lines = [l.strip() for l in body.split('\n') if l.strip()]
    
    i = 0
    while i < len(lines) - 3:
        if lines[i] == 'LIVE' and i >= 2 and i < len(lines) - 2:
            team1 = lines[i-2] if i >= 2 else ""
            vs_check = lines[i-1] if i >= 1 else ""
            team2 = lines[i+1] if i+1 < len(lines) else ""
            tournament = lines[i+2] if i+2 < len(lines) else ""
            
            if vs_check.lower() == 'vs' and team1 and team2:
                time_str = ""
                for j in range(i+3, min(i+8, len(lines))):
                    tm = re.search(r'(\d+m\s*\d*s|\d+m)', lines[j])
                    if tm:
                        time_str = tm.group(1)
                        break
                
                matches.append({
                    'team1': team1,
                    'team2': team2,
                    'tournament': tournament,
                    'time': time_str
                })
                i += 5
                continue
        i += 1
    
    return matches

def main():
    conn = create_table()
    
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{now}] 📡 Парсинг live-матчей...")
        
        try:
            matches = parse_live()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            matches = []
        
        print(f"🔴 Найдено: {len(matches)}")
        
        for m in matches:
            print(f"   {m['team1']} VS {m['team2']} | {m['tournament']} | {m['time']}")
            conn.execute(
                "INSERT INTO live_matches (team1, team2, tournament, status, match_time, updated) VALUES (?, ?, ?, 'LIVE', ?, ?)",
                (m['team1'], m['team2'], m['tournament'], m['time'], now)
            )
        
        conn.commit()
        print(f"⏳ Обновление через 30 сек...")
        time.sleep(30)

if __name__ == "__main__":
    main()
