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
    URL = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"
    
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
                return None
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            return None
    
    async def get_upcoming_matches(self):
        html = await self.fetch_page(self.URL)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        matches = []
        
        tables = soup.find_all('table', class_='wikitable')
        
        for table in tables:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    try:
                        team1 = cols[1].get_text(strip=True)
                        team2 = cols[2].get_text(strip=True)
                        tournament = cols[0].get_text(strip=True)
                        
                        if team1 and team2 and team1 != 'TBD' and team2 != 'TBD':
                            matches.append({
                                'team1': team1,
                                'team2': team2,
                                'tournament': tournament
                            })
                    except:
                        continue
        
        return matches[:30]
    
    async def update_database(self):
        print("📡 Парсинг Liquipedia...")
        
        upcoming = await self.get_upcoming_matches()
        print(f"   Найдено предстоящих матчей: {len(upcoming)}")
        
        session = get_session()
        added = 0
        
        for m in upcoming:
            existing = session.query(Match).filter(
                Match.team1_name == m['team1'],
                Match.team2_name == m['team2'],
                Match.tournament == m['tournament']
            ).first()
            
            if existing:
                continue
            
            match = Match(
                match_external_id=f"liquipedia_{m['team1']}_{m['team2']}",
                tournament=m['tournament'],
                team1_name=m['team1'],
                team2_name=m['team2'],
                start_time=datetime.now() + timedelta(hours=3),
                is_finished=False,
                is_live=False
            )
            session.add(match)
            added += 1
        
        session.commit()
        session.close()
        print(f"✅ Liquipedia: добавлено {added} матчей")
        return added

async def main():
    async with LiquipediaParser() as parser:
        await parser.update_database()

if __name__ == "__main__":
    asyncio.run(main())
