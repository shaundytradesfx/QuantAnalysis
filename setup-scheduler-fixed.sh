#!/bin/bash

# Google Cloud Scheduler Setup Script for Forex Sentiment Analyzer
# This script creates Cloud Scheduler jobs to trigger the cron endpoints

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
TIME_ZONE="UTC"

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

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    print_error "Could not get service URL. Make sure the Cloud Run service is deployed first."
    exit 1
fi

print_status "Setting up Cloud Scheduler jobs..."
print_status "Service URL: ${SERVICE_URL}"

# Enable Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# Create or update scraper job (daily at 2:00 AM UTC)
print_status "Creating scraper job..."
gcloud scheduler jobs create http scraper-job \
    --location=${REGION} \
    --schedule="0 2 * * *" \
    --time-zone=${TIME_ZONE} \
    --uri="${SERVICE_URL}/api/cron/scrape" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{}' \
    --attempt-deadline=3600s \
    --max-retry-attempts=3 \
    --max-retry-duration=7200s \
    --min-backoff=60s \
    --max-backoff=300s \
    --description="Daily scraper job for Forex Factory data" \
    --quiet || \
gcloud scheduler jobs update http scraper-job \
    --location=${REGION} \
    --schedule="0 2 * * *" \
    --time-zone=${TIME_ZONE} \
    --uri="${SERVICE_URL}/api/cron/scrape" \
    --http-method=POST \
    --update-headers="Content-Type=application/json" \
    --message-body='{}' \
    --attempt-deadline=3600s \
    --max-retry-attempts=3 \
    --max-retry-duration=7200s \
    --min-backoff=60s \
    --max-backoff=300s \
    --description="Daily scraper job for Forex Factory data" \
    --quiet

# Create or update analysis job (daily at 3:00 AM UTC, after scraper)
print_status "Creating analysis job..."
gcloud scheduler jobs create http analysis-job \
    --location=${REGION} \
    --schedule="0 3 * * *" \
    --time-zone=${TIME_ZONE} \
    --uri="${SERVICE_URL}/api/cron/analyze" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{}' \
    --attempt-deadline=3600s \
    --max-retry-attempts=3 \
    --max-retry-duration=7200s \
    --min-backoff=60s \
    --max-backoff=300s \
    --description="Daily sentiment analysis job" \
    --quiet || \
gcloud scheduler jobs update http analysis-job \
    --location=${REGION} \
    --schedule="0 3 * * *" \
    --time-zone=${TIME_ZONE} \
    --uri="${SERVICE_URL}/api/cron/analyze" \
    --http-method=POST \
    --update-headers="Content-Type=application/json" \
    --message-body='{}' \
    --attempt-deadline=3600s \
    --max-retry-attempts=3 \
    --max-retry-duration=7200s \
    --min-backoff=60s \
    --max-backoff=300s \
    --description="Daily sentiment analysis job" \
    --quiet

# Create or update notification job (weekly on Monday at 6:00 AM UTC)
print_status "Creating notification job..."
gcloud scheduler jobs create http notification-job \
    --location=${REGION} \
    --schedule="0 6 * * 1" \
    --time-zone=${TIME_ZONE} \
    --uri="${SERVICE_URL}/api/cron/notify" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{}' \
    --attempt-deadline=3600s \
    --max-retry-attempts=3 \
    --max-retry-duration=7200s \
    --min-backoff=60s \
    --max-backoff=300s \
    --description="Weekly Discord notification job (Mondays at 6 AM UTC)" \
    --quiet || \
gcloud scheduler jobs update http notification-job \
    --location=${REGION} \
    --schedule="0 6 * * 1" \
    --time-zone=${TIME_ZONE} \
    --uri="${SERVICE_URL}/api/cron/notify" \
    --http-method=POST \
    --update-headers="Content-Type=application/json" \
    --message-body='{}' \
    --attempt-deadline=3600s \
    --max-retry-attempts=3 \
    --max-retry-duration=7200s \
    --min-backoff=60s \
    --max-backoff=300s \
    --description="Weekly Discord notification job (Mondays at 6 AM UTC)" \
    --quiet

print_success "Cloud Scheduler jobs created successfully!"

# List the created jobs
print_status "Created scheduler jobs:"
gcloud scheduler jobs list --location=${REGION} --format="table(name,schedule,state,httpTarget.uri)"

print_status "Job schedules:"
echo "- Scraper: Daily at 2:00 AM UTC"
echo "- Analysis: Daily at 3:00 AM UTC"  
echo "- Notification: Weekly on Mondays at 6:00 AM UTC"

print_warning "Note: Make sure to set up the required secrets in Google Secret Manager before the jobs run:"
echo "- DATABASE_URL"
echo "- DISCORD_WEBHOOK_URL"
echo "- DISCORD_HEALTH_WEBHOOK_URL"

print_success "Scheduler setup completed!" 