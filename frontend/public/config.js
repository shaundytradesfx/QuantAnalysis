// Frontend Configuration for Firebase Hosting
const CONFIG = {
    // API Configuration
    API_BASE_URL: 'https://forex-sentiment-analyzer-ct7vuwq4za-uc.a.run.app',
    
    // Authentication Configuration
    AUTH_REQUIRED: false,
    AUTH_DOMAIN: 'finservcorp.net',
    
    // Application Configuration
    APP_NAME: 'Forex Sentiment Analyzer',
    VERSION: '1.0.0',
    
    // Feature Flags
    FEATURES: {
        DISCORD_INTEGRATION: true,
        REAL_TIME_UPDATES: true,
        MOBILE_SUPPORT: true
    },
    
    // UI Configuration
    THEME: {
        PRIMARY_COLOR: '#667eea',
        SECONDARY_COLOR: '#764ba2',
        SUCCESS_COLOR: '#28a745',
        ERROR_COLOR: '#dc3545',
        WARNING_COLOR: '#ffc107'
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
} 