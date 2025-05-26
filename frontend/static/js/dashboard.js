/**
 * Dashboard JavaScript for ForexSentiment Analysis
 * Handles API communication, chart rendering, and UI interactions
 */

class ForexDashboard {
    constructor() {
        this.apiBaseUrl = 'http://127.0.0.1:8000';
        this.selectedCurrency = 'USD';
        this.sentimentChart = null;
        this.sentimentData = {};
        this.eventsData = [];
        this.configData = [];
        this.activeTab = 'dashboard';
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadInitialData();
        this.initializeChart();
        this.selectCurrency('USD');
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Currency selection
        document.querySelectorAll('.currency-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const currency = e.currentTarget.dataset.currency;
                this.selectCurrency(currency);
            });
        });

        // Discord actions
        document.getElementById('test-webhook').addEventListener('click', () => {
            this.testDiscordWebhook();
        });

        document.getElementById('send-report').addEventListener('click', () => {
            this.sendWeeklyReport();
        });

        // Auto-refresh every 5 minutes
        setInterval(() => {
            this.refreshData();
        }, 5 * 60 * 1000);
    }

    switchTab(tabName) {
        // Update active tab
        this.activeTab = tabName;
        
        // Update navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Show/hide content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        const contentId = `${tabName}-content`;
        const contentElement = document.getElementById(contentId);
        if (contentElement) {
            contentElement.classList.remove('hidden');
        }
        
        // Load tab-specific data
        if (tabName === 'configuration') {
            this.loadConfigurationData();
        }
    }

    async loadInitialData() {
        this.showLoading(true);
        try {
            await Promise.all([
                this.loadHealthStatus(),
                this.loadSentimentData(),
                this.loadEventsData(),
                this.loadDiscordStatus()
            ]);
            this.updateUI();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.showLoading(false);
        }
    }

    async refreshData() {
        try {
            await Promise.all([
                this.loadHealthStatus(),
                this.loadSentimentData(),
                this.loadEventsData()
            ]);
            this.updateUI();
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }

    async loadHealthStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/health`);
            const health = await response.json();
            this.updateHealthStatus(health);
        } catch (error) {
            console.error('Error loading health status:', error);
            this.updateHealthStatus({ status: 'unhealthy', database: 'unknown', discord: 'unknown' });
        }
    }

    async loadSentimentData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/sentiments`);
            this.sentimentData = {};
            
            if (response.ok) {
                const sentiments = await response.json();
                sentiments.forEach(sentiment => {
                    this.sentimentData[sentiment.currency] = sentiment;
                });
            }
        } catch (error) {
            console.error('Error loading sentiment data:', error);
        }
    }

    async loadEventsData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/events?limit=50`);
            if (response.ok) {
                this.eventsData = await response.json();
            }
        } catch (error) {
            console.error('Error loading events data:', error);
        }
    }

    async loadConfigurationData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/config`);
            if (response.ok) {
                this.configData = await response.json();
                this.updateConfigurationUI();
            }
        } catch (error) {
            console.error('Error loading configuration data:', error);
        }
    }

    async loadDiscordStatus() {
        // This would be implemented when we have Discord status endpoints
        // For now, we'll show basic status
        this.updateDiscordStatus();
    }

    updateHealthStatus(health) {
        const statusElement = document.getElementById('health-status');
        const isHealthy = health.status === 'healthy';
        
        statusElement.innerHTML = `
            <div class="w-3 h-3 ${isHealthy ? 'bg-green-400' : 'bg-red-400'} rounded-full ${isHealthy ? 'animate-pulse' : ''}"></div>
            <span class="text-sm">${isHealthy ? 'System Healthy' : 'System Issues'}</span>
        `;
    }

    updateUI() {
        this.updateCurrentWeek();
        this.updateSidebarSentiments();
        this.updateCurrencySummary();
        this.updateIndicatorsTable();
        this.updateWeeklySummary();
        this.updateSentimentChart();
    }

    updateCurrentWeek() {
        const now = new Date();
        const monday = new Date(now);
        monday.setDate(now.getDate() - now.getDay() + 1);
        
        const weekText = `Week of ${monday.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        })}`;
        
        document.getElementById('current-week').textContent = weekText;
    }

    updateSidebarSentiments() {
        const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD'];
        
        currencies.forEach(currency => {
            const element = document.getElementById(`${currency.toLowerCase()}-sentiment`);
            if (element) {
                const sentiment = this.sentimentData[currency];
                if (sentiment) {
                    const sentimentClass = this.getSentimentClass(sentiment.final_sentiment);
                    const sentimentIcon = this.getSentimentIcon(sentiment.final_sentiment);
                    element.innerHTML = `<span class="${sentimentClass}">${sentimentIcon}</span>`;
                } else {
                    element.innerHTML = '<span class="text-gray-400">—</span>';
                }
            }
        });
    }

    updateCurrencySummary() {
        const summaryElement = document.getElementById('currency-summary');
        const sentiment = this.sentimentData[this.selectedCurrency];
        
        if (sentiment) {
            const sentimentClass = this.getSentimentClass(sentiment.final_sentiment);
            const sentimentIcon = this.getSentimentIcon(sentiment.final_sentiment);
            
            summaryElement.innerHTML = `
                <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                        <h3 class="font-semibold text-lg">${this.selectedCurrency}</h3>
                        <p class="text-sm text-gray-600">Overall Sentiment</p>
                    </div>
                    <div class="text-right">
                        <div class="${sentimentClass} text-2xl">${sentimentIcon}</div>
                        <p class="${sentimentClass} font-medium">${sentiment.final_sentiment}</p>
                    </div>
                </div>
                <div class="space-y-2">
                    <h4 class="font-medium">Recent Events:</h4>
                    ${sentiment.events.map(event => `
                        <div class="text-sm p-2 bg-gray-50 rounded">
                            <span class="font-medium">${event.event_name}</span>
                            <div class="text-gray-600">
                                Prev: ${event.previous_value !== null && event.previous_value !== undefined ? event.previous_value : 'N/A'} | 
                                Forecast: ${event.forecast_value !== null && event.forecast_value !== undefined ? event.forecast_value : 'N/A'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            summaryElement.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-chart-line text-4xl mb-4"></i>
                    <p>No sentiment data available for ${this.selectedCurrency}</p>
                </div>
            `;
        }
    }

    updateIndicatorsTable() {
        const tableBody = document.getElementById('indicators-table');
        const sentiment = this.sentimentData[this.selectedCurrency];
        
        // Debug logging
        console.log('updateIndicatorsTable called for currency:', this.selectedCurrency);
        console.log('Sentiment data:', sentiment);
        
        if (!sentiment || !sentiment.events || sentiment.events.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-4 py-8 text-center text-gray-500">
                        No economic indicators data available for ${this.selectedCurrency}
                    </td>
                </tr>
            `;
            return;
        }

        // Debug each event
        sentiment.events.forEach(event => {
            console.log(`Event: ${event.event_name}`);
            console.log(`- Previous: ${event.previous_value} (type: ${typeof event.previous_value})`);
            console.log(`- Forecast: ${event.forecast_value} (type: ${typeof event.forecast_value})`);
            console.log(`- Sentiment: ${event.sentiment_label}`);
        });

        tableBody.innerHTML = sentiment.events.map(event => {
            const sentimentClass = this.getSentimentClass(event.sentiment_label);
            const sentimentIcon = this.getSentimentIcon(event.sentiment_label);
            const eventDate = new Date(event.scheduled_datetime).toLocaleDateString();
            
            // Debug the null check logic
            const prevValue = event.previous_value !== null && event.previous_value !== undefined ? event.previous_value : 'N/A';
            const forecastValue = event.forecast_value !== null && event.forecast_value !== undefined ? event.forecast_value : 'N/A';
            
            console.log(`Processing ${event.event_name}: prev=${prevValue}, forecast=${forecastValue}`);
            
            return `
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-sm">${event.event_name}</td>
                    <td class="px-4 py-3 text-sm font-medium">${this.selectedCurrency}</td>
                    <td class="px-4 py-3 text-sm">${prevValue}</td>
                    <td class="px-4 py-3 text-sm">${forecastValue}</td>
                    <td class="px-4 py-3 text-sm">
                        <span class="${sentimentClass}">${sentimentIcon} ${event.sentiment_label}</span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">
                        ${eventDate}
                    </td>
                </tr>
            `;
        }).join('');
    }

    updateWeeklySummary() {
        const summaryElement = document.getElementById('weekly-summary');
        const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD'];
        
        summaryElement.innerHTML = currencies.map(currency => {
            const sentiment = this.sentimentData[currency];
            const sentimentClass = sentiment ? this.getSentimentClass(sentiment.final_sentiment) : 'text-gray-400';
            const sentimentIcon = sentiment ? this.getSentimentIcon(sentiment.final_sentiment) : '—';
            const sentimentText = sentiment ? sentiment.final_sentiment : 'No Data';
            
            return `
                <div class="bg-white p-4 rounded-lg border border-gray-200 text-center cursor-pointer hover:shadow-md transition-shadow"
                     onclick="dashboard.selectCurrency('${currency}')">
                    <div class="text-2xl mb-2">${this.getCurrencyFlag(currency)}</div>
                    <h3 class="font-semibold text-lg mb-1">${currency}</h3>
                    <div class="${sentimentClass} text-sm">
                        ${sentimentIcon} ${sentimentText}
                    </div>
                </div>
            `;
        }).join('');
    }

    updateDiscordStatus() {
        const statusElement = document.getElementById('discord-status');
        statusElement.innerHTML = `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm">Webhook Connection</span>
                <span class="text-green-600 text-sm">
                    <i class="fas fa-check-circle mr-1"></i>Connected
                </span>
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="text-sm">Last Report Sent</span>
                <span class="text-gray-600 text-sm">2 days ago</span>
            </div>
        `;
    }

    updateConfigurationUI() {
        const configElement = document.getElementById('config-settings');
        
        if (this.configData.length === 0) {
            configElement.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-cog text-4xl mb-4"></i>
                    <p>No configuration settings found</p>
                </div>
            `;
            return;
        }

        configElement.innerHTML = this.configData.map(config => `
            <div class="border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                    <label class="font-medium text-gray-700">${config.key}</label>
                    <span class="text-xs text-gray-500">
                        Updated: ${new Date(config.updated_at).toLocaleDateString()}
                    </span>
                </div>
                <div class="flex space-x-2">
                    <input 
                        type="text" 
                        value="${config.value}" 
                        class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        data-config-key="${config.key}"
                    >
                    <button 
                        onclick="dashboard.updateConfigValue('${config.key}')"
                        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                        Update
                    </button>
                </div>
            </div>
        `).join('');
    }

    async updateConfigValue(key) {
        const input = document.querySelector(`[data-config-key="${key}"]`);
        const value = input.value;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ key, value })
            });
            
            if (response.ok) {
                this.showSuccess(`Configuration ${key} updated successfully`);
                await this.loadConfigurationData();
            } else {
                this.showError(`Failed to update configuration ${key}`);
            }
        } catch (error) {
            console.error('Error updating configuration:', error);
            this.showError('Error updating configuration');
        }
    }

    initializeChart() {
        const ctx = document.getElementById('sentimentChart').getContext('2d');
        
        this.sentimentChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Bullish', 'Bearish', 'Neutral'],
                datasets: [{
                    data: [0, 0, 1],
                    backgroundColor: ['#10b981', '#ef4444', '#6b7280'],
                    borderWidth: 0
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
        
        this.updateSentimentChart();
    }

    updateSentimentChart() {
        if (!this.sentimentChart) return;
        
        const sentiment = this.sentimentData[this.selectedCurrency];
        
        if (sentiment && sentiment.events) {
            const bullishCount = sentiment.events.filter(e => 
                e.sentiment_label === 'Bullish'
            ).length;
            
            const bearishCount = sentiment.events.filter(e => 
                e.sentiment_label === 'Bearish'
            ).length;
            
            const neutralCount = sentiment.events.filter(e => 
                e.sentiment_label === 'Neutral'
            ).length;
            
            this.sentimentChart.data.datasets[0].data = [bullishCount, bearishCount, neutralCount];
        } else {
            this.sentimentChart.data.datasets[0].data = [0, 0, 1];
        }
        
        this.sentimentChart.update();
    }

    selectCurrency(currency) {
        this.selectedCurrency = currency;
        
        // Update UI to show selected currency
        document.querySelectorAll('.currency-item').forEach(item => {
            item.classList.remove('bg-blue-50', 'border-blue-200');
        });
        
        const selectedItem = document.querySelector(`[data-currency="${currency}"]`);
        if (selectedItem) {
            selectedItem.classList.add('bg-blue-50', 'border-blue-200');
        }
        
        document.getElementById('selected-currency').textContent = currency;
        
        this.updateCurrencySummary();
        this.updateIndicatorsTable();
        this.updateSentimentChart();
    }

    async testDiscordWebhook() {
        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/discord/test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                this.showSuccess('Discord webhook test completed successfully!');
            } else {
                this.showError(result.message || 'Discord webhook test failed');
            }
        } catch (error) {
            console.error('Error testing Discord webhook:', error);
            this.showError('Error testing Discord webhook');
        } finally {
            this.showLoading(false);
        }
    }

    async sendWeeklyReport() {
        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/discord/send-report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                this.showSuccess('Weekly report sent to Discord successfully!');
            } else {
                this.showError(result.message || 'Failed to send weekly report');
            }
        } catch (error) {
            console.error('Error sending weekly report:', error);
            this.showError('Error sending weekly report');
        } finally {
            this.showLoading(false);
        }
    }

    getSentimentClass(sentiment) {
        switch (sentiment?.toLowerCase()) {
            case 'bullish': return 'sentiment-bullish';
            case 'bearish': return 'sentiment-bearish';
            default: return 'sentiment-neutral';
        }
    }

    getSentimentIcon(sentiment) {
        switch (sentiment?.toLowerCase()) {
            case 'bullish': return '🟢';
            case 'bearish': return '🔴';
            default: return '⚪';
        }
    }

    getCurrencyFlag(currency) {
        const flags = {
            'USD': '🇺🇸',
            'EUR': '🇪🇺',
            'GBP': '🇬🇧',
            'JPY': '🇯🇵',
            'AUD': '🇦🇺',
            'CAD': '🇨🇦',
            'CHF': '🇨🇭',
            'NZD': '🇳🇿'
        };
        return flags[currency] || '🏳️';
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.toggle('hidden', !show);
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new ForexDashboard();
}); 