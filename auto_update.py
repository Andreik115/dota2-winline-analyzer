# auto_update.py
import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.collectors.update_matches import main

async def run_loop():
    while True:
        print(f"\n⏰ {time.strftime('%H:%M:%S')} — Обновление...")
        try:
            await main()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        print(f"😴 Жду 30 минут...")
        await asyncio.sleep(1800)  # 30 минут

if __name__ == "__main__":
    asyncio.run(run_loop())
