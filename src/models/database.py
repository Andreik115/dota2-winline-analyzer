from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path
import os

DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "dota2.db"
DATABASE_PATH.parent.mkdir(exist_ok=True)

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_external_id = Column(String, unique=True)
    tournament = Column(String)
    team1_name = Column(String)
    team2_name = Column(String)
    team1_odds = Column(Float, nullable=True)
    team2_odds = Column(Float, nullable=True)
    start_time = Column(DateTime, nullable=True)
    is_live = Column(Boolean, default=False)
    is_finished = Column(Boolean, default=False)
    score_team1 = Column(Integer, nullable=True)
    score_team2 = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

def init_db():
    Base.metadata.create_all(engine)
    print("✅ База данных создана")

def get_session():
    return SessionLocal()

init_db()
