import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dota2_analyzer.db")

class LiveMatch(Base):
    __tablename__ = 'live_matches'
    
    id = Column(Integer, primary_key=True)
    liquipedia_id = Column(String, unique=True, nullable=False)
    team_a = Column(String, nullable=False)
    team_b = Column(String, nullable=False)
    tournament = Column(String)
    status = Column(String, default="LIVE")  # LIVE, FINISHED
    picks_a = Column(JSON, default=[])       # Список героев команды А
    picks_b = Column(JSON, default=[])       # Список героев команды Б
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    odds_history = relationship("OddsHistory", back_populates="match", cascade="all, delete-orphan")

class OddsHistory(Base):
    __tablename__ = 'odds_history'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('live_matches.id'), nullable=False)
    odds_a = Column(Float, nullable=False)
    odds_b = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    match = relationship("LiveMatch", back_populates="odds_history")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()
