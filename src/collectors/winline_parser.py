import aiohttp
from src.utils.normalizer import TeamNormalizer

class WinlineParser:
    # Внутренний эндпоинт линии Winline (актуальный формат JSON-структуры)
    API_URL = "https://winline.ru"  # 4 - ID категории Dota 2
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    async def get_live_odds(self, team_a: str, team_b: str):
        """Ищет матч по названиям команд и возвращает коэффициенты П1 и П2"""
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            try:
                async with session.get(self.API_URL, timeout=10) as resp:
                    if resp.status != 200:
                        return None
                    
                    data = await resp.json()
                    events = data.get("data", {}).get("events", [])
                    
                    for event in events:
                        w_team_a = event.get("team1_name", "")
                        w_team_b = event.get("team2_name", "")
                        
                        # Сопоставляем команды через нормализатор
                        if TeamNormalizer.is_same_team(team_a, w_team_a) and TeamNormalizer.is_same_team(team_b, w_team_b):
                            outcomes = event.get("outcomes", {})
                            # Обычные исходы на победу (П1 и П2)
                            odds_a = outcomes.get("1", {}).get("coefficient")
                            odds_b = outcomes.get("2", {}).get("coefficient")
                            
                            if odds_a and odds_b:
                                return {"odds_a": float(odds_a), "odds_b": float(odds_b)}
            except Exception as e:
                print(f"⚠️ Ошибка парсинга Winline: {e}")
            return None
