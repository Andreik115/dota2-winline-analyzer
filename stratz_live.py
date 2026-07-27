# stratz_live.py
import requests, json, sqlite3, os, time
from datetime import datetime
from dotenv import load_dotenv
from src.ai.gigachat_analyzer import analyzer

load_dotenv()
KEY = os.getenv("STRATZ_API_KEY")
DB = "data/dota2.db"

def get_live_matches():
    query = """
    {
        live {
            matches {
                matchId
                radiantTeamId
                direTeamId
                gameState
                gameTime
                radiantScore
                direScore
                radiantKills
                direKills
                radiantNetworthLead
                radiantExperienceLead
            }
        }
    }
    """
    r = requests.post("https://api.stratz.com/graphql",
                       headers={"Authorization": f"Bearer {KEY}"},
                       json={"query": query})
    if r.status_code == 200:
        return r.json()["data"]["live"]["matches"]
    return []

def analyze_live():
    matches = get_live_matches()
    
    if not matches:
        print(f"[{datetime.now():%H:%M:%S}] Нет live-матчей")
        return
    
    print(f"\n{'='*50}")
    print(f"[{datetime.now():%H:%M:%S}] LIVE-МАТЧЕЙ: {len(matches)}")
    print(f"{'='*50}")
    
    for m in matches:
        mid = m["matchId"]
        radiant = m.get("radiantTeamId", "Radiant")
        dire = m.get("direTeamId", "Dire")
        time_sec = m.get("gameTime", 0)
        score = f"{m.get('radiantScore', 0)}-{m.get('direScore', 0)}"
        gold_lead = m.get("radiantNetworthLead", 0)
        state = m.get("gameState", "Unknown")
        
        print(f"\n🎮 Матч {mid}")
        print(f"   {radiant} vs {dire}")
        print(f"   Время: {time_sec//60} мин | Счёт: {score}")
        print(f"   Gold lead: {gold_lead} | Статус: {state}")
        
        # AI-анализ
        prompt = f"""
        LIVE-матч Dota 2:
        Radiant vs Dire
        Время игры: {time_sec//60} минут
        Счёт: {score}
        Преимущество по золоту: {gold_lead} (положительное = Radiant лидирует)
        
        Кратко: кто выигрывает и почему? 2 предложения.
        """
        
        try:
            ai = analyzer.client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            print(f"   🤖 AI: {ai.choices[0].message.content}")
        except:
            print(f"   🤖 AI: недоступен")

if __name__ == "__main__":
    print("🔴 LIVE-анализатор запущен (STRATZ API)")
    print("   Жду матчи...\n")
    
    while True:
        analyze_live()
        time.sleep(30)  # Проверка каждые 30 секунд
