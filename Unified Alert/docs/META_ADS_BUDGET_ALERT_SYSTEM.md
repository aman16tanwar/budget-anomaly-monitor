# Meta Ads Budget Alert System - Complete Documentation

## Overview
A real-time monitoring system for Meta Ads that detects budget anomalies and potential security breaches by monitoring active campaigns and ad sets under a Business Manager account. Uses BigQuery for data storage to enable advanced analytics and future ML capabilities.

## Key Features
- **Business Manager Integration**: Monitor all ad accounts under a single Business ID
- **Active-Only Monitoring**: Only tracks ACTIVE campaigns and ad sets
- **Real-time Alerts**: Google Chat Space notifications
- **Hacker Detection**: Identifies suspicious new campaigns and unusual budget changes
- **BigQuery Storage**: All data stored in BigQuery for analytics and ML
- **Multi-Platform Ready**: Table naming convention supports future expansion to Google Ads, DV360, etc.

## System Architecture

### Data Flow
1. **Cloud Scheduler** triggers monitoring every 5 minutes
2. **Cloud Run** service fetches data from Meta Ads API
3. **BigQuery** stores all data for historical tracking and analytics
4. **Google Chat** receives formatted alerts for team action

### Google Cloud Services Used
- **Cloud Run**: Hosts the FastAPI monitoring application
- **Cloud Scheduler**: Automated triggers every 5 minutes
- **BigQuery**: Primary data storage for all monitoring data
- **Secret Manager**: Secure API credential storage (optional if using .env)

### BigQuery Dataset Structure
Dataset: `generative-ai-418805.budget_alert`

#### Table Naming Convention
All tables use platform prefixes for multi-platform support:
- `meta_*` - Facebook/Meta Ads tables
- `google_ads_*` - Google Ads tables (future)
- `dv360_*` - Display & Video 360 tables (future)
- `linkedin_*` - LinkedIn Ads tables (future)

## Detection Logic

### 1. New Campaign Detection
Flags campaigns created within the last hour if:
- Budget exceeds $5,000 CAD (configurable)
- Created outside business hours (8 AM - 6 PM)
- Multiple campaigns created rapidly (>3 in 30 minutes)

### 2. Budget Change Detection
Monitors existing campaigns/ad sets for:
- **Critical**: Budget increase >300%
- **Warning**: Budget increase >150%
- **Emergency**: Multiple critical alerts

### 3. Active-Only Filtering
- Uses Meta's `effective_status: ['ACTIVE']` parameter
- Ignores paused, deleted, or archived campaigns
- Only monitors accounts with `account_status = 1` (ACTIVE)

### 4. Delivery Status Monitoring (Zombie Campaign Detection)
Identifies campaigns with budget that cannot deliver ads:
- **No Active Ad Sets**: Campaign is active but all ad sets are paused
- **No Ads**: Ad sets are active but contain no ads
- **All Ads Paused**: Ads exist but all are paused or disapproved
- **Risk Level**: Higher budget = higher risk of waste
- Prevents budget allocation waste on non-deliverable campaigns

## Implementation Details

### Core Components

#### 1. MetaBudgetMonitor Class
Main monitoring class that:
- Initializes Meta API connection
- Fetches active accounts from Business Manager
- Monitors campaigns and ad sets
- Sends Google Chat alerts

#### 2. Anomaly Detection Methods
- `_check_campaign_anomalies()`: Validates campaign budgets
- `_check_adset_anomalies()`: Validates ad set budgets
- Historical comparison with Firestore data

#### 3. Alert System
- Formatted Google Chat cards with severity levels
- Direct links to Ads Manager
- Acknowledge functionality for team response

### Configuration
```python
{
    "thresholds": {
        "budget_increase_warning": 1.5,     # 150% increase
        "budget_increase_critical": 3.0,    # 300% increase
        "new_campaign_max_budget": 5000,    # CAD
        "new_adset_max_budget": 2000,       # CAD
    },
    "monitoring": {
        "check_interval_minutes": 5,
        "campaign_status_filter": ["ACTIVE"],
        "adset_status_filter": ["ACTIVE"],
    }
}
```

## Setup Instructions

### 1. Prerequisites
- Google Cloud Project with billing enabled
- Meta Business Manager ID
- Meta App with Ads Management permissions
- Google Chat Space with webhook URL

### 2. Meta API Setup
1. Create a Meta App at developers.facebook.com
2. Add "Ads Management" permission
3. Generate a long-lived access token
4. Note your App ID and App Secret

### 3. Google Cloud Setup
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable cloudfunctions.googleapis.com firestore.googleapis.com secretmanager.googleapis.com

# Create secrets
echo -n "YOUR_ACCESS_TOKEN" | gcloud secrets create meta-access-token --data-file=-
echo -n "YOUR_APP_SECRET" | gcloud secrets create meta-app-secret --data-file=-
echo -n "YOUR_APP_ID" | gcloud secrets create meta-app-id --data-file=-
```

### 4. Deploy the System
```bash
# Make deploy script executable
chmod +x deploy.sh

# Update variables in deploy.sh
PROJECT_ID="your-project-id"
BUSINESS_ID="your-meta-business-id"
GOOGLE_CHAT_WEBHOOK_URL="your-webhook-url"

# Run deployment
./deploy.sh
```

### 5. Google Chat Setup
1. Create a webhook in your Google Chat Space
2. Copy the webhook URL
3. Update the environment variable in Cloud Function

## Alert Examples

### Critical Alert
```
🚨 Meta Ads Budget Alert
⛔ CRITICAL ALERTS
CAMPAIGN: Summer Sale 2024
New campaign with unusually high budget: $25,000.00 CAD
[VIEW IN ADS MANAGER] [ACKNOWLEDGE]
```

### Warning Alert
```
⚠️ WARNING ALERTS
AD SET: Budget increased by 175%
Previous: $100.00 → Current: $275.00
```

### Zombie Campaign Alert
```
🧟 ZOMBIE CAMPAIGN ALERT
CAMPAIGN: Summer Sale 2024
Daily Budget: $15,000.00 CAD
Issue: No active ad sets (all 5 paused)
Days Inactive: 3
Potential Waste: $45,000.00
[VIEW IN ADS MANAGER] [PAUSE CAMPAIGN]
```

## Monitoring Dashboard

### BigQuery Tables

#### Core Tables
1. **`meta_campaign_snapshots`**: Hourly snapshots of campaign budgets
2. **`meta_adset_snapshots`**: Hourly snapshots of ad set budgets
3. **`meta_anomalies`**: All detected anomalies with risk scores
4. **`meta_account_activity`**: Daily activity patterns for ML
5. **`meta_current_state`**: Current state for quick comparison

#### Views
1. **`meta_recent_anomalies_view`**: Summary of recent anomalies
2. **`meta_budget_trends_view`**: Budget trend analysis
3. **`meta_ml_features`**: Pre-computed features for ML models

### Sample BigQuery Queries

```sql
-- Get recent critical anomalies
SELECT 
  account_name,
  campaign_name,
  message,
  current_budget,
  risk_score,
  detected_at
FROM `generative-ai-418805.budget_alert.meta_anomalies`
WHERE anomaly_type = 'CRITICAL'
  AND detected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY risk_score DESC
LIMIT 10;

-- Analyze budget trends by account
SELECT 
  account_id,
  DATE(snapshot_timestamp) as date,
  SUM(budget_amount) as total_daily_budget,
  COUNT(DISTINCT campaign_id) as active_campaigns,
  MAX(budget_change_percentage) as max_budget_change
FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots`
WHERE snapshot_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY account_id, date
ORDER BY date DESC, total_daily_budget DESC;

-- Find accounts with multiple anomalies
SELECT 
  account_name,
  COUNT(*) as anomaly_count,
  AVG(risk_score) as avg_risk_score,
  SUM(CASE WHEN acknowledged = FALSE THEN 1 ELSE 0 END) as unacknowledged_count
FROM `generative-ai-418805.budget_alert.meta_anomalies`
WHERE detected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY account_name
HAVING anomaly_count > 3
ORDER BY anomaly_count DESC;
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Solution: Implement exponential backoff
   - Use batch requests for multiple accounts

2. **Missing Permissions**
   - Ensure Meta App has `ads_management` permission
   - Check Business Manager user roles

3. **No Alerts Received**
   - Verify Google Chat webhook URL
   - Check Cloud Function logs
   - Ensure Firestore is initialized

### Debug Commands
```bash
# View function logs
gcloud functions logs read monitor-meta-budgets --limit=50

# Test function manually
gcloud functions call monitor-meta-budgets

# Check scheduler job
gcloud scheduler jobs list
```

## Security Best Practices

1. **API Credentials**
   - Never hardcode credentials
   - Use Secret Manager for all sensitive data
   - Rotate access tokens regularly

2. **Access Control**
   - Limit Cloud Function invocation to scheduler only
   - Use service accounts with minimal permissions
   - Enable audit logging

3. **Alert Security**
   - Use HTTPS webhooks only
   - Implement webhook signature verification
   - Don't include sensitive data in alerts

## Cost Optimization

### Estimated Monthly Costs (USD)
- **Cloud Run**: ~$20-40/month (with min instances = 1)
- **BigQuery**: 
  - Storage: ~$20/month (for 1TB of data)
  - Queries: ~$5/month (for 1TB of queries)
- **Cloud Scheduler**: Free (under 3 jobs)
- **Secret Manager**: ~$5/month
- **Total**: ~$50-70/month

### BigQuery Cost Optimization
1. Tables are partitioned by date for efficient querying
2. Only query necessary date ranges
3. Use clustering on frequently filtered columns
4. Consider table expiration policies for old data
5. Use materialized views for frequently accessed aggregations

### Optimization Tips
1. Adjust polling frequency based on risk level
2. Set `--min-instances 0` in Cloud Run to save costs (with slight cold start delay)
3. Use batch Meta API requests to reduce calls
4. Archive old BigQuery data to Cloud Storage after 90 days

## Future Enhancements

1. **Machine Learning with BigQuery ML**
   - Build anomaly detection models using BigQuery ML
   - Predict budget anomalies before they occur
   - Learn normal spending patterns per account
   - Use the `meta_ml_features` table for model training

2. **Enhanced Delivery Monitoring**
   - Fully integrate ad set and ad level data fetching
   - Automated zombie campaign pausing (with approval workflow)
   - Delivery prediction models using BigQuery ML
   - Historical delivery pattern analysis

3. **Multi-Platform Support**
   - Add Google Ads monitoring (`google_ads_*` tables)
   - Add DV360 monitoring (`dv360_*` tables)
   - Create unified cross-platform views
   - Single dashboard for all ad platforms

3. **Advanced Detection**
   - Geographic anomaly detection
   - Audience targeting changes
   - Bid strategy modifications
   - Creative performance anomalies

4. **Integration**
   - Slack/Teams support
   - PagerDuty for critical alerts
   - Automated campaign pausing
   - Looker Studio dashboards

## Support & Maintenance

### Regular Tasks
- Review false positive rate monthly
- Adjust thresholds based on feedback
- Update Meta API version quarterly
- Monitor system performance

### Monitoring Metrics
- Detection accuracy: >95%
- False positive rate: <5%
- Alert response time: <2 minutes
- System uptime: 99.9%

## API Reference

### Cloud Run Endpoints
```
# Health check
GET https://YOUR-SERVICE-URL.run.app/

# Trigger monitoring manually  
POST https://YOUR-SERVICE-URL.run.app/monitor
Body: {
  "business_id": "optional_override",
  "force_run": true
}

# Get monitoring status
GET https://YOUR-SERVICE-URL.run.app/status

# Send test alert
POST https://YOUR-SERVICE-URL.run.app/test-alert
```

### BigQuery Schema

#### meta_campaign_snapshots
```sql
{
  snapshot_id: STRING,
  campaign_id: STRING,
  account_id: STRING,
  account_name: STRING,
  campaign_name: STRING,
  campaign_status: STRING,
  budget_amount: NUMERIC,
  budget_type: STRING,  -- 'daily' | 'lifetime'
  budget_currency: STRING,
  previous_budget_amount: NUMERIC,
  budget_change_percentage: FLOAT64,
  is_new_campaign: BOOLEAN,
  created_time: TIMESTAMP,
  snapshot_timestamp: TIMESTAMP,
  objective: STRING,
  bid_strategy: STRING,
  optimization_goal: STRING
}
```

#### meta_anomalies
```sql
{
  anomaly_id: STRING,
  anomaly_type: STRING,  -- 'CRITICAL' | 'WARNING' | 'INFO'
  anomaly_category: STRING,  -- 'budget_increase' | 'new_campaign' | 'velocity'
  level: STRING,  -- 'campaign' | 'adset'
  account_id: STRING,
  account_name: STRING,
  campaign_id: STRING,
  campaign_name: STRING,
  message: STRING,
  current_budget: NUMERIC,
  previous_budget: NUMERIC,
  budget_increase_percentage: FLOAT64,
  risk_score: FLOAT64,
  detected_at: TIMESTAMP,
  created_outside_business_hours: BOOLEAN,
  alert_sent: BOOLEAN,
  acknowledged: BOOLEAN,
  false_positive: BOOLEAN
}
```

## Contact & Support
For issues or questions:
1. Check Cloud Function logs
2. Review this documentation
3. Contact your Google Cloud administrator