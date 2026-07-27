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
        
        try:
            import sqlite3
            conn = sqlite3.connect("data/dota2.db")
            t1_matches = conn.execute(
                "SELECT team1_name, team2_name, tournament FROM matches WHERE team1_name LIKE ? OR team2_name LIKE ? ORDER BY id DESC LIMIT 5",
                (f"%{team1}%", f"%{team1}%")
            ).fetchall()
            t2_matches = conn.execute(
                "SELECT team1_name, team2_name, tournament FROM matches WHERE team1_name LIKE ? OR team2_name LIKE ? ORDER BY id DESC LIMIT 5",
                (f"%{team2}%", f"%{team2}%")
            ).fetchall()
            conn.close()
            
            history = ""
            if t1_matches:
                history += f"\nПоследние матчи {team1}: найдено {len(t1_matches)}."
            if t2_matches:
                history += f"\nПоследние матчи {team2}: найдено {len(t2_matches)}."
        except:
            history = ""
        
        prompt = f"""
        Ты — профессиональный аналитик Dota 2 и киберспортивных ставок.
        
        Проанализируй матч: {team1} vs {team2}.
        Коэффициенты Winline: П1={odds1}, П2={odds2}.
        {history}
        
        На основе коэффициентов букмекера и своего знания киберспорта Dota 2:
        1. Кто фаворит?
        2. Какой коэффициент привлекательнее?
        3. Краткая рекомендация (2-3 предложения).
        
        Если команды малоизвестные — честно скажи, посоветуй пропустить матч.
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
