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
            return "⚠️ GigaChat API ключ не настроен. Добавьте ключ в .env файл."
        
        prompt = f"""
        Проанализируй матч Dota 2: {team1} vs {team2}.
        {'Коэффициенты: П1=' + str(odds1) + ', П2=' + str(odds2) if odds1 else ''}
        Дай краткий прогноз (2-3 предложения) и объясни почему.
        """
        
        try:
            response = self.client.chat(
                Chat(
                    messages=[Messages(role=MessagesRole.USER, content=prompt)],
                    temperature=GIGACHAT_TEMPERATURE,
                    max_tokens=500
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Ошибка GigaChat: {str(e)}"

analyzer = Dota2Analyzer()
