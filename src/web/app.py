from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.database import get_session, Match

app = FastAPI(
    title="Dota 2 Winline Analyzer",
    description="AI-анализ матчей Dota 2 с коэффициентами Winline",
    version="0.1.0"
)

static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    session = get_session()
    matches = session.query(Match).order_by(Match.start_time.desc()).limit(20).all()
    session.close()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "matches": matches,
            "title": "Dota 2 Winline Analyzer"
        }
    )

@app.get("/match/{match_id}", response_class=HTMLResponse)
async def match_detail(request: Request, match_id: int):
    session = get_session()
    match = session.query(Match).filter(Match.id == match_id).first()
    session.close()
    
    if not match:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Матч не найден"}
        )
    
    return templates.TemplateResponse(
        "match_detail.html",
        {
            "request": request,
            "match": match,
            "title": f"{match.team1_name} vs {match.team2_name}"
        }
    )

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Сервер работает"}
