# winline_parser.py
import time, sqlite3, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

DB_PATH = "data/dota2.db"

class WinlineParser:
    URL = "https://winline.ru/stavki/sport/kibersport/dota_2"
    
    def __init__(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    
    def parse(self):
        print("📡 Загружаю Winline...")
        self.driver.get(self.URL)
        time.sleep(5)
        
        events = self.driver.find_elements(By.CSS_SELECTOR, ".event-card")
        print(f"   Найдено событий: {len(events)}")
        
        matches = []
        for event in events:
            try:
                text = event.text
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                # Первые две строки — команды (если не начинаются с цифр)
                team1, team2 = "", ""
                odds = []
                
                for line in lines:
                    # Проверяем коэффициент (число.двецифры)
                    if re.match(r'^\d+\.\d{2}$', line):
                        odds.append(float(line))
                    elif not team1 and not line.startswith('+') and not line[0].isdigit():
                        team1 = line
                    elif team1 and not team2 and not line.startswith('+') and not line[0].isdigit():
                        team2 = line
                
                if team1 and team2 and len(odds) >= 2:
                    matches.append({
                        'team1': team1,
                        'team2': team2,
                        'odds1': odds[0],  # П1
                        'odds2': odds[2] if len(odds) >= 3 else odds[1]  # П2
                    })
                    print(f"   {team1} ({odds[0]}) vs {team2} ({odds[-1]})")
            except:
                pass
        
        return matches
    
   def update_db(self):
    matches = self.parse()
    
    if not matches:
        print("⚠️ Матчи не найдены")
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    added = 0
    updated = 0
    
    for m in matches:
        # Ищем матч по фрагментам
        cursor = conn.execute(
            "SELECT id FROM matches WHERE (team1_name LIKE ? OR team2_name LIKE ?)",
            (f"%{m['team1']}%", f"%{m['team2']}%")
        )
        row = cursor.fetchone()
        
        if row:
            # Обновляем коэффициенты
            conn.execute(
                "UPDATE matches SET team1_odds=?, team2_odds=? WHERE id=?",
                (m['odds1'], m['odds2'], row[0])
            )
            updated += 1
        else:
            # Добавляем новый матч
            ext_id = f"winline_{m['team1']}_{m['team2']}".replace(' ', '_')
            try:
                conn.execute(
                    "INSERT INTO matches (match_external_id, tournament, team1_name, team2_name, team1_odds, team2_odds) VALUES (?, ?, ?, ?, ?, ?)",
                    (ext_id, "Winline Dota 2", m['team1'], m['team2'], m['odds1'], m['odds2'])
                )
                added += 1
            except:
                pass
    
    conn.commit()
    conn.close()
    print(f"✅ Добавлено: {added}, Обновлено: {updated}")
    return added + updated
