# Forex Factory Sentiment Analyzer

A tool to analyze economic indicators from Forex Factory calendar to determine currency sentiment.

## Features

- Automated scraping of high-impact economic indicators from Forex Factory
- Storage of economic event data, forecasts, and previous values
- Sentiment calculation comparing forecast vs previous values
- Conflict resolution when multiple indicators for a currency conflict
- Weekly Discord notifications with sentiment analysis
- Health monitoring and alerts for failed runs
- Scheduled execution with configurable times

## Project Structure

```
.
├── src
│   ├── scraper        # HTML parsing and data extraction
│   ├── database       # Database models and connection
│   ├── analysis       # Sentiment calculation logic
│   ├── discord        # Discord notification utilities
│   └── utils          # Utility modules for logging and monitoring
├── tests              # Unit and integration tests
├── alembic            # Database migrations
├── requirements.txt   # Python dependencies
└── env.template       # Environment variables template
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy env.template to .env and fill in the required values
5. Set up the database:
   ```
   alembic upgrade head
   ```
6. Install the package in development mode:
   ```
   pip install -e .
   ```

## Usage

### Running the Scraper

To run the scraper once:

```
python -m src.main scrape
```

### Running Sentiment Analysis

To run sentiment analysis for the current week:

```
python -m src.main analyze
```

To run sentiment analysis for a specific week:

```
python -m src.main analyze --week-start 2024-01-08 --week-end 2024-01-14
```

### Running the Scheduler

To run the scraper on a schedule (as defined in the .env file):

```
python -m src.main schedule
```

### Running Health Checks

To check the health of the application:

```
python -m src.main health
```

## Sentiment Analysis

The sentiment analysis engine processes economic indicators to determine currency sentiment:

### Sentiment Calculation Logic

1. **Individual Event Analysis**: For each economic event, compares forecast vs previous values:
   - If `Forecast > Previous + threshold` → **Bullish** (+1)
   - If `Forecast < Previous - threshold` → **Bearish** (-1)
   - If `|Forecast - Previous| ≤ threshold` → **Neutral** (0)

2. **Currency-Level Conflict Resolution**: When multiple events exist for a currency:
   - **Majority Rules**: If one sentiment type has more events, it wins
   - **Tie Resolution**: If tied, defaults to "Bearish with Consolidation" or "Bullish with Consolidation"
   - **Missing Data**: Events with missing forecast/previous values are marked as neutral

3. **Data Persistence**: Final sentiments are stored in the `sentiments` table with:
   - Currency code
   - Week start/end dates
   - Final sentiment label
   - Detailed JSON with all event analysis
   - Computation timestamp

### Sentiment Threshold

The `SENTIMENT_THRESHOLD` environment variable controls the minimum difference required to trigger bullish/bearish sentiment. Default is 0.0, meaning any positive/negative change triggers sentiment.

## Development

### Running Tests

Run all tests:

```
python run_tests.py
```

Run tests with coverage:

```
python run_tests.py --with-coverage
```

Run tests for a specific module:

```
python run_tests.py --module scraper
python run_tests.py --module analysis
```

Generate HTML coverage report:

```
python run_tests.py --with-coverage --html-report
```

## Configuration

The following environment variables can be configured in the .env file:

- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: forex_sentiment)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password
- `DISCORD_WEBHOOK_URL`: Discord webhook URL for sentiment reports
- `DISCORD_HEALTH_WEBHOOK_URL`: Discord webhook URL for health alerts
- `SCRAPER_SCHEDULE_TIME`: Time to run the scraper daily (default: 02:00 UTC)
- `ANALYSIS_SCHEDULE_DAY`: Day to run the analysis weekly (default: Monday)
- `ANALYSIS_SCHEDULE_TIME`: Time to run the analysis weekly (default: 06:00 UTC)
- `SENTIMENT_THRESHOLD`: Delta threshold for sentiment calculation (default: 0.0)

## Deployment

- Schedule the scraper to run daily at the time specified in the .env file (default: 02:00 UTC)
- Schedule the analysis to run weekly on the day and time specified in the .env file (default: Mondays at 06:00 UTC)
- Set up monitoring to check the health of the application regularly
- Ensure Discord webhook URLs are configured correctly for sentiment reports and health alerts

## License

Proprietary - All rights reserved. 