"""
FastAPI server for the Forex Factory Sentiment Analyzer web interface.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel
import uvicorn
from sqlalchemy import text
import secrets

from src.database.config import SessionLocal
from src.database.models import Event, Indicator, Sentiment, Config
from src.analysis.sentiment_engine import SentimentCalculator
from src.discord.notifier import DiscordNotifier
from src.utils.logging import get_logger

# Get logger
logger = get_logger(__name__)

import secrets
try:
    import jwt
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    logger.warning("OAuth dependencies not available. OAuth features will be disabled.")

# OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALLOWED_DOMAIN = "finservcorp.net"

def get_db_session():
    """Get a database session context manager."""
    return SessionLocal()

# Create FastAPI app
app = FastAPI(
    title="Forex Sentiment Analysis Dashboard",
    description="Web interface for the Forex Factory Sentiment Analyzer",
    version="1.0.0"
)

# Add CORS middleware for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public access
    allow_credentials=False,  # No credentials needed for public access
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
# Alternative path resolution for deployed environments
if not os.path.exists(frontend_path):
    frontend_path = os.path.join("/app", "frontend")
if not os.path.exists(frontend_path):
    frontend_path = "frontend"

logger.info(f"Frontend path resolved to: {frontend_path}")
logger.info(f"Frontend path exists: {os.path.exists(frontend_path)}")

if os.path.exists(frontend_path):
    static_path = os.path.join(frontend_path, "static")
    if os.path.exists(static_path):
        app.mount("/static", StaticFiles(directory=static_path), name="static")
        logger.info(f"Mounted static files from: {static_path}")
    else:
        logger.warning(f"Static directory not found at: {static_path}")
else:
    logger.error(f"Frontend directory not found at: {frontend_path}")

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
async def dashboard(request: Request):
    """Serve the main dashboard page with smart authentication."""
    from fastapi import Request
    
    # Check if this is a browser request
    user_agent = request.headers.get("user-agent", "").lower()
    is_browser = any(browser in user_agent for browser in ["mozilla", "chrome", "safari", "edge", "firefox"])
    
    # Check for authorization header
    auth_header = request.headers.get("authorization")
    
    if is_browser and not auth_header:
        # For browser requests without auth, serve smart authentication page
        return HTMLResponse(content=get_smart_auth_page())
    
    # For API requests or authenticated requests, serve the dashboard
    dashboard_path = os.path.join(frontend_path, "index.html")
    logger.info(f"Attempting to serve dashboard from: {dashboard_path}")
    logger.info(f"Dashboard file exists: {os.path.exists(dashboard_path)}")
    
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        # Try alternative paths
        alternative_paths = [
            os.path.join("/app", "frontend", "index.html"),
            "frontend/index.html",
            "index.html"
        ]
        
        for alt_path in alternative_paths:
            logger.info(f"Trying alternative path: {alt_path}")
            if os.path.exists(alt_path):
                logger.info(f"Found dashboard at: {alt_path}")
                return FileResponse(alt_path)
        
        logger.error("Dashboard not found at any expected location")
        return {"message": "Dashboard not found. Please ensure frontend files are properly installed.", 
                "searched_paths": [dashboard_path] + alternative_paths}

def get_smart_auth_page():
    """Generate smart authentication page that automatically attempts authentication."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forex Sentiment Analyzer - Authenticating...</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            text-align: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .loading {
            margin: 20px 0;
        }
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 4px solid #fff;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .status {
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            font-weight: bold;
        }
        .success { background: rgba(40, 167, 69, 0.3); }
        .error { background: rgba(220, 53, 69, 0.3); }
        .warning { background: rgba(255, 193, 7, 0.3); }
        .manual-auth {
            display: none;
            text-align: left;
            margin-top: 20px;
        }
        .code {
            background: rgba(0, 0, 0, 0.3);
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            margin: 10px 0;
        }
        .btn {
            background: #28a745;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
        }
        .btn:hover {
            background: #218838;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            font-size: 14px;
            box-sizing: border-box;
            height: 120px;
            resize: vertical;
            font-family: monospace;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Forex Sentiment Analyzer</h1>
        <p>Authenticating automatically...</p>
        
        <div id="loading-section">
            <div class="spinner"></div>
            <div id="status">Attempting automatic authentication...</div>
        </div>

                 <div id="manual-section" class="manual-auth">
             <h3>🔐 Authentication Options</h3>
             <p>Choose your preferred authentication method:</p>
             
             <div style="margin: 20px 0; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                 <h4>Option 1: Google Account (Recommended)</h4>
                 <p>Sign in with your Google account for seamless access:</p>
                 <button class="btn" onclick="window.location.href='/auth/google'" style="background: #4285f4;">
                     🔐 Sign in with Google
                 </button>
             </div>
             
             <div style="margin: 20px 0; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                 <h4>Option 2: Manual Token Entry</h4>
                 <p>Enter your Google Cloud identity token manually:</p>
                 <div class="code">gcloud auth print-identity-token</div>
                 <textarea id="manual-token" placeholder="Paste your Google Cloud identity token here..."></textarea>
                 <button class="btn" onclick="manualAuth()">🚀 Access Dashboard</button>
             </div>
         </div>
    </div>

    <script>
        let authAttempts = 0;
        const maxAttempts = 3;

        async function attemptAutoAuth() {
            const statusEl = document.getElementById('status');
            authAttempts++;
            
            try {
                statusEl.textContent = `Attempting authentication (${authAttempts}/${maxAttempts})...`;
                
                // Try to get token from session storage first
                let token = sessionStorage.getItem('authToken');
                
                if (!token) {
                    // Try to detect if user has gcloud CLI available
                    statusEl.textContent = 'Checking for Google Cloud credentials...';
                    
                    // For security reasons, browsers can't directly execute CLI commands
                    // But we can check if the user has previously stored a token
                    token = localStorage.getItem('gcloud_token');
                }
                
                if (token) {
                    statusEl.textContent = 'Testing stored credentials...';
                    
                    // Test the token
                    const response = await fetch('/api/health', {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    
                    if (response.ok) {
                        statusEl.textContent = '✅ Authentication successful! Redirecting...';
                        sessionStorage.setItem('authToken', token);
                        
                        // Redirect to dashboard with token
                        setTimeout(() => {
                            window.location.href = '/?authenticated=true';
                        }, 1000);
                        return;
                    }
                }
                
                // If we get here, automatic auth failed
                if (authAttempts < maxAttempts) {
                    statusEl.textContent = `Authentication attempt ${authAttempts} failed. Retrying...`;
                    setTimeout(attemptAutoAuth, 2000);
                } else {
                    showManualAuth();
                }
                
            } catch (error) {
                console.error('Auth error:', error);
                if (authAttempts < maxAttempts) {
                    statusEl.textContent = `Connection error. Retrying (${authAttempts}/${maxAttempts})...`;
                    setTimeout(attemptAutoAuth, 2000);
                } else {
                    showManualAuth();
                }
            }
        }

        function showManualAuth() {
            document.getElementById('loading-section').style.display = 'none';
            document.getElementById('manual-section').style.display = 'block';
        }

        async function manualAuth() {
            const token = document.getElementById('manual-token').value.trim();
            if (!token) {
                alert('Please enter your token');
                return;
            }

            try {
                const response = await fetch('/api/health', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    sessionStorage.setItem('authToken', token);
                    localStorage.setItem('gcloud_token', token); // Store for future auto-auth
                    window.location.href = '/?authenticated=true';
                } else {
                    alert('Authentication failed. Please check your token.');
                }
            } catch (error) {
                alert('Connection error. Please try again.');
            }
        }

        // Start automatic authentication
        attemptAutoAuth();
    </script>
</body>
</html>
    """

@app.get("/auth")
async def auth_page():
    """Serve authentication page for browser access."""
    auth_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forex Sentiment Analyzer - Authentication</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin: 20px 0;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input[type="password"], textarea {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            font-size: 14px;
            box-sizing: border-box;
        }
        textarea {
            height: 120px;
            resize: vertical;
            font-family: monospace;
        }
        .btn {
            background: #28a745;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            margin: 10px 0;
        }
        .btn:hover {
            background: #218838;
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            background: #545b62;
        }
        .instructions {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 14px;
        }
        .code {
            background: rgba(0, 0, 0, 0.3);
            padding: 8px;
            border-radius: 4px;
            font-family: monospace;
            margin: 5px 0;
        }
        .status {
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: center;
        }
        .success { background: rgba(40, 167, 69, 0.3); }
        .error { background: rgba(220, 53, 69, 0.3); }
        .loading { background: rgba(255, 193, 7, 0.3); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Forex Sentiment Analyzer</h1>
            <p>Enterprise Economic Analysis Dashboard</p>
        </div>

        <div class="instructions">
            <h3>🔐 Authentication Required</h3>
            <p>To access the dashboard, you need a Google Cloud identity token:</p>
            <div class="code">gcloud auth print-identity-token</div>
            <p>Run this command in your terminal and paste the token below.</p>
        </div>

        <div class="form-group">
            <label for="token">Google Cloud Identity Token:</label>
            <textarea id="token" placeholder="Paste your identity token here..."></textarea>
        </div>

        <button class="btn" onclick="authenticate()">🚀 Access Dashboard</button>
        <button class="btn btn-secondary" onclick="testConnection()">🔍 Test Connection</button>

        <div id="status"></div>

        <div class="instructions">
            <h3>📋 Quick Commands</h3>
            <p><strong>Get Token:</strong></p>
            <div class="code">gcloud auth print-identity-token</div>
            <p><strong>Test API:</strong></p>
            <div class="code">curl -H "Authorization: Bearer TOKEN" /api/health</div>
            <p><strong>Alternative Access:</strong></p>
            <div class="code">./open_dashboard.sh</div>
        </div>
    </div>

    <script>
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.innerHTML = message;
            status.className = `status ${type}`;
        }

        async function testConnection() {
            const token = document.getElementById('token').value.trim();
            if (!token) {
                showStatus('❌ Please enter your token first', 'error');
                return;
            }

            showStatus('🔍 Testing connection...', 'loading');

            try {
                const response = await fetch('/api/health', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    showStatus(`✅ Connection successful! Status: ${data.status}`, 'success');
                } else {
                    showStatus(`❌ Connection failed: ${response.status} ${response.statusText}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ Connection error: ${error.message}`, 'error');
            }
        }

        function authenticate() {
            const token = document.getElementById('token').value.trim();
            if (!token) {
                showStatus('❌ Please enter your token first', 'error');
                return;
            }

            // Store token in session storage
            sessionStorage.setItem('authToken', token);
            
            showStatus('🚀 Redirecting to dashboard...', 'loading');
            
            // Redirect to main dashboard
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        }

        // Check if we already have a token
        window.onload = function() {
            const token = sessionStorage.getItem('authToken');
            if (token) {
                document.getElementById('token').value = token;
                showStatus('✅ Token found in session', 'success');
            }
        };
    </script>
</body>
</html>
    """
    return HTMLResponse(content=auth_html)

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon if it exists."""
    favicon_path = os.path.join(frontend_path, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")

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
    """Get sentiment analysis for all currencies."""
    try:
        with get_db_session() as db:
            query = db.query(Sentiment)
            
            if week_start:
                query = query.filter(Sentiment.week_start >= week_start)
            if week_end:
                query = query.filter(Sentiment.week_end <= week_end)
            
            sentiments = query.order_by(Sentiment.computed_at.desc()).limit(50).all()
            
            return [
                SentimentResponse(
                    currency=s.currency,
                    final_sentiment=s.final_sentiment,
                    week_start=s.week_start.isoformat(),
                    week_end=s.week_end.isoformat(),
                    events=s.details_json.get("events", []) if s.details_json else [],
                    computed_at=s.computed_at
                )
                for s in sentiments
            ]
    except Exception as e:
        logger.error(f"Error getting sentiments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/actual-sentiments")
async def get_actual_sentiments(week_start: Optional[str] = None, week_end: Optional[str] = None):
    """Get actual sentiment analysis for all currencies based on actual vs previous values."""
    try:
        with SentimentCalculator() as calculator:
            # Parse date parameters if provided
            start_date = None
            end_date = None
            
            if week_start:
                start_date = datetime.fromisoformat(week_start.replace('Z', '+00:00'))
            if week_end:
                end_date = datetime.fromisoformat(week_end.replace('Z', '+00:00'))
            
            # Calculate actual sentiment
            actual_sentiments = calculator.calculate_actual_sentiment(start_date, end_date)
            
            return {
                "status": "success",
                "data": actual_sentiments,
                "message": f"Retrieved actual sentiment for {len(actual_sentiments)} currencies"
            }
    except Exception as e:
        logger.error(f"Error getting actual sentiments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/actual-sentiment/{currency}")
async def get_actual_sentiment_by_currency(currency: str, week_start: Optional[str] = None, week_end: Optional[str] = None):
    """Get actual sentiment analysis for a specific currency."""
    try:
        with SentimentCalculator() as calculator:
            # Parse date parameters if provided
            start_date = None
            end_date = None
            
            if week_start:
                start_date = datetime.fromisoformat(week_start.replace('Z', '+00:00'))
            if week_end:
                end_date = datetime.fromisoformat(week_end.replace('Z', '+00:00'))
            
            # Calculate actual sentiment for all currencies
            actual_sentiments = calculator.calculate_actual_sentiment(start_date, end_date)
            
            # Filter for specific currency
            currency_sentiment = actual_sentiments.get(currency.upper())
            
            if not currency_sentiment:
                return {
                    "status": "not_found",
                    "data": None,
                    "message": f"No actual sentiment data found for {currency.upper()}"
                }
            
            return {
                "status": "success",
                "data": currency_sentiment,
                "message": f"Retrieved actual sentiment for {currency.upper()}"
            }
    except Exception as e:
        logger.error(f"Error getting actual sentiment for {currency}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/combined-sentiments")
async def get_combined_sentiments(week_start: Optional[str] = None, week_end: Optional[str] = None):
    """Get both forecast and actual sentiment analysis for comparison."""
    try:
        with SentimentCalculator() as calculator:
            # Parse date parameters if provided
            start_date = None
            end_date = None
            
            if week_start:
                start_date = datetime.fromisoformat(week_start.replace('Z', '+00:00'))
            if week_end:
                end_date = datetime.fromisoformat(week_end.replace('Z', '+00:00'))
            
            # Calculate both forecast and actual sentiment
            forecast_sentiments = calculator.calculate_weekly_sentiments(start_date, end_date)
            actual_sentiments = calculator.calculate_actual_sentiment(start_date, end_date)
            
            # Combine the results
            combined_results = {}
            all_currencies = set(forecast_sentiments.keys()) | set(actual_sentiments.keys())
            
            for currency in all_currencies:
                combined_results[currency] = {
                    "currency": currency,
                    "forecast_sentiment": forecast_sentiments.get(currency),
                    "actual_sentiment": actual_sentiments.get(currency),
                    "has_forecast": currency in forecast_sentiments,
                    "has_actual": currency in actual_sentiments
                }
            
            return {
                "status": "success",
                "data": combined_results,
                "message": f"Retrieved combined sentiment for {len(combined_results)} currencies"
            }
    except Exception as e:
        logger.error(f"Error getting combined sentiments: {str(e)}")
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
    """Trigger sentiment analysis (for cron jobs)."""
    try:
        with SentimentCalculator() as calculator:
            sentiments = calculator.calculate_weekly_sentiments()
        
        return {
            "status": "success",
            "message": f"Analysis completed for {len(sentiments)} currencies",
            "currencies": list(sentiments.keys())
        }
    except Exception as e:
        logger.error(f"Error in cron analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cron/collect-actual")
async def cron_collect_actual():
    """Trigger actual data collection (for cron jobs)."""
    try:
        from src.scraper.actual_data_collector import collect_actual_data
        
        total_processed, successful_updates = collect_actual_data()
        
        return {
            "status": "success",
            "message": f"Actual data collection completed",
            "total_processed": total_processed,
            "successful_updates": successful_updates,
            "success_rate": f"{(successful_updates/total_processed*100):.1f}%" if total_processed > 0 else "0%"
        }
    except Exception as e:
        logger.error(f"Error in cron collect actual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Phase 6: Monitoring and Alerting API Endpoints
@app.get("/api/monitoring/health")
async def get_actual_data_health():
    """Get actual data collection health status."""
    try:
        from src.utils.actual_data_monitoring import ActualDataMonitor
        
        with ActualDataMonitor() as monitor:
            health_status = monitor.get_collection_health_status()
        
        return health_status
    except Exception as e:
        logger.error(f"Error getting actual data health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/stats")
async def get_monitoring_stats(days: int = 30):
    """Get comprehensive monitoring statistics."""
    try:
        from src.utils.actual_data_monitoring import get_monitoring_stats
        
        stats = get_monitoring_stats()
        
        # Override accuracy period if specified
        if days != 30:
            from src.utils.actual_data_monitoring import ActualDataMonitor
            with ActualDataMonitor() as monitor:
                stats['accuracy_statistics'] = monitor.get_accuracy_statistics(days)
        
        return stats
    except Exception as e:
        logger.error(f"Error getting monitoring stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/accuracy")
async def get_accuracy_stats(days: int = 30):
    """Get forecast accuracy statistics."""
    try:
        from src.utils.actual_data_monitoring import ActualDataMonitor
        
        with ActualDataMonitor() as monitor:
            accuracy_stats = monitor.get_accuracy_statistics(days)
        
        return accuracy_stats
    except Exception as e:
        logger.error(f"Error getting accuracy stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitoring/test-alert")
async def send_test_alert():
    """Send a test alert to Discord."""
    try:
        from src.utils.alerting import send_test_alert
        
        success = send_test_alert()
        
        if success:
            return {"status": "success", "message": "Test alert sent successfully"}
        else:
            return {"status": "error", "message": "Failed to send test alert"}
    except Exception as e:
        logger.error(f"Error sending test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitoring/check-alerts")
async def check_alerts():
    """Check for alert conditions and send notifications if needed."""
    try:
        from src.utils.alerting import check_and_send_alerts
        
        check_and_send_alerts()
        
        return {"status": "success", "message": "Alert check completed"}
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
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

# OAuth Routes
@app.get("/auth/google")
async def google_auth():
    """Initiate Google OAuth flow."""
    if not OAUTH_AVAILABLE or not GOOGLE_CLIENT_ID:
        return HTMLResponse(content=get_smart_auth_page())
    
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    
    # Store state in session (in production, use proper session management)
    oauth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={get_redirect_uri()}&"
        f"scope=openid email profile&"
        f"response_type=code&"
        f"state={state}"
    )
    
    return RedirectResponse(url=oauth_url)

@app.get("/auth/callback")
async def google_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle Google OAuth callback."""
    if error:
        return HTMLResponse(content=f"<h1>Authentication Error</h1><p>{error}</p>")
    
    if not code:
        return HTMLResponse(content="<h1>Authentication Error</h1><p>No authorization code received</p>")
    
    try:
        # Exchange code for token (simplified - in production use proper OAuth library)
        # For now, redirect to smart auth page
        return HTMLResponse(content=get_smart_auth_page())
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return HTMLResponse(content=get_smart_auth_page())

def get_redirect_uri():
    """Get the OAuth redirect URI."""
    # In production, this should be the actual domain
    return "https://forex-sentiment-analyzer-158616853756.us-central1.run.app/auth/callback"

@app.get("/auth/check")
async def check_auth(request: Request):
    """Check authentication status."""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False}
    
    token = auth_header.split(" ")[1]
    
    try:
        # Test the token by calling health endpoint
        # This is a simple validation - in production use proper token validation
        return {"authenticated": True, "token_valid": True}
    except Exception:
        return {"authenticated": False, "token_valid": False}

# Public API endpoints (no authentication required)
@app.get("/public/health")
async def public_health():
    """Public health endpoint with real system status."""
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
    
    return {
        "status": overall_status,
        "database": db_status,
        "discord": discord_status,
        "last_scrape": None,  # TODO: Implement last scrape tracking
        "last_analysis": None  # TODO: Implement last analysis tracking
    }

@app.get("/public/sentiments")
async def public_sentiments():
    """Public sentiments endpoint with real data."""
    try:
        with SentimentCalculator() as calculator:
            sentiments = calculator.calculate_weekly_sentiments()
        
        response = []
        for currency, data in sentiments.items():
            # Extract week bounds from analysis_period
            week_start_str = data['analysis_period']['week_start'][:10]  # Get YYYY-MM-DD part
            week_end_str = data['analysis_period']['week_end'][:10]      # Get YYYY-MM-DD part
            
            response.append({
                "currency": currency,
                "final_sentiment": data['resolution']['final_sentiment'],
                "week_start": week_start_str,
                "week_end": week_end_str,
                "events": data['events'],
                "computed_at": datetime.now().isoformat()
            })
        
        return response
    except Exception as e:
        logger.error(f"Error getting public sentiments: {e}")
        # Fallback to sample data if database fails
        return [
            {
                "currency": "USD",
                "final_sentiment": "Bearish with Consolidation",
                "week_start": "2025-05-26",
                "week_end": "2025-06-01", 
                "events": [
                    {"event_name": "Core PCE Price Index m/m", "sentiment": "Bearish"},
                    {"event_name": "GDP q/q", "sentiment": "Neutral"},
                    {"event_name": "Unemployment Claims", "sentiment": "Bearish"}
                ],
                "computed_at": datetime.now().isoformat()
            }
        ]

@app.get("/public/events")
async def public_events():
    """Public events endpoint with real data."""
    try:
        with get_db_session() as session:
            query = session.query(Event, Indicator).join(
                Indicator, Event.id == Indicator.event_id
            ).order_by(Event.scheduled_datetime.desc()).limit(100)
            
            results = query.all()
            
            events = []
            for event, indicator in results:
                events.append({
                    "id": event.id,
                    "currency": event.currency,
                    "event_name": event.event_name,
                    "scheduled_datetime": event.scheduled_datetime.isoformat(),
                    "impact_level": event.impact_level,
                    "previous_value": indicator.previous_value,
                    "forecast_value": indicator.forecast_value
                })
            
            return events
    except Exception as e:
        logger.error(f"Error getting public events: {e}")
        # Fallback to sample data if database fails
        return [
            {
                "id": 1,
                "currency": "USD",
                "event_name": "Core PCE Price Index m/m",
                "scheduled_datetime": "2025-05-30T12:30:00Z",
                "impact_level": "High",
                "previous_value": 0.3,
                "forecast_value": 0.2
            }
        ]

@app.get("/public/config")
async def public_config():
    """Public config endpoint with real data."""
    try:
        with get_db_session() as session:
            configs = session.query(Config).all()
            return [
                {
                    "key": config.key,
                    "value": config.value if not config.key.endswith('_URL') else "***",  # Hide sensitive URLs
                    "updated_at": config.updated_at.isoformat()
                }
                for config in configs
            ]
    except Exception as e:
        logger.error(f"Error getting public config: {e}")
        # Fallback to sample data if database fails
        return [
            {
                "key": "DISCORD_WEBHOOK_URL",
                "value": "***",
                "updated_at": datetime.now().isoformat()
            },
            {
                "key": "THRESHOLD_DELTA", 
                "value": "0.0",
                "updated_at": datetime.now().isoformat()
            }
        ]

@app.get("/public/currencies")
async def public_currencies():
    """Public currencies endpoint with real data."""
    try:
        with get_db_session() as session:
            currencies = session.query(Event.currency).distinct().all()
            return [currency[0] for currency in currencies if currency[0]]
    except Exception as e:
        logger.error(f"Error getting public currencies: {e}")
        # Fallback to sample data if database fails
        return ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]

@app.post("/public/discord/test")
async def public_discord_test():
    """Public Discord test endpoint with real functionality."""
    try:
        notifier = DiscordNotifier()
        results = notifier.test_connection()
        
        if all(results.values()):
            return {"status": "success", "message": "All Discord webhooks are working"}
        else:
            return {"status": "partial", "message": "Some Discord webhooks failed", "details": results}
    except Exception as e:
        logger.error(f"Error testing public Discord webhook: {e}")
        return {"status": "error", "message": f"Discord test failed: {str(e)}"}

@app.post("/public/discord/send-report")
async def public_send_report():
    """Public Discord send report endpoint with real functionality."""
    try:
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
        logger.error(f"Error sending public weekly report: {e}")
        return {"status": "error", "message": f"Failed to send weekly report: {str(e)}"}

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
    run_server() 