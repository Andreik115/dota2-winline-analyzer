# liqui_live.py
import sqlite3, time, re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

DB = "data/dota2.db"

def create_tables():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT, team2 TEXT,
            score1 TEXT, score2 TEXT,
            tournament TEXT, winner TEXT
        )
    """)
    conn.commit()
    return conn

def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    conn = create_tables()
    added = 0
    
    # Страницы с результатами
    urls = [
        "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches",
        "https://liquipedia.net/dota2/Main_Page",
    ]
    
    for url in urls:
        print(f"📡 Загружаю {url}...")
        driver.get(url)
        time.sleep(5)  # Ждём JavaScript
        
        # Ищем все матчи через XPath
        elements = driver.find_elements(By.XPATH, 
            "//*[contains(text(),':') and contains(text(),'-')] | //*[contains(@class,'match')] | //*[contains(@class,'versus')]")
        
        for el in elements[:50]:
            text = el.text.strip()
            if not text or len(text) > 200:
                continue
            
            # Ищем счёт в формате "2:1" или "2-1"
            scores = re.findall(r'(\d+)\s*[-:]\s*(\d+)', text)
            if not scores:
                continue
            
            print(f"   Найдено: {text[:120]}")
            
            # Пробуем извлечь команды
            for s1, s2 in scores:
                parts = re.split(r'\d+\s*[-:]\s*\d+', text)
                if len(parts) >= 2:
                    team1 = parts[0].strip()[-30:]
                    team2 = parts[1].strip()[:30]
                    if team1 and team2 and len(team1) > 2 and len(team2) > 2:
                        try:
                            conn.execute(
                                "INSERT INTO match_results (team1, team2, score1, score2, winner) VALUES (?, ?, ?, ?, ?)",
                                (team1, team2, s1, s2, team1 if int(s1) > int(s2) else team2)
                            )
                            added += 1
                        except:
                            pass
    
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM match_results").fetchone()[0]
    conn.close()
    driver.quit()
    
    print(f"\n✅ Готово! Добавлено: {added}, всего в базе: {total}")

if __name__ == "__main__":
    main()
