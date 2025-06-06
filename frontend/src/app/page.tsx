"use client";

import { useEffect } from 'react';
import Script from 'next/script';
import { SAMPLE_DATA, SampleDataType } from '../data/sampleData';

// Declare global window interface for dashboard functions
declare global {
  interface Window {
    SAMPLE_DATA: SampleDataType;
    initializeDashboard?: () => void;
  }
}

export default function Dashboard() {
  useEffect(() => {
    // Set sample data globally for dashboard.js compatibility
    if (typeof window !== 'undefined') {
      window.SAMPLE_DATA = SAMPLE_DATA;
    }
  }, []);

  return (
    <>
      <Script src="https://cdn.tailwindcss.com" strategy="beforeInteractive" />
      <Script src="https://cdn.jsdelivr.net/npm/chart.js" strategy="beforeInteractive" />
      <Script 
        src="/static/js/dashboard.js" 
        strategy="afterInteractive"
        onLoad={() => {
          // Initialize dashboard after script loads and data is available
          if (typeof window !== 'undefined' && window.SAMPLE_DATA) {
            const initEvent = new Event('DOMContentLoaded');
            document.dispatchEvent(initEvent);
          }
        }}
      />
      
      <div className="bg-gray-50 font-sans">
        {/* Custom Styles */}
        <style jsx global>{`
          /* Custom styles for enhanced UI */
          .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          .card-hover {
            transition: all 0.3s ease;
          }
          .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
          }
          .sentiment-bullish { color: #10b981; }
          .sentiment-bearish { color: #ef4444; }
          .sentiment-neutral { color: #6b7280; }
          .currency-flag {
            width: 24px;
            height: 18px;
            border-radius: 2px;
          }
          .nav-tab {
            cursor: pointer;
            transition: all 0.3s ease;
          }
          .nav-tab:hover {
            color: #bfdbfe;
          }
          .nav-tab.active {
            color: #ffffff;
            border-bottom: 2px solid #ffffff;
          }
          
          /* Phase 3: Actual Sentiment Styles */
          .sentiment-forecast { color: #3b82f6; }
          .sentiment-actual { color: #059669; }
          .accuracy-match { color: #f59e0b; }
          .accuracy-mismatch { color: #dc2626; }
          .accuracy-no-data { color: #6b7280; }
          
          .sentiment-toggle {
            background: #f3f4f6;
            border-radius: 0.5rem;
            padding: 0.25rem;
            display: inline-flex;
          }
          
          .sentiment-toggle button {
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            border: none;
            background: transparent;
            color: #6b7280;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
            font-weight: 500;
          }
          
          .sentiment-toggle button.active {
            background: #ffffff;
            color: #1f2937;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          }
          
          .sentiment-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.75rem;
            font-weight: 500;
          }
          
          .accuracy-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.125rem 0.375rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            font-weight: 500;
          }
          
          .accuracy-match { background: #fef3c7; color: #92400e; }
          .accuracy-mismatch { background: #fee2e2; color: #991b1b; }
          .accuracy-no-data { background: #f3f4f6; color: #6b7280; }
        `}</style>

        {/* Header */}
        <header className="gradient-bg text-white shadow-lg">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <i className="fas fa-chart-line text-2xl"></i>
                <h1 className="text-2xl font-bold">ForexSentiment</h1>
              </div>
              <nav className="hidden md:flex space-x-6">
                <a href="#dashboard" className="nav-tab active" data-tab="dashboard">Dashboard</a>
                <a href="#discord" className="nav-tab" data-tab="discord">Discord Integration</a>
                <a href="#configuration" className="nav-tab" data-tab="configuration">Configuration</a>
              </nav>
              <div className="flex items-center space-x-4">
                <div id="health-status" className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm">System Healthy</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="flex min-h-screen">
          {/* Sidebar */}
          <aside className="w-64 bg-white shadow-lg">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-black mb-4">Currency Filters</h2>
              
              {/* Major Currencies */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-black mb-3">Major Currencies</h3>
                <div className="space-y-2">
                  <div className="currency-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" data-currency="USD">
                    <span className="currency-flag">🇺🇸</span>
                    <span className="font-medium text-black">USD</span>
                    <div className="ml-auto flex flex-col items-end space-y-1">
                      <span id="usd-sentiment" className="text-sm"></span>
                      <span id="usd-actual-sentiment" className="text-xs opacity-75"></span>
                    </div>
                  </div>
                  <div className="currency-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" data-currency="EUR">
                    <span className="currency-flag">🇪🇺</span>
                    <span className="font-medium text-black">EUR</span>
                    <div className="ml-auto flex flex-col items-end space-y-1">
                      <span id="eur-sentiment" className="text-sm"></span>
                      <span id="eur-actual-sentiment" className="text-xs opacity-75"></span>
                    </div>
                  </div>
                  <div className="currency-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" data-currency="GBP">
                    <span className="currency-flag">🇬🇧</span>
                    <span className="font-medium text-black">GBP</span>
                    <div className="ml-auto flex flex-col items-end space-y-1">
                      <span id="gbp-sentiment" className="text-sm"></span>
                      <span id="gbp-actual-sentiment" className="text-xs opacity-75"></span>
                    </div>
                  </div>
                  <div className="currency-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" data-currency="JPY">
                    <span className="currency-flag">🇯🇵</span>
                    <span className="font-medium text-black">JPY</span>
                    <div className="ml-auto flex flex-col items-end space-y-1">
                      <span id="jpy-sentiment" className="text-sm"></span>
                      <span id="jpy-actual-sentiment" className="text-xs opacity-75"></span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Minor Currencies */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-black mb-3">Minor Currencies</h3>
                <div className="space-y-2">
                  <div className="currency-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" data-currency="AUD">
                    <span className="currency-flag">🇦🇺</span>
                    <span className="font-medium text-black">AUD</span>
                    <div className="ml-auto flex flex-col items-end space-y-1">
                      <span id="aud-sentiment" className="text-sm"></span>
                      <span id="aud-actual-sentiment" className="text-xs opacity-75"></span>
                    </div>
                  </div>
                  <div className="currency-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" data-currency="CAD">
                    <span className="currency-flag">🇨🇦</span>
                    <span className="font-medium text-black">CAD</span>
                    <div className="ml-auto flex flex-col items-end space-y-1">
                      <span id="cad-sentiment" className="text-sm"></span>
                      <span id="cad-actual-sentiment" className="text-xs opacity-75"></span>
                    </div>
                  </div>
                  <div className="currency-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" data-currency="CHF">
                    <span className="currency-flag">🇨🇭</span>
                    <span className="font-medium text-black">CHF</span>
                    <div className="ml-auto flex flex-col items-end space-y-1">
                      <span id="chf-sentiment" className="text-sm"></span>
                      <span id="chf-actual-sentiment" className="text-xs opacity-75"></span>
                    </div>
                  </div>
                  <div className="currency-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" data-currency="NZD">
                    <span className="currency-flag">🇳🇿</span>
                    <span className="font-medium text-black">NZD</span>
                    <div className="ml-auto flex flex-col items-end space-y-1">
                      <span id="nzd-sentiment" className="text-sm"></span>
                      <span id="nzd-actual-sentiment" className="text-xs opacity-75"></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 p-6">
            {/* Dashboard Tab Content */}
            <div id="dashboard-content" className="tab-content">
              {/* Current Analysis Header */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h1 className="text-3xl font-bold text-black mb-2">Economic Sentiment Analysis</h1>
                    <p id="current-week" className="text-black">Loading current week data...</p>
                  </div>
                  {/* Phase 3: Sentiment View Toggle */}
                  <div className="sentiment-toggle">
                    <button id="forecast-view" className="active" data-view="forecast">
                      <i className="fas fa-chart-line mr-1"></i>Forecast
                    </button>
                    <button id="actual-view" data-view="actual">
                      <i className="fas fa-check-circle mr-1"></i>Actual
                    </button>
                    <button id="comparison-view" data-view="comparison">
                      <i className="fas fa-balance-scale mr-1"></i>Compare
                    </button>
                  </div>
                </div>
              </div>

              {/* Selected Currency Analysis */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Sentiment Chart */}
                <div className="bg-white rounded-lg shadow-md p-6 card-hover">
                  <h2 className="text-xl font-semibold text-black mb-4">
                    <span id="selected-currency">USD</span> Sentiment Analysis
                  </h2>
                  <div className="relative h-64">
                    <canvas id="sentimentChart"></canvas>
                  </div>
                </div>

                {/* Currency Summary */}
                <div className="bg-white rounded-lg shadow-md p-6 card-hover">
                  <h2 className="text-xl font-semibold text-black mb-4">Currency Summary</h2>
                  <div id="currency-summary" className="space-y-4">
                    {/* Will be populated by JavaScript */}
                  </div>
                </div>
              </div>

              {/* Economic Indicators Table */}
              <div className="bg-white rounded-lg shadow-md p-6 card-hover mb-8">
                <h2 className="text-xl font-semibold text-black mb-4">Economic Indicators</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full table-auto">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Event</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Currency</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Previous</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Forecast</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Actual</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Sentiment</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Actual Sentiment</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Accuracy</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-black">Date</th>
                      </tr>
                    </thead>
                    <tbody id="indicators-table" className="divide-y divide-gray-200">
                      {/* Will be populated by JavaScript */}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Weekly Currency Summary */}
              <div className="bg-white rounded-lg shadow-md p-6 card-hover">
                <h2 className="text-xl font-semibold text-black mb-4">Weekly Currency Summary</h2>
                <div id="weekly-summary" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Will be populated by JavaScript */}
                </div>
              </div>
            </div>

            {/* Discord Integration Tab Content */}
            <div id="discord-content" className="tab-content hidden">
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-black mb-2">Discord Integration</h1>
                <p className="text-black">Manage Discord webhook connections and send reports</p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6 card-hover">
                <h2 className="text-xl font-semibold text-black mb-4">Discord Integration</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-medium text-black mb-3">Webhook Status</h3>
                    <div id="discord-status" className="space-y-2">
                      {/* Will be populated by JavaScript */}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-black mb-3">Actions</h3>
                    <div className="space-y-3">
                      <button id="test-webhook" className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                        <i className="fas fa-vial mr-2"></i>Test Webhook
                      </button>
                      <button id="send-report" className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                        <i className="fas fa-paper-plane mr-2"></i>Send Weekly Report
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Configuration Tab Content */}
            <div id="configuration-content" className="tab-content hidden">
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-black mb-2">Configuration</h1>
                <p className="text-black">Manage system configuration settings</p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6 card-hover">
                <h2 className="text-xl font-semibold text-black mb-4">System Configuration</h2>
                <div id="config-settings" className="space-y-4">
                  {/* Will be populated by JavaScript */}
                </div>
              </div>
            </div>
          </main>
        </div>

        {/* Loading Overlay */}
        <div id="loading-overlay" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden">
          <div className="bg-white rounded-lg p-6 flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="text-lg">Loading...</span>
          </div>
        </div>

        {/* Font Awesome CDN */}
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet" />
    </div>
    </>
  );
}
