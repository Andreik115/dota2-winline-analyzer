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
            if data.get("picks"):
                return data
    except:
        pass
    return None

def save_match(conn, data, match_id):
    radiant_picks = [str(p["hero_id"]) for p in data["picks"] if p.get("is_radiant")]
    dire_picks = [str(p["hero_id"]) for p in data["picks"] if not p.get("is_radiant")]
    
    gold = ",".join([str(a) for a in (data.get("radiant_gold_adv") or []) if a is not None])
    xp = ",".join([str(a) for a in (data.get("radiant_xp_adv") or []) if a is not None])
    
    conn.execute("""
        INSERT OR IGNORE INTO match_details VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_id,
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

def main():
    conn = create_table()
    added = 0
    target = 500
    page = 0
    
    print("=" * 50)
    print("📡 Скачиваю паблик-матчи высокого MMR")
    print("=" * 50)
    
    while added < target and page < 20:
        url = f"https://api.opendota.com/api/publicMatches?mmr_descending=1&offset={page*100}"
        r = requests.get(url)
        matches = r.json()
        
        if not matches:
            print(f"   Страница {page+1}: пусто, конец")
            break
        
        print(f"\n   Страница {page+1}: {len(matches)} матчей")
        
        for m in matches:
            if added >= target:
                break
            
            mid = m["match_id"]
            exists = conn.execute("SELECT 1 FROM match_details WHERE match_id=?", (mid,)).fetchone()
            if exists:
                continue
            
            data = fetch_match(mid)
            if data:
                save_match(conn, data, mid)
                added += 1
                print(f"      ✅ {added}/{target} — матч {mid}")
            else:
                print(f"      ❌ матч {mid}")
            
            time.sleep(0.1)
        
        page += 1
    
    conn.close()
    print(f"\n{'=' * 50}")
    print(f"✅ ГОТОВО! Скачано {added} матчей")
    print(f"{'=' * 50}")

if __name__ == "__main__":
    main()
