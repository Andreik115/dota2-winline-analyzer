from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3, time, re
from datetime import datetime

URL = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"
DB = "data/dota2.db"

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def parse():
    driver = get_driver()
    driver.get(URL)
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

def main():
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n[20:56:31] 📡 Парсинг Liquipedia")
        
        try:
            matches = parse()
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(30)
            continue
        
        live = [m for m in matches if m['status'] == 'LIVE']
        upcoming = [m for m in matches if m['status'] == 'UPCOMING']
        
        print(f"🔴 LIVE: {len(live)}")
        for m in live:
            print(f"   {m['team1']} VS {m['team2']} | {m['tournament']} | ⏱️ {m['time']}")
        
        # СОХРАНЯЕМ В БАЗУ
        conn = sqlite3.connect(DB)
        conn.execute("DELETE FROM live_matches")
        for m in matches:
            conn.execute(
                "INSERT INTO live_matches (team1, team2, tournament, status, match_time, updated) VALUES (?, ?, ?, ?, ?, ?)",
                (m['team1'], m['team2'], m['tournament'], m['status'], m['time'], now)
            )
        conn.commit()
        conn.close()
        print(f"💾 Сохранено в базу: {len(matches)} матчей")
        
        print(f"⏳ Обновление через 30 сек...")
        time.sleep(30)

if __name__ == "__main__":
    main()
