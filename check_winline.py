# check_winline.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get('https://winline.ru/stavki/sport/kibersport/dota_2')
time.sleep(5)

body = driver.find_element(By.TAG_NAME, 'body').text
lines = body.split('\n')

print("=== ПЕРВЫЕ 50 СТРОК С WINLINE ===")
for l in lines[:50]:
    if l.strip():
        print(l.strip())

driver.quit()
