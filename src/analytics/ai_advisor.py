from gigachat import GigaChat

class GigaChatAnalyzer:
    def __init__(self, credentials: str):
        # Передаем авторизационные данные (Client ID / Client Secret)
        self.giga = GigaChat(credentials=credentials, verify_ssl_certs=False)

    def analyze_match(self, match_data: dict) -> str:
        # Формируем жесткий контекст для ИИ без лишней "воды"
        prompt = f"""
        Проанализируй киберспортивный матч Dota 2 и оцени адекватность коэффициентов букмекера Winline.
        Текущий статус: {match_data['status']}
        Турнир: {match_data['tournament']}
        
        Команда A: {match_data['team_a']}
        - Статистика игроков по Dotabuff: {match_data['dotabuff_team_a']}
        - Выбранные герои (Пики): {match_data['picks_a']}
        
        Команда Б: {match_data['team_b']}
        - Статистика игроков по Dotabuff: {match_data['dotabuff_team_b']}
        - Выбранные герои (Пики): {match_data['picks_b']}
        
        Текущие live-коэффициенты на Winline:
        Победа {match_data['team_a']}: {match_data['odds_a']}
        Победа {match_data['team_b']}: {match_data['odds_b']}
        
        Сделай краткий экспертный вывод: на кого выгоднее ставить (найди перекос в линии/валуйность) и обоснуй синергию пиков против статистики игроков. Ответь строго по делу.
        """
        
        response = self.giga.chat(prompt)
        return response.choices[0].message.content
