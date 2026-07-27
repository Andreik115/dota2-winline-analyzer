# steam_history.py
import requests
import sqlite3
import time
import os
from dotenv import load_dotenv

load_dotenv()
STEAM_KEY = os.getenv("STEAM_API_KEY")
DB_PATH = "data/dota2.db"

def create_history_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            opponent TEXT,
            result TEXT,
            tournament TEXT,
            match_date TEXT
        )
    """)
    conn.commit()
    return conn

def get_team_matches(team_name):
    """Ищет матчи команды через Steam API (упрощённо — по названию)"""
    # Steam API не ищет по названию команды напрямую.
    # Используем OpenDota API для поиска завершённых матчей команды
    url = f"https://api.opendota.com/api/teams/search?q={team_name}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.json():
            team_id = r.json()[0].get("team_id")
            if team_id:
                # Получаем матчи команды
                r2 = requests.get(f"https://api.opendota.com/api/teams/{team_id}/matches?limit=20", timeout=10)
                if r2.status_code == 200:
                    return r2.json()
    except:
        pass
    return []

def main():
    print("📡 Собираю историю команд...")
    conn = create_history_table()
    
    # Получаем список команд из нашей базы
    teams = set()
    for row in conn.execute("SELECT team1_name FROM matches UNION SELECT team2_name FROM matches"):
        teams.add(row[0])
    
    print(f"   Уникальных команд: {len(teams)}")
    
    added = 0
    for team in list(teams)[:20]:  # Топ-20 команд
        print(f"\n   Команда: {team}")
        matches = get_team_matches(team)
        
        if not matches:
            print(f"      ❌ Нет данных")
            continue
        
        for m in matches[:10]:
            opponent = m.get("opposing_team_name", "Unknown")
            result = "W" if m.get("radiant_win") == (m.get("radiant_team_id") == m.get("team_id")) else "L"
            league = m.get("league_name", "Unknown")
            
            conn.execute(
                "INSERT INTO team_history (team_name, opponent, result, tournament, match_date) VALUES (?, ?, ?, ?, ?)",
                (team, opponent, result, league, str(m.get("start_time", "")))
            )
            added += 1
        
        print(f"      ✅ Добавлено матчей: {len(matches[:10])}")
        time.sleep(0.5)
    
    conn.commit()
    conn.close()
    print(f"\n✅ Всего добавлено: {added} записей истории")

if __name__ == "__main__":
    main()
