import re

class TeamNormalizer:
    @staticmethod
    def normalize(team_name: str) -> str:
        if not team_name:
            return ""
        # Приводим к нижнему регистру
        name = team_name.lower().strip()
        # Удаляем спонсорские приставки и частые теги
        name = re.sub(r'\b(team|gaming|esports|pro|club)\b', '', name)
        # Оставляем только буквы и цифры
        name = "".join(c for c in name if c.isalnum())
        return name

    @classmethod
    def is_same_team(cls, team_1: str, team_2: str) -> bool:
        n1 = cls.normalize(team_1)
        n2 = cls.normalize(team_2)
        return n1 == n2 or n1 in n2 or n2 in n1
