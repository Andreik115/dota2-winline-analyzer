# update_data.py
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.collectors.update_matches import main

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 Обновление данных из OpenDota API")
    print("=" * 50)
    asyncio.run(main())
    print("\n📊 Теперь открой http://localhost:8000 и обнови страницу")
