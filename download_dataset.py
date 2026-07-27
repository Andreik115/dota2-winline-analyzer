# download_dataset.py
import requests
import sqlite3
import time
import os

DB_PATH = "data/dota2.db"
MATCHES_TO_FETCH = 500  # Сколько матчей скачать

def create_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS match_details (
            match_id INTEGER PRIMARY KEY,
            radiant_team TEXT,
            dire_team TEXT,
            radiant_win INTEGER,
            duration INTEGER,
            radiant_gold_adv TEXT,
            radiant_xp_adv TEXT,
            radiant_picks TEXT,
            dire_picks TEXT,
            league TEXT,
            start_time INTEGER
        )
    """)
    conn.commit()
    return conn

def fetch_match_details(match_id):
    url = f"https://api.opendota.com/api/matches/{match_id}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def main():
    print("📡 Получаю список про-матчей...")
    r = requests.get("https://api.opendota.com/api/proMatches")
    matches = r.json()
    print(f"   Доступно: {len(matches)} матчей")
    
    conn = create_table()
    added = 0
    
    for match in matches[:MATCHES_TO_FETCH]:
        match_id = match.get("match_id")
        
        # Проверяем, есть ли уже
        exists = conn.execute("SELECT 1 FROM match_details WHERE match_id=?", (match_id,)).fetchone()
        if exists:
            continue
        
        print(f"   Скачиваю матч {match_id}... ({added+1}/{MATCHES_TO_FETCH})")
        details = fetch_match_details(match_id)
        
        if not details:
            time.sleep(0.5)
            continue
        
        # Собираем пики
        radiant_picks = []
        dire_picks = []
        for p in details.get("picks", []):
            hero = p.get("hero_id")
            if p.get("is_radiant"):
                radiant_picks.append(str(hero))
            else:
                dire_picks.append(str(hero))
        
        # Собираем преимущество по золоту (каждые 60 секунд)
        gold_adv = []
        for adv in details.get("radiant_gold_adv", []):
            if adv is not None:
                gold_adv.append(str(adv))
        
        xp_adv = []
        for adv in details.get("radiant_xp_adv", []):
            if adv is not None:
                xp_adv.append(str(adv))
        
        conn.execute("""
            INSERT OR IGNORE INTO match_details 
            (match_id, radiant_team, dire_team, radiant_win, duration,
             radiant_gold_adv, radiant_xp_adv, radiant_picks, dire_picks, league, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id,
            (details.get("radiant_team") or {}).get("name", "Radiant"),
            (details.get("dire_team") or {}).get("name", "Dire"),
            1 if details.get("radiant_win") else 0,
            details.get("duration", 0),
            ",".join(gold_adv),
            ",".join(xp_adv),
            ",".join(radiant_picks),
            ",".join(dire_picks),
            details.get("league", {}).get("name", "Unknown"),
            details.get("start_time", 0)
        ))
        conn.commit()
        added += 1
        time.sleep(0.3)  # Пауза, чтобы не забанили
    
    conn.close()
    print(f"\n✅ Скачано {added} матчей с деталями!")

if __name__ == "__main__":
    main()
