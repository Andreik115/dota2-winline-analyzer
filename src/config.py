import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent
DATABASE_PATH = ROOT_DIR / "data" / "dota2.db"
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY", "")
UPDATE_INTERVAL = 30
GIGACHAT_MODEL = "GigaChat-Pro"
GIGACHAT_TEMPERATURE = 0.3
