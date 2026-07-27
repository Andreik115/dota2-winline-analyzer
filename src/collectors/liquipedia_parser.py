# src/collectors/liquipedia_parser.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import aiohttp
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from src.models.database import get_session, Match

class LiquipediaParser:
    # Пробуем разные страницы
    URLS = [
        "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches",
        "https://liquipedia.net/dota2/Main_Page",
    ]
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def fetch_page(self, url):
        try:
            async with self.session.get(url, timeout=15) as r:
                if r.status == 200:
                    return await r.text()
                print(f"   Статус {r.status} для {url[:50]}...")
                return None
        except Exception as e:
            print(f"   Ошибка: {e}")
            return None
    
    async def get_matches(self):
        """Пробуем все URL и все известные селекторы"""
        all_matches = []
        
        for url in self.URLS:
            html = await self.fetch_page(url)
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Пробуем разные селекторы
            selectors = [
                'table.wikitable tr',
                '.match-card',
                '.infobox_matches_content .match',
                'tr[data-toggle-area]',
                '.teamcard',
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for el in elements:
                    text = el.get_text(strip=True)
                    # Ищем две команды разделённые счётом (например "Team Spirit 2:1 VP")
                    if text and len(text) > 10:
                        all_matches.append(text[:100])
            
            if all_matches:
                break
        
        return all_matches[:30]
    
    async def update_database(self):
        print("📡 Парсинг Liquipedia...")
        
        matches = await self.get_matches()
        print(f"   Найдено элементов: {len(matches)}")
        
        if matches:
            print("   Примеры:")
            for m in matches[:3]:
                print(f"   • {m}")
        
        # Пока просто выводим, без сохранения
        return len(matches)

async def main():
    async with LiquipediaParser() as parser:
        await parser.update_database()

if __name__ == "__main__":
    asyncio.run(main())
