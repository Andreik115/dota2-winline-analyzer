from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.database import Base

class LiveMatch(Base):
    __tablename__ = 'live_matches'
    
    id = Column(Integer, primary_key=True)
    liquipedia_id = Column(String, unique=True, nullable=False)
    team_a = Column(String, nullable=False)
    team_b = Column(String, nullable=False)
    tournament = Column(String)
    status = Column(String, default="LIVE")  # LIVE, FINISHED
    picks_a = Column(JSON, default=[])
    picks_b = Column(JSON, default=[])
    ai_prediction = Column(String, default="Ожидание изменения коэффициентов...")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    odds_history = relationship("OddsHistory", back_populates="match", lazy="selectin", cascade="all, delete-orphan")

class OddsHistory(Base):
    __tablename__ = 'odds_history'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('live_matches.id'), nullable=False)
    odds_a = Column(Float, nullable=False)
    odds_b = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    match = relationship("LiveMatch", back_populates="odds_history")
