from gigachat import GigaChat

class GigaChatAnalyzer:
    def __init__(self, auth_token: str):
        # Инициализация клиента. verify_ssl_certs=False часто нужен для работы в РФ средах
        self.giga = GigaChat(credentials=auth_token, verify_ssl_certs=False)

    def generate_bet_signal(self, context: dict) -> str:
        # Формируем жесткий аналитический промпт
        prompt = f"""
        Роль: Профессиональный аналитик киберспорта Dota 2 и каппер.
        Задача: Оценить валуйность (перекос линии) коэффициентов Winline на основе Live-статистики.

        Матч: {context['team_a']} vs {context['team_b']} ({context['tournament']})
        
        [ДРАФТЫ]
        Пики {context['team_a']}: {', '.join(context['picks_a']) if context['picks_a'] else 'В процессе'}
        Пики {context['team_b']}: {', '.join(context['picks_b']) if context['picks_b'] else 'В процессе'}

        [ИСТОРИЧЕСКИЙ КУРС ПО DOTABUFF]
        Винрейты/Сигнатурки {context['team_a']}: {context['dotabuff_meta_a']}
        Винрейты/Сигнатурки {context['team_b']}: {context['dotabuff_meta_b']}

        [ТЕКУЩИЕ КЭФЫ WINLINE]
        Победа {context['team_a']}: {context['current_odds_a']} (Предыдущий: {context['prev_odds_a']})
        Победа {context['team_b']}: {context['current_odds_b']} (Предыдущий: {context['prev_odds_b']})

        Выдай краткий ответ в формате:
        1. Анализ драфта (У кого стратегический перевес по синергии и контрпикам).
        2. Оценка линии Winline (Букмекер переоценивает или недооценивает кого-то из-за движения кэфов?).
        3. Рекомендация (Ставка на П1 / Ставка на П2 / Пропустить матч) с процентом уверенности.
        """
        try:
            response = self.giga.chat(prompt)
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Ошибка генерации ИИ-вердикта: {e}"
