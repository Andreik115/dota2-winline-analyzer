import aiohttp
from bs4 import BeautifulSoup
from src.utils.normalizer import TeamNormalizer

class LiquipediaParser:
    API_URL = "https://liquipedia.net"
    HEADERS = {
        "User-Agent": "Dota2WinlineAnalyzer/2.0 (your_email@example.com)",
        "Accept-Encoding": "gzip"
    }

    async def fetch_live_matches(self):
        """Сканирует главную страницу через API парсинга секций для поиска Live-игр"""
        params = {
            "action": "parse",
            "page": "Main_Page",
            "format": "json",
            "prop": "text"
        }
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            async with session.get(self.API_URL, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                html = data.get("parse", {}).get("text", {}).get("*", "")
                
                soup = BeautifulSoup(html, 'lxml')
                matches = []
                
                # Селектор блоков текущих матчей на Liquipedia
                match_boxes = soup.select('.infobox-matches')
                for box in match_boxes:
                    is_live = box.select_one('.live') or box.select_one('.match-countdown .live')
                    if not is_live:
                        continue
                        
                    t_left = box.select_one('.team-left a')
                    t_right = box.select_one('.team-right a')
                    tournament_node = box.select_one('.league-icon-small a')
                    
                    if t_left and t_right:
                        team_a = t_left.get_text(strip=True)
                        team_b = t_right.get_text(strip=True)
                        match_id = f"{TeamNormalizer.normalize(team_a)}_{TeamNormalizer.normalize(team_b)}"
                        
                        matches.append({
                            "liquipedia_id": match_id,
                            "team_a": team_a,
                            "team_b": team_b,
                            "tournament": tournament_node.get('title', 'Unknown') if tournament_node else 'Unknown',
                            "picks_a": [], # Герои парсятся со страницы матча, если драфт начался
                            "picks_b": []
                        })
                return matches
