import asyncio
from src.collectors.liquipedia_parser.py import LiquipediaLiveParser
from src.analytics.ai_advisor import GigaChatAnalyzer

async def main():
    # Инициализируем парсеры и ИИ
    liquipedia = LiquipediaLiveParser()
    # Замените на ваши реальные учетные данные GigaChat Auth
    ai_analyzer = GigaChatAnalyzer(credentials="YOUR_GIGACHAT_CREDENTIALS")
    
    print("⏳ Шаг 1: Сканируем Live-матчи на Liquipedia...")
    live_matches = await liquipedia.get_live_matches()
    
    if not live_matches:
        print("❌ Живых матчей прямо сейчас не найдено.")
        return

    for match in live_matches:
        print(f"🔥 Найдена игра: {match['team_a']} против {match['team_b']}")
        
        # Имитируем подгрузку данных из сопредельных модулей (Winline API и Dotabuff)
        # В реальном коде здесь вызываются методы соответствующих парсеров
        aggregated_data = {
            **match,
            "dotabuff_team_a": "Винрейт состава 58%, сигнатурный Invoker у мидера (74% винрейт)",
            "dotabuff_team_b": "Винрейт состава 51%, керри играет на некомфортном герое",
            "picks_a": ["Invoker", "Faceless Void", "Snapfire", "Chen", "Centaur"],
            "picks_b": ["Anti-Mage", "Lina", "Slardar", "Rubick", "Io"],
            "odds_a": 2.10,  # Данные парсера Winline
            "odds_b": 1.65
        }
        
        print("🤖 Отправляем агрегированную модель в GigaChat...")
        ai_opinion = ai_analyzer.analyze_match(aggregated_data)
        
        print("\n=== ВЕРДИКТ ИИ ДЛЯ СТАВКИ ===")
        print(ai_opinion)
        print("=============================\n")

if __name__ == "__main__":
    asyncio.run(main())
