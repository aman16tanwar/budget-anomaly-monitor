# 🚨 Unified Multi-Platform Budget Monitoring System

A comprehensive budget anomaly detection system that monitors both **Meta Ads** and **Google Ads** platforms, providing unified alerting through Google Chat.

## 📊 System Overview

- **🔵 Meta Ads**: Monitors business manager campaigns for budget anomalies
- **🔴 Google Ads**: Monitors 194+ accounts with 5,100+ campaigns  
- **📧 Unified Alerts**: Combined Google Chat notifications
- **🏗️ Production Ready**: Dockerized Cloud Run job with CI/CD

## 🎯 Key Features

### Budget Anomaly Detection
- **New Campaign Alerts**: High-budget campaigns (≥$5,000)
- **Budget Increase Alerts**: 1.5x warnings, 3.0x critical alerts
- **Business Hours Context**: After-hours activity flagging
- **Smart Deduplication**: Prevents alert spam

### Multi-Platform Monitoring
- **Meta Business Manager**: Full account hierarchy
- **Google Ads Manager**: 194 active client accounts
- **Unified BigQuery Storage**: `meta_*` and `google_ads_*` tables
- **Cross-Platform Alerting**: Single Google Chat card

## 🚀 Quick Start

### 1. Configuration
Ensure `.env` file contains all required credentials:
```bash
# Meta Ads
META_BUSINESS_ID=639849309470605
META_ACCESS_TOKEN=your_meta_token

# Google Ads  
GOOGLE_ADS_LOGIN_CUSTOMER_ID=9820928751
GOOGLE_ADS_DEVELOPER_TOKEN=your_google_ads_token

# Shared
GCP_PROJECT_ID=generative-ai-418805
GOOGLE_CHAT_WEBHOOK_URL=your_webhook_url
```

### 2. Local Testing
```bash
# Test configuration
python test_webhook.py

# Test unified monitoring
python unified_budget_monitoring_job.py

# Test alerts
python simple_alert_test.py
```

### 3. Production Deployment
```bash
# Build container
docker build -t unified-budget-monitor .

# Deploy to Cloud Run Jobs
gcloud run jobs deploy unified-budget-monitor \
  --image=gcr.io/generative-ai-418805/unified-budget-monitor \
  --region=us-central1 \
  --task-timeout=600 \
  --memory=1Gi

# Schedule with Cloud Scheduler
gcloud scheduler jobs create http unified-budget-monitoring \
  --schedule="*/5 * * * *" \
  --uri=https://your-cloud-run-job-url \
  --http-method=POST
```

## 📁 File Structure

### 🎯 Main Entry Points
- **`unified_budget_monitoring_job.py`** - Production job (monitors both platforms)
- **`cloud_run_job.py`** - Legacy Meta-only job
- **`app.py`** - FastAPI web service

### 🔵 Meta Ads System
- **`meta_api_implementation_bigquery.py`** - Core Meta monitoring
- **`meta_api_with_delivery.py`** - Delivery status checking
- **`simple_delivery_check.py`** - Zombie campaign detection

### 🔴 Google Ads System  
- **`google_ads_budget_monitor.py`** - Core Google Ads monitoring
- **`google_ads_main.py`** - Account discovery utility

### 📧 Alert System
- **`unified_chat_alerts.py`** - Multi-platform Google Chat alerts
- **`handle_chat_interaction.py`** - Interactive acknowledgments

### 🧪 Testing & Utilities
- **`test_webhook.py`** - Test Google Chat connectivity
- **`simple_alert_test.py`** - Test alert formatting
- **`run_monitor_direct.py`** - Direct execution utility

## 🔧 Configuration Details

### Environment Variables
```bash
# Required for Meta Ads
META_BUSINESS_ID=your_business_id
META_ACCESS_TOKEN=your_access_token

# Required for Google Ads
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_manager_account_id
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
GOOGLE_ADS_CLIENT_ID=your_oauth_client_id
GOOGLE_ADS_CLIENT_SECRET=your_oauth_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token

# Required for Both
GCP_PROJECT_ID=generative-ai-418805
GOOGLE_CHAT_WEBHOOK_URL=your_webhook_url

# Optional Thresholds
BUDGET_INCREASE_WARNING=1.5
BUDGET_INCREASE_CRITICAL=3.0
NEW_CAMPAIGN_MAX_BUDGET=5000
```

### BigQuery Tables
- **Meta Tables**: `meta_campaign_snapshots`, `meta_anomalies`, `meta_current_state`
- **Google Ads Tables**: `google_ads_campaign_snapshots`, `google_ads_anomalies`, `google_ads_current_state`

## 📊 Monitoring Results

### Recent Performance
- **Google Ads**: 194 active accounts, 5,100+ campaigns monitored
- **Meta Ads**: Full business manager coverage
- **Anomalies Detected**: 31 new high-budget Google Ads campaigns
- **Alert Delivery**: <30 seconds to Google Chat

### Alert Examples
```
🚨 Multi-Platform Budget Alert
📊 PLATFORM SUMMARY
🔵 Meta Ads: 1 anomaly  
🔴 Google Ads: 31 anomalies

🔴 GOOGLE ADS ALERTS
🆕 31 NEW high-budget campaigns:
💰 $16,584 CAD - WR - Search (Ad Grant) - UMS - Florida
💰 $10,000 CAD - WR - Ad Grant - Parksville - DSA - BC
```

## 🛠️ Troubleshooting

### Common Issues
1. **Authentication Errors**: Verify all tokens are valid and not expired
2. **BigQuery Permissions**: Ensure service account has BigQuery admin role
3. **Google Chat Webhook**: Test webhook URL with `test_webhook.py`
4. **Missing Dependencies**: Check `requirements.txt` is complete

### Debug Commands
```bash
# Check health
python unified_budget_monitoring_job.py health

# Test Meta connection
python meta_main.py

# Test Google Ads connection  
python google_ads_main.py

# Test alerts
python simple_alert_test.py
```

## 📖 Documentation

See `/docs/` folder for detailed guides:
- **Cloud Build Setup**: `CLOUD_BUILD_SETUP_GUIDE.md`
- **Cloud Run Deployment**: `CLOUD_RUN_DEPLOYMENT_GUIDE.md`
- **Interactive Alerts**: `INTERACTIVE_ALERTS_SETUP.md`
- **System Architecture**: `META_ADS_BUDGET_ALERT_SYSTEM.md`

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] Service accounts have proper permissions  
- [ ] Google Chat webhook tested
- [ ] BigQuery dataset exists
- [ ] Docker image builds successfully
- [ ] Cloud Run job deploys
- [ ] Cloud Scheduler configured
- [ ] Monitoring dashboard updated

---

**🚀 Your unified budget monitoring system is ready for production!**