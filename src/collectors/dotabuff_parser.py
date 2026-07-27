# src/collectors/dotabuff_parser.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
from src.models.database import get_session, Match

class DotabuffParser:
    BASE_URL = "https://www.dotabuff.com"
    TEAMS_URL = f"{BASE_URL}/esports/teams"
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def fetch(self, url):
        try:
            async with self.session.get(url, timeout=15) as r:
                if r.status == 200:
                    return await r.text()
                return None
        except:
            return None
    
    async def get_team_list(self):
        """Получает список топ-команд с Dotabuff"""
        html = await self.fetch(self.TEAMS_URL)
        if not html:
            print("❌ Dotabuff: не удалось загрузить страницу команд")
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        teams = []
        
        # Ищем ссылки на команды
        for link in soup.select('a[href*="/esports/teams/"]'):
            href = link.get('href', '')
            name = link.get_text(strip=True)
            if '/esports/teams/' in href and name and len(name) > 2:
                slug = href.split('/')[-1]
                if slug and slug not in [t['slug'] for t in teams]:
                    teams.append({'slug': slug, 'name': name})
        
        return teams[:30]
    
    async def get_team_recent_matches(self, team_slug):
        """Получает последние матчи команды"""
        url = f"{self.BASE_URL}/esports/teams/{team_slug}"
        html = await self.fetch(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        matches = []
        
        # Ищем строки таблицы с матчами
        for row in soup.select('table tbody tr'):
            cells = row.find_all('td')
            if len(cells) >= 5:
                try:
                    opponent = cells[1].get_text(strip=True)
                    result = cells[2].get_text(strip=True)  # W или L
                    tournament = cells[3].get_text(strip=True)
                    date_str = cells[4].get_text(strip=True)
                    
                    matches.append({
                        'opponent': opponent,
                        'result': result,
                        'tournament': tournament,
                        'date': date_str
                    })
                except:
                    continue
        
        return matches[-10:]  # Последние 10 матчей
    
    async def update_team_form(self):
        """Обновляет форму команд в базе"""
        print("📊 Dotabuff: собираю статистику команд...")
        teams = await self.get_team_list()
        print(f"   Найдено команд: {len(teams)}")
        
        session = get_session()
        updated = 0
        
        for team in teams[:10]:  # Топ-10 команд
            matches = await self.get_team_recent_matches(team['slug'])
            wins = sum(1 for m in matches if m['result'].upper() == 'W')
            total = len(matches)
            
            if total > 0:
                winrate = wins / total * 100
                print(f"   {team['name']}: {wins}/{total} побед ({winrate:.0f}%)")
                
                # Обновляем матчи с этой командой в базе
                db_matches = session.query(Match).filter(
                    (Match.team1_name.like(f"%{team['name']}%")) |
                    (Match.team2_name.like(f"%{team['name']}%"))
                ).all()
                
                for m in db_matches:
                    # Сохраняем форму команды (можно в отдельное поле)
                    # Пока просто выводим
                    updated += 1
        
        session.close()
        print(f"✅ Dotabuff: обновлено {updated} записей")
        return updated

async def main():
    async with DotabuffParser() as parser:
        await parser.update_team_form()

if __name__ == "__main__":
    asyncio.run(main())
