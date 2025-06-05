#!/bin/bash

# Google Cloud Run Deployment Script for Forex Sentiment Analyzer
# This script builds and deploys the application to Google Cloud Run
# Updated with Phase 6 monitoring and actual data functionality

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="capital-nexus-research"
REGION="us-central1"
SERVICE_NAME="forex-sentiment-analyzer"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

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

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    print_error "PROJECT_ID is not set. Please edit this script and set your Google Cloud Project ID."
    exit 1
fi

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "You are not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

print_status "Starting deployment to Google Cloud Run with actual data functionality..."

# Set the project
print_status "Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
print_status "Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudscheduler.googleapis.com

# Build the Docker image
print_status "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} .

# Deploy to Cloud Run with all environment variables
print_status "Deploying to Cloud Run with actual data and monitoring functionality..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 3600 \
    --concurrency 100 \
    --max-instances 10 \
    --set-env-vars="PYTHONPATH=/app,FOREX_FACTORY_API_URL=https://nfs.faireconomy.media/ff_calendar_thisweek.json,ACTUAL_DATA_COLLECTION_ENABLED=true,ACTUAL_DATA_COLLECTION_INTERVAL=4,ACTUAL_DATA_RETRY_LIMIT=3,ACTUAL_DATA_LOOKBACK_DAYS=7,ACTUAL_DATA_TIMEOUT_SECONDS=30,INCLUDE_ACTUAL_SENTIMENT_IN_REPORTS=true,SHOW_FORECAST_ACCURACY_IN_REPORTS=true,SHOW_SURPRISES_IN_REPORTS=true,ENABLE_DISCORD_ALERTS=true,ALERT_COOLDOWN_HOURS=4"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

print_success "Deployment completed successfully!"
print_success "Service URL: ${SERVICE_URL}"

# Test the health endpoint
print_status "Testing health endpoint..."
if curl -f "${SERVICE_URL}/api/health" > /dev/null 2>&1; then
    print_success "Health check passed!"
else
    print_warning "Health check failed. The service might still be starting up."
fi

# Test actual data functionality endpoint
print_status "Testing actual data endpoints..."
if curl -f "${SERVICE_URL}/api/actual-data/status" > /dev/null 2>&1; then
    print_success "Actual data endpoints are responding!"
else
    print_warning "Actual data endpoints not responding yet. May need time to initialize."
fi

print_status "Next steps:"
echo "1. Verify secrets are configured in Google Secret Manager:"
echo "   - DATABASE_URL"
echo "   - DISCORD_WEBHOOK_URL"
echo "   - DISCORD_HEALTH_WEBHOOK_URL"
echo ""
echo "2. Run database migrations on production:"
echo "   curl -X POST \"${SERVICE_URL}/api/migrate\""
echo ""
echo "3. Test actual data collection:"
echo "   curl -X POST \"${SERVICE_URL}/api/actual-data/collect\""
echo ""
echo "4. Run the scheduler setup script:"
echo "   ./setup-scheduler.sh"
echo ""
echo "5. Deploy the frontend:"
echo "   cd frontend && npm run build && firebase deploy"
echo ""
echo "6. Test Discord integration:"
echo "   curl -X POST \"${SERVICE_URL}/api/discord/test\""

print_success "Production deployment with actual data functionality completed!" 