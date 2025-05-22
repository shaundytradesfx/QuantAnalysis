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