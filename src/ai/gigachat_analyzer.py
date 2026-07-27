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

    def analyze_match(self, team1, team2, odds1=None, odds2=None, tournament=""):
        if not self.client:
            return "GigaChat API ключ не настроен."
        
        # Строим промпт, который заставляет GigaChat думать как аналитик
        prompt = f"""Ты — профессиональный аналитик киберспортивных ставок. Твоя специализация — Dota 2.

=== МАТЧ ===
{team1} vs {team2}
Турнир: {tournament}
Коэффициенты: П1 = {odds1}, П2 = {odds2}

=== ТВОЯ ЗАДАЧА ===
Дай анализ матча в формате:

📊 БУКМЕКЕР: Кто фаворит по кэфам? (1 предложение)
🎯 ОЦЕНКА: Что ты знаешь об этих командах? Их стиль, игроки, история? Если команды неизвестные — так и скажи.
💰 СТАВКА: Рекомендация — ставить или пропустить. Если ставить, то на кого и почему.
⚡ УВЕРЕННОСТЬ: Высокая / Средняя / Низкая

Если кэфы близкие (разница <0.3) и команды равные — лучше пропустить.
Если это ноунейм-команды — честно скажи пропустить.
Отвечай строго по формату, без лишнего текста."""

        try:
            response = self.client.chat(
                Chat(
                    messages=[Messages(role=MessagesRole.USER, content=prompt)],
                    temperature=0.3,
                    max_tokens=600
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка GigaChat: {e}"

analyzer = Dota2Analyzer()
