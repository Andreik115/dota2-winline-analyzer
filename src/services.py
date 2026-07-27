import os
from bs4 import BeautifulSoup
import httpx
from src.normalizer import TeamNormalizer

class DotaAnalyzerService:
    def __init__(self):
        # Используем httpx, так как он есть в вашем стек-листе
        self.client = httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10.0)
        self.gigachat_token = os.getenv("GIGACHAT_CREDENTIALS", "YOUR_TOKEN")

    async def fetch_liquipedia_matches(self):
        """Парсинг текущих live-матчей с Ликипедии"""
        url = "https://liquipedia.net"
        try:
            resp = await self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                html = data.get("parse", {}).get("text", {}).get("*", "")
                soup = BeautifulSoup(html, 'lxml')
                matches = []
                
                for box in soup.select('.infobox-matches'):
                    if box.select_one('.live') or box.select_one('.match-countdown .live'):
                        t_left = box.select_one('.team-left a')
                        t_right = box.select_one('.team-right a')
                        tourney = box.select_one('.league-icon-small a')
                        
                        if t_left and t_right:
                            team_a = t_left.get_text(strip=True)
                            team_b = t_right.get_text(strip=True)
                            matches.append({
                                "liquipedia_id": f"{TeamNormalizer.normalize(team_a)}_{TeamNormalizer.normalize(team_b)}",
                                "team_a": team_a,
                                "team_b": team_b,
                                "tournament": tourney.get('title', 'Unknown') if tourney else 'Unknown'
                            })
                return matches
        except Exception as e:
            print(f"❌ Ошибка Liquipedia API: {e}")
        return []

    async def fetch_winline_odds(self, team_a: str, team_b: str):
        """Парсинг live-коэффициентов с Winline"""
        url = "https://winline.ru"  # Категория Dota 2
        try:
            resp = await self.client.get(url)
            if resp.status_code == 200:
                events = resp.json().get("data", {}).get("events", [])
                for ev in events:
                    w_a, w_b = ev.get("team1_name", ""), ev.get("team2_name", "")
                    if TeamNormalizer.is_same_team(team_a, w_a) and TeamNormalizer.is_same_team(team_b, w_b):
                        outcomes = ev.get("outcomes", {})
                        return {
                            "odds_a": float(outcomes.get("1", {}).get("coefficient", 1.0)),
                            "odds_b": float(outcomes.get("2", {}).get("coefficient", 1.0))
                        }
        except Exception as e:
            print(f"❌ Ошибка Winline API: {e}")
        return None

    async def get_gigachat_prediction(self, ctx: dict) -> str:
        """Запрос аналитики у GigaChat по протоколу HTTPX"""
        url = "https://sberbank.ru"
        headers = {
            "Authorization": f"Bearer {self.gigachat_token}",
            "Content-Type": "application/json"
        }
        prompt = f"Проанализируй live-матч Dota 2. Команда А: {ctx['team_a']}, Команда Б: {ctx['team_b']}. Текущие кэфы Winline: П1 - {ctx['odds_a']}, П2 - {ctx['odds_b']}. Исторический винрейт А: 56%, Б: 48%. Напиши краткий вердикт для ставки и % уверенности."
        
        payload = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            resp = await self.client.post(url, headers=headers, json=payload, verify=False)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Ошибка ИИ: {e}"
        return "Не удалось сгенерировать прогноз."
