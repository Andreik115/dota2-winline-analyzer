# src/collectors/update_matches.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import aiohttp
from datetime import datetime, timedelta
from src.models.database import get_session, Match

class MatchUpdater:
    BASE_URL = "https://api.stratz.com/api/v1"
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def get_pro_matches(self):
        """Получает последние про-матчи через STRATZ"""
        # Берём матчи за последние 7 дней
        url = f"{self.BASE_URL}/match/public"
        headers = {"Accept": "application/json"}
        
        async with self.session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data[:50]  # Первые 50 матчей
            print(f"❌ Ошибка STRATZ API: {resp.status}")
            return []
    
    async def update_database(self):
        print("📡 Запрашиваю матчи из STRATZ API...")
        
        matches = await self.get_pro_matches()
        
        if not matches:
            print("❌ Не удалось получить матчи")
            return 0, 0
        
        session = get_session()
        added = 0
        
        for match in matches:
            match_id_str = str(match.get('id'))
            
            # Проверяем, есть ли уже
            existing = session.query(Match).filter(
                Match.match_external_id == match_id_str
            ).first()
            
            if existing:
                continue
            
            radiant_team = match.get('radiantTeam', {}) or {}
            dire_team = match.get('direTeam', {}) or {}
            league = match.get('league', {}) or {}
            
            new_match = Match(
                match_external_id=match_id_str,
                tournament=league.get('name', 'Неизвестный турнир'),
                team1_name=radiant_team.get('name', 'Radiant'),
                team2_name=dire_team.get('name', 'Dire'),
                start_time=datetime.now() - timedelta(hours=match.get('durationSeconds', 0) / 3600),
                is_finished=True,
                score_team1=match.get('radiantKillsTeam', 0),
                score_team2=match.get('direKillsTeam', 0),
            )
            session.add(new_match)
            added += 1
        
        session.commit()
        session.close()
        
        print(f"✅ Готово! Добавлено матчей: {added}")
        return added, 0

async def main():
    async with MatchUpdater() as updater:
        await updater.update_database()

if __name__ == "__main__":
    asyncio.run(main())
