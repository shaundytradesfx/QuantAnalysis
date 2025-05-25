# Forex Factory Economic Calendar Sentiment Analysis

A comprehensive tool for analyzing economic calendar sentiment from Forex Factory and delivering automated weekly reports via Discord.

## Features

- **Automated Data Scraping**: Retrieves high-impact economic events from Forex Factory
- **Sentiment Analysis**: Calculates bullish/bearish/neutral sentiment based on forecast vs previous values
- **Conflict Resolution**: Handles multiple events per currency with majority rules
- **Discord Integration**: Sends formatted weekly reports to Discord channels
- **Database Persistence**: Stores events, indicators, and calculated sentiments
- **Health Monitoring**: Tracks system health and sends alerts
- **Scheduling**: Automated daily scraping and weekly reporting

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd QuantitativeAnalysis

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.template .env
# Edit .env with your configuration
```

### 2. Database Setup

```bash
# Run database migrations
alembic upgrade head
```

### 3. Discord Setup (Optional)

1. Create Discord webhooks for your channels
2. Set environment variables:
   ```bash
   export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your/main/webhook"
   export DISCORD_HEALTH_WEBHOOK_URL="https://discord.com/api/webhooks/your/health/webhook"
   ```

### 4. Test Discord Integration

```bash
# Test Discord message formatting and webhook connections
python demo_discord_notification.py
```

## Usage

### Command Line Interface

The application provides several commands:

#### Scrape Economic Data
```bash
python -m src.main scrape
```

#### Run Sentiment Analysis
```bash
# Analyze current week
python -m src.main analyze

# Analyze specific week
python -m src.main analyze --week-start 2024-07-29 --week-end 2024-08-04
```

#### Send Discord Notifications
```bash
# Send notification for current week
python -m src.main notify

# Send notification for specific week
python -m src.main notify --week-start 2024-07-29 --week-end 2024-08-04

# Test Discord webhook connections
python -m src.main notify --test
```

#### Start Scheduler
```bash
# Run automated scheduling (daily scraping + weekly reports)
python -m src.main schedule
```

#### Health Check
```bash
python -m src.main health
```

### Discord Message Format

The Discord notifications include:

- **Header**: Week identification and analysis date
- **Currency Sections**: Individual analysis for each currency
  - Event details (previous vs forecast values)
  - Individual event sentiments
  - Overall currency assessment with narrative
- **Net Summary**: Quick overview of all currency sentiments
- **Footer**: Bot identification and next run schedule

Example Discord message:
```
📊 Economic Directional Analysis: Week of May 19, 2025

🇺🇸 USD
1. CPI y/y: Prev=2.10, Forecast=2.30 → 🟢 Bullish
2. Unemployment Rate: Prev=3.80, Forecast=3.70 → 🟢 Bullish
Overall: 🟢 Bullish – Positive economic indicators suggest upside potential for USD & related assets

🇪🇺 EUR
1. PMI Manufacturing: Prev=49.20, Forecast=48.80 → 🔴 Bearish
Overall: 🔴 Bearish – Negative economic indicators suggest downside pressure for EUR & related assets

📈 Net Summary:
• USD: Bullish
• EUR: Bearish

Generated automatically by EconSentimentBot. Next run: May 26, 2025 at 06:00 UTC
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `DISCORD_WEBHOOK_URL` | Main Discord webhook for reports | No |
| `DISCORD_HEALTH_WEBHOOK_URL` | Discord webhook for health alerts | No |
| `SENTIMENT_THRESHOLD` | Threshold for sentiment calculation (default: 0.0) | No |

### Database Configuration

The application uses PostgreSQL with the following tables:
- `events`: Economic calendar events
- `indicators`: Previous and forecast values
- `sentiments`: Calculated weekly sentiments
- `config`: Application configuration

## Architecture

### Components

1. **Scraper Module** (`src/scraper/`): Fetches data from Forex Factory
2. **Analysis Engine** (`src/analysis/`): Calculates sentiment from economic data
3. **Discord Notifier** (`src/discord/`): Formats and sends Discord messages
4. **Database Layer** (`src/database/`): Data models and persistence
5. **Scheduler** (`src/scheduler.py`): Automated task scheduling
6. **Health Monitor** (`src/health_check.py`): System health tracking

### Sentiment Calculation Logic

1. **Individual Events**: Compare forecast vs previous values
   - `Forecast > Previous + δ` → Bullish
   - `Forecast < Previous - δ` → Bearish
   - Otherwise → Neutral

2. **Currency Aggregation**: Resolve conflicts using majority rules
   - Majority bullish → Bullish
   - Majority bearish → Bearish
   - Ties → "Bearish/Bullish with Consolidation"

## Testing

### Run All Tests
```bash
python run_tests.py
```

### Test Specific Components
```bash
# Test sentiment engine
python -m pytest tests/analysis/test_sentiment_engine.py -v

# Test Discord notifier
python -m pytest tests/discord/test_notifier.py -v

# Test scraper
python -m pytest tests/scraper/ -v
```

### Demo Scripts
```bash
# Test Discord functionality
python demo_discord_notification.py

# Test sentiment calculation
python demo_sentiment_test.py
```

## Development Timeline

- **Day 1-2**: Database setup, scraper implementation
- **Day 3**: Monitoring, scheduling, health checks
- **Day 4**: Sentiment calculation engine
- **Day 5**: Sentiment persistence and testing
- **Day 6**: Discord notification system ✅
- **Day 7**: Frontend dashboard (optional)

## Monitoring & Alerts

The system includes comprehensive monitoring:

- **Health Checks**: Automatic system health verification
- **Discord Alerts**: Error notifications sent to health webhook
- **Run Tracking**: Database logging of all operations
- **Performance Monitoring**: Execution time tracking

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure all tests pass before submitting

## License

[Add your license information here]

## Support

For issues and questions:
1. Check the logs for error details
2. Run health checks to verify system status
3. Test Discord connections if notifications fail
4. Review database connectivity for data issues 