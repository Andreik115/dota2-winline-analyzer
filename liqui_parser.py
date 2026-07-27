# liqui_parser.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sqlite3
import os

DB_PATH = "data/dota2.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_external_id TEXT UNIQUE,
            tournament TEXT,
            team1_name TEXT,
            team2_name TEXT,
            team1_odds REAL,
            team2_odds REAL,
            start_time TEXT,
            is_live INTEGER DEFAULT 0,
            is_finished INTEGER DEFAULT 0,
            score_team1 INTEGER,
            score_team2 INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

async def fetch_matches():
    url = "https://liquipedia.net/dota2/Liquipedia:Upcoming_and_ongoing_matches"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            html = await r.text()
    
    soup = BeautifulSoup(html, 'lxml')
    matches = []
    
    # Ищем команды
    team_blocks = soup.select('.block-team')
    tournaments = soup.select('.match-info-tournament-name')
    
    teams = []
    for t in team_blocks:
        text = t.get_text(strip=True)
        if text and text != 'TBD':
            teams.append(text)
    
    # Разбиваем на пары
    for i in range(0, len(teams) - 1, 2):
        team1 = teams[i]
        team2 = teams[i+1]
        
        # Ищем турнир
        tour = "Неизвестный турнир"
        tour_idx = i // 2
        if tour_idx < len(tournaments):
            tour = tournaments[tour_idx].get_text(strip=True)
        
        matches.append((team1, team2, tour))
    
    return matches

async def main():
    print("📡 Парсинг Liquipedia...")
    matches = await fetch_matches()
    print(f"   Найдено матчей: {len(matches)}")
    
    if not matches:
        print("❌ Матчи не найдены")
        return
    
    conn = init_db()
    added = 0
    
    for team1, team2, tour in matches:
        ext_id = f"liq_{team1}_{team2}_{tour}".replace(' ', '_')
        try:
            conn.execute(
                "INSERT INTO matches (match_external_id, tournament, team1_name, team2_name, start_time) VALUES (?, ?, ?, ?, ?)",
                (ext_id, tour, team1, team2, datetime.now() + timedelta(hours=3))
            )
            added += 1
        except sqlite3.IntegrityError:
            pass  # Уже существует
    
    conn.commit()
    conn.close()
    print(f"✅ Добавлено: {added}")

if __name__ == "__main__":
    asyncio.run(main())
