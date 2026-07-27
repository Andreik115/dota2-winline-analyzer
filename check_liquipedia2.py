import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def main():
    async with aiohttp.ClientSession() as s:
        r = await s.get(
            'https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        html = await r.text()
        soup = BeautifulSoup(html, 'lxml')
        
        # Ищем все div с классами, содержащими match
        for pattern in ['match', 'team', 'versus', 'tournament', 'game', 'event']:
            elements = soup.select(f'[class*="{pattern}"]')
            if elements:
                print(f'\nЭлементы с "{pattern}" в классе: {len(elements)}')
                for el in elements[:3]:
                    print(f'  Класс: {el.get("class", [])}')
                    print(f'  Текст: {el.get_text(strip=True)[:80]}')
                    print()

asyncio.run(main())
