# Cloud Run Deployment Guide for Meta Ads Budget Monitor

## Overview
This guide explains how to deploy the Meta Ads Budget Monitoring system to Google Cloud Run using environment variables instead of shell scripts.

## Architecture
- **Cloud Run**: Hosts the FastAPI application
- **Cloud Scheduler**: Triggers monitoring at regular intervals
- **Firestore**: Stores historical data and anomalies
- **Secret Manager**: Stores sensitive credentials (optional)

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Meta Business Manager** access
3. **Meta App** with Ads Management permissions
4. **Google Chat Space** with webhook URL
5. **gcloud CLI** installed and configured

## Setup Instructions

### 1. Prepare Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```env
# Meta API Configuration
META_BUSINESS_ID=1234567890
META_ACCESS_TOKEN=your_long_lived_token_here
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret

# Google Cloud Configuration
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Google Chat Configuration
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/XXX/messages?key=YYY
```

### 2. Create Service Account (for local development)

```bash
# Create service account
gcloud iam service-accounts create meta-budget-monitor \
    --display-name="Meta Budget Monitor Service Account"

# Download key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=meta-budget-monitor@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:meta-budget-monitor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:meta-budget-monitor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 3. Enable Required APIs

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com
```

### 4. Initialize Firestore

```bash
# Create Firestore database (if not exists)
gcloud firestore databases create --region=us-central1
```

### 5. Deploy to Cloud Run

#### Option A: Deploy from Source (Recommended)

```bash
# Deploy directly from source
gcloud run deploy meta-budget-monitor \
    --source . \
    --region us-central1 \
    --platform managed \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1 \
    --allow-unauthenticated \
    --set-env-vars-from-file .env
```

#### Option B: Build and Deploy Manually

```bash
# Build container
gcloud builds submit --config cloudbuild.yaml

# Or build locally
docker build -t gcr.io/YOUR_PROJECT_ID/meta-budget-monitor .
docker push gcr.io/YOUR_PROJECT_ID/meta-budget-monitor

# Deploy
gcloud run deploy meta-budget-monitor \
    --image gcr.io/YOUR_PROJECT_ID/meta-budget-monitor \
    --region us-central1 \
    --platform managed \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1 \
    --allow-unauthenticated \
    --set-env-vars-from-file .env
```

### 6. Set Up Cloud Scheduler

Get your Cloud Run service URL:
```bash
SERVICE_URL=$(gcloud run services describe meta-budget-monitor \
    --region us-central1 \
    --format 'value(status.url)')
```

Create scheduler job:
```bash
gcloud scheduler jobs create http meta-budget-monitor-schedule \
    --location us-central1 \
    --schedule "*/5 * * * *" \
    --time-zone "America/Toronto" \
    --uri "${SERVICE_URL}/monitor" \
    --http-method POST \
    --headers Content-Type=application/json \
    --body '{"force_run": false}'
```

### 7. Configure Google Chat Webhook

1. In your Google Chat Space, create a webhook
2. Copy the webhook URL
3. Update the `GOOGLE_CHAT_WEBHOOK_URL` in Cloud Run:

```bash
gcloud run services update meta-budget-monitor \
    --region us-central1 \
    --update-env-vars GOOGLE_CHAT_WEBHOOK_URL=YOUR_WEBHOOK_URL
```

## API Endpoints

Once deployed, your Cloud Run service will have these endpoints:

- `GET /` - Health check and status
- `POST /monitor` - Manually trigger monitoring
- `GET /status` - Get detailed monitoring status
- `GET /health` - Detailed health check
- `POST /test-alert` - Send test alert to Google Chat
- `POST /webhook/google-chat` - Handle Google Chat interactions

## Testing the Deployment

### 1. Check Service Health
```bash
curl https://YOUR-SERVICE-URL.run.app/health
```

### 2. Send Test Alert
```bash
curl -X POST https://YOUR-SERVICE-URL.run.app/test-alert
```

### 3. Manually Trigger Monitoring
```bash
curl -X POST https://YOUR-SERVICE-URL.run.app/monitor \
    -H "Content-Type: application/json" \
    -d '{"force_run": true}'
```

## Managing Secrets (Production)

For production, use Secret Manager instead of .env files:

```bash
# Create secrets
echo -n "YOUR_ACCESS_TOKEN" | gcloud secrets create meta-access-token --data-file=-
echo -n "YOUR_APP_SECRET" | gcloud secrets create meta-app-secret --data-file=-

# Update Cloud Run to use secrets
gcloud run services update meta-budget-monitor \
    --region us-central1 \
    --set-secrets="META_ACCESS_TOKEN=meta-access-token:latest,META_APP_SECRET=meta-app-secret:latest"
```

## Monitoring & Logs

### View Logs
```bash
# Recent logs
gcloud run services logs read meta-budget-monitor --region us-central1 --limit 50

# Tail logs
gcloud run services logs tail meta-budget-monitor --region us-central1
```

### View Metrics
```bash
# Open Cloud Console
gcloud app browse
# Navigate to Cloud Run > meta-budget-monitor > Metrics
```

## Cost Optimization

### Estimated Monthly Costs
- **Cloud Run**: ~$20-40 (with min instance = 1)
- **Firestore**: ~$20 (1GB storage, 500K operations)
- **Cloud Scheduler**: Free (under 3 jobs)
- **Total**: ~$40-60/month

### Cost Saving Tips
1. Set `--min-instances 0` if you don't need instant response
2. Reduce `--max-instances` based on your needs
3. Increase `CHECK_INTERVAL_MINUTES` to reduce API calls

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Error: The Application Default Credentials are not available
   ```
   Solution: Ensure service account key is properly configured

2. **Meta API Error**
   ```
   Error: Invalid OAuth 2.0 Access Token
   ```
   Solution: Regenerate long-lived access token

3. **Google Chat Not Receiving Alerts**
   - Verify webhook URL is correct
   - Check Cloud Run logs for errors
   - Test with `/test-alert` endpoint

### Debug Commands
```bash
# Check service status
gcloud run services describe meta-budget-monitor --region us-central1

# Check environment variables
gcloud run services describe meta-budget-monitor \
    --region us-central1 \
    --format export | grep env

# Test scheduler job
gcloud scheduler jobs run meta-budget-monitor-schedule --location us-central1
```

## Security Best Practices

1. **Use Secret Manager** for production credentials
2. **Enable VPC Connector** if accessing private resources
3. **Set up IAM** properly:
   ```bash
   # Restrict who can invoke the service
   gcloud run services add-iam-policy-binding meta-budget-monitor \
       --region us-central1 \
       --member="serviceAccount:YOUR-SCHEDULER-SA@YOUR-PROJECT.iam.gserviceaccount.com" \
       --role="roles/run.invoker"
   ```
4. **Enable Cloud Audit Logs** for monitoring access

## Updating the Service

To update code or configuration:

```bash
# Update code and redeploy
gcloud run deploy meta-budget-monitor \
    --source . \
    --region us-central1

# Update only environment variables
gcloud run services update meta-budget-monitor \
    --region us-central1 \
    --update-env-vars KEY=VALUE

# Update from new .env file
gcloud run services update meta-budget-monitor \
    --region us-central1 \
    --set-env-vars-from-file .env
```

## Rollback

If needed, rollback to a previous revision:

```bash
# List revisions
gcloud run revisions list --service meta-budget-monitor --region us-central1

# Rollback
gcloud run services update-traffic meta-budget-monitor \
    --region us-central1 \
    --to-revisions REVISION_NAME=100
```