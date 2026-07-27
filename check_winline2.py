# check_winline2.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time, re

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get('https://winline.ru/stavki/sport/kibersport/dota_2')
time.sleep(5)

# Ищем элементы с классом, содержащим "event" или "match"
selectors = [
    "[class*='event']",
    "[class*='match']", 
    "[class*='game']",
    "[class*='sport-event']",
    "[data-testid*='event']",
    "[data-testid*='match']"
]

for sel in selectors:
    elems = driver.find_elements(By.CSS_SELECTOR, sel)
    if elems:
        print(f"\n{sel}: {len(elems)} шт.")
        for e in elems[:2]:
            print(f"  Текст: {e.text[:150]}")
            print(f"  Класс: {e.get_attribute('class')[:100]}")
            print()

driver.quit()
