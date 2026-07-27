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

    def analyze_match(self, team1, team2, odds1=None, odds2=None):
        if not self.client:
            return "GigaChat API ключ не настроен."

        prompt = f"""Ты профессиональный аналитик Dota 2. 
Проанализируй матч: {team1} vs {team2}.
Коэффициенты Winline: П1={odds1}, П2={odds2}.

Ответь кратко (2-3 предложения):
1. Кто фаворит по кэфам?
2. На кого стоит ставить и почему?
Если команды малоизвестные - скажи пропустить матч."""

        try:
            response = self.client.chat(
                Chat(
                    messages=[Messages(role=MessagesRole.USER, content=prompt)],
                    temperature=GIGACHAT_TEMPERATURE,
                    max_tokens=300
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка GigaChat: {e}"

analyzer = Dota2Analyzer()
