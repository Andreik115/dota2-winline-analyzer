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
    lines = [l.strip() for l in driver.find_element(By.TAG_NAME, "body").text.split('\n') if l.strip()]
    driver.quit()
    
    matches = []
    i = 18  # Пропускаем меню
    
    while i < len(lines) - 5:
        # Ищем паттерн: team1 \n vs \n (Bo3) \n team2 \n турнир \n статус
        if lines[i+1] == 'vs' and lines[i+2].startswith('(Bo'):
            team1 = lines[i]
            team2 = lines[i+3]
            tournament = lines[i+4]
            status = lines[i+5]
            
            # Определяем время
            time_str = ""
            if re.match(r'\d+m', status):
                time_str = status
                status = "LIVE"
            elif status == 'LIVE':
                # Время может быть дальше
                if i+6 < len(lines) and re.match(r'\d+m', lines[i+6]):
                    time_str = lines[i+6]
            else:
                time_str = status
                status = "UPCOMING"
            
            matches.append({
                'team1': team1,
                'team2': team2,
                'tournament': tournament,
                'status': status,
                'time': time_str
            })
            i += 6
        else:
            i += 1
    
    return matches

def main():
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n{'='*50}")
        print(f"[{now}] 📡 Парсинг Liquipedia")
        print(f"{'='*50}")
        
        try:
            matches = parse()
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(30)
            continue
        
        live = [m for m in matches if m['status'] == 'LIVE']
        upcoming = [m for m in matches if m['status'] == 'UPCOMING']
        
        print(f"\n🔴 LIVE ({len(live)}):")
        for m in live:
            print(f"   {m['team1']} VS {m['team2']} | {m['tournament']} | ⏱️ {m['time']}")
        
        print(f"\n⏳ Предстоящие ({len(upcoming)}):")
        for m in upcoming:
            print(f"   {m['team1']} VS {m['team2']} | {m['tournament']} | ⏰ {m['time']}")
        
        print(f"\n⏳ Обновление через 30 сек...")
        time.sleep(30)

if __name__ == "__main__":
    main()
