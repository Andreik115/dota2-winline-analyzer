# ai_recommend.py
import sqlite3, time, re
from datetime import datetime
from src.ai.gigachat_analyzer import analyzer

DB = "data/dota2.db"

def get_live_matches(conn):
    """Берёт live-матчи из таблицы live_matches"""
    rows = conn.execute(
        "SELECT DISTINCT team1, team2, tournament, match_time FROM live_matches WHERE status='LIVE' ORDER BY id DESC LIMIT 10"
    ).fetchall()
    return [{'team1': r[0], 'team2': r[1], 'tournament': r[2], 'time': r[3]} for r in rows]

def get_matches_with_odds(conn):
    """Берёт матчи с коэффициентами"""
    rows = conn.execute(
        "SELECT team1_name, team2_name, tournament, team1_odds, team2_odds FROM matches WHERE team1_odds IS NOT NULL ORDER BY id DESC LIMIT 30"
    ).fetchall()
    return [{'team1': r[0], 'team2': r[1], 'tournament': r[2], 'odds1': r[3], 'odds2': r[4]} for r in rows]

def find_live_odds(team1, team2, conn):
    """Ищет кэфы для live-матча"""
    row = conn.execute(
        "SELECT team1_odds, team2_odds FROM matches WHERE team1_name LIKE ? AND team2_name LIKE ? AND team1_odds IS NOT NULL",
        (f"%{team1}%", f"%{team2}%")
    ).fetchone()
    if row:
        return row[0], row[1]
    row = conn.execute(
        "SELECT team2_odds, team1_odds FROM matches WHERE team1_name LIKE ? AND team2_name LIKE ? AND team1_odds IS NOT NULL",
        (f"%{team2}%", f"%{team1}%")
    ).fetchone()
    if row:
        return row[0], row[1]
    return None, None

def main():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT, team2 TEXT, tournament TEXT,
            odds1 REAL, odds2 REAL,
            ai_verdict TEXT, created TEXT
        )
    """)
    conn.commit()
    
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n{'='*60}")
        print(f"[{now}] 🤖 AI-АНАЛИЗ")
        print(f"{'='*60}")
        
        # 1. Проверяем live-матчи
        live = get_live_matches(conn)
        print(f"\n🔴 LIVE: {len(live)} матчей")
        
        for m in live:
            odds1, odds2 = find_live_odds(m['team1'], m['team2'], conn)
            print(f"   {m['team1']} VS {m['team2']} | {m['tournament']} | {'💰 Кэфы: '+str(odds1)+'/'+str(odds2) if odds1 else '⚪ Нет кэфов'}")
        
        # 2. Анализируем матчи с кэфами
        matches = get_matches_with_odds(conn)
        print(f"\n💵 Матчей с кэфами: {len(matches)}")
        
        analyzed = 0
        for m in matches[:10]:  # Топ-10
            # Проверяем, не анализировали ли уже
            exist = conn.execute(
                "SELECT id FROM ai_recommendations WHERE team1=? AND team2=? AND created LIKE ?",
                (m['team1'], m['team2'], datetime.now().strftime('%Y-%m-%d') + '%')
            ).fetchone()
            
            if exist:
                continue
            
            print(f"\n   ═══ {m['team1']} ({m['odds1']}) VS {m['team2']} ({m['odds2']}) ═══")
            print(f"   🏆 {m['tournament']}")
            
            try:
                verdict = analyzer.analyze_match(
                    m['team1'], m['team2'],
                    m['odds1'], m['odds2'],
                    m['tournament']
                )
                print(f"   🤖 {verdict[:250]}")
                
                conn.execute(
                    "INSERT INTO ai_recommendations (team1, team2, tournament, odds1, odds2, ai_verdict, created) VALUES (?,?,?,?,?,?,?)",
                    (m['team1'], m['team2'], m['tournament'], m['odds1'], m['odds2'], verdict, now)
                )
                conn.commit()
                analyzed += 1
            except Exception as e:
                print(f"   ❌ Ошибка AI: {e}")
        
        total = conn.execute("SELECT COUNT(*) FROM ai_recommendations").fetchone()[0]
        print(f"\n📊 Всего рекомендаций: {total} (+{analyzed} новых)")
        print(f"⏳ Обновление через 120 сек...")
        time.sleep(120)

if __name__ == "__main__":
    main()
