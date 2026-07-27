# winline_parser.py
import time
import sqlite3
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
    
    def get_matches_with_odds(self):
        """Собирает матчи и коэффициенты"""
        print("📡 Загружаю Winline...")
        self.driver.get(self.URL)
        time.sleep(5)  # Ждём загрузку
        
        matches = []
        
        # Ищем все текстовые блоки на странице
        body = self.driver.find_element(By.TAG_NAME, "body").text
        
        # Ищем названия команд и коэффициенты
        # Пример структуры Winline: Team Spirit 1.85 Virtus.pro 2.10
        lines = body.split('\n')
        
        i = 0
        while i < len(lines) - 3:
            line = lines[i].strip()
            # Ищем строки, похожие на названия команд
            if line and line[0].isupper() and len(line) > 3:
                try:
                    # Проверяем, есть ли дальше числа (коэффициенты)
                    next_lines = [lines[i+j].strip() for j in range(1, 5)]
                    nums = []
                    for nl in next_lines:
                        try:
                            nums.append(float(nl))
                        except:
                            pass
                    
                    if len(nums) >= 2:
                        team1 = line
                        team2_candidate = ""
                        for nl in next_lines:
                            if nl and nl[0].isupper() and len(nl) > 3:
                                team2_candidate = nl
                                break
                        
                        if team2_candidate:
                            matches.append({
                                'team1': team1,
                                'team2': team2_candidate,
                                'odds1': nums[0],
                                'odds2': nums[-1]
                            })
                except:
                    pass
            i += 1
        
        return matches[:30]
    
    def update_db(self):
        matches = self.get_matches_with_odds()
        print(f"   Найдено матчей с кэфами: {len(matches)}")
        
        if not matches:
            print("⚠️ Не удалось распарсить. Сохраняю скриншот...")
            self.driver.save_screenshot("winline_debug.png")
            print("   Скриншот сохранён: winline_debug.png")
            return 0
        
        conn = sqlite3.connect(DB_PATH)
        updated = 0
        
        for m in matches:
            # Ищем матч по названиям команд
            cursor = conn.execute(
                "SELECT id FROM matches WHERE team1_name LIKE ? AND team2_name LIKE ?",
                (f"%{m['team1']}%", f"%{m['team2']}%")
            )
            row = cursor.fetchone()
            if row:
                conn.execute(
                    "UPDATE matches SET team1_odds=?, team2_odds=? WHERE id=?",
                    (m['odds1'], m['odds2'], row[0])
                )
                updated += 1
        
        conn.commit()
        conn.close()
        print(f"✅ Обновлено коэффициентов: {updated}")
        return updated
    
    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    parser = WinlineParser(headless=False)  # Увидишь браузер
    parser.update_db()
    parser.close()
