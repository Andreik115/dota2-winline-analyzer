# download_dataset.py
import requests
import sqlite3
import time
import os

DB_PATH = "data/dota2.db"

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
    
    for i, match in enumerate(matches[:100]):  # Берём 100 матчей
        match_id = match.get("match_id")
        
        exists = conn.execute("SELECT 1 FROM match_details WHERE match_id=?", (match_id,)).fetchone()
        if exists:
            print(f"   [{i+1}/100] Матч {match_id} уже есть, пропускаю")
            continue
        
        print(f"   [{i+1}/100] Скачиваю матч {match_id}...")
        details = fetch_match_details(match_id)
        
        if not details:
            print(f"   ⚠️ Не удалось скачать {match_id}")
            continue
        
        radiant_picks = []
        dire_picks = []
        for p in details.get("picks", []):
            hero = str(p.get("hero_id"))
            if p.get("is_radiant"):
                radiant_picks.append(hero)
            else:
                dire_picks.append(hero)
        
        gold_adv = []
        for adv in details.get("radiant_gold_adv", []) or []:
            if adv is not None:
                gold_adv.append(str(adv))
        
        xp_adv = []
        for adv in details.get("radiant_xp_adv", []) or []:
            if adv is not None:
                xp_adv.append(str(adv))
        
        conn.execute("""
            INSERT OR IGNORE INTO match_details 
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
    
    conn.close()
    print(f"\n✅ Скачано {added} матчей!")

if __name__ == "__main__":
    main()
