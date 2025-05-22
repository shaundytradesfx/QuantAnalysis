. Implementation Checklist

Note: Backend and Frontend tasks are separated. Each item is marked as “[ ]” to show as TODO.
10.1 Backend Tasks
Project Setup & Infrastructure
 Initialize Git repository and CI pipeline (lint, unit test).
 Provision PostgreSQL instance (cloud-managed or on-premise).
 Create environment configuration file (e.g., .env) template with placeholder keys.
 Set up logging framework (e.g., structured JSON logs).
Database Schema & Migrations
 Define events, indicators, sentiments, config tables.
 Create migration scripts (e.g., Flyway, Alembic).
 Run migrations on dev DB; verify schema correctness.
Scraper Module (Service A)
 Implement HTTP fetcher (with retry/backoff).
 Write HTML parsing logic (identify “High Impact” events).
 Normalize date/time to UTC.
 Validate and convert numeric fields.
 Insert/Update logic into events and indicators tables.
 Logging & error handling (retry on transient failures).
 Unit tests with sample HTML snapshots (mock responses).
Sentiment Calculation Engine (Service B)
 Query logic: retrieve current-week events with latest indicator snapshots.
 Implement comparison logic (Forecast vs Previous with threshold δ).
 Conflict-resolution logic per currency.
 Persist final sentiment and details in sentiments table.
 Unit tests for various scenarios (all bullish, mixed signals, ties).
Discord Integration (Service C)
 Build message templating utility (Markdown formatting).
 Implement HTTP POST to DISCORD_WEBHOOK_URL.
 Add retry logic on 5xx or network errors.
 Health-check notifier: separate webhook for errors.
 Unit test: stub Discord webhook (e.g., local HTTP server) to verify payload.
Configuration & Scheduling
 Create config table migration.
 Build logic to read config keys at runtime (Discord URLs, schedule times, δ).
 Integrate a scheduler (e.g., cron job or APScheduler) for:
Daily Scraper run at 02:00 UTC
Weekly Analysis + Discord publish at 06:00 UTC every Monday
Monitoring & Alerts
 Instrument metrics (e.g., number of events parsed, sentiments generated) for logs or a monitoring dashboard.
 If daily run fails or weekly run fails, send detailed error via “Health Check” Discord.
 Create runbook notes: “How to troubleshoot scrape errors,” “How to re-trigger a run manually.”
Testing & Deployment
 Run end-to-end flow on staging: simulate a week’s worth of data, verify Discord output.
 Load-test scraper with an artificially large HTML to ensure performance <2 minutes.
 Prepare Dockerfile or deployment scripts (e.g., Terraform or CloudFormation) for production rollout.
 Deployment to production environment; schedule cron jobs.
10.2 Frontend (Configuration Dashboard / CLI)
Minimal Config Dashboard (Optional)
 Create a simple web interface (e.g., Node.js/Express + React or Flask + HTML) with password/token-based access.
 Form to update DISCORD_WEBHOOK_URL, DISCORD_HEALTH_WEBHOOK_URL, SCHEDULE_TIMES, THRESHOLD_DELTA.
 Display last 7 run statuses (pull from logs or a jobs table).
CLI Alternative
 If no web UI, build a command-line script (python manage.py update-config --key KEY --value VAL) to modify config table.
 Validate entries (e.g., proper URL format for webhook).
Documentation & README
 Document environment variables, database setup, and secrets management.
 Describe steps to run scraper and analysis locally.
 Provide sample JSON config and instructions for adding new economies or event categories.
Authentication & Access Control
 If web UI is chosen, set up a single static token (stored in secrets) used in request headers.
 Ensure HTTPS is enforced (if hosted externally).
11. Open Questions & Clarifications

Threshold “δ” Value
The PRD uses δ = 0.0 by default. Do you want to set a nonzero threshold (e.g., ignore small revisions <0.1%)?
Treatment of Non-Numeric Forecasts
Some events may list “N/A” or “Survey.” Should these default to Neutral, or be excluded from sentiment count?
Additional Conflict-Resolution Weights
Do certain indicators carry more weight (e.g., CPI > PMI)? If yes, we should store a priority field per event type.
Discord Formatting Preferences
Would you prefer embeds rather than plain Markdown text? (Embeds allow richer formatting but require a bot token rather than a webhook.)
Support for Multiple Languages
Currently, the tool only prepares English text. If on-boarding colleagues in non-English regions (e.g., Japanese traders), would localization be needed?
Time Zone for “Current Week” Definition
We define week as Monday 00:00 UTC – Sunday 23:59 UTC. If your trading operation runs in Asia/Dubai (UTC+4), should we align to that local week boundary?
