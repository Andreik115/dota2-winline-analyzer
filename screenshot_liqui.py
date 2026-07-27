from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

print("Загружаю страницу...")
driver.get('https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches')
time.sleep(5)

driver.save_screenshot('liqui_screen.png')
print('✅ Скриншот: liqui_screen.png')

body = driver.find_element('tag name', 'body').text
lines = [l.strip() for l in body.split('\n') if l.strip()][:60]
print('\n=== ТЕКСТ СТРАНИЦЫ ===')
for l in lines:
    print(l)

driver.quit()
