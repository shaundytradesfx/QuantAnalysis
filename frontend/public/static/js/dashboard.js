/**
 * Dashboard JavaScript for Forex Sentiment Analyzer
 * Handles API communication with Cloud Run backend
 */

// Global variables
let currentCurrency = 'USD';
let sentimentChart = null;
let sentimentData = {};
let eventsData = [];
// Phase 3: Add actual sentiment variables
let currentView = 'forecast'; // 'forecast', 'actual', 'comparison'
let actualSentimentData = {};
let combinedSentimentData = {};

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
        
        // Initialize chart first
        initializeSentimentChart();
        
        // Load initial data (this will update the chart)
        await loadDashboardData();
        
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
        // Phase 3: For now, use sample data that includes actual sentiment
        // In production, this would fetch from the actual API endpoints
        if (window.SAMPLE_DATA) {
            console.log('Using sample data with actual sentiment support');
            
            // Process sample data for forecast sentiment
            sentimentData = {};
            window.SAMPLE_DATA.sentiments.forEach(sentiment => {
                sentimentData[sentiment.currency] = sentiment;
            });
            
            // Phase 3: Process sample data for actual sentiment
            actualSentimentData = {};
            combinedSentimentData = {};
            
            window.SAMPLE_DATA.sentiments.forEach(sentiment => {
                // Create actual sentiment data
                actualSentimentData[sentiment.currency] = {
                    ...sentiment,
                    final_sentiment: sentiment.actual_sentiment || sentiment.final_sentiment,
                    events: sentiment.events.map(event => ({
                        ...event,
                        sentiment: event.actual_sentiment || event.sentiment,
                        sentiment_label: event.actual_sentiment_label || event.sentiment_label
                    }))
                };
                
                // Create combined sentiment data for comparison view
                combinedSentimentData[sentiment.currency] = {
                    ...sentiment,
                    forecast_sentiment: sentiment.final_sentiment,
                    actual_sentiment: sentiment.actual_sentiment || sentiment.final_sentiment,
                    forecast_accuracy: sentiment.forecast_accuracy || null
                };
            });
            
            eventsData = window.SAMPLE_DATA.events || [];
            
        } else {
            // Fallback to API calls if sample data not available
            const [sentiments, events] = await Promise.all([
                fetchAPI('/api/sentiments'),
                fetchAPI('/api/events?limit=50')
            ]);
            
            sentimentData = {};
            sentiments.forEach(sentiment => {
                sentimentData[sentiment.currency] = sentiment;
            });
            
            eventsData = events;
            
            // Phase 3: Try to load actual sentiment data
            try {
                const actualSentiments = await fetchAPI('/api/actual-sentiments');
                actualSentimentData = {};
                actualSentiments.forEach(sentiment => {
                    actualSentimentData[sentiment.currency] = sentiment;
                });
                
                const combinedSentiments = await fetchAPI('/api/combined-sentiments');
                combinedSentimentData = combinedSentiments;
            } catch (error) {
                console.warn('Actual sentiment data not available:', error);
                // Fallback to forecast data
                actualSentimentData = sentimentData;
                combinedSentimentData = sentimentData;
            }
        }
        
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
        updateDiscordStatus({ status: 'error', message: 'Failed to connect to Discord' });
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
 * Fetch data using real API calls to the Cloud Run backend
 */
async function fetchAPI(endpoint, options = {}) {
    try {
        // Get the API base URL from config
        const baseUrl = window.CONFIG?.API_BASE_URL || 'https://forex-sentiment-analyzer-158616853756.us-central1.run.app';
        
        // Convert protected endpoints to public endpoints
        let publicEndpoint = endpoint;
        if (endpoint.startsWith('/api/')) {
            publicEndpoint = endpoint.replace('/api/', '/public/');
        }
        
        // Construct full URL
        const url = `${baseUrl}${publicEndpoint}`;
        
        // Set up request options
        const requestOptions = {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        // Make the API call
        console.log(`Making API call to: ${url}`);
        const response = await fetch(url, requestOptions);
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`API response for ${publicEndpoint}:`, data);
        return data;
        
    } catch (error) {
        console.error(`API call failed for ${endpoint}:`, error);
        
        // Fallback to sample data if API fails
        console.warn('Falling back to sample data due to API error');
        
        // Return static data based on endpoint as fallback
        if (endpoint.includes('health')) {
            return SAMPLE_DATA.health;
        } else if (endpoint.includes('sentiments')) {
            return SAMPLE_DATA.sentiments;
        } else if (endpoint.includes('events')) {
            return SAMPLE_DATA.events;
        } else if (endpoint.includes('config')) {
            return SAMPLE_DATA.config;
        } else if (endpoint.includes('currencies')) {
            return SAMPLE_DATA.currencies;
        } else if (endpoint.includes('discord/test')) {
            return { status: "error", message: "API connection failed - please try the production environment at https://forex-sentiment-frontend.web.app" };
        } else if (endpoint.includes('discord/send-report')) {
            return { status: "error", message: "API connection failed - please try the production environment at https://forex-sentiment-frontend.web.app" };
        }
        
        // Default response
        return { status: "error", message: "API connection failed" };
    }
}

/**
 * Helper function to check if an event is in the future
 * Updated to be more business-logic aware for economic data releases
 */
function isEventInFuture(scheduledDatetime) {
    const now = new Date();
    const eventDate = new Date(scheduledDatetime);
    
    // For demo purposes with sample data, consider current date as June 5, 2025
    // Events on June 6+ should show "not released", June 5 and earlier should show actual data
    const currentDate = new Date('2025-06-05T23:59:59Z'); // End of June 5th, 2025
    
    // Add debug logging to troubleshoot
    console.log('Event date:', eventDate.toISOString(), 'Current date:', currentDate.toISOString(), 'Is future:', eventDate > currentDate);
    
    // Only consider events after June 5, 2025 as "future"
    return eventDate > currentDate;
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
    
    // Get current sentiment data based on selected view
    const currentData = getCurrentSentimentData();
    console.log('updateCurrencySidebar - Current view:', currentView, 'Data keys:', Object.keys(currentData)); // Debug log
    
    currencies.forEach(currency => {
        const sentimentElement = document.getElementById(`${currency.toLowerCase()}-sentiment`);
        const actualSentimentElement = document.getElementById(`${currency.toLowerCase()}-actual-sentiment`);
        
        if (sentimentElement) {
            const sentiment = currentData[currency];
            if (sentiment) {
                const sentimentClass = getSentimentClass(sentiment.final_sentiment);
                sentimentElement.innerHTML = getSentimentIndicator(sentiment.final_sentiment, 'forecast');
                sentimentElement.className = `text-sm ${sentimentClass}`;
            } else {
                sentimentElement.textContent = 'not released';
                sentimentElement.className = 'text-sm text-gray-400';
            }
        }
        
        // Phase 3: Update actual sentiment display
        if (actualSentimentElement) {
            const actualSentiment = actualSentimentData[currency];
            if (actualSentiment && actualSentiment.actual_available) {
                const actualSentimentClass = getSentimentClass(actualSentiment.final_sentiment);
                actualSentimentElement.innerHTML = getSentimentIndicator(actualSentiment.final_sentiment, 'actual');
                actualSentimentElement.className = `text-xs opacity-75 ${actualSentimentClass}`;
            } else {
                actualSentimentElement.textContent = 'Actual: not released';
                actualSentimentElement.className = 'text-xs opacity-75 text-gray-400';
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
    
    // Get current sentiment data based on selected view
    const currentData = getCurrentSentimentData();
    const sentiment = currentData[currentCurrency];
    console.log('updateCurrencySummary - Current view:', currentView, 'Currency:', currentCurrency, 'Sentiment:', sentiment?.final_sentiment); // Debug log
    
    if (sentiment) {
        const sentimentClass = getSentimentClass(sentiment.final_sentiment);
        
        // Count events by sentiment
        const eventCounts = {
            bullish: 0,
            bearish: 0,
            neutral: 0
        };
        
        sentiment.events.forEach(event => {
            if (event.sentiment === 1) eventCounts.bullish++;
            else if (event.sentiment === -1) eventCounts.bearish++;
            else eventCounts.neutral++;
        });
        
        summaryElement.innerHTML = `
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                    <h3 class="font-semibold text-lg">${currentCurrency}</h3>
                    <p class="text-gray-600">Current Sentiment (${currentView})</p>
                </div>
                <div class="text-right">
                    <span class="text-2xl font-bold ${sentimentClass}">${sentiment.final_sentiment}</span>
                    <p class="text-sm text-gray-500">${sentiment.events.length} events</p>
                </div>
            </div>
            <div class="mt-4">
                <h4 class="font-medium mb-2">Event Breakdown:</h4>
                <div class="grid grid-cols-3 gap-2 mb-4">
                    <div class="text-center p-2 bg-green-50 rounded">
                        <div class="text-lg font-bold text-green-600">${eventCounts.bullish}</div>
                        <div class="text-xs text-green-600">Bullish</div>
                    </div>
                    <div class="text-center p-2 bg-red-50 rounded">
                        <div class="text-lg font-bold text-red-600">${eventCounts.bearish}</div>
                        <div class="text-xs text-red-600">Bearish</div>
                    </div>
                    <div class="text-center p-2 bg-gray-50 rounded">
                        <div class="text-lg font-bold text-gray-600">${eventCounts.neutral}</div>
                        <div class="text-xs text-gray-600">Neutral</div>
                    </div>
                </div>
                <h4 class="font-medium mb-2">Recent Events:</h4>
                <div class="space-y-3">
                    ${sentiment.events.slice(0, 5).map(event => {
                        const eventSentimentClass = getSentimentClass(event.sentiment_label);
                        const inversionBadge = event.is_inverse ? 
                            '<span class="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full ml-2">Inverse</span>' : '';
                        
                        return `
                            <div class="border-l-4 ${event.sentiment === 1 ? 'border-green-400' : event.sentiment === -1 ? 'border-red-400' : 'border-gray-400'} pl-3">
                                <div class="flex items-center justify-between">
                                    <span class="font-medium text-sm">${event.event_name}</span>
                                    <span class="text-xs ${eventSentimentClass}">${event.sentiment_label}</span>
                                </div>
                                ${event.data_available ? `
                                    <div class="text-xs text-gray-500 mt-1">
                                        Prev: ${formatValue(event.previous_value)} → Forecast: ${formatValue(event.forecast_value)}
                                        ${inversionBadge}
                                    </div>
                                    <div class="text-xs text-gray-600 mt-1 italic">
                                        ${event.reason}
                                    </div>
                                ` : `
                                    <div class="text-xs text-gray-500 mt-1">
                                        ${event.reason}
                                    </div>
                                `}
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    } else {
        summaryElement.innerHTML = `
            <div class="text-center text-gray-500">
                <p>No sentiment data available for ${currentCurrency} in ${currentView} view</p>
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
    
    // Get current sentiment data based on selected view
    const currentData = getCurrentSentimentData();
    console.log('updateIndicatorsTable - Current view:', currentView, 'Events count:', filteredEvents.length); // Debug log
    
    tableBody.innerHTML = filteredEvents.map(event => {
        // Check if event is in the future to determine if actual data should be shown
        const eventInFuture = isEventInFuture(event.scheduled_datetime);
        
        // Get detailed sentiment info if available from current view data
        const currencySentiment = currentData[event.currency];
        let detailedEvent = null;
        
        if (currencySentiment && currencySentiment.events) {
            detailedEvent = currencySentiment.events.find(e => 
                e.event_name === event.event_name || e.event_id === event.id
            );
        }
        
        // Use detailed sentiment info if available, otherwise calculate basic sentiment
        let sentiment, sentimentClass, reason = '', isInverse = false;
        let actualValue = 'not released', actualSentiment = 'not released', actualSentimentClass = '', accuracy = '';
        
        if (detailedEvent) {
            sentiment = detailedEvent.sentiment_label;
            sentimentClass = getSentimentClass(sentiment);
            reason = detailedEvent.reason || '';
            isInverse = detailedEvent.is_inverse || false;
            
            // Phase 3: Add actual data only if event is not in the future
            if (detailedEvent.actual_available && !eventInFuture) {
                actualValue = formatValue(detailedEvent.actual_value);
                actualSentiment = detailedEvent.actual_sentiment_label || 'not released';
                actualSentimentClass = getSentimentClass(actualSentiment);
                accuracy = detailedEvent.accuracy || '';
            }
        } else {
            sentiment = getSentimentFromValues(event.previous_value, event.forecast_value);
            sentimentClass = getSentimentClass(sentiment);
            
            // Phase 3: Check if event has actual data and is not in the future
            if (event.actual_value !== undefined && !eventInFuture) {
                actualValue = formatValue(event.actual_value);
                actualSentiment = event.actual_sentiment_label || getSentimentFromValues(event.previous_value, event.actual_value);
                actualSentimentClass = getSentimentClass(actualSentiment);
            }
        }
        
        const inversionBadge = isInverse ? 
            '<span class="inline-block px-1 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded ml-1">INV</span>' : '';
        
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-3 text-sm">
                    <div class="font-medium">${event.event_name}</div>
                    ${reason ? `<div class="text-xs text-gray-500 mt-1 italic">${reason}</div>` : ''}
                </td>
                <td class="px-4 py-3 text-sm font-medium">${event.currency}</td>
                <td class="px-4 py-3 text-sm">${formatValue(event.previous_value)}</td>
                <td class="px-4 py-3 text-sm">${formatValue(event.forecast_value)}</td>
                <td class="px-4 py-3 text-sm">${actualValue}</td>
                <td class="px-4 py-3 text-sm">
                    <div class="flex items-center">
                        <span class="${sentimentClass}">${sentiment}</span>
                        ${inversionBadge}
                    </div>
                </td>
                <td class="px-4 py-3 text-sm">
                    ${actualSentiment !== 'not released' ? `<span class="${actualSentimentClass}">${actualSentiment}</span>` : '<span class="text-gray-400">' + actualSentiment + '</span>'}
                </td>
                <td class="px-4 py-3 text-sm">
                    ${accuracy ? getAccuracyBadge(accuracy) : ''}
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
    
    const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD'];
    
    // Get current sentiment data based on selected view
    const currentData = getCurrentSentimentData();
    console.log('updateWeeklySummary - Current view:', currentView, 'Data available for currencies:', Object.keys(currentData)); // Debug log
    
    summaryElement.innerHTML = currencies.map(currency => {
        const sentiment = currentData[currency];
        if (!sentiment) {
            return `
                <div class="bg-white rounded-lg shadow p-4 card-hover">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-medium">${currency}</span>
                        <span class="text-2xl">${getCurrencyFlag(currency)}</span>
                    </div>
                    <div class="text-center text-gray-400">not released</div>
                </div>
            `;
        }
        
        const sentimentClass = getSentimentClass(sentiment.final_sentiment);
        const eventCount = sentiment.events ? sentiment.events.length : 0;
        
        return `
            <div class="bg-white rounded-lg shadow p-4 card-hover cursor-pointer" onclick="selectCurrency('${currency}')">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-medium">${currency}</span>
                    <span class="text-2xl">${getCurrencyFlag(currency)}</span>
                </div>
                <div class="text-center">
                    <div class="text-lg font-bold ${sentimentClass}">${sentiment.final_sentiment}</div>
                    <div class="text-xs text-gray-500">${eventCount} events</div>
                    <div class="text-xs text-blue-500">${currentView} view</div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Initialize sentiment chart - CHANGED TO PIE CHART
 */
function initializeSentimentChart() {
    const ctx = document.getElementById('sentimentChart');
    if (!ctx) return;
    
    sentimentChart = new Chart(ctx, {
        type: 'pie',  // Changed from 'bar' to 'pie'
        data: {
            labels: [],
            datasets: [{
                label: 'Sentiment Distribution',
                data: [],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)', // Green for bullish
                    'rgba(239, 68, 68, 0.8)',  // Red for bearish
                    'rgba(107, 114, 128, 0.8)' // Gray for neutral
                ],
                borderColor: [
                    'rgb(16, 185, 129)',
                    'rgb(239, 68, 68)',
                    'rgb(107, 114, 128)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,  // Show legend for pie chart
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} events (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Update sentiment chart - Updated for current view data
 */
function updateSentimentChart() {
    if (!sentimentChart) return;
    
    // Get current sentiment data based on selected view
    const currentData = getCurrentSentimentData();
    const sentiment = currentData[currentCurrency];
    console.log('updateSentimentChart - Current view:', currentView, 'Currency:', currentCurrency, 'Sentiment data:', sentiment ? 'available' : 'not available'); // Debug log
    
    if (!sentiment || !sentiment.events) {
        sentimentChart.data.labels = ['No Data'];
        sentimentChart.data.datasets[0].data = [1];
        sentimentChart.data.datasets[0].backgroundColor = ['rgba(107, 114, 128, 0.8)'];
        sentimentChart.update();
        return;
    }
    
    // Count sentiment types
    const sentimentCounts = {
        'Bullish': 0,
        'Bearish': 0,
        'Neutral': 0
    };
    
    sentiment.events.forEach(event => {
        if (event.sentiment === 1) sentimentCounts.Bullish++;
        else if (event.sentiment === -1) sentimentCounts.Bearish++;
        else sentimentCounts.Neutral++;
    });
    
    // Filter out zero counts for cleaner pie chart
    const filteredLabels = [];
    const filteredData = [];
    const filteredColors = [];
    
    const colorMap = {
        'Bullish': 'rgba(16, 185, 129, 0.8)',
        'Bearish': 'rgba(239, 68, 68, 0.8)',
        'Neutral': 'rgba(107, 114, 128, 0.8)'
    };
    
    Object.entries(sentimentCounts).forEach(([label, count]) => {
        if (count > 0) {
            filteredLabels.push(label);
            filteredData.push(count);
            filteredColors.push(colorMap[label]);
        }
    });
    
    sentimentChart.data.labels = filteredLabels;
    sentimentChart.data.datasets[0].data = filteredData;
    sentimentChart.data.datasets[0].backgroundColor = filteredColors;
    sentimentChart.update();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Currency selection
    document.querySelectorAll('.currency-item').forEach(item => {
        item.addEventListener('click', function() {
            const currency = this.getAttribute('data-currency');
            selectCurrency(currency);
        });
    });
    
    // Phase 3: Sentiment view toggles - Fixed to handle all button variations
    document.querySelectorAll('.sentiment-toggle button').forEach(button => {
        button.addEventListener('click', function() {
            const view = this.getAttribute('data-view');
            console.log('Toggle button clicked:', view); // Debug log
            switchSentimentView(view);
        });
    });
    
    // Discord actions
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
 * Select currency and update displays
 */
function selectCurrency(currency) {
    currentCurrency = currency;
    
    // Update UI state
    document.querySelectorAll('.currency-item').forEach(item => {
        item.classList.remove('bg-blue-50', 'border-blue-200');
        if (item.getAttribute('data-currency') === currency) {
            item.classList.add('bg-blue-50', 'border-blue-200');
        }
    });
    
    // Update displays
    updateCurrencySummary();
    updateIndicatorsTable();
    updateSentimentChart(); // Add chart update when currency changes
}

/**
 * Phase 3: Switch sentiment view - Fixed to handle comparison view correctly
 */
function switchSentimentView(view) {
    console.log('Switching to view:', view); // Debug log
    currentView = view;
    
    // Update toggle button states
    document.querySelectorAll('.sentiment-toggle button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Handle the comparison view ID mismatch
    let buttonId = `${view}-view`;
    if (view === 'comparison') {
        buttonId = 'comparison-view'; // Match the HTML ID
    }
    
    const activeButton = document.getElementById(buttonId);
    if (activeButton) {
        activeButton.classList.add('active');
        console.log('Activated button:', buttonId); // Debug log
    } else {
        console.error('Button not found:', buttonId); // Debug log
    }
    
    // Update all displays based on current view
    updateCurrencySidebar();
    updateCurrencySummary();
    updateIndicatorsTable();
    updateWeeklySummary();
    updateSentimentChart();
    
    console.log('View switched to:', currentView); // Debug log
}

/**
 * Phase 3: Get sentiment data based on current view
 */
function getCurrentSentimentData() {
    if (currentView === 'actual') {
        return actualSentimentData;
    } else if (currentView === 'comparison') {
        return combinedSentimentData;
    }
    return sentimentData; // forecast view (default)
}

/**
 * Phase 3: Get accuracy badge HTML
 */
function getAccuracyBadge(accuracy) {
    if (!accuracy || accuracy === 'no_data' || accuracy === 'no_forecast') {
        return '<span class="accuracy-badge accuracy-no-data"><i class="fas fa-question-circle"></i> No Data</span>';
    } else if (accuracy === 'match') {
        return '<span class="accuracy-badge accuracy-match"><i class="fas fa-check-circle"></i> Match</span>';
    } else if (accuracy === 'mismatch') {
        return '<span class="accuracy-badge accuracy-mismatch"><i class="fas fa-times-circle"></i> Mismatch</span>';
    }
    return '';
}

/**
 * Phase 3: Get sentiment indicator HTML
 */
function getSentimentIndicator(sentiment, type = 'forecast') {
    const iconClass = type === 'actual' ? 'fas fa-check-circle' : 'fas fa-chart-line';
    const colorClass = type === 'actual' ? 'sentiment-actual' : 'sentiment-forecast';
    const sentimentClass = getSentimentClass(sentiment);
    
    return `<span class="sentiment-indicator ${colorClass}">
        <i class="${iconClass}"></i>
        <span class="${sentimentClass}">${sentiment}</span>
    </span>`;
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
    if (value === null || value === undefined) return 'not released';
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