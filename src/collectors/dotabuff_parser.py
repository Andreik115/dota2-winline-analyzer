# src/collectors/dotabuff_parser.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from src.models.database import get_session, Match

class DotabuffParser:
    URL = "https://www.dotabuff.com/esports/teams"
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def fetch(self, url):
        try:
            async with self.session.get(url, timeout=15) as r:
                if r.status == 200:
                    return await r.text()
                print(f"   Статус {r.status}")
                return None
        except Exception as e:
            print(f"   Ошибка: {e}")
            return None
    
    async def update_team_form(self):
        print("📊 Dotabuff: пробую разные селекторы...")
        html = await self.fetch(self.URL)
        if not html:
            return 0
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Пробуем найти команды
        for selector in ['a[href*="/esports/teams/"]', 'table tr td a', '.team-name', 'h3']:
            elements = soup.select(selector)
            if elements:
                print(f"   Селектор '{selector}': найдено {len(elements)}")
                for el in elements[:5]:
                    print(f"   • {el.get_text(strip=True)[:50]}")
        
        return 0

async def main():
    async with DotabuffParser() as parser:
        await parser.update_team_form()

if __name__ == "__main__":
    asyncio.run(main())
