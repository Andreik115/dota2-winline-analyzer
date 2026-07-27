import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database import init_db, AsyncSessionLocal, get_db
from src.models import LiveMatch, OddsHistory
from src.services import DotaAnalyzerService

# Фоновый обработчик сбора данных
async def background_crawler():
    service = DotaAnalyzerService()
    print("🚀 Фоновый воркер запущен...")
    
    while True:
        async with AsyncSessionLocal() as db:
            try:
                # 1. Парсим матчи
                live_games = await service.fetch_liquipedia_matches()
                
                for game in live_games:
                    # Проверяем наличие матча в БД
                    stmt = select(LiveMatch).where(LiveMatch.liquipedia_id == game['liquipedia_id'])
                    result = await db.execute(stmt)
                    match_record = result.scalar_one_or_none()
                    
                    if not match_record:
                        match_record = LiveMatch(
                            liquipedia_id=game['liquipedia_id'],
                            team_a=game['team_a'],
                            team_b=game['team_b'],
                            tournament=game['tournament']
                        )
                        db.add(match_record)
                        await db.commit()
                        await db.refresh(match_record)
                    
                    # 2. Получаем кэфы
                    odds = await service.fetch_winline_odds(match_record.team_a, match_record.team_b)
                    if odds:
                        # Сравниваем движение коэффициентов
                        has_changes = True
                        if match_record.odds_history:
                            last_odds = match_record.odds_history[-1]
                            if abs(last_odds.odds_a - odds['odds_a']) < 0.03:
                                has_changes = False
                        
                        # Сохраняем новые котировки в историю
                        new_odds = OddsHistory(match_id=match_record.id, odds_a=odds['odds_a'], odds_b=odds['odds_b'])
                        db.add(new_odds)
                        
                        # 3. Пересчитываем прогноз ИИ, если кэфы значительно сдвинулись
                        if has_changes:
                            ctx = {**odds, "team_a": match_record.team_a, "team_b": match_record.team_b, "tournament": match_record.tournament}
                            prediction = await service.get_gigachat_prediction(ctx)
                            match_record.ai_prediction = prediction
                            db.add(match_record)
                            
                        await db.commit()
            except Exception as e:
                print(f"⚠️ Ошибка в фоновом цикле: {e}")
                await db.rollback()
                
        await asyncio.sleep(45)  # Опрос каждые 45 секунд

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # Инициализация БД при старте приложения
    asyncio.create_task(background_crawler()) # Запуск бесконечного парсера в бэкграунде
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def render_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    # Вытягиваем все матчи со статусом LIVE
    stmt = select(LiveMatch).where(LiveMatch.status == "LIVE")
    result = await db.execute(stmt)
    matches = result.scalars().all()
    
    return templates.TemplateResponse("index.html", {"request": request, "matches": matches})

if __name__ == "__main__":
    import uvicorn
    # Запуск сервера на порту 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
