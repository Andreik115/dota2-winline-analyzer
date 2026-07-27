# team_data_parser.py
import requests
import sqlite3
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime

DB = "data/dota2.db"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def create_tables():
    conn = sqlite3.connect(DB)
    # Составы команд
    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_rosters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            player_name TEXT,
            position TEXT,
            join_date TEXT,
            updated TEXT
        )
    """)
    # История матчей команд
    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            opponent TEXT,
            result TEXT,
            score TEXT,
            tournament TEXT,
            match_date TEXT
        )
    """)
    # Пики героев
    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_heroes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            hero_name TEXT,
            picks INTEGER,
            wins INTEGER,
            winrate REAL,
            updated TEXT
        )
    """)
    conn.commit()
    return conn

def get_team_slug(team_name):
    """Преобразует название команды в slug для Liquipedia"""
    # Team Spirit -> Team_Spirit
    # Natus Vincere -> Natus_Vincere
    slug = team_name.replace(' ', '_')
    return slug

def parse_team_page(team_name):
    """Парсит страницу команды: состав, последние матчи"""
    slug = get_team_slug(team_name)
    url = f"https://liquipedia.net/dota2/{slug}"
    
    print(f"   📡 {url}...", end=" ")
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"❌ {r.status_code}")
            return [], [], []
        
        soup = BeautifulSoup(r.text, 'lxml')
        print("✅")
        
        # === ПАРСИМ СОСТАВ ===
        roster = []
        # Ищем таблицу с игроками (обычно class="wikitable" с заголовком "Player")
        for table in soup.select('table.wikitable'):
            headers = [th.get_text(strip=True).lower() for th in table.select('th')]
            if 'player' in ' '.join(headers) or 'игрок' in ' '.join(headers):
                for row in table.select('tr')[1:]:
                    cells = row.select('td')
                    if len(cells) >= 2:
                        player = cells[0].get_text(strip=True)
                        position = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        join_date = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        
                        if player and len(player) > 2:
                            roster.append({
                                'player': player,
                                'position': position,
                                'join_date': join_date
                            })
                break  # Берём только первую таблицу с игроками
        
        # === ПАРСИМ ПОСЛЕДНИЕ МАТЧИ ===
        results = []
        for table in soup.select('table.wikitable'):
            rows = table.select('tr')
            for row in rows[1:]:
                cells = row.select('td')
                if len(cells) >= 4:
                    text = row.get_text(strip=True)
                    # Ищем паттерн "Команда 2:1 Команда" или "W" / "L"
                    score_match = re.findall(r'(\d+)\s*[-:]\s*(\d+)', text)
                    opponent = ""
                    result = ""
                    
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if cell_text in ['W', 'L']:
                            result = cell_text
                        elif len(cell_text) > 2 and cell_text != team_name and not re.match(r'^\d', cell_text):
                            opponent = cell_text
                    
                    if opponent and result:
                        score = score_match[0] if score_match else ""
                        results.append({
                            'opponent': opponent,
                            'result': result,
                            'score': f"{score[0]}:{score[1]}" if score else ""
                        })
        
        return roster, results, []
    
    except Exception as e:
        print(f"❌ {e}")
        return [], [], []

def update_database(conn, team_name, roster, results):
    """Сохраняет данные в базу"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Удаляем старые данные команды
    conn.execute("DELETE FROM team_rosters WHERE team_name=?", (team_name,))
    
    # Сохраняем состав
    for p in roster:
        conn.execute(
            "INSERT INTO team_rosters (team_name, player_name, position, join_date, updated) VALUES (?, ?, ?, ?, ?)",
            (team_name, p['player'], p['position'], p['join_date'], now)
        )
    
    # Сохраняем результаты
    for r in results:
        conn.execute(
            "INSERT INTO team_results (team_name, opponent, result, score, tournament, match_date) VALUES (?, ?, ?, ?, ?, ?)",
            (team_name, r['opponent'], r['result'], r['score'], '', '')
        )
    
    conn.commit()

def main():
    conn = create_tables()
    
    # Берём список команд из базы
    teams = set()
    for row in conn.execute("SELECT team1_name FROM matches UNION SELECT team2_name FROM matches"):
        team = row[0].strip()
        if len(team) >= 4 and not re.search(r'\d', team):  # Пропускаем ноунеймов с цифрами
            teams.add(team)
    
    for row in conn.execute("SELECT team1 FROM live_matches UNION SELECT team2 FROM live_matches"):
        team = row[0].strip()
        if len(team) >= 4:
            teams.add(team)
    
    teams = list(teams)[:30]  # Топ-30 команд
    print(f"\n{'='*50}")
    print(f"📡 Парсинг данных {len(teams)} команд с Liquipedia")
    print(f"{'='*50}\n")
    
    for i, team in enumerate(teams):
        print(f"[{i+1}/{len(teams)}] {team}")
        
        # Проверяем, обновляли ли сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        existing = conn.execute(
            "SELECT COUNT(*) FROM team_rosters WHERE team_name=? AND updated LIKE ?",
            (team, today + '%')
        ).fetchone()[0]
        
        if existing > 0:
            print(f"   ✅ Уже обновлено сегодня ({existing} игроков)")
            continue
        
        roster, results, _ = parse_team_page(team)
        
        if roster:
            print(f"   👥 Состав: {len(roster)} игроков")
            for p in roster[:5]:
                print(f"      {p['player']} - {p['position']}")
        
        if results:
            print(f"   📊 Последние матчи: {len(results)}")
            for r in results[-5:]:
                print(f"      {r['result']} vs {r['opponent']} {r['score']}")
        
        update_database(conn, team, roster, results)
        
        if roster or results:
            print(f"   💾 Сохранено")
        else:
            print(f"   ⚠️ Нет данных")
        
        time.sleep(0.5)  # Пауза между командами
    
    # Статистика
    total_players = conn.execute("SELECT COUNT(*) FROM team_rosters").fetchone()[0]
    total_results = conn.execute("SELECT COUNT(*) FROM team_results").fetchone()[0]
    teams_with_data = conn.execute("SELECT COUNT(DISTINCT team_name) FROM team_rosters").fetchone()[0]
    
    conn.close()
    print(f"\n{'='*50}")
    print(f"✅ ГОТОВО!")
    print(f"   Команд с составами: {teams_with_data}")
    print(f"   Всего игроков: {total_players}")
    print(f"   Результатов матчей: {total_results}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
