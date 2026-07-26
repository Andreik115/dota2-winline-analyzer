# src/collectors/update_matches.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import aiohttp
from datetime import datetime
from src.models.database import get_session, Match

class OpenDotaUpdater:
    BASE_URL = "https://api.opendota.com/api"
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def get_pro_matches(self, limit: int = 100):
        """Получает последние профессиональные матчи"""
        url = f"{self.BASE_URL}/proMatches"
        async with self.session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
            print(f"❌ Ошибка API: {resp.status}")
            return []
    
    async def get_live_matches(self):
        """Получает текущие live-матчи"""
        url = f"{self.BASE_URL}/live"
        async with self.session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
            return []
    
    async def update_database(self):
        """Обновляет базу данных свежими матчами"""
        print("📡 Запрашиваю матчи из OpenDota API...")
        
        # Получаем про-матчи
        pro_matches = await self.get_pro_matches(limit=50)
        
        # Получаем live-матчи
        live_matches = await self.get_live_matches()
        
        session = get_session()
        added = 0
        updated = 0
        
        # Обрабатываем про-матчи
        for match in pro_matches:
            match_id_str = str(match.get('match_id'))
            radiant_team = match.get('radiant_team', {}) or {}
            dire_team = match.get('dire_team', {}) or {}
            
            team1_name = radiant_team.get('name', 'Radiant')
            team2_name = dire_team.get('name', 'Dire')
            
            # Проверяем, есть ли уже такой матч
            existing = session.query(Match).filter(
                Match.match_external_id == match_id_str
            ).first()
            
            if existing:
                # Обновляем счёт если матч завершён
                if match.get('radiant_win') is not None:
                    existing.score_team1 = match.get('radiant_score')
                    existing.score_team2 = match.get('dire_score')
                    existing.is_finished = True
                    existing.is_live = False
                    updated += 1
            else:
                # Добавляем новый матч
                new_match = Match(
                    match_external_id=match_id_str,
                    tournament=match.get('league_name', 'Неизвестный турнир'),
                    team1_name=team1_name,
                    team2_name=team2_name,
                    start_time=datetime.fromtimestamp(match.get('start_time', 0)),
                    is_finished=bool(match.get('radiant_win') is not None),
                    score_team1=match.get('radiant_score'),
                    score_team2=match.get('dire_score'),
                    team1_odds=None,  # Пока нет парсинга Winline
                    team2_odds=None
                )
                session.add(new_match)
                added += 1
        
        # Обрабатываем live-матчи
        for match in live_matches:
            match_id_str = str(match.get('match_id'))
            radiant_team = match.get('radiant_team', {}) or {}
            dire_team = match.get('dire_team', {}) or {}
            
            team1_name = radiant_team.get('name', 'Radiant')
            team2_name = dire_team.get('name', 'Dire')
            
            existing = session.query(Match).filter(
                Match.match_external_id == match_id_str
            ).first()
            
            if not existing:
                new_match = Match(
                    match_external_id=match_id_str,
                    tournament=match.get('league_name', 'Live-матч'),
                    team1_name=team1_name,
                    team2_name=team2_name,
                    start_time=datetime.now(),
                    is_live=True,
                    is_finished=False
                )
                session.add(new_match)
                added += 1
            else:
                existing.is_live = True
                updated += 1
        
        session.commit()
        session.close()
        
        print(f"✅ Готово! Добавлено: {added}, Обновлено: {updated}")
        return added, updated

async def main():
    async with OpenDotaUpdater() as updater:
        await updater.update_database()

if __name__ == "__main__":
    asyncio.run(main())
