from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from src.config import GIGACHAT_API_KEY, GIGACHAT_MODEL, GIGACHAT_TEMPERATURE
import sqlite3

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

    def get_team_history(self, team_name):
        """Собирает историю из всех доступных таблиц"""
        try:
            conn = sqlite3.connect("data/dota2.db")
            
            # Из таблицы matches
            m1 = conn.execute(
                "SELECT team1_name, team2_name, team1_odds, team2_odds, tournament FROM matches WHERE (team1_name LIKE ? OR team2_name LIKE ?) AND team1_odds IS NOT NULL LIMIT 10",
                (f"%{team_name}%", f"%{team_name}%")
            ).fetchall()
            
            # Из match_results
            m2 = conn.execute(
                "SELECT team1, team2, score1, score2, winner, tournament FROM match_results WHERE team1 LIKE ? OR team2 LIKE ? LIMIT 10",
                (f"%{team_name}%", f"%{team_name}%")
            ).fetchall()
            
            # Из team_history
            m3 = conn.execute(
                "SELECT opponent, result, score, tournament FROM team_history WHERE team_name LIKE ? LIMIT 10",
                (f"%{team_name}%",)
            ).fetchall()
            
            conn.close()
            
            history = ""
            if m1:
                history += f"\nКоэффициенты Winline на {team_name}:"
                for r in m1[:5]:
                    history += f"\n  {r[0]} vs {r[1]} (кэфы: {r[2]}/{r[3]}, {r[4]})"
            
            if m2:
                history += f"\nРезультаты матчей {team_name}:"
                for r in m2[:5]:
                    history += f"\n  {r[0]} {r[2]}:{r[3]} {r[1]} | {r[5]}"
            
            if m3:
                history += f"\nИстория встреч {team_name}:"
                for r in m3[:5]:
                    history += f"\n  vs {r[0]}: {r[1]} ({r[2]}) | {r[3]}"
            
            return history
        except:
            return ""

    def analyze_match(self, team1, team2, odds1=None, odds2=None, tournament=""):
        if not self.client:
            return "GigaChat API ключ не настроен."
        
        history1 = self.get_team_history(team1)
        history2 = self.get_team_history(team2)
        
        prompt = f"""Ты — профессиональный аналитик Dota 2. Твоя задача — дать рекомендацию по ставке.

=== МАТЧ ===
Команда 1: {team1}
Команда 2: {team2}
Турнир: {tournament}
Коэффициенты Winline: П1={odds1}, П2={odds2}

=== ДАННЫЕ ИЗ БАЗЫ ===
{history1}
{history2}

=== ЗАДАНИЕ ===
Проанализируй матч как профессиональный каппер:
1. Кто фаворит по коэффициентам?
2. Что говорят данные из базы (если есть)?
3. Итоговая рекомендация: СТАВИТЬ на команду X / ПРОПУСТИТЬ матч
4. Уровень уверенности: ВЫСОКИЙ / СРЕДНИЙ / НИЗКИЙ

Если данных недостаточно — честно скажи. Если команды ноунеймы — рекомендуй пропустить.
Отвечай кратко, по делу, без воды. Максимум 4-5 предложений."""

        try:
            response = self.client.chat(
                Chat(
                    messages=[Messages(role=MessagesRole.USER, content=prompt)],
                    temperature=0.2,
                    max_tokens=500
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка GigaChat: {e}"

analyzer = Dota2Analyzer()
