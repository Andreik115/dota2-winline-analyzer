# liqui_live_working.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time, re
from datetime import datetime

URL = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"

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
    text = driver.find_element(By.TAG_NAME, "body").text
    driver.quit()
    
    lines = text.split('\n')
    matches = []
    i = 0
    
    while i < len(lines) - 5:
        # Ищем структуру: Команда1 \n vs \n (Bo3) \n Команда2 \n Турнир \n LIVE
        if lines[i+1].strip().lower() == 'vs' and lines[i+4].strip() == 'LIVE':
            team1 = lines[i].strip()
            team2 = lines[i+3].strip()
            tournament = lines[i+4].strip()  # Это LIVE, турнир выше
            # Ищем турнир
            tournament = lines[i+5].strip() if i+5 < len(lines) and 'LIVE' not in lines[i+5] else ""
            
            # Ищем время
            time_str = ""
            for j in range(i+6, min(i+12, len(lines))):
                m = re.search(r'(\d+m\s*\d*s|\d+m)', lines[j])
                if m:
                    time_str = m.group(1)
                    break
            
            matches.append({
                'team1': team1,
                'team2': team2,
                'tournament': tournament,
                'time': time_str
            })
            i += 8
        else:
            i += 1
    
    return matches

def main():
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{now}] 📡 Парсинг...")
        
        try:
            matches = parse()
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(30)
            continue
        
        print(f"🔴 LIVE-МАТЧЕЙ: {len(matches)}")
        for m in matches:
            print(f"   {m['team1']} VS {m['team2']} | {m['tournament']} | ⏱️ {m['time']}")
        
        time.sleep(30)

if __name__ == "__main__":
    main()
