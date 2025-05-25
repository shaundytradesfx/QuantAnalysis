# Usage Guide - Quantitative Analysis Tool

## Current Status

✅ **WORKING COMPONENTS:**
- Sentiment Analysis Engine (core logic)
- Environment Configuration (python-dotenv)
- HTTP Requests (requests library)
- HTML Parsing (BeautifulSoup)
- Testing Framework (pytest, coverage)

⚠️ **PENDING COMPONENTS:**
- Database Integration (requires psycopg2-binary - Python 3.13 compatibility issue)
- XML Parsing (requires lxml - Python 3.13 compatibility issue)

## Quick Start

### 1. Environment Setup

The virtual environment is located at `/tmp/quantanalysis_venv` to avoid disk space issues on the external drive.

```bash
# Activate the virtual environment
source /tmp/quantanalysis_venv/bin/activate

# Verify installation
pip list
```

### 2. Test Core Functionality

```bash
# Test sentiment analysis logic
python demo_sentiment_test.py

# Test individual components
python test_env.py          # Environment variables
python test_requests.py     # HTTP requests
python test_beautifulsoup.py # HTML parsing

# Run all tests with pytest
pytest demo_sentiment_test.py -v
```

### 3. Available Commands

#### Sentiment Analysis Demo
```bash
python demo_sentiment_test.py
```
This demonstrates:
- Individual event sentiment calculation
- Currency-level conflict resolution
- Multiple test scenarios (bullish, bearish, neutral, missing data)
- Tie-breaking logic

#### Component Tests
```bash
# Test environment loading
python test_env.py

# Test HTTP functionality
python test_requests.py

# Test HTML parsing
python test_beautifulsoup.py
```

## Core Features Demonstrated

### 1. Sentiment Calculation Logic

The sentiment engine implements the following rules:
- **Bullish**: Forecast > Previous + threshold
- **Bearish**: Forecast < Previous - threshold  
- **Neutral**: |Forecast - Previous| ≤ threshold
- **Missing Data**: Treated as Neutral with reason tracking

### 2. Conflict Resolution

When multiple events exist for a currency:
- **Majority Rules**: Most common sentiment wins
- **Tie Breaking**: Bearish bias ("Bearish with Consolidation")
- **Audit Trail**: Full breakdown of sentiment counts

### 3. Test Scenarios

The demo includes comprehensive test cases:
1. **USD**: All bullish events → Bullish
2. **EUR**: Mixed events with bearish majority → Bearish  
3. **GBP**: Tie scenario → Bearish with Consolidation
4. **JPY**: Missing data → Neutral

## Environment Configuration

Create a `.env` file with:
```bash
SENTIMENT_THRESHOLD=0.1
DATABASE_URL=postgresql://user:pass@localhost/dbname
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Next Steps

### For Full Database Integration:

1. **Install Database Dependencies** (when Python 3.13 compatibility is available):
```bash
pip install psycopg2-binary SQLAlchemy alembic
```

2. **Run Database Migrations**:
```bash
alembic upgrade head
```

3. **Test Full Application**:
```bash
python -m src.main analyze
python -m src.main scrape
```

### For Production Deployment:

1. **Install Additional Dependencies**:
```bash
pip install APScheduler discord-webhook pytz
```

2. **Configure Environment Variables**
3. **Set up Database**
4. **Configure Discord Webhooks**
5. **Schedule Cron Jobs**

## Troubleshooting

### Disk Space Issues
- Virtual environment moved to `/tmp/quantanalysis_venv`
- Use `--no-cache-dir` flag with pip installs
- Clean up temporary files regularly

### Python 3.13 Compatibility
- Some packages (psycopg2-binary, lxml) have compilation issues
- Core functionality works without database
- Consider using Python 3.11 or 3.12 for full compatibility

### Module Import Errors
- Ensure virtual environment is activated
- Check that packages are installed: `pip list`
- Verify Python path: `which python`

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
coverage run -m pytest
coverage report
coverage html

# Test specific functionality
python demo_sentiment_test.py
```

## Architecture Overview

```
Core Components (Working):
├── Sentiment Analysis Engine
├── Environment Configuration  
├── HTTP Client (requests)
├── HTML Parser (BeautifulSoup)
└── Testing Framework

Pending Components:
├── Database Layer (PostgreSQL + SQLAlchemy)
├── XML Parser (lxml)
├── Scheduler (APScheduler)
└── Discord Integration
```

The sentiment analysis logic is fully functional and tested. The main limitation is database integration due to Python 3.13 compatibility issues with compiled dependencies. 