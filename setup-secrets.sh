#!/bin/bash

# Google Secret Manager Setup Script for Forex Sentiment Analyzer
# This script helps create secrets in Google Secret Manager

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="capital-nexus-research"

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

print_status "Setting up Google Secret Manager secrets..."

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_description=$2
    
    echo ""
    print_status "Setting up secret: ${secret_name}"
    echo "Description: ${secret_description}"
    
    # Check if secret exists
    if gcloud secrets describe ${secret_name} --quiet > /dev/null 2>&1; then
        print_warning "Secret ${secret_name} already exists."
        read -p "Do you want to add a new version? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Skipping ${secret_name}"
            return
        fi
    else
        # Create the secret
        print_status "Creating secret ${secret_name}..."
        gcloud secrets create ${secret_name}
    fi
    
    # Prompt for secret value
    echo "Please enter the value for ${secret_name}:"
    read -s secret_value
    
    if [ -z "$secret_value" ]; then
        print_warning "Empty value provided. Skipping ${secret_name}"
        return
    fi
    
    # Add secret version
    echo "$secret_value" | gcloud secrets versions add ${secret_name} --data-file=-
    print_success "Secret ${secret_name} updated successfully!"
}

# Enable Secret Manager API
print_status "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Create secrets
create_or_update_secret "DATABASE_URL" "PostgreSQL database connection string (e.g., postgresql://user:password@host:port/database)"

create_or_update_secret "DISCORD_WEBHOOK_URL" "Discord webhook URL for sending weekly sentiment reports"

create_or_update_secret "DISCORD_HEALTH_WEBHOOK_URL" "Discord webhook URL for sending health alerts and error notifications"

# Create the secret for Cloud Run to access
print_status "Creating secret resource for Cloud Run..."
cat > forex-sentiment-secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: forex-sentiment-secrets
type: Opaque
data:
  DATABASE_URL: $(gcloud secrets versions access latest --secret="DATABASE_URL" | base64)
  DISCORD_WEBHOOK_URL: $(gcloud secrets versions access latest --secret="DISCORD_WEBHOOK_URL" | base64)
  DISCORD_HEALTH_WEBHOOK_URL: $(gcloud secrets versions access latest --secret="DISCORD_HEALTH_WEBHOOK_URL" | base64)
EOF

print_success "Secret configuration file created: forex-sentiment-secrets.yaml"

# Update Cloud Run service to use secrets (skip if service doesn't exist)
print_status "Checking if Cloud Run service exists..."
if gcloud run services describe forex-sentiment-analyzer --region=us-central1 --quiet > /dev/null 2>&1; then
    print_status "Updating Cloud Run service to use secrets..."
    gcloud run services update forex-sentiment-analyzer \
        --region=us-central1 \
        --update-secrets="DATABASE_URL=DATABASE_URL:latest" \
        --update-secrets="DISCORD_WEBHOOK_URL=DISCORD_WEBHOOK_URL:latest" \
        --update-secrets="DISCORD_HEALTH_WEBHOOK_URL=DISCORD_HEALTH_WEBHOOK_URL:latest" \
        --quiet
    print_success "Cloud Run service updated with secrets!"
else
    print_warning "Cloud Run service not found. Secrets will be configured during deployment."
fi

print_success "Secrets setup completed!"

print_status "Summary of created secrets:"
gcloud secrets list --format="table(name,createTime)"

print_warning "Security reminder:"
echo "- Never commit secret values to version control"
echo "- Regularly rotate your secrets"
echo "- Use least privilege access for service accounts"
echo "- Monitor secret access logs"

print_success "Secret Manager setup completed!" 