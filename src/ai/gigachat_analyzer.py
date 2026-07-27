from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from src.config import GIGACHAT_API_KEY, GIGACHAT_MODEL, GIGACHAT_TEMPERATURE

class Dota2Analyzer:
    def __init__(self):
        self.client = None
        if GIGACHAT_API_KEY:
            self.client = GigaChat(
                credentials=GIGACHAT_API_KEY,
                scope="GIGACHAT_API_PERS",
                model=GIGACHAT_MODEL,
                verify_ssl_certs=False
            )
    
    def analyze_match(self, team1: str, team2: str, odds1: float = None, odds2: float = None) -> str:
    if not self.client:
        return "⚠️ GigaChat API ключ не настроен."
    
    # Собираем историю команд из базы
    try:
        import sqlite3
        conn = sqlite3.connect("data/dota2.db")
        
        # Последние матчи team1
        t1_matches = conn.execute(
            "SELECT team1_name, team2_name, score_team1, score_team2, tournament FROM matches WHERE team1_name LIKE ? OR team2_name LIKE ? ORDER BY id DESC LIMIT 5",
            (f"%{team1}%", f"%{team1}%")
        ).fetchall()
        
        # Последние матчи team2
        t2_matches = conn.execute(
            "SELECT team1_name, team2_name, score_team1, score_team2, tournament FROM matches WHERE team1_name LIKE ? OR team2_name LIKE ? ORDER BY id DESC LIMIT 5",
            (f"%{team2}%", f"%{team2}%")
        ).fetchall()
        conn.close()
        
        history = ""
        if t1_matches:
            history += f"\nПоследние матчи {team1}: {len(t1_matches)} найдено."
        if t2_matches:
            history += f"\nПоследние матчи {team2}: {len(t2_matches)} найдено."
    except:
        history = ""
    
    prompt = f"""
    Ты — профессиональный аналитик Dota 2 и киберспортивных ставок.
    
    Проанализируй матч: {team1} vs {team2}.
    Коэффициенты Winline: П1={odds1}, П2={odds2}.
    {history}
    
    На основе коэффициентов букмекера и своего знания киберспорта Dota 2:
    1. Кто фаворит по мнению букмекера?
    2. Какой коэффициент выглядит более привлекательным?
    3. Дай краткую рекомендацию (2-3 предложения): на кого ставить и почему.
    
    Если команды малоизвестные — так и скажи честно, посоветуй пропустить матч.
    """
    
    try:
        response = self.client.chat(
            Chat(
                messages=[Messages(role=MessagesRole.USER, content=prompt)],
                temperature=GIGACHAT_TEMPERATURE,
                max_tokens=400
            )
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"
   

analyzer = Dota2Analyzer()
