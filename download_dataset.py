# download_dataset.py
import requests
import sqlite3
import time

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
            league TEXT
        )
    """)
    conn.commit()
    return conn

def fetch_match(match_id):
    url = f"https://api.opendota.com/api/matches/{match_id}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # Проверяем, что есть пики (значит матч полный)
            if data.get("picks"):
                return data
    except:
        pass
    return None

def main():
    conn = create_table()
    added = 0
    
    # Используем известные ID про-матчей, которые точно есть
    # Это диапазон недавних про-матчей
    print("📡 Скачиваю про-матчи...")
    
    # Сначала получим список из proMatches
    r = requests.get("https://api.opendota.com/api/proMatches")
    match_ids = [m["match_id"] for m in r.json()[:200]]
    
    print(f"   Будем пробовать {len(match_ids)} матчей")
    
    for i, mid in enumerate(match_ids):
        exists = conn.execute("SELECT 1 FROM match_details WHERE match_id=?", (mid,)).fetchone()
        if exists:
            continue
        
        print(f"   [{i+1}/{len(match_ids)}] Матч {mid}...", end=" ")
        data = fetch_match(mid)
        
        if data:
            radiant_picks = [str(p["hero_id"]) for p in data["picks"] if p.get("is_radiant")]
            dire_picks = [str(p["hero_id"]) for p in data["picks"] if not p.get("is_radiant")]
            
            gold = ",".join([str(a) for a in (data.get("radiant_gold_adv") or []) if a is not None])
            xp = ",".join([str(a) for a in (data.get("radiant_xp_adv") or []) if a is not None])
            
            conn.execute("""
                INSERT OR IGNORE INTO match_details VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mid,
                (data.get("radiant_team") or {}).get("name", "Radiant"),
                (data.get("dire_team") or {}).get("name", "Dire"),
                1 if data.get("radiant_win") else 0,
                data.get("duration", 0),
                gold, xp,
                ",".join(radiant_picks),
                ",".join(dire_picks),
                data.get("league", {}).get("name", "Unknown")
            ))
            conn.commit()
            added += 1
            print("✅")
        else:
            print("❌")
        
        if added >= 50:  # Хватит 50 матчей для обучения
            break
    
    conn.close()
    print(f"\n✅ Готово! Скачано {added} матчей с пиками и графиками")

if __name__ == "__main__":
    main()
