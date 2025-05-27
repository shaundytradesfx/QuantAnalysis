"""
FastAPI server for the Forex Factory Sentiment Analyzer web interface.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from sqlalchemy import text

from src.database.config import SessionLocal
from src.database.models import Event, Indicator, Sentiment, Config
from src.analysis.sentiment_engine import SentimentCalculator
from src.discord.notifier import DiscordNotifier
from src.utils.logging import get_logger

# Get logger
logger = get_logger(__name__)

def get_db_session():
    """Get a database session context manager."""
    return SessionLocal()

# Create FastAPI app
app = FastAPI(
    title="Forex Sentiment Analysis Dashboard",
    description="Web interface for the Forex Factory Sentiment Analyzer",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

# Pydantic models for API responses
class EventResponse(BaseModel):
    id: int
    currency: str
    event_name: str
    scheduled_datetime: datetime
    impact_level: str
    previous_value: Optional[float]
    forecast_value: Optional[float]

class SentimentResponse(BaseModel):
    currency: str
    final_sentiment: str
    week_start: str
    week_end: str
    events: List[Dict[str, Any]]
    computed_at: datetime

class HealthResponse(BaseModel):
    status: str
    database: str
    discord: str
    last_scrape: Optional[str]
    last_analysis: Optional[str]

class ConfigResponse(BaseModel):
    key: str
    value: str
    updated_at: datetime

class ConfigUpdateRequest(BaseModel):
    key: str
    value: str

# Frontend Routes
@app.get("/")
async def dashboard():
    """Serve the main dashboard page."""
    dashboard_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        return {"message": "Dashboard not found. Please ensure frontend files are properly installed."}

# API Routes
@app.get("/api/")
async def api_root():
    """API root endpoint."""
    return {"message": "Forex Sentiment Analysis API", "version": "1.0.0"}

@app.get("/api/health", response_model=HealthResponse)
async def get_health():
    """Get system health status."""
    try:
        # Check database connection
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check Discord connection
    try:
        notifier = DiscordNotifier()
        discord_results = notifier.test_connection()
        discord_status = "healthy" if all(discord_results.values()) else "unhealthy"
    except Exception as e:
        logger.error(f"Discord health check failed: {e}")
        discord_status = "unhealthy"
    
    # Overall status
    overall_status = "healthy" if db_status == "healthy" and discord_status == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        database=db_status,
        discord=discord_status,
        last_scrape=None,  # TODO: Implement last scrape tracking
        last_analysis=None  # TODO: Implement last analysis tracking
    )

@app.get("/api/sentiments", response_model=List[SentimentResponse])
async def get_sentiments(week_start: Optional[str] = None, week_end: Optional[str] = None):
    """Get sentiment analysis results."""
    try:
        with SentimentCalculator() as calculator:
            if week_start and week_end:
                start_date = datetime.strptime(week_start, "%Y-%m-%d")
                end_date = datetime.strptime(week_end, "%Y-%m-%d")
                sentiments = calculator.calculate_weekly_sentiments(start_date, end_date)
            else:
                sentiments = calculator.calculate_weekly_sentiments()
        
        response = []
        for currency, data in sentiments.items():
            # Extract week bounds from analysis_period
            week_start_str = data['analysis_period']['week_start'][:10]  # Get YYYY-MM-DD part
            week_end_str = data['analysis_period']['week_end'][:10]      # Get YYYY-MM-DD part
            
            response.append(SentimentResponse(
                currency=currency,
                final_sentiment=data['resolution']['final_sentiment'],
                week_start=week_start_str,
                week_end=week_end_str,
                events=data['events'],
                computed_at=datetime.now()
            ))
        
        return response
    except Exception as e:
        logger.error(f"Error getting sentiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events", response_model=List[EventResponse])
async def get_events(currency: Optional[str] = None, limit: int = 100):
    """Get economic events."""
    try:
        with get_db_session() as session:
            query = session.query(Event, Indicator).join(
                Indicator, Event.id == Indicator.event_id
            ).order_by(Event.scheduled_datetime.desc())
            
            if currency:
                query = query.filter(Event.currency == currency.upper())
            
            query = query.limit(limit)
            results = query.all()
            
            events = []
            for event, indicator in results:
                events.append(EventResponse(
                    id=event.id,
                    currency=event.currency,
                    event_name=event.event_name,
                    scheduled_datetime=event.scheduled_datetime,
                    impact_level=event.impact_level,
                    previous_value=indicator.previous_value,
                    forecast_value=indicator.forecast_value
                ))
            
            return events
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config", response_model=List[ConfigResponse])
async def get_config():
    """Get configuration settings."""
    try:
        with get_db_session() as session:
            configs = session.query(Config).all()
            return [
                ConfigResponse(
                    key=config.key,
                    value=config.value,
                    updated_at=config.updated_at
                )
                for config in configs
            ]
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def update_config(request: ConfigUpdateRequest):
    """Update configuration setting."""
    try:
        with get_db_session() as session:
            config = session.query(Config).filter(Config.key == request.key).first()
            
            if config:
                config.value = request.value
                config.updated_at = datetime.now()
            else:
                config = Config(
                    key=request.key,
                    value=request.value,
                    updated_at=datetime.now()
                )
                session.add(config)
            
            session.commit()
            return {"message": "Configuration updated successfully"}
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/currencies")
async def get_currencies():
    """Get list of available currencies."""
    try:
        with get_db_session() as session:
            currencies = session.query(Event.currency).distinct().all()
            return [currency[0] for currency in currencies if currency[0]]
    except Exception as e:
        logger.error(f"Error getting currencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discord/test")
async def test_discord_webhook():
    """Test Discord webhook connection."""
    try:
        notifier = DiscordNotifier()
        results = notifier.test_connection()
        
        if all(results.values()):
            return {"status": "success", "message": "All Discord webhooks are working"}
        else:
            return {"status": "partial", "message": "Some Discord webhooks failed", "details": results}
    except Exception as e:
        logger.error(f"Error testing Discord webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discord/send-report")
async def send_weekly_report():
    """Send weekly Discord report."""
    try:
        from src.analysis.sentiment_engine import SentimentCalculator
        
        # Get sentiment data for current week
        with SentimentCalculator() as calculator:
            sentiments = calculator.calculate_weekly_sentiments()
            week_start, _ = calculator.get_current_week_bounds()
        
        # Send Discord notification
        notifier = DiscordNotifier()
        success = notifier.send_weekly_report(sentiments, week_start)
        
        if success:
            return {"status": "success", "message": "Weekly report sent successfully"}
        else:
            return {"status": "error", "message": "Failed to send weekly report"}
    except Exception as e:
        logger.error(f"Error sending weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cron endpoints for Cloud Scheduler
@app.post("/api/cron/scrape")
async def cron_scrape():
    """Cron endpoint for running the scraper (triggered by Cloud Scheduler)."""
    try:
        from src.run_scraper import run_scraper
        
        logger.info("Cron job: Starting scraper...")
        result = run_scraper()
        
        if result == 0:
            return {"status": "success", "message": "Scraper completed successfully"}
        else:
            return {"status": "error", "message": "Scraper failed", "exit_code": result}
    except Exception as e:
        logger.error(f"Cron scraper error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cron/analyze")
async def cron_analyze():
    """Cron endpoint for running sentiment analysis (triggered by Cloud Scheduler)."""
    try:
        from src.run_analysis import run_analysis
        
        logger.info("Cron job: Starting sentiment analysis...")
        result = run_analysis()
        
        if result == 0:
            return {"status": "success", "message": "Analysis completed successfully"}
        else:
            return {"status": "error", "message": "Analysis failed", "exit_code": result}
    except Exception as e:
        logger.error(f"Cron analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cron/notify")
async def cron_notify():
    """Cron endpoint for sending Discord notifications (triggered by Cloud Scheduler)."""
    try:
        from src.analysis.sentiment_engine import SentimentCalculator
        
        logger.info("Cron job: Starting Discord notification...")
        
        # Get sentiment data for current week
        with SentimentCalculator() as calculator:
            sentiments = calculator.calculate_weekly_sentiments()
            week_start, _ = calculator.get_current_week_bounds()
        
        # Send Discord notification
        notifier = DiscordNotifier()
        success = notifier.send_weekly_report(sentiments, week_start)
        
        if success:
            return {"status": "success", "message": "Discord notification sent successfully"}
        else:
            return {"status": "error", "message": "Failed to send Discord notification"}
    except Exception as e:
        logger.error(f"Cron notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Run the FastAPI server."""
    logger.info(f"Starting FastAPI server on {host}:{port}")
    logger.info(f"Frontend path: {frontend_path}")
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server() 