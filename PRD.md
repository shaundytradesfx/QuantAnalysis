1. Objectives and Success Metrics

1.1 Objectives
Automate News Scanning: Programmatically retrieve all high-impact items from the Forex Factory economic calendar for the current week.
Data Storage & Tracking: Persist previous data releases and forecast values for each economic indicator.
Directional Analysis: Compare forecast versus previous values to categorize each currency’s short-term sentiment (bullish/neutral/bearish).
Conflict Resolution: When multiple same-country data points conflict (e.g., one bullish signal and two bearish), apply a clear rule (e.g., “majority rules” or “bearish with consolidation”) to define the net trend.
Weekly Report Delivery: Generate a formatted message summarizing each currency’s directional view and push it to a designated Discord channel every Monday (or configurable weekday).
1.2 Success Metrics
Data Coverage: ≥95% of all high-impact events in Forex Factory for the current week are captured and stored.
Analysis Accuracy: Directional outputs align with manual “forecast vs previous” assessments for ≥98% of indicators (validated with 20 random spot-checks).
Timeliness: Weekly Discord summary is posted within 5 minutes of the scheduled time, with zero missed reports for one month post-launch.
User Satisfaction: Internal trading desk rates usefulness ≥4/5 in a follow-up survey two weeks after rollout.
2. Scope and User Stories

2.1 Scope
In-Scope
Parsing high-impact items from Forex Factory (impact levels: “High”).
Data persistence for “previous” and “forecast” values.
Sentiment determination logic (bullish if Forecast > Previous, bearish if Forecast < Previous; neutral if equal or within a small delta).
Conflict-resolution algorithm when multiple indicators exist for one currency.
Discord integration (bot or webhook) for weekly push.
Configurable parameters for day/time of report, list of target economies, and consolidation thresholds.
Out-of-Scope
Real-time intraday alerts.
Detailed graphic dashboards (simple textual summary only).
Integration with trading execution platforms.
Historical backtesting or visualization beyond storing raw values.
2.2 User Stories
News Calendar Ingestion
As a backend service, I want to scrape Forex Factory’s economic calendar for current week high-impact releases, so that I have an up-to-date list of events to analyze.
Data Persistence
As a system, I want to store each event’s “previous” and “forecast” values in a database, so that I can reference past values for trend computation.
Directional Analysis Generation
As a data processor, I want to compare stored “forecast” versus “previous” for each event and assign a 1/0/–1 sentiment (bullish/neutral/bearish), so that I can produce a snapshot directional view per economy.
Conflict Resolution Logic
As a system, I want to aggregate multiple sentiments for a single currency by majority or pre-defined weight, so that I produce a final “net” trend label (e.g., “Bearish with Consolidation”).
Weekly Discord Report
As a user, I want to receive a neatly formatted Discord message every Monday summarizing each economy’s directional stance, so that I can start my trading week with macro context without manual data gathering.
Configuration Management
As an administrator, I want to configure the schedule (day/time), Discord webhook URL, and list of target economies via a simple JSON or environment variables, so that I can adjust without redeploying code.
3. Functional Requirements

3.1 Data Ingestion
FR1.1: The tool shall retrieve the Forex Factory calendar page HTML or API (if available) once daily to capture events for the upcoming week.
FR1.2: It shall filter events marked as “High Impact” for all major economies (e.g., USD, EUR, GBP, JPY, CAD, AUD, NZD, CHF).
FR1.3: It shall extract the following fields for each event:
Event Name (e.g., “CPI y/y”)
Currency (e.g., GBP)
Scheduled Date & Time (local time)
Previous Release Value (e.g., 2.2%)
Forecast Value (e.g., 3.3%)
3.2 Data Storage
FR2.1: The tool shall store raw event records in a relational database (e.g., PostgreSQL), with tables:
Events (id, currency, event_name, scheduled_datetime, impact_level)
Indicators (id, event_id → Events.id, previous_value, forecast_value, timestamp_collected)
FR2.2: It shall update stored “previous_value” and “forecast_value” if they change before the event (to capture real-time revisions).
FR2.3: It shall maintain a history of changes—any update to previous or forecast shall append a new record with a timestamp, preserving immutability of prior snapshots.
3.3 Sentiment Calculation
FR3.1: For each event entry, the tool shall compare Forecast vs Previous:
If Forecast > Previous by a configurable threshold δ (default: 0.0), mark sentiment = +1 (Bullish).
If Forecast < Previous by δ, mark sentiment = –1 (Bearish).
If |Forecast − Previous| ≤ δ, mark sentiment = 0 (Neutral).
FR3.2: For each currency per week, aggregate sentiments from all its events.
FR3.3: Apply conflict-resolution rules:
If all sentiments are identical, final sentiment = that value.
If mixed signals:
If majority of events lean bullish (e.g., 2 of 3), final sentiment = Bullish.
If majority bearish, final = Bearish.
If tie (e.g., 1 bullish, 1 bearish, 1 neutral), final = “Bearish with Consolidation” (or configurable wording).
3.4 Discord Notification
FR4.1: The tool shall assemble a textual report with:
Header: Week start date (e.g., “Economic Directional Analysis: Week of May 26, 2025”).
Per-Currency Section (ordered by G7 currency or priority):
Currency code (e.g., GBP)
List of events (e.g., “CPI y/y: Prev=2.2%, Forecast=3.3% → Bullish”)
Final sentiment statement (e.g., “Overall: Bullish for GBP—positive CPI surprise suggests upside for GBP & related assets”)
Net Summary: Table or bullet list of all currencies and their final directional labels.
FR4.2: It shall send this report via a configured Discord webhook URL at a scheduled time (e.g., Mondays at 06:00 UTC).
FR4.3: If any error occurs (e.g., data missing, API failure, parsing errors), send a “Health Check” message to a designated “Alerts” Discord channel with error details.
4. Non-Functional Requirements

4.1 Performance
NFR1.1: The daily scraping job must complete within 2 minutes, even if Forex Factory’s HTML structure changes slightly (resilient parsing).
NFR1.2: The weekly analysis routine (data aggregation + message generation) must complete within 30 seconds.
4.2 Reliability & Monitoring
NFR2.1: All scraping/parsing exceptions, database errors, and Discord message failures must be logged.
NFR2.2: Implement a retry mechanism: if scraping fails due to a transient network error, retry up to 3 times with exponential backoff.
NFR2.3: Maintain a “Last Successful Run” timestamp in the database; if older than 24 hours for daily ingest or older than 7 days for weekly report, send a critical alert via Discord.
4.3 Security
NFR3.1: Store Discord webhook URL (and any API keys) as encrypted environment variables (e.g., AWS Secrets Manager or Docker secrets).
NFR3.2: Restrict database access to the application’s service account with least privilege (read/write only to required tables).
NFR3.3: Ensure any logs containing sensitive data (e.g., historical values) are redacted if forwarded to external monitoring services.
4.4 Maintainability
NFR4.1: Codebase must be modular: separate scraper, database models, analysis engine, and notifier.
NFR4.2: Provide automated unit tests for parsing logic (mock sample HTML) and sentiment calculation.
NFR4.3: Document all REST endpoints or modules, with inline comments and a README explaining configuration variables and deployment steps.
5. Technical Architecture

5.1 High-Level Components
Scraper Module (Backend Service A)
Polls Forex Factory daily via HTTP GET.
Parses HTML (e.g., using BeautifulSoup or equivalent).
Normalizes event timestamp to UTC and filters “High Impact.”
Publishes raw event data to an internal “Scraper → DB” pipeline.
Database (PostgreSQL)
Tables: events, indicators, sentiments, config (for thresholds, webhook URLs, schedule).
Index on (currency, scheduled_datetime) for fast retrieval.
Audit table to store failed parsing attempts.
Analysis Engine (Backend Service B, Cron-Triggered Weekly)
Reads all events in the current week (Mon 00:00 UTC to Sun 23:59 UTC).
For each event, fetches the latest previous_value and forecast_value.
Applies sentiment rules (configurable δ threshold).
Aggregates per currency, applies conflict-resolution logic.
Persists computed “sentiments” in sentiments table with timestamp.
Discord Notifier (Backend Service C, Invoked by Analysis Engine)
Takes the aggregated results, formats a Discord payload (Markdown-supported).
Sends via HTTP POST to the configured Discord webhook.
On error, writes to log and triggers “Health Check” notifier to Admin Webhook.
Configuration & Monitoring (Frontend “Dashboard”)
A minimal static webpage (or simple CLI) to:
View & edit configuration (e.g., webhook URLs, schedule, δ threshold).
View last 7 runs (dates & statuses).
Health summary (Last successful scrape, last report).
Authentication via simple token (no user accounts needed internal-only).
5.2 Data Flow Diagram
+----------------------+       +----------------------+      +----------------------+
|  Forex Factory Site  |  -->  |  Scraper Module      |  --> |  PostgreSQL Database |
+----------------------+       +----------------------+      +----------------------+
                                        |
                             Daily Cron (e.g., 02:00 UTC)
                                        |
                                    (stores Events & Indicators)
                                        |
                          Weekly Cron (e.g., Monday 06:00 UTC)
                                        v
              +----------------------------------------------+
              |      Analysis Engine (Sentiment Logic)       |
              +----------------------------------------------+
                          |                     |
             Sentiments Table Persisted      If Errors → Health Check
                          |                     |
                          v                     |
              +----------------------------------------------+
              |          Discord Notifier (Webhook)          |
              +----------------------------------------------+
                          |
                Discord Channel: #economic-updates
6. Detailed Feature Specifications

6.1 Scraper Module
6.1.1 Inputs

Target URL: https://www.forexfactory.com/calendar.php
Weekly schedule: run once daily at 02:00 UTC (to capture new events/updates).
6.1.2 Behavior

Fetch
Use an HTTP client (e.g., requests) with a 10-second timeout.
If HTTP status ≠ 200, retry up to 3 times (2s, 4s, 8s pauses).
Parse
Identify table rows where impact="High" (Forex Factory uses a CSS class or icon for “High Impact”).
Extract columns: Date, Time, Currency code, Event Name, Previous, Forecast.
Convert Date/Time to UTC (accounting for homepage time zone).
Normalize & Validate
Ensure numeric parsing of “Previous” and “Forecast” (strip “%” and convert to float).
If any numeric field missing or non-parsable, store null and log a warning.
Store/Update
For each extracted row:
Check if event with same (currency, event_name, scheduled_datetime) exists.
If not, insert new row into events, then insert a new indicator record with previous_value, forecast_value.
If exists, compare stored previous_value/forecast_value—if changed, insert new row in indicators table (with reference to event_id).
Error Handling
Any exception during parsing should be caught; log at ERROR level with stack trace.
If >50% of high-impact events fail parsing in one run, send immediate alert to Admin Discord channel.
6.1.3 Outputs

New/updated rows in events and indicators.
Log entries: INFO for “N events processed,” WARNING for missing numeric, ERROR for fatal parsing exceptions.
6.2 Sentiment Calculation
6.2.1 Inputs

All rows in events and latest associated indicators for the current week window (Monday 00:00 UTC to Sunday 23:59 UTC).
6.2.2 Behavior

Fetch Current-Week Data
Query:
SELECT e.id, e.currency, e.event_name, i.previous_value, i.forecast_value
FROM events e
JOIN (
  SELECT DISTINCT ON (event_id) *
  FROM indicators
  WHERE timestamp_collected <= now()
  ORDER BY event_id, timestamp_collected DESC
) i ON i.event_id = e.id
WHERE e.scheduled_datetime BETWEEN '<week_start>' AND '<week_end>'
  AND e.impact_level = 'High';
Calculate Sentiment per Event
For each record:
If forecast_value OR previous_value is null → sentiment = 0 (Neutral) with “Data Unavailable” flag.
Else if (forecast_value − previous_value) > δ → sentiment = +1 (Bullish).
Else if (previous_value − forecast_value) > δ → sentiment = –1 (Bearish).
Else sentiment = 0 (Neutral).
Aggregate per Currency
Group by currency; collect list of (event_name, previous, forecast, sentiment).
Count (count_bullish, count_bearish, count_neutral).
Resolve Conflicts
If count_bullish > count_bearish and count_bullish > count_neutral → final = Bullish.
If count_bearish > count_bullish and count_bearish > count_neutral → final = Bearish.
If neither majority above, final = “Bearish with Consolidation” (or configurable text:
Logic example: if count_bearish ≥ count_bullish then “Bearish with Consolidation”; else “Bullish with Consolidation”).
Store final sentiment in sentiments table:
Schema: (id, currency, week_start, week_end, final_sentiment, details_json, computed_at).
Persist
Insert one row per currency into sentiments with a JSON blob (details_json) containing the array of event objects + sentiment per event.
6.2.3 Outputs

New rows in sentiments.
For auditing, metrics like “Total events analyzed,” “Conflicts detected,” “Currencies covered.”
6.3 Discord Notifier
6.3.1 Inputs

Newly inserted sentiments for the week.
Configurable Discord webhook URL.
Configurable “health check” webhook URL (for error/alert notifications).
6.3.2 Behavior

Build Message Payload
Header Section
**Economic Directional Analysis: Week of <YYYY-MM-DD>**
For each currency (order by priority list: USD, EUR, GBP, JPY, AUD, NZD, CAD, CHF):
**<CURRENCY CODE>**  
1. <Event 1 name>: Prev=<value>, Forecast=<value> → <Bullish/Neutral/Bearish>  
2. <Event 2 name>: …  
**Overall**: <Final Sentiment> – <Short narrative>  
Net Summary (bullet):
- USD: Bearish  
- EUR: Bullish  
- GBP: Bearish with Consolidation  
…  
Footer (optional):
_Generated automatically by EconSentimentBot. Next run: <next_monday_date> at <hh:mm UTC>_
Send via Webhook
HTTP POST JSON payload to DISCORD_WEBHOOK_URL:
{
  "content": "<assembled_markdown_message>"
}
If status code not 2xx, log error and retry once after 30 seconds.
If still fails, push a “Health Check” alert to DISCORD_HEALTH_WEBHOOK_URL with details (error code, payload snippet).
Error Handling
If no sentiment data found for a currency (e.g., missing all events), include a note: “No high-impact events recorded this week.”
If the entire payload is empty (no data at all), send a warning message instead of blank.
6.3.3 Outputs

A Discord message in channel #economic-updates summarizing directional analysis.
On failure, a separate Discord message in #alerts (or configured channel).
7. Data Model / Database Schema

7.1 Table: events
Column	Type	Description
id	SERIAL PRIMARY KEY	Internal unique identifier.
currency	VARCHAR(3)	ISO code (e.g., “GBP”).
event_name	TEXT	Name of the indicator (e.g., “CPI y/y”).
scheduled_datetime	TIMESTAMP WITH TZ	Scheduled date/time (converted to UTC).
impact_level	VARCHAR(10)	e.g., “High”, “Medium”, “Low”.
created_at	TIMESTAMP WITH TZ	When row inserted.
updated_at	TIMESTAMP WITH TZ	Last updated timestamp.
7.2 Table: indicators
Column	Type	Description
id	SERIAL PRIMARY KEY	Unique identifier.
event_id	INTEGER	Foreign key → events(id).
previous_value	NUMERIC(8,4)	Raw previous release value (nullable).
forecast_value	NUMERIC(8,4)	Raw forecast value (nullable).
timestamp_collected	TIMESTAMP WITH TZ	When this data snapshot was captured.
Index on (event_id, timestamp_collected DESC) for retrieving the latest snapshot.
7.3 Table: sentiments
Column	Type	Description
id	SERIAL PRIMARY KEY	Unique identifier.
currency	VARCHAR(3)	Currency code.
week_start	DATE	Monday date for this analysis window.
week_end	DATE	Sunday date for this analysis window.
final_sentiment	VARCHAR(50)	“Bullish”, “Bearish”, “Neutral”, or “Bearish with Consolidation” etc.
details_json	JSONB	Array of objects: { event_name, previous, forecast, sentiment }.
computed_at	TIMESTAMP WITH TZ	Timestamp when analysis was done.
7.4 Table: config
Column	Type	Description
key	VARCHAR(50) PRIMARY KEY	Configuration key (e.g., “DISCORD_WEBHOOK_URL”).
value	TEXT	Corresponding value.
updated_at	TIMESTAMP WITH TZ	When this config was last changed.
8. Security & Compliance

Secrets Management:
All Discord webhook URLs, database credentials, and other secrets must be stored in an encrypted secrets vault (e.g., AWS Secrets Manager, HashiCorp Vault).
Application retrieves these at runtime; never hard-code in source.
Network Security:
Restrict database to accept connections only from the application host(s) (via VPC/subnet/IP allowlist).
Outbound HTTP only to Forex Factory (for scraping) and Discord domains.
Data Privacy:
No personally identifiable information (PII) is stored. Only macroeconomic numbers.
Audit logs should avoid logging raw sensitive values; if needed, mask them.
Access Control:
The configuration dashboard (if hosted) requires a simple shared secret or token. No public access.
CI/CD pipeline (if used) must reference encrypted secrets and not expose them in logs.