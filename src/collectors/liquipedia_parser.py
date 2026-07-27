import aiohttp
from bs4 import BeautifulSoup

class LiquipediaLiveParser:
    # Liquipedia требует указывать корректный User-Agent, иначе заблокирует
    HEADERS = {"User-Agent": "Dota2WinlineAnalyzer/1.0 (contact@yourdomain.com)"}
    URL = "https://liquipedia.net"

    async def get_live_matches(self):
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            async with session.get(self.URL) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                live_matches = []
                
                # Ищем блоки матчей в панели "Matches" на главной странице
                match_tables = soup.select('.infobox-matches')
                for table in match_tables:
                    # Проверяем, идет ли матч прямо сейчас (класс 'live')
                    is_live = table.select_one('.live')
                    if is_live:
                        team_left = table.select_one('.team-left a').get_text(strip=True)
                        team_right = table.select_one('.team-right a').get_text(strip=True)
                        tournament = table.select_one('.league-icon-small a').get('title', 'Unknown')
                        
                        live_matches.append({
                            "team_a": team_left,
                            "team_b": team_right,
                            "tournament": tournament,
                            "status": "LIVE"
                        })
                return live_matches
