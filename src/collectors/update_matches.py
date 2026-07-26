import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import aiohttp
from datetime import datetime
from src.models.database import get_session, Match
from src.config import STRATZ_API_KEY

class MatchUpdater:
    BASE_URL = "https://api.stratz.com/graphql"
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        headers = {
            "Authorization": f"Bearer {STRATZ_API_KEY}",
            "Content-Type": "application/json"
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def get_pro_matches(self):
        query = """
        query {
            matches(request: { take: 20, isParsed: true }) {
                id
                radiantTeam { name }
                direTeam { name }
                league { name }
                endDateTime
                radiantKillsTeam
                direKillsTeam
            }
        }
        """
        
        try:
            async with self.session.post(self.BASE_URL, json={"query": query}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", {}).get("matches", [])
                print(f"❌ Ошибка: {resp.status}")
                return []
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return []
    
    async def update_database(self):
        print("📡 Запрашиваю матчи из STRATZ...")
        
        if not STRATZ_API_KEY:
            print("❌ Нет ключа STRATZ. Добавь в .env: STRATZ_API_KEY=твой_ключ")
            return 0, 0
        
        matches = await self.get_pro_matches()
        
        if not matches:
            return 0, 0
        
        session = get_session()
        added = 0
        
        for match in matches:
            match_id_str = str(match.get('id'))
            
            existing = session.query(Match).filter(
                Match.match_external_id == match_id_str
            ).first()
            
            if existing:
                continue
            
            radiant = match.get('radiantTeam', {}) or {}
            dire = match.get('direTeam', {}) or {}
            league = match.get('league', {}) or {}
            
            new_match = Match(
                match_external_id=match_id_str,
                tournament=league.get('name', 'Неизвестно'),
                team1_name=radiant.get('name', 'Radiant'),
                team2_name=dire.get('name', 'Dire'),
                start_time=datetime.fromtimestamp(match.get('endDateTime', 0)) if match.get('endDateTime') else datetime.now(),
                is_finished=True,
                score_team1=match.get('radiantKillsTeam'),
                score_team2=match.get('direKillsTeam'),
            )
            session.add(new_match)
            added += 1
        
        session.commit()
        session.close()
        print(f"✅ Добавлено: {added}")
        return added, 0

async def main():
    async with MatchUpdater() as updater:
        await updater.update_database()

if __name__ == "__main__":
    asyncio.run(main())
