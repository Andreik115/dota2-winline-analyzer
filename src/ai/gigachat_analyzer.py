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

    def prematch_analysis(self, team1, team2, odds1, odds2, odds_x=None, 
                          total_odds=None, fora_odds=None, tournament=""):
        """Полный прематч-анализ"""
        if not self.client:
            return "GigaChat не настроен"
        
        prompt = f"""Ты — профессиональный аналитик Dota 2. Дай полный прематч-анализ.

=== МАТЧ ===
{team1} vs {team2}
Турнир: {tournament}

=== КОЭФФИЦИЕНТЫ WINLINE ===
Исход: П1={odds1}, X={odds_x}, П2={odds2}
{'Тотал: ' + str(total_odds) if total_odds else ''}
{'Фора: ' + str(fora_odds) if fora_odds else ''}

=== ЗАДАНИЕ ===
Дай структурированный анализ:

📊 ЛИНИЯ: Кто фаворит? Есть ли перекос в линии?
🎯 СТИЛЬ: Какой стиль игры у команд (если знаешь)?
🦸 ГЕРОИ: Какие герои сильны в текущей мете для этих команд?
💰 СТАВКА: 
- Исход: рекомендация + уровень уверенности
- Тотал: больше/меньше (если есть кэфы)
- Фора: стоит ли брать (если есть кэфы)

⚡ ИТОГ: Одна финальная рекомендация.

Если команды неизвестны — честно скажи. Не выдумывай составы.
Будь конкретным. 5-7 предложений."""

        try:
            response = self.client.chat(
                Chat(messages=[Messages(role=MessagesRole.USER, content=prompt)],
                     temperature=0.3, max_tokens=700)
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка: {e}"

    def live_analysis(self, team1, team2, match_time, tournament="",
                      radiant_heroes=None, dire_heroes=None,
                      gold_lead=None, score=None):
        """Лайв-анализ с пиками"""
        if not self.client:
            return "GigaChat не настроен"
        
        heroes_text = ""
        if radiant_heroes:
            heroes_text += f"\nПики Radiant: {', '.join(radiant_heroes)}"
        if dire_heroes:
            heroes_text += f"\nПики Dire: {', '.join(dire_heroes)}"
        
        prompt = f"""Ты — аналитик Dota 2. Дай live-анализ матча.

=== LIVE-МАТЧ ===
{team1} vs {team2}
Турнир: {tournament}
Время: {match_time}
Счёт: {score or 'Неизвестно'}
Gold lead: {gold_lead or 'Неизвестно'}
{heroes_text}

=== ЗАДАНИЕ ===
Проанализируй:
🦸 ПИКИ: У какой команды лучше драфт? Синергии, контр-пики, win condition.
📊 СИТУАЦИЯ: Кто выигрывает по золоту/опыту?
⏰ ЛЕЙТ: У кого лучше late-game потенциал с таким драфтом?
💰 ЛАЙВ-СТАВКА: Если бы ты ставил сейчас — на кого?

Будь конкретным, основывайся на героях и ситуации. 5-7 предложений."""

        try:
            response = self.client.chat(
                Chat(messages=[Messages(role=MessagesRole.USER, content=prompt)],
                     temperature=0.3, max_tokens=600)
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка: {e}"

    def analyze_match(self, team1, team2, odds1=None, odds2=None, tournament=""):
        """Базовый анализ (для совместимости)"""
        return self.prematch_analysis(team1, team2, odds1, odds2, tournament=tournament)

analyzer = Dota2Analyzer()
