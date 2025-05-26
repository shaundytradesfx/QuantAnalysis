"""
Database models for the Forex Factory Sentiment Analyzer.
"""
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .config import Base

class Event(Base):
    """
    Economic events from Forex Factory calendar.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String(3), index=True)  # ISO code (e.g., "GBP")
    event_name = Column(Text)  # Name of the indicator (e.g., "CPI y/y")
    scheduled_datetime = Column(DateTime(timezone=True), index=True)
    impact_level = Column(String(10))  # e.g., "High", "Medium", "Low"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to indicators
    indicators = relationship("Indicator", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(id={self.id}, currency='{self.currency}', event_name='{self.event_name}')>"


class Indicator(Base):
    """
    Economic indicator values (previous and forecast).
    """
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    previous_value = Column(Float, nullable=True)  # Raw previous release value
    forecast_value = Column(Float, nullable=True)  # Raw forecast value
    timestamp_collected = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship to event
    event = relationship("Event", back_populates="indicators")
    
    def __repr__(self):
        return f"<Indicator(id={self.id}, event_id={self.event_id}, previous={self.previous_value}, forecast={self.forecast_value})>"


class Sentiment(Base):
    """
    Calculated sentiment per currency for a week.
    """
    __tablename__ = "sentiments"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String(3), index=True)  # Currency code
    week_start = Column(Date, index=True)  # Monday date for this analysis window
    week_end = Column(Date)  # Sunday date for this analysis window
    final_sentiment = Column(String(50))  # "Bullish", "Bearish", "Neutral", or "Bearish with Consolidation" etc.
    details_json = Column(JSON)  # Array of objects: { event_name, previous, forecast, sentiment }
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Sentiment(id={self.id}, currency='{self.currency}', final_sentiment='{self.final_sentiment}')>"


class Config(Base):
    """
    Application configuration stored in the database.
    """
    __tablename__ = "config"

    key = Column(String(50), primary_key=True)  # Configuration key (e.g., "DISCORD_WEBHOOK_URL")
    value = Column(Text)  # Corresponding value
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Config(key='{self.key}', updated_at='{self.updated_at}')>"


class AuditFailure(Base):
    """
    Audit table to store failed parsing attempts as specified in PRD.
    """
    __tablename__ = "audit_failures"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text)  # URL that failed to parse
    error_type = Column(String(50), index=True)  # Type of error (e.g., "PARSING_ERROR", "NETWORK_ERROR")
    error_message = Column(Text)  # Detailed error message
    html_snippet = Column(Text)  # Snippet of HTML that caused the issue (for debugging)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    retry_count = Column(Integer, default=0)  # Number of retry attempts
    resolved = Column(Boolean, default=False, index=True)  # Whether the issue was resolved
    
    def __repr__(self):
        return f"<AuditFailure(id={self.id}, error_type='{self.error_type}', resolved={self.resolved})>"


class Admin(Base):
    """
    Admin users for authentication.
    """
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Admin(id={self.id}, username='{self.username}')>" 