// Static sample data for public demo - Updated to match real API structure with Phase 3 actual sentiment data
const SAMPLE_DATA = {
    health: {
        status: "healthy",
        database: "healthy",
        discord: "healthy",
        last_scrape: "2025-06-02T14:00:00Z",
        last_analysis: "2025-06-02T15:00:00Z"
    },
    
    sentiments: [
        {
            currency: "USD",
            final_sentiment: "Bullish",
            week_start: "2025-06-02",
            week_end: "2025-06-08",
            events: [
                {
                    event_name: "ISM Manufacturing PMI",
                    previous_value: 48.7,
                    forecast_value: 49.3,
                    actual_value: 48.9,
                    sentiment: 1,
                    actual_sentiment: -1,
                    sentiment_label: "Bullish",
                    actual_sentiment_label: "Bearish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "mismatch",
                    reason: "Higher forecast for normal indicator",
                    is_inverse: false
                },
                {
                    event_name: "Fed Chair Powell Speaks",
                    previous_value: null,
                    forecast_value: null,
                    actual_value: null,
                    sentiment: 0,
                    actual_sentiment: 0,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Neutral",
                    data_available: false,
                    actual_available: false,
                    accuracy: "no_data",
                    reason: "Missing forecast or previous value",
                    is_inverse: false
                },
                {
                    event_name: "JOLTS Job Openings",
                    previous_value: 7.19,
                    forecast_value: null,
                    actual_value: 7.44,
                    sentiment: 0,
                    actual_sentiment: 1,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Bullish",
                    data_available: false,
                    actual_available: true,
                    accuracy: "no_forecast",
                    reason: "Missing forecast value",
                    is_inverse: false
                },
                {
                    event_name: "ADP Non-Farm Employment Change",
                    previous_value: 62.0,
                    forecast_value: 110.0,
                    actual_value: 146.0,
                    sentiment: 1,
                    actual_sentiment: 1,
                    sentiment_label: "Bullish",
                    actual_sentiment_label: "Bullish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "match",
                    reason: "Higher forecast for normal indicator",
                    is_inverse: false
                },
                {
                    event_name: "ISM Services PMI",
                    previous_value: 51.6,
                    forecast_value: 52.0,
                    actual_value: 51.2,
                    sentiment: 1,
                    actual_sentiment: -1,
                    sentiment_label: "Bullish",
                    actual_sentiment_label: "Bearish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "mismatch",
                    reason: "Higher forecast for normal indicator",
                    is_inverse: false
                },
                {
                    event_name: "Unemployment Claims",
                    previous_value: 240.0,
                    forecast_value: 232.0,
                    actual_value: 227.0,
                    sentiment: 1,
                    actual_sentiment: 1,
                    sentiment_label: "Bullish",
                    actual_sentiment_label: "Bullish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "match",
                    reason: "Lower forecast for inverse indicator (Unemployment Claims)",
                    is_inverse: true
                },
                {
                    event_name: "Average Hourly Earnings m/m",
                    previous_value: 0.2,
                    forecast_value: 0.3,
                    actual_value: 0.4,
                    sentiment: 1,
                    actual_sentiment: 1,
                    sentiment_label: "Bullish",
                    actual_sentiment_label: "Bullish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "match",
                    reason: "Higher forecast for normal indicator",
                    is_inverse: false
                },
                {
                    event_name: "Non-Farm Employment Change",
                    previous_value: 177.0,
                    forecast_value: 130.0,
                    actual_value: 256.0,
                    sentiment: -1,
                    actual_sentiment: 1,
                    sentiment_label: "Bearish",
                    actual_sentiment_label: "Bullish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "mismatch",
                    reason: "Lower forecast for normal indicator",
                    is_inverse: false
                },
                {
                    event_name: "Unemployment Rate",
                    previous_value: 4.2,
                    forecast_value: 4.2,
                    actual_value: 4.1,
                    sentiment: 1,
                    actual_sentiment: 1,
                    sentiment_label: "Bullish",
                    actual_sentiment_label: "Bullish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "match",
                    reason: "Forecast meets previous value (stability/meeting expectations)",
                    is_inverse: false
                }
            ],
            computed_at: "2025-06-02T15:00:00Z",
            // Phase 3: Add actual sentiment summary
            actual_sentiment: "Bullish",
            forecast_sentiment: "Bullish", 
            forecast_accuracy: 66, // 6 out of 9 events matched
            actual_available: true
        },
        {
            currency: "EUR",
            final_sentiment: "Neutral",
            week_start: "2025-06-02",
            week_end: "2025-06-08",
            events: [
                {
                    event_name: "Monetary Policy Statement",
                    previous_value: null,
                    forecast_value: null,
                    actual_value: null,
                    sentiment: 0,
                    actual_sentiment: 0,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Neutral",
                    data_available: false,
                    actual_available: false,
                    accuracy: "no_data",
                    reason: "Missing forecast or previous value",
                    is_inverse: false
                },
                {
                    event_name: "Main Refinancing Rate",
                    previous_value: 2.4,
                    forecast_value: 2.15,
                    actual_value: 2.15,
                    sentiment: -1,
                    actual_sentiment: -1,
                    sentiment_label: "Bearish",
                    actual_sentiment_label: "Bearish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "match",
                    reason: "Lower forecast for normal indicator",
                    is_inverse: false
                },
                {
                    event_name: "ECB Press Conference",
                    previous_value: null,
                    forecast_value: null,
                    actual_value: null,
                    sentiment: 0,
                    actual_sentiment: 0,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Neutral",
                    data_available: false,
                    actual_available: false,
                    accuracy: "no_data",
                    reason: "Missing forecast or previous value",
                    is_inverse: false
                }
            ],
            computed_at: "2025-06-02T15:00:00Z",
            // Phase 3: Add actual sentiment summary
            actual_sentiment: "Bearish",
            forecast_sentiment: "Neutral",
            forecast_accuracy: 100, // 1 out of 1 available event matched 
            actual_available: true
        },
        {
            currency: "AUD",
            final_sentiment: "Bearish",
            week_start: "2025-06-02",
            week_end: "2025-06-08",
            events: [
                {
                    event_name: "GDP q/q",
                    previous_value: 0.6,
                    forecast_value: 0.4,
                    actual_value: 0.3,
                    sentiment: -1,
                    actual_sentiment: -1,
                    sentiment_label: "Bearish",
                    actual_sentiment_label: "Bearish", 
                    data_available: true,
                    actual_available: true,
                    accuracy: "match",
                    reason: "Lower forecast for normal indicator",
                    is_inverse: false
                }
            ],
            computed_at: "2025-06-02T15:00:00Z",
            // Phase 3: Add actual sentiment summary
            actual_sentiment: "Bearish",
            forecast_sentiment: "Bearish",
            forecast_accuracy: 100, // 1 out of 1 event matched
            actual_available: true
        },
        {
            currency: "CAD",
            final_sentiment: "Neutral",
            week_start: "2025-06-02",
            week_end: "2025-06-08",
            events: [
                {
                    event_name: "Overnight Rate",
                    previous_value: 2.75,
                    forecast_value: 2.5,
                    actual_value: 2.5,
                    sentiment: -1,
                    actual_sentiment: -1,
                    sentiment_label: "Bearish",
                    actual_sentiment_label: "Bearish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "match",
                    reason: "Lower forecast for normal indicator",
                    is_inverse: false
                },
                {
                    event_name: "BOC Rate Statement",
                    previous_value: null,
                    forecast_value: null,
                    actual_value: null,
                    sentiment: 0,
                    actual_sentiment: 0,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Neutral",
                    data_available: false,
                    actual_available: false,
                    accuracy: "no_data",
                    reason: "Missing forecast or previous value",
                    is_inverse: false
                },
                {
                    event_name: "BOC Press Conference",
                    previous_value: null,
                    forecast_value: null,
                    actual_value: null,
                    sentiment: 0,
                    actual_sentiment: 0,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Neutral",
                    data_available: false,
                    actual_available: false,
                    accuracy: "no_data",
                    reason: "Missing forecast or previous value",
                    is_inverse: false
                },
                {
                    event_name: "Employment Change",
                    previous_value: 7.4,
                    forecast_value: null,
                    actual_value: 14.5,
                    sentiment: 0,
                    actual_sentiment: 1,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Bullish",
                    data_available: false,
                    actual_available: true,
                    accuracy: "no_forecast",
                    reason: "Missing forecast value",
                    is_inverse: false
                },
                {
                    event_name: "Unemployment Rate",
                    previous_value: 6.9,
                    forecast_value: null,
                    actual_value: 6.8,
                    sentiment: 0,
                    actual_sentiment: 1,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Bullish",
                    data_available: false,
                    actual_available: true,
                    accuracy: "no_forecast",
                    reason: "Missing forecast value",
                    is_inverse: false
                }
            ],
            computed_at: "2025-06-02T15:00:00Z",
            // Phase 3: Add actual sentiment summary
            actual_sentiment: "Bullish",
            forecast_sentiment: "Neutral",
            forecast_accuracy: 100, // 1 out of 1 available event matched
            actual_available: true
        },
        {
            currency: "CHF",
            final_sentiment: "Bullish",
            week_start: "2025-06-02",
            week_end: "2025-06-08",
            events: [
                {
                    event_name: "CPI m/m",
                    previous_value: 0.0,
                    forecast_value: 0.2,
                    actual_value: 0.1,
                    sentiment: 1,
                    actual_sentiment: 1,
                    sentiment_label: "Bullish",
                    actual_sentiment_label: "Bullish",
                    data_available: true,
                    actual_available: true,
                    accuracy: "match",
                    reason: "Higher forecast for normal indicator",
                    is_inverse: false
                }
            ],
            computed_at: "2025-06-02T15:00:00Z",
            // Phase 3: Add actual sentiment summary
            actual_sentiment: "Bullish",
            forecast_sentiment: "Bullish",
            forecast_accuracy: 100, // 1 out of 1 event matched
            actual_available: true
        },
        {
            currency: "JPY",
            final_sentiment: "Neutral",
            week_start: "2025-06-02",
            week_end: "2025-06-08",
            events: [
                {
                    event_name: "BOJ Gov Ueda Speaks",
                    previous_value: null,
                    forecast_value: null,
                    actual_value: null,
                    sentiment: 0,
                    actual_sentiment: 0,
                    sentiment_label: "Neutral",
                    actual_sentiment_label: "Neutral",
                    data_available: false,
                    actual_available: false,
                    accuracy: "no_data",
                    reason: "Missing forecast or previous value",
                    is_inverse: false
                }
            ],
            computed_at: "2025-06-02T15:00:00Z",
            // Phase 3: Add actual sentiment summary
            actual_sentiment: "Neutral",
            forecast_sentiment: "Neutral",
            forecast_accuracy: null, // No data available for comparison
            actual_available: false
        },
        {
            currency: "GBP",
            final_sentiment: "Neutral",
            week_start: "2025-06-02",
            week_end: "2025-06-08",
            events: [],
            computed_at: "2025-06-02T15:00:00Z",
            // Phase 3: Add actual sentiment summary
            actual_sentiment: "Neutral",
            forecast_sentiment: "Neutral",
            forecast_accuracy: null, // No events this week
            actual_available: false
        },
        {
            currency: "NZD",
            final_sentiment: "Neutral",
            week_start: "2025-06-02",
            week_end: "2025-06-08",
            events: [],
            computed_at: "2025-06-02T15:00:00Z",
            // Phase 3: Add actual sentiment summary
            actual_sentiment: "Neutral",
            forecast_sentiment: "Neutral", 
            forecast_accuracy: null, // No events this week
            actual_available: false
        }
    ],
    
    events: [
        {
            id: 1,
            currency: "USD",
            event_name: "ISM Manufacturing PMI",
            scheduled_datetime: "2025-06-03T14:00:00Z",
            impact_level: "High",
            previous_value: 48.7,
            forecast_value: 49.3,
            actual_value: 48.9,
            sentiment_label: "Bullish",
            actual_sentiment_label: "Bearish"
        },
        {
            id: 2,
            currency: "USD",
            event_name: "ADP Non-Farm Employment Change",
            scheduled_datetime: "2025-06-05T12:15:00Z",
            impact_level: "High",
            previous_value: 62.0,
            forecast_value: 110.0,
            actual_value: 146.0,
            sentiment_label: "Bullish",
            actual_sentiment_label: "Bullish"
        },
        {
            id: 3,
            currency: "USD",
            event_name: "ISM Services PMI",
            scheduled_datetime: "2025-06-05T14:00:00Z",
            impact_level: "High",
            previous_value: 51.6,
            forecast_value: 52.0,
            actual_value: 51.2,
            sentiment_label: "Bullish",
            actual_sentiment_label: "Bearish"
        },
        {
            id: 4,
            currency: "USD",
            event_name: "Unemployment Claims",
            scheduled_datetime: "2025-06-05T12:30:00Z",
            impact_level: "High",
            previous_value: 240.0,
            forecast_value: 232.0,
            actual_value: 227.0,
            sentiment_label: "Bullish",
            actual_sentiment_label: "Bullish"
        },
        {
            id: 5,
            currency: "USD",
            event_name: "Non-Farm Employment Change",
            scheduled_datetime: "2025-06-06T12:30:00Z",
            impact_level: "High",
            previous_value: 177.0,
            forecast_value: 130.0,
            actual_value: 256.0,
            sentiment_label: "Bearish",
            actual_sentiment_label: "Bullish"
        },
        {
            id: 6,
            currency: "EUR",
            event_name: "Main Refinancing Rate",
            scheduled_datetime: "2025-06-06T11:45:00Z",
            impact_level: "High",
            previous_value: 2.4,
            forecast_value: 2.15,
            actual_value: 2.15,
            sentiment_label: "Bearish",
            actual_sentiment_label: "Bearish"
        },
        {
            id: 7,
            currency: "AUD",
            event_name: "GDP q/q",
            scheduled_datetime: "2025-06-04T01:30:00Z",
            impact_level: "High",
            previous_value: 0.6,
            forecast_value: 0.4,
            actual_value: 0.3,
            sentiment_label: "Bearish",
            actual_sentiment_label: "Bearish"
        },
        {
            id: 8,
            currency: "CAD",
            event_name: "Overnight Rate",
            scheduled_datetime: "2025-06-05T14:00:00Z",
            impact_level: "High",
            previous_value: 2.75,
            forecast_value: 2.5,
            actual_value: 2.5,
            sentiment_label: "Bearish",
            actual_sentiment_label: "Bearish"
        },
        {
            id: 9,
            currency: "CHF",
            event_name: "CPI m/m",
            scheduled_datetime: "2025-06-03T07:30:00Z",
            impact_level: "High",
            previous_value: 0.0,
            forecast_value: 0.2,
            actual_value: 0.1,
            sentiment_label: "Bullish",
            actual_sentiment_label: "Bullish"
        }
    ],
    
    config: [
        {
            key: "DISCORD_WEBHOOK_URL",
            value: "***",
            updated_at: "2025-06-02T15:00:00Z"
        },
        {
            key: "THRESHOLD_DELTA",
            value: "0.0",
            updated_at: "2025-06-02T15:00:00Z"
        },
        {
            key: "SCRAPE_SCHEDULE",
            value: "Daily 2:00 AM UTC",
            updated_at: "2025-06-02T15:00:00Z"
        }
    ],
    
    currencies: ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD", "CNY"]
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SAMPLE_DATA;
} else {
    window.SAMPLE_DATA = SAMPLE_DATA;
} 