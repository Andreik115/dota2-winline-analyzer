# winline_parser.py
import time
import sqlite3
import os
import re
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
    
    def get_matches(self):
        print("📡 Загружаю Winline...")
        self.driver.get(self.URL)
        time.sleep(5)
        
        matches = []
        
        # Ищем все кнопки/блоки с коэффициентами
        # У Winline кэфы обычно в элементах с data-testid или class содержащим "outcome"
        try:
            # Ищем все элементы, которые могут содержать коэффициенты (числа)
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '.')]")
            
            odds_elements = []
            for el in elements:
                text = el.text.strip()
                # Проверяем, похоже ли на коэффициент (число с точкой)
                if re.match(r'^\d+\.\d{2}$', text):
                    odds_elements.append(float(text))
            
            # Ищем названия команд (текст КАПСОМ или с заглавной)
            team_elements = self.driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'team') or contains(@class, 'participant') or contains(@class, 'name')]")
            
            teams = []
            for el in team_elements:
                text = el.text.strip()
                if text and len(text) > 3:
                    teams.append(text)
            
            print(f"   Команд: {len(teams)}, Кэфов: {len(odds_elements)}")
            
            # Показываем что нашли
            print("   Команды:", teams[:10])
            print("   Кэфы:", odds_elements[:10])
            
        except Exception as e:
            print(f"   Ошибка: {e}")
        
        return matches
    
    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    parser = WinlineParser(headless=True)
    parser.get_matches()
    parser.close()
