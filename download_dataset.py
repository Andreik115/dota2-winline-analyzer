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
            if data.get("picks") and data.get("radiant_gold_adv"):
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
    
    # Этап 1: Про-матчи
    print("=" * 50)
    print("📡 Этап 1: Про-матчи")
    print("=" * 50)
    
    r = requests.get("https://api.opendota.com/api/proMatches")
    pro_ids = [m["match_id"] for m in r.json()[:300]]
    print(f"   Будем пробовать {len(pro_ids)} матчей\n")
    
    for i, mid in enumerate(pro_ids):
        if added >= target:
            break
        
        exists = conn.execute("SELECT 1 FROM match_details WHERE match_id=?", (mid,)).fetchone()
        if exists:
            continue
        
        print(f"   [{i+1}/{len(pro_ids)}] Про-матч {mid}...", end=" ")
        data = fetch_match(mid)
        
        if data:
            save_match(conn, data, mid)
            added += 1
            print(f"✅ (всего: {added})")
        else:
            print("❌")
        
        time.sleep(0.15)
    
    # Этап 2: Паблик-матчи высокого MMR
    if added < target:
        print(f"\n{'=' * 50}")
        print(f"📡 Этап 2: Паблик-матчи (high MMR)")
        print(f"{'=' * 50}\n")
        
        for page in range(5):
            if added >= target:
                break
            r = requests.get(f"https://api.opendota.com/api/publicMatches?mmr_descending=1&offset={page*100}")
            pub_matches = r.json()
            
            for i, m in enumerate(pub_matches):
                if added >= target:
                    break
                
                mid = m["match_id"]
                exists = conn.execute("SELECT 1 FROM match_details WHERE match_id=?", (mid,)).fetchone()
                if exists:
                    continue
                
                print(f"   [Стр.{page+1}] Паблик {mid}...", end=" ")
                data = fetch_match(mid)
                
                if data:
                    save_match(conn, data, mid)
                    added += 1
                    print(f"✅ (всего: {added})")
                else:
                    print("❌")
                
                time.sleep(0.1)
    
    conn.close()
    print(f"\n{'=' * 50}")
    print(f"✅ ГОТОВО! Скачано {added} матчей")
    print(f"   Файл: {DB_PATH}")
    print(f"{'=' * 50}")

if __name__ == "__main__":
    main()
