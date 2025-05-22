# Forex Factory Sentiment Analyzer

A tool to analyze economic indicators from Forex Factory calendar to determine currency sentiment.

## Features

- Automated scraping of high-impact economic indicators from Forex Factory
- Storage of economic event data, forecasts, and previous values
- Sentiment calculation comparing forecast vs previous values
- Conflict resolution when multiple indicators for a currency conflict
- Weekly Discord notifications with sentiment analysis

## Project Structure

```
.
├── src
│   ├── scraper        # HTML parsing and data extraction
│   ├── database       # Database models and connection
│   ├── analysis       # Sentiment calculation logic
│   └── discord        # Discord notification utilities
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

## Development

- Run the scraper manually:
  ```
  python -m src.run_scraper
  ```
- Run the analysis manually:
  ```
  python -m src.run_analysis
  ```
- Run tests:
  ```
  pytest
  ```

## Deployment

- Schedule the scraper to run daily at 02:00 UTC
- Schedule the analysis to run weekly on Mondays at 06:00 UTC
- Ensure Discord webhook URLs are configured correctly

## License

Proprietary - All rights reserved. 