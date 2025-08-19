# Simplified Interactive Alerts Setup - Single Cloud Function

You can use a SINGLE Cloud Function to handle both monitoring and interactive buttons!

## Option 1: Modify Existing Cloud Function (Recommended)

### Step 1: Update your existing main.py

Replace your current `main.py` with the combined version that handles both:
- Scheduled monitoring runs
- Google Chat button interactions

```python
# In your main.py, add this logic at the beginning:

def monitor_meta_budgets_bq(request):
    """Main entry point for the Cloud Function"""
    
    # Check if this is a Google Chat interaction
    request_json = request.get_json(silent=True)
    
    # Google Chat interactions have an 'action' field
    if request_json and 'action' in request_json:
        # Handle button click
        return handle_chat_interaction(request)
    else:
        # Handle scheduled monitoring
        business_id = os.getenv('META_BUSINESS_ID', request.args.get('business_id'))
        project_id = os.getenv('GCP_PROJECT')
        
        if not business_id:
            return {'error': 'No business_id provided'}, 400
        
        # Initialize and run monitor
        monitor = MetaBudgetMonitorBQ(business_id, project_id)
        monitor.run_monitoring_cycle()
        
        return {'status': 'success', 'business_id': business_id}
```

### Step 2: Configure Google Chat

1. Go to your Google Chat space
2. Click on the space name → "Apps & integrations" 
3. Click on "Webhooks"
4. If you have an existing webhook:
   - Note down the webhook URL (you'll still use this for sending alerts)
5. Configure your space to receive interactive messages:
   - The space needs to be configured to send button clicks back to your Cloud Function URL

### Step 3: Update Your Cloud Function URL in Google Chat

Unfortunately, Google Chat webhooks are one-way (only for sending messages TO chat). For interactive buttons, you need to:

1. **Use Google Chat API** instead of webhooks for full interactivity, OR
2. **Keep it simple** with one-way notifications (no buttons)

## Option 2: Simple One-Way Notifications (No Additional Setup)

If you don't need interactive buttons, the current implementation already works perfectly:

1. ✅ Duplicate notifications are prevented
2. ✅ Zombie campaigns are filtered out
3. ✅ Alerts are sent to Google Chat
4. ✅ All anomalies are tracked in BigQuery

You can manually update acknowledgments in BigQuery:

```sql
-- Manually acknowledge an anomaly
UPDATE `generative-ai-418805.budget_alert.meta_anomalies`
SET 
    acknowledged = TRUE,
    acknowledged_by = 'your.email@company.com',
    acknowledged_at = CURRENT_TIMESTAMP(),
    acknowledgment_note = 'Manually acknowledged - legitimate budget increase'
WHERE campaign_name = 'Your Campaign Name'
AND acknowledged = FALSE
AND detected_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
```

## Option 3: Use Google Chat App (For Full Interactivity)

To get working interactive buttons, you'd need to:

1. Create a Google Chat App (not just a webhook)
2. Set up OAuth and permissions
3. Configure the app to point to your Cloud Function

This is more complex but gives you full interactivity.

## Recommendation

For most use cases, Option 2 (simple one-way notifications) works great:
- You get instant alerts
- Duplicates are prevented
- You can track everything in BigQuery
- Manual acknowledgment via BigQuery queries when needed

The deduplication logic ensures you won't get spammed with the same alert every 5 minutes!