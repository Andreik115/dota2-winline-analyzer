import asyncio
import os
from src.models.database import init_db, get_session, LiveMatch, OddsHistory
from src.collectors.liquipedia_parser import LiquipediaParser
from src.collectors.winline_parser import WinlineParser
from src.analytics.gigachat_analyzer import GigaChatAnalyzer

# Переменная окружения для GigaChat
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS", "YOUR_GIGACHAT_API_KEY")

async def monitor_lifecycle():
    init_db()
    
    liq_parser = LiquipediaParser()
    win_parser = WinlineParser()
    ai_core = GigaChatAnalyzer(auth_token=GIGACHAT_CREDENTIALS)
    
    print("🚀 Система Live-анализа Dota2-Winline запущена.")

    while True:
        db = get_session()
        try:
            # 1. Получаем активные игры с Liquipedia
            live_games = await liq_parser.fetch_live_matches()
            
            for game in live_games:
                # Ищем игру в локальной базе данных
                match_record = db.query(LiveMatch).filter_by(liquipedia_id=game['liquipedia_id']).first()
                if not match_record:
                    match_record = LiveMatch(
                        liquipedia_id=game['liquipedia_id'],
                        team_a=game['team_a'],
                        team_b=game['team_b'],
                        tournament=game['tournament']
                    )
                    db.add(match_record)
                    db.commit()
                
                # 2. Стягиваем коэффициенты с Winline для этой игры
                odds = await win_parser.get_live_odds(match_record.team_a, match_record.team_b)
                
                if odds:
                    # Извлекаем прошлые кэфы для анализа тренда
                    last_odds = db.query(OddsHistory).filter_by(match_id=match_record.id).order_by(OddsHistory.timestamp.desc()).first()
                    prev_a = last_odds.odds_a if last_odds else odds['odds_a']
                    prev_b = last_odds.odds_b if last_odds else odds['odds_b']
                    
                    # Сохраняем новые кэфы в историю
                    new_odds_record = OddsHistory(match_id=match_record.id, odds_a=odds['odds_a'], odds_b=odds['odds_b'])
                    db.add(new_odds_record)
                    db.commit()
                    
                    # Имитируем агрегацию мета-данных из Dotabuff (заглушка на основе вашего старого файла)
                    dotabuff_meta_a = "Средний винрейт героев пула: 54%. У мидера стрик 5 побед."
                    dotabuff_meta_b = "Средний винрейт героев пула: 49%. Керри играет на слабом в патче герое."
                    
                    # Подготовка контекста для GigaChat
                    ai_context = {
                        "team_a": match_record.team_a,
                        "team_b": match_record.team_b,
                        "tournament": match_record.tournament,
                        "picks_a": match_record.picks_a,
                        "picks_b": match_record.picks_b,
                        "dotabuff_meta_a": dotabuff_meta_a,
                        "dotabuff_meta_b": dotabuff_meta_b,
                        "current_odds_a": odds['odds_a'],
                        "current_odds_b": odds['odds_b'],
                        "prev_odds_a": prev_a,
                        "prev_odds_b": prev_b
                    }
                    
                    # 3. Вызываем ИИ, если коэффициенты изменились больше чем на 0.05
                    if abs(odds['odds_a'] - prev_a) > 0.05 or abs(odds['odds_b'] - prev_b) > 0.05 or not last_odds:
                        print(f"📊 Динамика кэфов изменилась для {match_record.team_a} vs {match_record.team_b}. Запрос к ИИ...")
                        analysis_result = ai_core.generate_bet_signal(ai_context)
                        print(f"\n[РЕКОМЕНДАЦИЯ GIGACHAT]:\n{analysis_result}\n{'-'*40}")
                        
        except Exception as e:
            print(f"🛑 Ошибка в цикле мониторинга: {e}")
        finally:
            db.close()
            
        # Пауза 60 секунд между итерациями парсинга лайва
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(monitor_lifecycle())
