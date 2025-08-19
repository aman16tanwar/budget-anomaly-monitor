# Budget Alert System - Morning Reminder Feature

## Overview

The system now includes smart alert scheduling:
- **Immediate alerts** for new budget anomalies
- **24-hour deduplication** to prevent spam
- **Morning reminders** at 9 AM PST for unacknowledged alerts

## How It Works

### Alert Schedule

1. **First Detection**: Immediate alert when budget increase is detected
2. **Next 24 Hours**: No duplicate alerts (deduplication active)
3. **9 AM PST Window (8-10 AM)**: System sends reminders for unacknowledged alerts older than 24 hours
4. **Rest of Day**: Standard 24-hour deduplication continues

### Example Timeline

- **Monday 2:00 PM**: Budget increases from $1000 to $5000 → Alert sent
- **Monday 2:05 PM - Tuesday 2:00 PM**: No duplicate alerts
- **Tuesday 9:00 AM**: If still unacknowledged → Morning reminder sent
- **Tuesday 9:05 AM - Wednesday 9:00 AM**: No more alerts unless budget changes

## Features

### 1. Smart Deduplication
- During regular hours: 24-hour deduplication
- During morning hours (8-10 AM PST): Only 4-hour deduplication
- This allows morning reminders while preventing spam

### 2. Clear Alert Messages
- Regular alerts show: "Duplicate alerts are suppressed for 24 hours"
- Morning alerts show: "This may include unacknowledged alerts from yesterday"

### 3. Manual Acknowledgment
When you verify a budget increase is legitimate:

```sql
-- Mark specific anomaly as acknowledged
UPDATE `generative-ai-418805.budget_alert.meta_anomalies`
SET 
    acknowledged = TRUE,
    acknowledged_by = 'your.email@company.com',
    acknowledged_at = CURRENT_TIMESTAMP(),
    acknowledgment_note = 'Verified - legitimate budget increase for Q4 campaign'
WHERE campaign_id = '123456789'
AND current_budget = 5000
AND acknowledged = FALSE;
```

## Monitoring Unacknowledged Alerts

Check which alerts need attention:

```sql
-- View all unacknowledged budget alerts from the last 48 hours
SELECT 
    detected_at,
    account_name,
    campaign_name,
    message,
    current_budget,
    previous_budget,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), detected_at, HOUR) as hours_since_detection
FROM `generative-ai-418805.budget_alert.meta_anomalies`
WHERE acknowledged = FALSE
AND anomaly_category IN ('budget_increase', 'new_campaign')
AND detected_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
ORDER BY detected_at DESC;
```

## Cloud Scheduler Configuration

To ensure morning reminders work properly, schedule your Cloud Function to run:
- Every 5 minutes during business hours (for immediate alerts)
- At least once between 8-10 AM PST (for morning reminders)

Example cron expressions:
```
# Every 5 minutes
*/5 * * * *

# Or specifically ensure morning coverage
*/5 8-18 * * *  # Every 5 minutes from 8 AM to 6 PM PST
```

## Benefits

1. **No Alert Fatigue**: You won't get the same alert every 5 minutes
2. **Daily Reminder**: Unacknowledged alerts get a morning reminder
3. **Flexible Acknowledgment**: Mark alerts as acknowledged when convenient
4. **Clear Tracking**: All alerts and acknowledgments stored in BigQuery