# Interactive Google Chat Alerts Setup Guide

This guide explains how to set up interactive buttons in Google Chat alerts that allow users to acknowledge budget anomalies.

## Overview

The system now includes:
1. **Deduplication**: Prevents sending duplicate alerts for the same budget anomaly within 24 hours
2. **Interactive Buttons**: Each alert includes "ACKNOWLEDGE" and "FALSE POSITIVE" buttons
3. **Acknowledgment Tracking**: Updates BigQuery when users click buttons

## What's Changed

### 1. Zombie Campaign Notifications Removed
- Zombie campaign anomalies are still detected and stored in BigQuery
- They are NO LONGER sent to Google Chat
- Only budget increase and new campaign alerts are sent

### 2. Duplicate Alert Prevention
- When a budget increase is detected, it checks if there's already an unacknowledged alert for the same:
  - Campaign ID
  - Account ID
  - Anomaly category
  - Current budget amount
  - Within the last 24 hours
- If a matching unacknowledged alert exists, no new notification is sent

### 3. Interactive Acknowledgment (Requires Additional Setup)
To enable interactive buttons, you need to:

#### Step 1: Deploy the Interaction Handler
```bash
# Deploy the handler as a Cloud Function
gcloud functions deploy handle-chat-interaction \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point handle_chat_interaction \
  --source ./budget-anomaly-monitor \
  --set-env-vars GCP_PROJECT=generative-ai-418805
```

#### Step 2: Configure Google Chat Webhook
1. Go to your Google Chat space
2. Click on the space name → "Manage webhooks"
3. Edit your existing webhook
4. Add the Cloud Function URL as the "Callback URL"
5. Save the configuration

#### Step 3: Update Environment Variables
Add the interaction handler URL to your environment:
```bash
CHAT_INTERACTION_URL=https://YOUR-REGION-YOUR-PROJECT.cloudfunctions.net/handle-chat-interaction
```

## How It Works

### Alert Flow
1. **Budget Increase Detected** → Check for existing unacknowledged alerts
2. **No Duplicate Found** → Create anomaly in BigQuery → Send Google Chat alert
3. **User Clicks Button** → Cloud Function updates BigQuery → Sends confirmation

### Button Actions
- **✅ ACKNOWLEDGE**: Marks the anomaly as acknowledged (legitimate budget change)
- **❌ FALSE POSITIVE**: Marks the anomaly as a false positive

### After Acknowledgment
- The anomaly is marked as acknowledged in BigQuery
- No more duplicate alerts will be sent for this specific budget amount
- If the budget changes again, a new alert will be sent

## Testing

1. **Test Deduplication**:
   - Trigger a budget increase
   - Wait for alert
   - Run the monitor again within 5 minutes
   - Verify no duplicate alert is sent

2. **Test Acknowledgment** (if interactive buttons are set up):
   - Click "ACKNOWLEDGE" on an alert
   - Check BigQuery to verify the anomaly is marked as acknowledged
   - Run the monitor again
   - Verify no new alert for the same budget

## Monitoring

Check acknowledgment status in BigQuery:
```sql
SELECT 
  campaign_name,
  current_budget,
  acknowledged,
  acknowledged_by,
  acknowledged_at,
  acknowledgment_note
FROM `generative-ai-418805.budget_alert.meta_anomalies`
WHERE detected_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY detected_at DESC;
```

## Important Notes

1. **24-Hour Window**: After 24 hours, if the anomaly is still unacknowledged and the budget hasn't changed, a reminder alert will be sent
2. **Budget Changes**: If the budget changes again (e.g., from $5000 to $10000), a new alert will be sent regardless of acknowledgment status
3. **False Positives**: Anomalies marked as false positives are still stored but won't trigger future alerts