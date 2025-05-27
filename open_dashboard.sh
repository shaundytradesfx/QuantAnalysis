#!/bin/bash

# Forex Sentiment Analyzer - Dashboard Access Script
# This script opens the browser access tool for seamless dashboard access

echo "🚀 Opening Forex Sentiment Analyzer Dashboard Access Tool..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACCESS_TOOL="$SCRIPT_DIR/simple_browser_access.html"

# Check if the access tool exists
if [ ! -f "$ACCESS_TOOL" ]; then
    echo "❌ Error: simple_browser_access.html not found in $SCRIPT_DIR"
    echo "Please ensure the file exists and try again."
    exit 1
fi

# Open the browser access tool
echo "📊 Opening browser access tool..."

# Try different browsers based on the operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$ACCESS_TOOL"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open > /dev/null; then
        xdg-open "$ACCESS_TOOL"
    elif command -v firefox > /dev/null; then
        firefox "$ACCESS_TOOL"
    elif command -v google-chrome > /dev/null; then
        google-chrome "$ACCESS_TOOL"
    else
        echo "❌ No suitable browser found. Please open $ACCESS_TOOL manually."
        exit 1
    fi
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows
    start "$ACCESS_TOOL"
else
    echo "❌ Unsupported operating system. Please open $ACCESS_TOOL manually."
    exit 1
fi

echo "✅ Browser access tool opened successfully!"
echo ""
echo "📋 Instructions:"
echo "1. Run: gcloud auth print-identity-token"
echo "2. Copy the token and paste it in the browser"
echo "3. Click 'Open Dashboard' to access your Forex Sentiment Analyzer"
echo ""
echo "🌐 Direct URL: https://forex-sentiment-analyzer-158616853756.us-central1.run.app"
echo ""
echo "💡 Tip: Bookmark the browser access tool for easy future access!" 