#!/bin/bash

# Firebase Deployment Script for Forex Sentiment Analyzer Frontend
# This script deploys the frontend to Firebase Hosting for public access

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FIREBASE_PROJECT_ID="forex-sentiment-frontend"
FRONTEND_DIR="frontend"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "🚀 Starting Firebase deployment for Forex Sentiment Analyzer frontend..."

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    print_error "Firebase CLI is not installed. Installing now..."
    npm install -g firebase-tools
fi

# Check if user is authenticated with Firebase
print_status "Checking Firebase authentication..."
if ! firebase projects:list &> /dev/null; then
    print_warning "Not authenticated with Firebase. Please login..."
    firebase login
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Validate frontend files
print_status "Validating frontend files..."
required_files=("$FRONTEND_DIR/index.html" "$FRONTEND_DIR/config.js")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file not found: $file"
        exit 1
    fi
done

print_success "Frontend files validated successfully!"

# Initialize Firebase project if not already done
if [ ! -f "firebase.json" ]; then
    print_status "Initializing Firebase project..."
    firebase init hosting --project $FIREBASE_PROJECT_ID
else
    print_status "Firebase project already initialized"
fi

# Update Cloud Run CORS settings for Firebase domain
print_status "Updating Cloud Run CORS settings..."
FIREBASE_DOMAIN="${FIREBASE_PROJECT_ID}.web.app"
print_warning "Make sure to add $FIREBASE_DOMAIN to your Cloud Run CORS settings"

# Deploy to Firebase Hosting
print_status "Deploying frontend to Firebase Hosting..."
firebase deploy --only hosting --project $FIREBASE_PROJECT_ID

# Get the deployed URL
DEPLOYED_URL="https://${FIREBASE_PROJECT_ID}.web.app"

print_success "🎉 Frontend deployed successfully!"
print_success "Frontend URL: $DEPLOYED_URL"

print_status "📋 Next steps:"
echo "1. Update Cloud Run CORS settings to allow requests from:"
echo "   - $DEPLOYED_URL"
echo "   - https://${FIREBASE_PROJECT_ID}.firebaseapp.com"
echo ""
echo "2. Test the frontend by visiting:"
echo "   $DEPLOYED_URL"
echo ""
echo "3. Update any documentation with the new frontend URL"

print_warning "⚠️  Important notes:"
echo "- The frontend is now publicly accessible (no authentication required)"
echo "- API calls still require authentication tokens"
echo "- Users will see an authentication prompt when accessing API features"
echo "- The Cloud Run service can now focus on API-only functionality"

print_success "🚀 Firebase deployment completed successfully!" 