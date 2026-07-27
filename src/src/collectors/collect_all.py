# collect_all.py
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.collectors.liquipedia_parser import LiquipediaParser
from src.collectors.dotabuff_parser import DotabuffParser

async def collect_all():
    print("=" * 50)
    print("🔄 Сбор данных")
    print("=" * 50)
    
    # Liquipedia — расписание
    print("\n📋 Liquipedia:")
    try:
        async with LiquipediaParser() as lp:
            await lp.update_database()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Dotabuff — статистика команд
    print("\n📊 Dotabuff:")
    try:
        async with DotabuffParser() as dp:
            await dp.update_team_form()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n✅ Сбор завершён!")
    print("📊 Открой http://localhost:8000")

if __name__ == "__main__":
    asyncio.run(collect_all())
