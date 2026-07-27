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
        
        tables = soup.find_all('table')
        print(f'Найдено таблиц: {len(tables)}')
        
        for i, t in enumerate(tables[:5]):
            classes = t.get('class', [])
            rows = t.find_all('tr')
            print(f'\nТаблица {i}, классы={classes}, строк={len(rows)}')
            if rows:
                first_row_text = rows[0].get_text(strip=True)[:100]
                print(f'  Первая строка: {first_row_text}')

asyncio.run(main())
