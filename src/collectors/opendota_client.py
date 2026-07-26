import aiohttp
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

class OpenDotaClient:
    BASE_URL = "https://api.opendota.com/api"
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def get_pro_matches(self, limit: int = 50) -> List[Dict]:
        url = f"{self.BASE_URL}/proMatches"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []
    
    async def get_live_matches(self) -> List[Dict]:
        url = f"{self.BASE_URL}/live"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []
    
    async def get_team_matches(self, team_id: int, limit: int = 20) -> List[Dict]:
        url = f"{self.BASE_URL}/teams/{team_id}/matches"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data[:limit]
            return []
    
    async def get_hero_stats(self) -> List[Dict]:
        url = f"{self.BASE_URL}/heroStats"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []

async def test_fetch():
    async with OpenDotaClient() as client:
        print("📡 Запрашиваю матчи с OpenDota...")
        matches = await client.get_pro_matches(limit=5)
        for match in matches:
            radiant = match.get('radiant_team', {}).get('name', 'Radiant')
            dire = match.get('dire_team', {}).get('name', 'Dire')
            league = match.get('league_name', 'Неизвестно')
            print(f"🏆 {radiant} vs {dire} | {league}")

if __name__ == "__main__":
    asyncio.run(test_fetch())
