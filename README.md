# Forex Factory Sentiment Analyzer

A comprehensive system for automated economic calendar analysis and sentiment tracking from Forex Factory, with Discord notifications and a modern web dashboard.

## 🚀 Features

- **Automated Data Scraping**: Retrieves high-impact economic events from Forex Factory
- **Sentiment Analysis**: Calculates bullish/bearish/neutral sentiment based on forecast vs previous values
- **Discord Integration**: Automated weekly reports and health alerts
- **Web Dashboard**: Modern, responsive interface for viewing analysis and managing the system
- **Database Persistence**: PostgreSQL storage with full audit trail
- **Conflict Resolution**: Intelligent aggregation when multiple indicators conflict
- **Health Monitoring**: System status tracking and alerting

## 📊 Web Dashboard

The system includes a modern web dashboard built with vanilla JavaScript, Tailwind CSS, and Chart.js:

### Features
- **Real-time Sentiment Analysis**: View current week sentiment for all major currencies
- **Interactive Charts**: Doughnut charts showing sentiment distribution
- **Economic Indicators Table**: Detailed view of events and their impact
- **Currency Filtering**: Easy navigation between different currencies
- **Discord Integration**: Test webhooks and send reports directly from the UI
- **Responsive Design**: Works on desktop and mobile devices
- **Auto-refresh**: Data updates every 5 minutes

### Access the Dashboard
1. Start the web server:
   ```bash
   python -m src.main web
   ```
2. Open your browser to `http://127.0.0.1:8000`

## 🛠 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd QuantitativeAnalysis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   createdb forex_sentiment
   ```

4. **Configure environment variables**
   ```bash
   cp env.template .env
   # Edit .env with your database credentials and Discord webhook URL
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

## 🎯 Usage

### Command Line Interface

The system provides several commands for different operations:

```bash
# Run the scraper once
python -m src.main scrape

# Run sentiment analysis
python -m src.main analyze

# Send Discord notification
python -m src.main notify

# Test Discord webhook
python -m src.main notify --test

# Start the scheduler (automated runs)
python -m src.main schedule

# Check system health
python -m src.main health

# Start the web dashboard
python -m src.main web
```

### Web Dashboard

Access the web interface at `http://127.0.0.1:8000` for:
- Viewing sentiment analysis results
- Managing system configuration
- Testing Discord integration
- Monitoring system health

### Discord Integration

The system sends automated weekly reports to Discord with:
- Currency sentiment analysis (Bullish/Bearish/Neutral)
- Individual event details (Previous vs Forecast)
- Overall market assessment
- Next run schedule

Example Discord message:
```
📊 Economic Directional Analysis: Week of May 19, 2025

🇺🇸 USD
1. CPI y/y: Prev=2.10, Forecast=2.30 → 🟢 Bullish
2. Unemployment Rate: Prev=3.80, Forecast=3.70 → 🟢 Bullish
Overall: 🟢 Bullish – Positive economic indicators suggest upside potential

📈 Net Summary:
• USD: Bullish
• EUR: Bearish

Generated automatically by EconSentimentBot. Next run: May 26, 2025 at 06:00 UTC
```

## 🏗 Architecture

### Backend Components
- **Scraper Module**: HTML parsing and data extraction from Forex Factory
- **Analysis Engine**: Sentiment calculation with conflict resolution
- **Discord Notifier**: Webhook integration and message formatting
- **Database Layer**: PostgreSQL with SQLAlchemy ORM
- **Scheduler**: APScheduler for automated runs
- **FastAPI Server**: REST API for the web dashboard

### Frontend Components
- **Dashboard**: Modern web interface with real-time data
- **Charts**: Interactive sentiment visualization
- **API Integration**: RESTful communication with backend
- **Responsive Design**: Mobile-friendly interface

### Database Schema
- `events`: Economic calendar events
- `indicators`: Previous/forecast values with timestamps
- `sentiments`: Calculated weekly sentiment analysis
- `config`: System configuration settings
- `audit_failures`: Error tracking and debugging

## 📅 Automated Schedule

- **Daily Scraper**: Runs at 02:00 UTC to capture new events
- **Weekly Analysis**: Runs every Monday at 06:00 UTC
- **Discord Reports**: Sent automatically after analysis completion

## 🔧 Configuration

Key environment variables:

```bash
# Database
DB_HOST=localhost
DB_USER=shaun
DB_NAME=forex_sentiment

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Analysis
SENTIMENT_THRESHOLD=0.0  # Threshold for bullish/bearish classification
```

## 🧪 Testing

Run the test suite:
```bash
python run_tests.py
```

Test individual components:
```bash
# Test Discord integration
python demo_discord_notification.py

# Test sentiment analysis
python demo_sentiment_test.py

# Test database connection
python test_database_connection.py
```

## 📈 Monitoring

### Health Checks
- Database connectivity
- Discord webhook status
- Last successful scraper run
- Last analysis completion

### Logging
- Structured JSON logging
- Error tracking with stack traces
- Performance metrics
- Audit trail for all operations

## 🚀 Deployment

### Production Setup
1. Configure production database
2. Set up environment variables
3. Configure reverse proxy (nginx)
4. Set up systemd services for automation
5. Configure monitoring and alerting

### Docker Deployment
```bash
# Build and run with Docker
docker build -t forex-sentiment .
docker run -d -p 8000:8000 forex-sentiment
```

## 📚 API Documentation

When the server is running, visit `http://127.0.0.1:8000/docs` for interactive API documentation.

### Key Endpoints
- `GET /api/health` - System health status
- `GET /api/sentiments` - Current sentiment analysis
- `GET /api/events` - Economic events data
- `POST /api/discord/test` - Test Discord webhooks
- `POST /api/discord/send-report` - Send weekly report

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting guide in USAGE_GUIDE.md
2. Review the logs for error details
3. Test individual components using the demo scripts
4. Open an issue with detailed error information

## 🎉 Acknowledgments

- Forex Factory for providing economic calendar data
- Discord for webhook integration
- The open-source community for the excellent libraries used 