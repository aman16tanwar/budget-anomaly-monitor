# Cloud Build Setup Guide - Step by Step

## Prerequisites
1. Google Cloud project with billing enabled
2. Git repository (GitHub, GitLab, or Cloud Source Repos)
3. gcloud CLI installed and authenticated

## Step 1: Enable Required APIs
```bash
# Enable necessary services
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
```

## Step 2: Set Up Secrets in Secret Manager
Instead of hardcoding sensitive data, we'll use Secret Manager:

```bash
# Create secrets for the monitoring service
echo -n "your-meta-business-id" | gcloud secrets create meta-business-id --data-file=-
echo -n "your-meta-access-token" | gcloud secrets create meta-access-token --data-file=-
echo -n "your-meta-app-secret" | gcloud secrets create meta-app-secret --data-file=-
echo -n "your-meta-app-id" | gcloud secrets create meta-app-id --data-file=-
echo -n "your-webhook-url" | gcloud secrets create google-chat-webhook --data-file=-
echo -n "your-project-id" | gcloud secrets create gcp-project-id --data-file=-
```

## Step 3: Create Service Account for Cloud Run
```bash
# Create service account
gcloud iam service-accounts create budget-monitor-sa \
    --display-name="Budget Monitor Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:budget-monitor-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:budget-monitor-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:budget-monitor-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Step 4: Grant Cloud Build Permissions
```bash
# Get Cloud Build service account
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin"

# Grant Service Account User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor"

# Grant Cloud Scheduler admin (for creating scheduled jobs)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/cloudscheduler.admin"
```

## Step 5: Connect Your Repository

### For GitHub:
1. Go to Cloud Console > Cloud Build > Triggers
2. Click "Connect Repository"
3. Select GitHub
4. Authenticate and select your repo
5. Create trigger:
   ```
   Name: deploy-dashboard-on-push
   Event: Push to branch
   Branch: ^main$
   Included files: dashboard-monitor/**
   Build configuration: /dashboard-monitor/cloudbuild.yaml
   ```
6. Create another trigger for budget-anomaly-monitor:
   ```
   Name: deploy-monitor-on-push
   Event: Push to branch
   Branch: ^main$
   Included files: budget-anomaly-monitor/**
   Build configuration: /budget-anomaly-monitor/cloudbuild.yaml
   ```

### For Manual Testing:
```bash
# Test dashboard deployment
cd dashboard-monitor
gcloud builds submit --config=cloudbuild.yaml

# Test monitor deployment
cd ../budget-anomaly-monitor
gcloud builds submit --config=cloudbuild.yaml
```

## Step 6: Understanding the Build Process

When you push code:
1. **Trigger activates** → Cloud Build starts
2. **Step 1** → Builds Docker image from your Dockerfile
3. **Step 2** → Pushes image to Container Registry
4. **Step 3** → Deploys to Cloud Run with your settings
5. **Step 4** → (Monitor only) Creates scheduler for periodic runs

## Step 7: Monitoring Your Builds

```bash
# View build history
gcloud builds list --limit=5

# Stream logs for a specific build
gcloud builds log BUILD_ID

# Or use the Console
# Cloud Console > Cloud Build > History
```

## Step 8: Your First Deployment

1. Make a small change to your code (e.g., update a comment)
2. Commit and push:
   ```bash
   git add .
   git commit -m "feat: trigger cloud build deployment"
   git push origin main
   ```
3. Watch the magic happen in Cloud Build History!

## Troubleshooting

### Build fails at Docker step:
- Check your Dockerfile syntax
- Ensure requirements.txt is correct

### Build fails at deployment:
- Check service account permissions
- Verify secrets exist in Secret Manager

### Scheduled job not running:
- Check Cloud Scheduler logs
- Verify service account has invoker permissions

## Cost Optimization

- Cloud Build: 120 free build-minutes/day
- Set `--max-instances` to control Cloud Run costs
- Use `--min-instances=0` for services that can scale to zero

## Next Steps

1. Set up different configurations for staging/production
2. Add unit tests to the build process
3. Set up notifications for build failures
4. Create a rollback strategy

Need help? Check the build logs first - they usually tell you exactly what went wrong!