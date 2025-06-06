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
        
        // Set up event listeners (ensure this happens after DOM is ready)
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
 * Check if an event's actual data should be available based on current date
 */
function isActualDataAvailable(scheduledDateTime) {
    const now = new Date();
    const eventDate = new Date(scheduledDateTime);
    
    // Actual data should only be available if the event has occurred (past date)
    // Add a small buffer (1 hour) to account for data publishing delays
    const bufferMs = 60 * 60 * 1000; // 1 hour in milliseconds
    return now.getTime() > (eventDate.getTime() + bufferMs);
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
            
            // Phase 3: Process sample data for actual sentiment with date validation
            actualSentimentData = {};
            combinedSentimentData = {};
            
            window.SAMPLE_DATA.sentiments.forEach(sentiment => {
                // Create actual sentiment data with date validation
                const processedEvents = sentiment.events.map(event => {
                    // Find the corresponding event in eventsData to get scheduled_datetime
                    const eventDetail = window.SAMPLE_DATA.events.find(e => 
                        e.event_name === event.event_name && e.currency === sentiment.currency
                    );
                    
                    // Check if actual data should be available based on date
                    const actualAvailable = eventDetail ? 
                        isActualDataAvailable(eventDetail.scheduled_datetime) && event.actual_available : 
                        false;
                    
                    return {
                        ...event,
                        actual_available: actualAvailable,
                        // If actual data shouldn't be available, remove actual values
                        actual_value: actualAvailable ? event.actual_value : null,
                        actual_sentiment: actualAvailable ? event.actual_sentiment : null,
                        actual_sentiment_label: actualAvailable ? event.actual_sentiment_label : null,
                        accuracy: actualAvailable ? event.accuracy : null
                    };
                });
                
                // Check if any events have actual data available
                const hasActualData = processedEvents.some(event => event.actual_available);
                
                actualSentimentData[sentiment.currency] = {
                    ...sentiment,
                    events: processedEvents,
                    actual_available: hasActualData,
                    final_sentiment: hasActualData ? sentiment.actual_sentiment : sentiment.final_sentiment
                };
                
                // Create combined sentiment data for comparison view
                combinedSentimentData[sentiment.currency] = {
                    ...sentiment,
                    events: processedEvents,
                    forecast_sentiment: sentiment.final_sentiment,
                    actual_sentiment: hasActualData ? sentiment.actual_sentiment : null,
                    forecast_accuracy: hasActualData ? sentiment.forecast_accuracy : null,
                    actual_available: hasActualData
                };
            });
            
            // Process events data with date validation
            eventsData = window.SAMPLE_DATA.events.map(event => ({
                ...event,
                actual_available: isActualDataAvailable(event.scheduled_datetime),
                actual_value: isActualDataAvailable(event.scheduled_datetime) ? event.actual_value : null,
                actual_sentiment_label: isActualDataAvailable(event.scheduled_datetime) ? event.actual_sentiment_label : null
            }));
            
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
        const actualSentimentElement = document.getElementById(`${currency.toLowerCase()}-actual-sentiment`);
        
        if (sentimentElement) {
            // Get data based on current view
            const currentData = getCurrentViewData();
            const sentiment = currentData[currency];
            
            if (sentiment) {
                const sentimentClass = getSentimentClass(sentiment.final_sentiment);
                sentimentElement.innerHTML = getSentimentIndicator(sentiment.final_sentiment, currentView === 'actual' ? 'actual' : 'forecast');
                sentimentElement.className = `text-sm ${sentimentClass}`;
            } else {
                sentimentElement.textContent = 'not released';
                sentimentElement.className = 'text-sm text-black';
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
                actualSentimentElement.className = 'text-xs opacity-75 text-black';
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
    
    // Get data based on current view
    const currentData = getCurrentSentimentData();
    const sentiment = currentData[currentCurrency];
    
    if (!sentiment) {
        summaryElement.innerHTML = `
            <div class="text-center text-black py-8">
                <i class="fas fa-chart-line text-4xl mb-4 opacity-50"></i>
                <p>No data available for ${currentCurrency}</p>
                <p class="text-sm text-black">Data may not be released yet</p>
            </div>
        `;
        return;
    }
    
    // Get appropriate sentiment based on view
    let displaySentiment = sentiment.final_sentiment;
    let title = 'Forecast Sentiment';
    let description = 'Based on forecast vs previous values';
    
    if (currentView === 'actual') {
        if (sentiment.actual_available) {
            displaySentiment = sentiment.actual_sentiment || sentiment.final_sentiment;
            title = 'Actual Sentiment';
            description = 'Based on actual vs previous values';
        } else {
            displaySentiment = 'not released';
            title = 'Actual Sentiment';
            description = 'Actual data not yet available';
        }
    } else if (currentView === 'comparison') {
        title = 'Forecast vs Actual Comparison';
        description = sentiment.actual_available ? 
            `Forecast accuracy: ${sentiment.forecast_accuracy || 'N/A'}%` : 
            'Actual data not yet available for comparison';
    }
    
    const sentimentClass = getSentimentClass(displaySentiment);
    const eventCount = sentiment.events ? sentiment.events.length : 0;
    const availableEvents = sentiment.events ? 
        sentiment.events.filter(e => currentView === 'actual' ? e.actual_available : e.data_available).length : 0;
    
    let summaryContent = `
        <div class="mb-6">
            <h3 class="text-lg font-semibold text-black mb-2">${title}</h3>
            <p class="text-sm text-black mb-4">${description}</p>
            <div class="text-center p-6 bg-gray-50 rounded-lg">
                <div class="text-3xl font-bold ${sentimentClass} mb-2">${displaySentiment}</div>
                <div class="text-sm text-black">
                    ${availableEvents} of ${eventCount} events ${currentView === 'actual' ? 'released' : 'available'}
                </div>
            </div>
        </div>
    `;
    
    // Add comparison details if in comparison view
    if (currentView === 'comparison' && sentiment.actual_available) {
        summaryContent += `
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="text-center p-4 bg-blue-50 rounded-lg">
                    <div class="text-sm text-black mb-1">Forecast</div>
                    <div class="text-lg font-semibold ${getSentimentClass(sentiment.forecast_sentiment || sentiment.final_sentiment)}">
                        ${sentiment.forecast_sentiment || sentiment.final_sentiment}
                    </div>
                </div>
                <div class="text-center p-4 bg-green-50 rounded-lg">
                    <div class="text-sm text-black mb-1">Actual</div>
                    <div class="text-lg font-semibold ${getSentimentClass(sentiment.actual_sentiment || 'Neutral')}">
                        ${sentiment.actual_sentiment || 'not released'}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add event breakdown
    if (sentiment.events && sentiment.events.length > 0) {
        const relevantEvents = sentiment.events.filter(event => 
            currentView === 'actual' ? event.actual_available : event.data_available
        );
        
        if (relevantEvents.length > 0) {
            summaryContent += `
                <div>
                    <h4 class="font-medium text-black mb-3">Event Breakdown</h4>
                    <div class="space-y-2">
                        ${relevantEvents.map(event => {
                            let eventSentiment, eventValue;
                            if (currentView === 'actual' && event.actual_available) {
                                eventSentiment = event.actual_sentiment_label || event.sentiment_label;
                                eventValue = event.actual_value;
                            } else {
                                eventSentiment = event.sentiment_label;
                                eventValue = event.forecast_value;
                            }
                            
                            const eventSentimentClass = getSentimentClass(eventSentiment);
                            
                            return `
                                <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                                    <span class="text-sm font-medium text-black">${event.event_name}</span>
                                    <div class="flex items-center space-x-2">
                                        <span class="text-sm text-black">${formatValue(eventValue)}</span>
                                        <span class="text-sm ${eventSentimentClass}">${eventSentiment}</span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
    }
    
    summaryElement.innerHTML = summaryContent;
}

/**
 * Update indicators table
 */
function updateIndicatorsTable() {
    const tableBody = document.getElementById('indicators-table');
    if (!tableBody) return;
    
    // Filter events for selected currency, or show all if none selected
    const filteredEvents = eventsData.filter(event => 
        currentCurrency === 'all' || event.currency === currentCurrency
    );
    
    if (filteredEvents.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="px-4 py-8 text-center text-black">
                    No events found for ${currentCurrency}
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = filteredEvents.map(event => {
        // Get data based on current view
        const currentData = getCurrentSentimentData();
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
            // For actual view, show actual sentiment as primary
            if (currentView === 'actual') {
                sentiment = detailedEvent.actual_sentiment_label || detailedEvent.sentiment_label;
                actualValue = formatValue(detailedEvent.actual_value);
                actualSentiment = detailedEvent.actual_sentiment_label || 'not released';
            } else {
                sentiment = detailedEvent.sentiment_label;
                if (detailedEvent.actual_available) {
                    actualValue = formatValue(detailedEvent.actual_value);
                    actualSentiment = detailedEvent.actual_sentiment_label || 'not released';
                }
            }
            
            sentimentClass = getSentimentClass(sentiment);
            actualSentimentClass = getSentimentClass(actualSentiment);
            reason = detailedEvent.reason || '';
            isInverse = detailedEvent.is_inverse || false;
            accuracy = detailedEvent.accuracy || '';
        } else {
            sentiment = getSentimentFromValues(event.previous_value, event.forecast_value);
            sentimentClass = getSentimentClass(sentiment);
            
            // Check if event has actual data available
            if (event.actual_available && event.actual_value !== null) {
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
                    <div class="font-medium text-black">${event.event_name}</div>
                    ${reason ? `<div class="text-xs text-black mt-1 italic">${reason}</div>` : ''}
                </td>
                <td class="px-4 py-3 text-sm font-medium text-black">${event.currency}</td>
                <td class="px-4 py-3 text-sm text-black">${formatValue(event.previous_value)}</td>
                <td class="px-4 py-3 text-sm text-black">${formatValue(event.forecast_value)}</td>
                <td class="px-4 py-3 text-sm text-black">${actualValue}</td>
                <td class="px-4 py-3 text-sm">
                    <div class="flex items-center">
                        <span class="${sentimentClass}">${sentiment}</span>
                        ${inversionBadge}
                    </div>
                </td>
                <td class="px-4 py-3 text-sm">
                    ${actualSentiment !== 'not released' ? `<span class="${actualSentimentClass}">${actualSentiment}</span>` : '<span class="text-black">' + actualSentiment + '</span>'}
                </td>
                <td class="px-4 py-3 text-sm">
                    ${accuracy ? getAccuracyBadge(accuracy) : ''}
                </td>
                <td class="px-4 py-3 text-sm text-black">
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
    
    summaryElement.innerHTML = currencies.map(currency => {
        // Get data based on current view
        const currentData = getCurrentSentimentData();
        const sentiment = currentData[currency];
        
        if (!sentiment) {
            return `
                <div class="bg-white rounded-lg shadow p-4 card-hover">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-black">${currency}</span>
                        <span class="text-2xl">${getCurrencyFlag(currency)}</span>
                    </div>
                    <div class="text-center text-black">not released</div>
                </div>
            `;
        }
        
        // Get sentiment based on current view
        let displaySentiment = sentiment.final_sentiment;
        let viewLabel = '';
        
        if (currentView === 'actual' && sentiment.actual_available) {
            displaySentiment = sentiment.actual_sentiment || sentiment.final_sentiment;
            viewLabel = '(Actual)';
        } else if (currentView === 'comparison') {
            displaySentiment = sentiment.forecast_sentiment || sentiment.final_sentiment;
            viewLabel = '(Compare)';
        } else {
            viewLabel = '(Forecast)';
        }
        
        const sentimentClass = getSentimentClass(displaySentiment);
        const eventCount = sentiment.events ? sentiment.events.length : 0;
        const actualAvailable = sentiment.actual_available || false;
        
        return `
            <div class="bg-white rounded-lg shadow p-4 card-hover cursor-pointer" onclick="selectCurrency('${currency}')">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-medium text-black">${currency}</span>
                    <span class="text-2xl">${getCurrencyFlag(currency)}</span>
                </div>
                <div class="text-center">
                    <div class="text-lg font-bold ${sentimentClass}">${displaySentiment}</div>
                    <div class="text-xs text-black">${eventCount} events ${viewLabel}</div>
                    ${currentView === 'actual' && !actualAvailable ? 
                        '<div class="text-xs text-orange-500 mt-1">not released</div>' : ''}
                    ${currentView === 'comparison' && actualAvailable && sentiment.forecast_accuracy !== null ? 
                        `<div class="text-xs text-blue-500 mt-1">${sentiment.forecast_accuracy}% accuracy</div>` : ''}
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
    
    sentimentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Sentiment Score',
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
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Forecast Sentiment'
                }
            }
        }
    });
}

/**
 * Update sentiment chart
 */
function updateSentimentChart() {
    if (!sentimentChart) return;
    
    // Get data based on current view
    const currentData = getCurrentSentimentData();
    const sentiment = currentData[currentCurrency];
    
    if (!sentiment || !sentiment.events) {
        sentimentChart.data.labels = ['No Data'];
        sentimentChart.data.datasets[0].data = [0];
        sentimentChart.data.datasets[0].backgroundColor = ['rgba(107, 114, 128, 0.8)'];
        sentimentChart.update();
        return;
    }
    
    // Count sentiment types based on current view
    const sentimentCounts = {
        'Bullish': 0,
        'Bearish': 0,
        'Neutral': 0
    };
    
    sentiment.events.forEach(event => {
        let sentimentValue;
        
        if (currentView === 'actual' && event.actual_available) {
            sentimentValue = event.actual_sentiment;
        } else {
            sentimentValue = event.sentiment;
        }
        
        if (sentimentValue === 1) sentimentCounts.Bullish++;
        else if (sentimentValue === -1) sentimentCounts.Bearish++;
        else sentimentCounts.Neutral++;
    });
    
    sentimentChart.data.labels = Object.keys(sentimentCounts);
    sentimentChart.data.datasets[0].data = Object.values(sentimentCounts);
    
    // Update chart title based on view
    const chartTitle = currentView === 'actual' ? 'Actual Sentiment' : 
                      currentView === 'comparison' ? 'Forecast vs Actual' : 
                      'Forecast Sentiment';
    
    sentimentChart.options.plugins.title = {
        display: true,
        text: `${currentCurrency} ${chartTitle}`
    };
    
    sentimentChart.update();
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
 * Helper function to get current view data for sidebar
 */
function getCurrentViewData() {
    return getCurrentSentimentData();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    console.log('Setting up event listeners...');
    
    // Currency selection
    document.querySelectorAll('.currency-item').forEach(item => {
        item.addEventListener('click', function() {
            const currency = this.getAttribute('data-currency');
            selectCurrency(currency);
        });
    });
    
    // Phase 3: Sentiment view toggles with enhanced error handling
    const toggleButtons = document.querySelectorAll('.sentiment-toggle button');
    console.log(`Found ${toggleButtons.length} toggle buttons`);
    
    toggleButtons.forEach((button, index) => {
        const view = button.getAttribute('data-view');
        const buttonId = button.id;
        console.log(`Setting up toggle button ${index}: ID=${buttonId}, view=${view}`);
        
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const clickedView = this.getAttribute('data-view');
            console.log(`Toggle button clicked: ${clickedView}`);
            
            if (clickedView) {
                switchSentimentView(clickedView);
            } else {
                console.error('No data-view attribute found on button');
            }
        });
    });
    
    // Also set up individual button listeners as backup
    const forecastBtn = document.getElementById('forecast-view');
    const actualBtn = document.getElementById('actual-view');
    const comparisonBtn = document.getElementById('comparison-view');
    
    if (forecastBtn) {
        forecastBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Forecast button clicked directly');
            switchSentimentView('forecast');
        });
    } else {
        console.warn('Forecast button not found');
    }
    
    if (actualBtn) {
        actualBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Actual button clicked directly');
            switchSentimentView('actual');
        });
    } else {
        console.warn('Actual button not found');
    }
    
    if (comparisonBtn) {
        comparisonBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Comparison button clicked directly');
            switchSentimentView('comparison');
        });
    } else {
        console.warn('Comparison button not found');
    }
    
    // Discord actions
    const testWebhookBtn = document.getElementById('test-webhook');
    if (testWebhookBtn) {
        testWebhookBtn.addEventListener('click', testDiscordWebhook);
    }
    
    const sendReportBtn = document.getElementById('send-report');
    if (sendReportBtn) {
        sendReportBtn.addEventListener('click', sendWeeklyReport);
    }
    
    console.log('Event listeners setup complete');
}

/**
 * Select currency and update displays
 */
function selectCurrency(currency) {
    console.log(`Selecting currency: ${currency}`);
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
    updateSentimentChart();
}

/**
 * Phase 3: Switch sentiment view
 */
function switchSentimentView(view) {
    console.log(`Switching to view: ${view}`);
    currentView = view;
    
    // Update toggle button states
    document.querySelectorAll('.sentiment-toggle button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const targetButton = document.getElementById(`${view}-view`);
    if (targetButton) {
        targetButton.classList.add('active');
        console.log(`Activated button: ${view}-view`);
    } else {
        console.error(`Button not found: ${view}-view`);
    }
    
    // Update all displays based on current view
    console.log('Updating displays for new view...');
    updateCurrencySidebar();
    updateCurrencySummary();
    updateIndicatorsTable();
    updateWeeklySummary();
    updateSentimentChart();
    
    console.log(`View switched to: ${currentView}`);
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
                <h4 class="font-medium text-black">${item.key}</h4>
                <p class="text-sm text-black">Last updated: ${new Date(item.updated_at).toLocaleDateString()}</p>
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