# ForexSentiment Dashboard

A streamlined web dashboard for the Forex Factory Sentiment Analyzer, built with vanilla JavaScript, Tailwind CSS, and Chart.js. Only includes features with full backend support.

## Features

- **Real-time Sentiment Analysis**: View current week sentiment analysis for major currencies
- **Interactive Charts**: Doughnut charts showing sentiment distribution for selected currencies
- **Economic Indicators Table**: Detailed view of economic events and their impact
- **Currency Filtering**: Easy navigation between different currencies
- **Discord Integration**: Test webhooks and send weekly reports directly from the dashboard
- **Configuration Management**: Update system settings through the web interface
- **Responsive Design**: Works on desktop and mobile devices
- **Auto-refresh**: Data refreshes every 5 minutes automatically

## Navigation Tabs

The dashboard includes only functional tabs with backend support:

### 1. Dashboard (Default)
- Currency sentiment analysis with interactive charts
- Economic indicators table for selected currency
- Weekly currency summary grid
- Real-time data updates

### 2. Sentiment Analysis
- Same as Dashboard tab - focused view of sentiment data
- Currency-specific analysis and charts

### 3. Discord Integration
- Test Discord webhook connectivity
- Send weekly reports manually
- View webhook status and connection health

### 4. Configuration
- View and update system configuration settings
- Real-time configuration management
- Settings persistence to database

## Removed Features

The following UI elements have been removed as they lack backend implementations:
- ❌ Calendar tab (no calendar backend)
- ❌ Data Storage tab (no data management backend)
- ❌ Reports tab (no reports backend)
- ❌ Logs tab (no logs viewer backend)
- ❌ Settings tab (merged into Configuration)
- ❌ Report History sidebar (no history backend)

## API Integration

The dashboard integrates with these backend endpoints:

- `GET /api/health` - System health status
- `GET /api/sentiments` - Sentiment analysis data
- `GET /api/events` - Economic events data
- `GET /api/config` - Configuration settings
- `POST /api/config` - Update configuration
- `POST /api/discord/test` - Test Discord webhooks
- `POST /api/discord/send-report` - Send weekly reports

## Usage

1. Start the FastAPI server:
   ```bash
   python -m src.main web
   ```

2. Open your browser to `http://127.0.0.1:8000`

3. Navigate between tabs using the header navigation:
   - **Dashboard**: Main sentiment analysis view
   - **Discord Integration**: Webhook management
   - **Configuration**: System settings

## Features Overview

### Currency Selection
- Click on any currency in the sidebar to view its analysis
- Sentiment indicators show at-a-glance status for each currency
- Selected currency is highlighted with blue background

### Sentiment Analysis
- Doughnut chart shows distribution of bullish/bearish/neutral events
- Currency summary panel shows overall sentiment and recent events
- Color-coded indicators: 🟢 Bullish, 🔴 Bearish, ⚪ Neutral

### Economic Indicators
- Table shows recent economic events for selected currency
- Displays previous values, forecasts, and calculated sentiment
- Filtered by currency selection

### Discord Integration
- Test webhook connectivity with one click
- Send weekly reports directly from the dashboard
- Real-time status indicators for webhook health

### Configuration Management
- View all system configuration settings
- Update settings with immediate persistence
- Real-time validation and feedback

## Browser Compatibility

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Development

The dashboard uses modern JavaScript features and requires no build process. All dependencies are loaded via CDN:

- Tailwind CSS (styling)
- Chart.js (charts)
- Font Awesome (icons)

For development, simply edit the files and refresh the browser. The FastAPI server supports hot reloading when started with the `--reload` flag.

## Architecture

- **Frontend**: Vanilla JavaScript with ES6+ classes
- **Styling**: Tailwind CSS utility-first framework
- **Charts**: Chart.js for interactive data visualization
- **Icons**: Font Awesome for consistent iconography
- **Backend**: FastAPI REST API
- **Database**: PostgreSQL with real-time data

## Performance

- Lightweight frontend with minimal dependencies
- Efficient API calls with error handling
- Auto-refresh every 5 minutes for real-time data
- Responsive design optimized for all screen sizes
