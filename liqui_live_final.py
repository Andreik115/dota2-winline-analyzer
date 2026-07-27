# liqui_live_final.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3, time, re
from datetime import datetime

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

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def parse():
    driver = get_driver()
    try:
        driver.get(URL)
        time.sleep(5)
        text = driver.find_element(By.TAG_NAME, "body").text
    finally:
        driver.quit()
    
    matches = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        if line.strip() == 'LIVE' and i >= 2 and i+2 < len(lines):
            team1 = lines[i-2].strip()
            vs_line = lines[i-1].strip()
            team2 = lines[i+1].strip()
            tournament = lines[i+2].strip() if i+2 < len(lines) else ""
            
            # Ищем время матча (например "23m 52s")
            time_str = ""
            for j in range(i+3, min(i+8, len(lines))):
                m = re.search(r'(\d{1,2}m\s*\d{1,2}s|\d{1,2}m)', lines[j])
                if m:
                    time_str = m.group(1)
                    break
            
            if vs_line.lower() in ['vs', '(bo3)', '(bo5)'] or 'vs' in vs_line.lower():
                matches.append({
                    'team1': team1,
                    'team2': team2,
                    'tournament': tournament,
                    'time': time_str
                })
    
    return matches

def main():
    conn = create_table()
    
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"[{now}] 📡 Парсинг...")
        
        try:
            matches = parse()
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(30)
            continue
        
        print(f"🔴 LIVE: {len(matches)}")
        for m in matches:
            print(f"   {m['team1']} VS {m['team2']} | {m['tournament']} | {m['time']}")
            conn.execute(
                "INSERT OR IGNORE INTO live_matches (team1, team2, tournament, status, match_time, updated) VALUES (?, ?, ?, 'LIVE', ?, ?)",
                (m['team1'], m['team2'], m['tournament'], m['time'], now)
            )
        conn.commit()
        time.sleep(30)

if __name__ == "__main__":
    main()
