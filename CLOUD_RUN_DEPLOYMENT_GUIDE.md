# Google Cloud Run Deployment Guide

This guide will help you deploy the Forex Factory Sentiment Analyzer to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**: Create a Google Cloud account with billing enabled
2. **Google Cloud CLI**: Install and configure the `gcloud` CLI
3. **Docker**: Install Docker for local testing (optional)
4. **PostgreSQL Database**: Have a PostgreSQL database accessible from the internet

## Step-by-Step Deployment

### 1. Initial Setup

#### 1.1 Install Google Cloud CLI
```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Download from https://cloud.google.com/sdk/docs/install
```

#### 1.2 Authenticate and Set Project
```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create forex-sentiment-analyzer --name="Forex Sentiment Analyzer"

# Set the project
gcloud config set project forex-sentiment-analyzer

# Enable billing (required even for free tier)
# Go to: https://console.cloud.google.com/billing
```

### 2. Configure Deployment Scripts

#### 2.1 Update Project ID in Scripts
Edit the following files and set your `PROJECT_ID`:

**deploy.sh**:
```bash
PROJECT_ID="your-project-id-here"
```

**setup-scheduler.sh**:
```bash
PROJECT_ID="your-project-id-here"
```

**setup-secrets.sh**:
```bash
PROJECT_ID="your-project-id-here"
```

### 3. Set Up Secrets

#### 3.1 Run the Secrets Setup Script
```bash
./setup-secrets.sh
```

This will prompt you for:
- **DATABASE_URL**: Your PostgreSQL connection string
  - Format: `postgresql://username:password@host:port/database`
  - Example: `postgresql://user:pass@34.123.45.67:5432/forex_sentiment`
- **DISCORD_WEBHOOK_URL**: Your Discord webhook URL for reports
- **DISCORD_HEALTH_WEBHOOK_URL**: Your Discord webhook URL for alerts

### 4. Deploy to Cloud Run

#### 4.1 Run the Deployment Script
```bash
./deploy.sh
```

This script will:
- Enable required Google Cloud APIs
- Build the Docker image using Cloud Build
- Deploy the service to Cloud Run
- Configure environment variables
- Test the health endpoint

#### 4.2 Verify Deployment
After deployment, you should see output like:
```
Service URL: https://forex-sentiment-analyzer-xxx-uc.a.run.app
Health check passed!
```

### 5. Set Up Scheduled Tasks

#### 5.1 Run the Scheduler Setup Script
```bash
./setup-scheduler.sh
```

This creates three Cloud Scheduler jobs:
- **Scraper**: Daily at 2:00 AM UTC
- **Analysis**: Daily at 3:00 AM UTC  
- **Notification**: Weekly on Mondays at 6:00 AM UTC

### 6. Deploy Frontend (Optional)

#### 6.1 Using Firebase Hosting
```bash
cd frontend

# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase project
firebase init hosting

# Build the frontend
npm run build

# Deploy to Firebase
firebase deploy
```

#### 6.2 Update Frontend API URL
Update your frontend configuration to point to the Cloud Run service URL.

### 7. Testing the Deployment

#### 7.1 Test Health Endpoint
```bash
curl https://your-service-url/api/health
```

#### 7.2 Test Cron Endpoints
```bash
# Test scraper
curl -X POST https://your-service-url/api/cron/scrape

# Test analysis
curl -X POST https://your-service-url/api/cron/analyze

# Test notification
curl -X POST https://your-service-url/api/cron/notify
```

#### 7.3 Test Frontend
Visit your frontend URL and verify:
- Dashboard loads correctly
- API endpoints return data
- Currency filtering works

## Local Development with Docker

### 1. Local Testing
```bash
# Create .env file with your secrets
cp env.template .env
# Edit .env with your values

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### 2. Database Migration
```bash
# Run migrations in the container
docker-compose exec app python -m alembic upgrade head
```

## Monitoring and Maintenance

### 1. View Logs
```bash
# Cloud Run logs
gcloud logs read --service=forex-sentiment-analyzer --region=us-central1

# Scheduler logs
gcloud logs read --filter="resource.type=cloud_scheduler_job"
```

### 2. Update Secrets
```bash
# Update a secret
echo "new-secret-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Update Cloud Run to use new secret version
gcloud run services update forex-sentiment-analyzer \
    --region=us-central1 \
    --update-secrets="SECRET_NAME=SECRET_NAME:latest"
```

### 3. Scale Configuration
```bash
# Update resource limits
gcloud run services update forex-sentiment-analyzer \
    --region=us-central1 \
    --memory=1Gi \
    --cpu=2 \
    --max-instances=5
```

## Cost Optimization

### Free Tier Limits
- **Cloud Run**: 2M requests/month, 180K vCPU-seconds, 360K GiB-seconds
- **Cloud Scheduler**: 3 jobs free
- **Secret Manager**: 6 active secret versions free
- **Cloud Build**: 120 build-minutes/day

### Cost Monitoring
1. Set up billing alerts in Google Cloud Console
2. Monitor usage in Cloud Run metrics
3. Use minimum resource allocation for development

## Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
gcloud builds log BUILD_ID

# Common fixes:
# - Check Dockerfile syntax
# - Verify requirements.txt
# - Check for missing dependencies
```

#### 2. Service Won't Start
```bash
# Check service logs
gcloud logs read --service=forex-sentiment-analyzer --limit=50

# Common fixes:
# - Verify environment variables
# - Check database connectivity
# - Verify secrets are accessible
```

#### 3. Scheduler Jobs Failing
```bash
# Check scheduler logs
gcloud logs read --filter="resource.type=cloud_scheduler_job" --limit=20

# Common fixes:
# - Verify service URL is correct
# - Check service is responding to health checks
# - Verify authentication/permissions
```

#### 4. Database Connection Issues
- Ensure database allows connections from Google Cloud IPs
- Verify DATABASE_URL format is correct
- Check firewall rules on database server

### Getting Help

1. **Google Cloud Support**: Available with paid support plans
2. **Stack Overflow**: Tag questions with `google-cloud-run`
3. **Google Cloud Documentation**: https://cloud.google.com/run/docs

## Security Best Practices

1. **Secrets Management**:
   - Never commit secrets to version control
   - Rotate secrets regularly
   - Use least privilege access

2. **Network Security**:
   - Use VPC connectors for private database access
   - Enable Cloud Armor for DDoS protection
   - Use HTTPS only

3. **Access Control**:
   - Use IAM roles with minimal permissions
   - Enable audit logging
   - Monitor access patterns

## Next Steps

After successful deployment:

1. **Set up monitoring**: Configure Cloud Monitoring alerts
2. **Backup strategy**: Set up database backups
3. **CI/CD pipeline**: Automate deployments with Cloud Build triggers
4. **Performance tuning**: Monitor and optimize based on usage patterns

## Support

For issues specific to this application, please check:
- Application logs in Cloud Run
- Database connectivity
- Discord webhook configuration
- Forex Factory API availability 