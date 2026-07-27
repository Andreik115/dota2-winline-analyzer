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
        except:
            return None
    
    async def get_matches(self):
        html = await self.fetch_page(self.URL)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        matches = []
        
        # Ищем все блоки команд
        team_blocks = soup.select('.block-team')
        
        # Ищем турниры
        tournaments = soup.select('.match-info-tournament-name')
        
        # Обрабатываем попарно (team1, team2)
        for i in range(0, len(team_blocks) - 1, 2):
            try:
                team1 = team_blocks[i].get_text(strip=True)
                team2 = team_blocks[i+1].get_text(strip=True)
                
                # Ищем ближайший турнир
                tournament = "Неизвестный турнир"
                tour_idx = i // 2
                if tour_idx < len(tournaments):
                    tournament = tournaments[tour_idx].get_text(strip=True)
                
                if team1 and team2 and team1 != 'TBD' and team2 != 'TBD':
                    matches.append({
                        'team1': team1,
                        'team2': team2,
                        'tournament': tournament
                    })
            except:
                continue
        
        print(f"   Найдено пар команд: {len(matches)}")
        return matches[:30]
    
    async def update_database(self):
        print("📡 Парсинг Liquipedia...")
        
        matches = await self.get_matches()
        
        session = get_session()
        added = 0
        
        for m in matches:
            ext_id = f"liquipedia_{m['team1']}_{m['team2']}_{m['tournament']}".replace(' ', '_')
            
            existing = session.query(Match).filter(
                Match.match_external_id == ext_id
            ).first()
            
            if existing:
                continue
            
            match = Match(
                match_external_id=ext_id,
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
