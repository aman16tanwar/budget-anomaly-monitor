# Unified Multi-Platform Budget Monitoring Structure

## 📁 Directory Structure
```
unified/
├── 📄 Configuration Files
│   ├── .env                           # Combined environment variables
│   ├── .dockerignore                  # Docker ignore rules
│   ├── Dockerfile                     # Multi-platform container
│   ├── requirements.txt               # All dependencies
│   ├── cloudbuild.yaml               # Cloud Build configuration
│   └── cloudbuild-job.yaml          # Cloud Run Job build
│
├── 🎯 Main Application Files
│   ├── unified_budget_monitoring_job.py  # MAIN ENTRY POINT
│   ├── app.py                            # FastAPI web service
│   ├── cloud_run_job.py                 # Legacy Meta-only job
│   └── handle_chat_interaction.py       # Interactive alerts
│
├── 🔵 Meta Ads Monitoring
│   ├── meta_api_implementation_bigquery.py
│   ├── meta_api_enhanced.py
│   ├── meta_api_with_delivery.py
│   └── simple_delivery_check.py
│
├── 🔴 Google Ads Monitoring  
│   ├── google_ads_budget_monitor.py
│   ├── main.py                       # Account discovery
│   └── generate_user_credentials.py
│
├── 📧 Alert System
│   ├── unified_chat_alerts.py        # Multi-platform alerts
│   └── test_webhook.py              # Alert testing
│
├── 🖼️ Assets
│   ├── images/
│   │   ├── google-ads-logo.png
│   │   ├── logo.png
│   │   ├── favicon.png
│   │   └── loader.gif
│   └── meta.json                     # Service account credentials
│
├── 📊 Data & Configuration
│   ├── customer_clients.csv          # Google Ads accounts
│   ├── googleads.json               # Google Ads service account
│   └── bigquery_schema.sql          # Database schema
│
├── 🧪 Testing & Utilities
│   ├── test_unified_alert.py         # Alert testing
│   ├── simple_alert_test.py         # Simple tests
│   ├── run_monitor_direct.py        # Direct execution
│   └── requirements_*.txt           # Additional dependencies
│
└── 📖 Documentation
    ├── META_ADS_BUDGET_ALERT_SYSTEM.md
    ├── CLOUD_BUILD_SETUP_GUIDE.md
    ├── CLOUD_RUN_DEPLOYMENT_GUIDE.md
    ├── DELIVERY_IMPLEMENTATION_SUMMARY.md
    ├── INTERACTIVE_ALERTS_SETUP.md
    └── MORNING_REMINDER_SETUP.md
```

## 🎯 Key Features
- **Single Entry Point**: `unified_budget_monitoring_job.py`
- **Multi-Platform**: Meta Ads + Google Ads monitoring
- **Unified Alerts**: Combined Google Chat notifications  
- **Production Ready**: Docker containerization
- **CI/CD Pipeline**: Cloud Build integration
- **Interactive Features**: Google Chat acknowledgments
- **Comprehensive Monitoring**: 194 Google Ads accounts + Meta Business Manager

## 🚀 Deployment
```bash
# Build and deploy
docker build -t unified-budget-monitor .
gcloud run jobs deploy unified-budget-monitor --image=unified-budget-monitor
```