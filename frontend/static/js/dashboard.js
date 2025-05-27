/**
 * Dashboard JavaScript for Forex Sentiment Analyzer
 * Handles API communication with Cloud Run backend
 */

// Global variables
let currentCurrency = 'USD';
let sentimentChart = null;
let sentimentData = {};
let eventsData = [];

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Initialize the dashboard
 */
async function initializeDashboard() {
    try {
        // Show loading overlay
        showLoading(true);
        
        // Initialize navigation
        initializeNavigation();
        
        // Load initial data
        await loadDashboardData();
        
        // Initialize chart
        initializeSentimentChart();
        
        // Set up event listeners
        setupEventListeners();
        
        // Hide loading overlay
        showLoading(false);
        
        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showError('Failed to initialize dashboard: ' + error.message);
        showLoading(false);
    }
}

/**
 * Initialize navigation tabs
 */
function initializeNavigation() {
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all tabs
            navTabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(content => content.classList.add('hidden'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Show corresponding content
            const tabName = this.getAttribute('data-tab');
            const content = document.getElementById(tabName + '-content');
            if (content) {
                content.classList.remove('hidden');
            }
            
            // Load tab-specific data
            loadTabData(tabName);
        });
    });
}

/**
 * Load data for specific tab
 */
async function loadTabData(tabName) {
    try {
        switch (tabName) {
            case 'dashboard':
                await loadDashboardData();
                break;
            case 'discord':
                await loadDiscordData();
                break;
            case 'configuration':
                await loadConfigurationData();
                break;
        }
    } catch (error) {
        console.error(`Error loading ${tabName} data:`, error);
        showError(`Failed to load ${tabName} data: ` + error.message);
    }
}

/**
 * Load dashboard data
 */
async function loadDashboardData() {
    try {
        // Load sentiments and events in parallel
        const [sentiments, events] = await Promise.all([
            fetchAPI('/api/sentiments'),
            fetchAPI('/api/events?limit=50')
        ]);
        
        sentimentData = {};
        sentiments.forEach(sentiment => {
            sentimentData[sentiment.currency] = sentiment;
        });
        
        eventsData = events;
        
        // Update UI
        updateCurrentWeekDisplay();
        updateCurrencySidebar();
        updateCurrencySummary();
        updateIndicatorsTable();
        updateWeeklySummary();
        updateSentimentChart();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        throw error;
    }
}

/**
 * Load Discord integration data
 */
async function loadDiscordData() {
    try {
        const status = await fetchAPI('/api/discord/test');
        updateDiscordStatus(status);
    } catch (error) {
        console.error('Error loading Discord data:', error);
        updateDiscordStatus({ status: 'error', message: error.message });
    }
}

/**
 * Load configuration data
 */
async function loadConfigurationData() {
    try {
        const config = await fetchAPI('/api/config');
        updateConfigurationDisplay(config);
    } catch (error) {
        console.error('Error loading configuration data:', error);
        showError('Failed to load configuration: ' + error.message);
    }
}

/**
 * Fetch data from API with authentication
 */
async function fetchAPI(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : (CONFIG.API_BASE_URL + endpoint);
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
}

/**
 * Update current week display
 */
function updateCurrentWeekDisplay() {
    const currentWeekElement = document.getElementById('current-week');
    if (currentWeekElement) {
        const now = new Date();
        const weekStart = new Date(now.setDate(now.getDate() - now.getDay() + 1));
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);
        
        const formatDate = (date) => date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        
        currentWeekElement.textContent = `Week of ${formatDate(weekStart)} - ${formatDate(weekEnd)}`;
    }
}

/**
 * Update currency sidebar
 */
function updateCurrencySidebar() {
    const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD'];
    
    currencies.forEach(currency => {
        const sentimentElement = document.getElementById(`${currency.toLowerCase()}-sentiment`);
        if (sentimentElement) {
            const sentiment = sentimentData[currency];
            if (sentiment) {
                const sentimentClass = getSentimentClass(sentiment.final_sentiment);
                sentimentElement.textContent = sentiment.final_sentiment;
                sentimentElement.className = `ml-auto text-sm ${sentimentClass}`;
            } else {
                sentimentElement.textContent = 'N/A';
                sentimentElement.className = 'ml-auto text-sm text-gray-400';
            }
        }
    });
}

/**
 * Update currency summary
 */
function updateCurrencySummary() {
    const summaryElement = document.getElementById('currency-summary');
    if (!summaryElement) return;
    
    const selectedCurrencyElement = document.getElementById('selected-currency');
    if (selectedCurrencyElement) {
        selectedCurrencyElement.textContent = currentCurrency;
    }
    
    const sentiment = sentimentData[currentCurrency];
    if (sentiment) {
        const sentimentClass = getSentimentClass(sentiment.final_sentiment);
        summaryElement.innerHTML = `
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                    <h3 class="font-semibold text-lg">${currentCurrency}</h3>
                    <p class="text-gray-600">Current Sentiment</p>
                </div>
                <div class="text-right">
                    <span class="text-2xl font-bold ${sentimentClass}">${sentiment.final_sentiment}</span>
                    <p class="text-sm text-gray-500">${sentiment.events.length} events</p>
                </div>
            </div>
            <div class="mt-4">
                <h4 class="font-medium mb-2">Recent Events:</h4>
                <div class="space-y-2">
                    ${sentiment.events.slice(0, 3).map(event => `
                        <div class="text-sm">
                            <span class="font-medium">${event.event_name}</span>
                            <span class="text-gray-500">- ${event.sentiment || 'Neutral'}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } else {
        summaryElement.innerHTML = `
            <div class="text-center text-gray-500">
                <p>No sentiment data available for ${currentCurrency}</p>
            </div>
        `;
    }
}

/**
 * Update indicators table
 */
function updateIndicatorsTable() {
    const tableBody = document.getElementById('indicators-table');
    if (!tableBody) return;
    
    const filteredEvents = eventsData.filter(event => 
        !currentCurrency || event.currency === currentCurrency
    );
    
    tableBody.innerHTML = filteredEvents.map(event => {
        const sentiment = getSentimentFromValues(event.previous_value, event.forecast_value);
        const sentimentClass = getSentimentClass(sentiment);
        
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-3 text-sm">${event.event_name}</td>
                <td class="px-4 py-3 text-sm font-medium">${event.currency}</td>
                <td class="px-4 py-3 text-sm">${formatValue(event.previous_value)}</td>
                <td class="px-4 py-3 text-sm">${formatValue(event.forecast_value)}</td>
                <td class="px-4 py-3 text-sm">
                    <span class="${sentimentClass}">${sentiment}</span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-500">
                    ${new Date(event.scheduled_datetime).toLocaleDateString()}
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Update weekly summary
 */
function updateWeeklySummary() {
    const summaryElement = document.getElementById('weekly-summary');
    if (!summaryElement) return;
    
    const currencies = Object.keys(sentimentData);
    
    summaryElement.innerHTML = currencies.map(currency => {
        const sentiment = sentimentData[currency];
        const sentimentClass = getSentimentClass(sentiment.final_sentiment);
        
        return `
            <div class="bg-white p-4 rounded-lg shadow-sm border cursor-pointer hover:shadow-md transition-shadow"
                 onclick="selectCurrency('${currency}')">
                <div class="flex items-center justify-between">
                    <h3 class="font-semibold text-lg">${currency}</h3>
                    <span class="text-2xl">${getCurrencyFlag(currency)}</span>
                </div>
                <div class="mt-2">
                    <span class="text-sm font-medium ${sentimentClass}">${sentiment.final_sentiment}</span>
                    <p class="text-xs text-gray-500 mt-1">${sentiment.events.length} events analyzed</p>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Initialize sentiment chart
 */
function initializeSentimentChart() {
    const ctx = document.getElementById('sentimentChart');
    if (!ctx) return;
    
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Bullish', 'Bearish', 'Neutral'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#10b981', '#ef4444', '#6b7280'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    updateSentimentChart();
}

/**
 * Update sentiment chart
 */
function updateSentimentChart() {
    if (!sentimentChart) return;
    
    const currencies = Object.keys(sentimentData);
    const sentimentCounts = { Bullish: 0, Bearish: 0, Neutral: 0 };
    
    currencies.forEach(currency => {
        const sentiment = sentimentData[currency].final_sentiment;
        if (sentiment.includes('Bullish')) {
            sentimentCounts.Bullish++;
        } else if (sentiment.includes('Bearish')) {
            sentimentCounts.Bearish++;
        } else {
            sentimentCounts.Neutral++;
        }
    });
    
    sentimentChart.data.datasets[0].data = [
        sentimentCounts.Bullish,
        sentimentCounts.Bearish,
        sentimentCounts.Neutral
    ];
    
    sentimentChart.update();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Currency selection
    document.querySelectorAll('.currency-item').forEach(item => {
        item.addEventListener('click', function() {
            const currency = this.getAttribute('data-currency');
            selectCurrency(currency);
        });
    });
    
    // Discord integration buttons
    const testWebhookBtn = document.getElementById('test-webhook');
    if (testWebhookBtn) {
        testWebhookBtn.addEventListener('click', testDiscordWebhook);
    }
    
    const sendReportBtn = document.getElementById('send-report');
    if (sendReportBtn) {
        sendReportBtn.addEventListener('click', sendWeeklyReport);
    }
}

/**
 * Select currency
 */
function selectCurrency(currency) {
    currentCurrency = currency;
    
    // Update active currency in sidebar
    document.querySelectorAll('.currency-item').forEach(item => {
        item.classList.remove('bg-blue-50', 'border-blue-200');
        if (item.getAttribute('data-currency') === currency) {
            item.classList.add('bg-blue-50', 'border-blue-200');
        }
    });
    
    // Update displays
    updateCurrencySummary();
    updateIndicatorsTable();
}

/**
 * Test Discord webhook
 */
async function testDiscordWebhook() {
    try {
        showLoading(true);
        const result = await fetchAPI('/api/discord/test', { method: 'POST' });
        showSuccess('Discord webhook test completed: ' + result.message);
        await loadDiscordData();
    } catch (error) {
        showError('Discord webhook test failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * Send weekly report
 */
async function sendWeeklyReport() {
    try {
        showLoading(true);
        const result = await fetchAPI('/api/discord/send-report', { method: 'POST' });
        showSuccess('Weekly report sent successfully: ' + result.message);
    } catch (error) {
        showError('Failed to send weekly report: ' + error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * Update Discord status display
 */
function updateDiscordStatus(status) {
    const statusElement = document.getElementById('discord-status');
    if (!statusElement) return;
    
    const statusClass = status.status === 'success' ? 'text-green-600' : 'text-red-600';
    statusElement.innerHTML = `
        <div class="flex items-center space-x-2">
            <div class="w-3 h-3 rounded-full ${status.status === 'success' ? 'bg-green-400' : 'bg-red-400'}"></div>
            <span class="${statusClass}">${status.message || status.status}</span>
        </div>
    `;
}

/**
 * Update configuration display
 */
function updateConfigurationDisplay(config) {
    const configElement = document.getElementById('config-settings');
    if (!configElement) return;
    
    configElement.innerHTML = config.map(item => `
        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
                <h4 class="font-medium">${item.key}</h4>
                <p class="text-sm text-gray-500">Last updated: ${new Date(item.updated_at).toLocaleDateString()}</p>
            </div>
            <div class="text-right">
                <span class="text-sm font-mono bg-white px-2 py-1 rounded border">
                    ${item.value.length > 50 ? item.value.substring(0, 50) + '...' : item.value}
                </span>
            </div>
        </div>
    `).join('');
}

/**
 * Utility functions
 */

function getSentimentClass(sentiment) {
    if (sentiment.includes('Bullish')) return 'sentiment-bullish';
    if (sentiment.includes('Bearish')) return 'sentiment-bearish';
    return 'sentiment-neutral';
}

function getSentimentFromValues(previous, forecast) {
    if (!previous || !forecast) return 'Neutral';
    if (forecast > previous) return 'Bullish';
    if (forecast < previous) return 'Bearish';
    return 'Neutral';
}

function formatValue(value) {
    if (value === null || value === undefined) return 'N/A';
    return typeof value === 'number' ? value.toFixed(2) : value;
}

function getCurrencyFlag(currency) {
    const flags = {
        'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'JPY': '🇯🇵',
        'AUD': '🇦🇺', 'CAD': '🇨🇦', 'CHF': '🇨🇭', 'NZD': '🇳🇿',
        'CNY': '🇨🇳'
    };
    return flags[currency] || '🏳️';
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.toggle('hidden', !show);
    }
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'error');
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
} 