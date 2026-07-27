# liqui_live.py
import requests
import sqlite3
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup

DB = "data/dota2.db"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def create_tables():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT, team2 TEXT,
            score1 TEXT, score2 TEXT,
            tournament TEXT, status TEXT,
            match_time TEXT, updated TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT, team2 TEXT,
            score1 TEXT, score2 TEXT,
            tournament TEXT, match_date TEXT,
            winner TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT, opponent TEXT,
            result TEXT, score TEXT,
            tournament TEXT, match_date TEXT
        )
    """)
    conn.commit()
    return conn

def parse_main_page():
    """Парсит главную страницу: live + последние результаты"""
    print("📡 Главная страница...")
    live = []
    results = []
    
    try:
        r = requests.get("https://liquipedia.net/dota2/Main_Page", headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return live, results
        
        soup = BeautifulSoup(r.text, 'lxml')
        
        # Ищем все таблицы
        for table in soup.select('table'):
            rows = table.select('tr')
            for row in rows:
                cells = row.select('td')
                text = row.get_text(strip=True)
                
                # Ищем паттерн матча: "Команда1 2:1 Команда2"
                match_pattern = re.findall(
                    r'([A-Za-zА-Яа-я0-9 .]+?)\s+(\d{1,2})\s*[-:]\s*(\d{1,2})\s+([A-Za-zА-Яа-я0-9 .]+)',
                    text
                )
                
                for t1, s1, s2, t2 in match_pattern:
                    t1 = t1.strip().rstrip('.')
                    t2 = t2.strip().rstrip('.')
                    if len(t1) >= 3 and len(t2) >= 3 and t1 != t2:
                        # Определяем результат
                        winner = t1 if int(s1) > int(s2) else t2
                        results.append({
                            'team1': t1, 'team2': t2,
                            'score1': s1, 'score2': s2,
                            'winner': winner
                        })
        
        # Ищем live-индикаторы
        for tag in soup.find_all(['span', 'div'], string=re.compile(r'LIVE|live', re.I)):
            parent = tag.find_parent('tr') or tag.find_parent('div')
            if parent:
                live_text = parent.get_text(strip=True)[:200]
                if live_text not in [l.get('text', '') for l in live]:
                    live.append({'text': live_text})
        
        print(f"   Live: {len(live)}, Результатов: {len(results)}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    return live, results

def parse_tournament_results():
    """Парсит страницы популярных турниров"""
    print("📡 Турниры...")
    results = []
    
    tournaments = [
        "https://liquipedia.net/dota2/The_International/2024",
        "https://liquipedia.net/dota2/ESL_One/Bangkok/2024",
        "https://liquipedia.net/dota2/DreamLeague/Season_25",
        "https://liquipedia.net/dota2/Riyadh_Masters/2024",
    ]
    
    for url in tournaments:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            
            soup = BeautifulSoup(r.text, 'lxml')
            tour_name = url.split('/')[-2] + ' ' + url.split('/')[-1]
            
            for row in soup.select('table.wikitable tr'):
                cells = row.select('td')
                text = row.get_text(strip=True)
                
                match_pattern = re.findall(
                    r'([A-Za-zА-Яа-я0-9 .]+?)\s+(\d{1,2})\s*[-:]\s*(\d{1,2})\s+([A-Za-zА-Яа-я0-9 .]+)',
                    text
                )
                
                for t1, s1, s2, t2 in match_pattern:
                    t1, t2 = t1.strip(), t2.strip()
                    if len(t1) >= 3 and len(t2) >= 3:
                        winner = t1 if int(s1) > int(s2) else t2
                        results.append({
                            'team1': t1, 'team2': t2,
                            'score1': s1, 'score2': s2,
                            'tournament': tour_name,
                            'winner': winner
                        })
        except:
            pass
    
    print(f"   Результатов с турниров: {len(results)}")
    return results

def parse_team_page(team_name):
    """Парсит страницу команды для истории"""
    slug = team_name.replace(' ', '_').replace('.', '')
    url = f"https://liquipedia.net/dota2/{slug}"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        
        soup = BeautifulSoup(r.text, 'lxml')
        matches = []
        
        for row in soup.select('table.wikitable tr'):
            text = row.get_text(strip=True)
            match_pattern = re.findall(
                r'([A-Za-zА-Яа-я0-9 .]+?)\s+(\d{1,2})\s*[-:]\s*(\d{1,2})\s+([A-Za-zА-Яа-я0-9 .]+)',
                text
            )
            
            for t1, s1, s2, t2 in match_pattern:
                t1, t2 = t1.strip(), t2.strip()
                if len(t1) >= 3 and len(t2) >= 3:
                    # Кто opponent, кто команда
                    if team_name.lower() in t1.lower():
                        opponent = t2
                        result = "W" if int(s1) > int(s2) else "L"
                        score = f"{s1}:{s2}"
                    else:
                        opponent = t1
                        result = "W" if int(s2) > int(s1) else "L"
                        score = f"{s2}:{s1}"
                    
                    matches.append({
                        'team_name': team_name,
                        'opponent': opponent,
                        'result': result,
                        'score': score
                    })
        
        return matches[-20:]
    except:
        return []

def save_to_db(conn, live_matches, tournament_results):
    """Сохраняет всё в базу"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Сохраняем live
    for m in live_matches:
        text = m.get('text', '')
        conn.execute(
            "INSERT INTO live_matches (team1, team2, status, updated) VALUES (?, ?, ?, ?)",
            (text[:100], '', 'LIVE', now)
        )
    
    # Сохраняем результаты
    added = 0
    for r in tournament_results:
        try:
            conn.execute(
                "INSERT INTO match_results (team1, team2, score1, score2, tournament, winner) VALUES (?, ?, ?, ?, ?, ?)",
                (r['team1'], r['team2'], r['score1'], r['score2'],
                 r.get('tournament', 'Unknown'), r['winner'])
            )
            added += 1
        except:
            pass
    
    conn.commit()
    return added

def main():
    conn = create_tables()
    
    while True:
        print(f"\n{'='*50}")
        print(f"[{datetime.now():%H:%M:%S}] 🔄 Сбор данных с Liquipedia")
        print(f"{'='*50}")
        
        # Собираем данные
        live, main_results = parse_main_page()
        tour_results = parse_tournament_results()
        all_results = main_results + tour_results
        
        # Сохраняем
        added = save_to_db(conn, live, all_results)
        
        # Статистика
        total_results = conn.execute("SELECT COUNT(*) FROM match_results").fetchone()[0]
        total_live = conn.execute("SELECT COUNT(*) FROM live_matches").fetchone()[0]
        
        print(f"\n📊 В базе:")
        print(f"   Результатов: {total_results} (+{added} новых)")
        print(f"   Live-записей: {total_live}")
        
        # Показываем последние результаты
        if all_results:
            print(f"\n📋 Последние матчи:")
            for r in all_results[-5:]:
                print(f"   {r['team1']} {r['score1']}:{r['score2']} {r['team2']} | {r.get('tournament', '')}")
        
        print(f"\n⏳ Следующее обновление через 60 сек...")
        time.sleep(60)

if __name__ == "__main__":
    main()
