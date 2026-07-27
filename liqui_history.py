# liqui_history.py
import requests
import sqlite3
import time
import re
from bs4 import BeautifulSoup

DB_PATH = "data/dota2.db"

def create_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            opponent TEXT,
            result TEXT,
            score TEXT,
            tournament TEXT,
            match_date TEXT
        )
    """)
    conn.commit()
    return conn

def get_team_results(team_name):
    """Парсит страницу результатов команды на Liquipedia"""
    slug = team_name.replace(' ', '_').replace('.', '')
    url = f"https://liquipedia.net/dota2/{slug}/Results"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            # Пробуем без /Results
            r = requests.get(f"https://liquipedia.net/dota2/{slug}", headers=headers, timeout=15)
            if r.status_code != 200:
                return []
        
        soup = BeautifulSoup(r.text, 'lxml')
        matches = []
        
        # Ищем таблицы с результатами
        for table in soup.select('table.wikitable'):
            rows = table.select('tr')
            for row in rows[1:]:  # Пропускаем заголовок
                cells = row.select('td')
                if len(cells) >= 6:
                    try:
                        date = cells[0].get_text(strip=True)
                        opponent_cell = cells[3] if len(cells) > 3 else cells[2]
                        opponent = opponent_cell.get_text(strip=True)
                        result_cell = cells[4] if len(cells) > 4 else cells[3]
                        result_text = result_cell.get_text(strip=True)
                        tournament = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        
                        # Определяем результат (W/L/D)
                        result = "?"
                        if 'W' in result_text or 'win' in result_text.lower():
                            result = "W"
                        elif 'L' in result_text or 'loss' in result_text.lower():
                            result = "L"
                        
                        score = re.findall(r'\d+[-:]\d+', result_text)
                        score = score[0] if score else ""
                        
                        matches.append({
                            'date': date,
                            'opponent': opponent,
                            'result': result,
                            'score': score,
                            'tournament': tournament
                        })
                    except:
                        continue
        
        return matches[-10:]  # Последние 10 матчей
    except Exception as e:
        print(f"      Ошибка: {e}")
        return []

def main():
    print("📡 Собираю историю команд из Liquipedia...")
    conn = create_table()
    
    # Получаем список команд
    teams = set()
    for row in conn.execute("SELECT team1_name FROM matches UNION SELECT team2_name FROM matches"):
        teams.add(row[0])
    
    teams = list(teams)
    print(f"   Уникальных команд: {len(teams)}")
    
    added = 0
    for i, team in enumerate(teams):
        # Пропускаем явные ноунеймы (короткие или с цифрами)
        if len(team) < 4 or re.search(r'\d', team):
            continue
        
        print(f"   [{i+1}/{len(teams)}] {team}...", end=" ")
        
        # Проверяем, есть ли уже история
        existing = conn.execute(
            "SELECT COUNT(*) FROM team_history WHERE team_name=?", (team,)
        ).fetchone()[0]
        
        if existing > 0:
            print(f"уже есть ({existing} матчей)")
            continue
        
        matches = get_team_results(team)
        
        if not matches:
            print("не найдено")
            continue
        
        for m in matches:
            conn.execute(
                "INSERT INTO team_history (team_name, opponent, result, score, tournament, match_date) VALUES (?, ?, ?, ?, ?, ?)",
                (team, m['opponent'], m['result'], m['score'], m['tournament'], m['date'])
            )
            added += 1
        
        print(f"✅ +{len(matches)} матчей")
        time.sleep(0.5)  # Пауза чтобы не забанили
    
    conn.commit()
    
    # Статистика
    total = conn.execute("SELECT COUNT(*) FROM team_history").fetchone()[0]
    teams_with = conn.execute("SELECT COUNT(DISTINCT team_name) FROM team_history").fetchone()[0]
    
    conn.close()
    print(f"\n{'=' * 50}")
    print(f"✅ ГОТОВО!")
    print(f"   Всего матчей в истории: {total}")
    print(f"   Команд с данными: {teams_with}")
    print(f"{'=' * 50}")

if __name__ == "__main__":
    main()
