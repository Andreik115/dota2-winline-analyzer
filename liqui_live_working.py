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
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    matches = []
    
    for i, line in enumerate(lines):
        if line == 'LIVE' and i >= 2 and i < len(lines) - 2:
            # Ищем "Команда1 vs Команда2" перед LIVE
            # Структура: Команда1 \n vs \n (Bo3) \n Команда2 \n Турнир \n LIVE
            if i >= 4:
                team1 = lines[i-4]
                team2 = lines[i-1]
                vs_check = lines[i-3]
                
                if vs_check.lower() == 'vs' and team1 != 'LIVE' and team2 != 'LIVE':
                    tournament = lines[i+1] if i+1 < len(lines) else ""
                    
                    time_str = ""
                    for j in range(i+2, min(i+8, len(lines))):
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
        
        if not matches:
            print("   Нет активных матчей")
        
        time.sleep(30)

if __name__ == "__main__":
    main()
