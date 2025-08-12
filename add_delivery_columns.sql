-- Add delivery status columns to campaign snapshots table
-- Run this in BigQuery to add the new columns

ALTER TABLE `generative-ai-418805.budget_alert.meta_campaign_snapshots`
ADD COLUMN IF NOT EXISTS total_adsets INTEGER,
ADD COLUMN IF NOT EXISTS active_adsets INTEGER,
ADD COLUMN IF NOT EXISTS adsets_with_active_ads INTEGER,
ADD COLUMN IF NOT EXISTS delivery_status_simple STRING,
ADD COLUMN IF NOT EXISTS start_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS stop_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_future_campaign BOOLEAN;

-- Also add to anomalies table
ALTER TABLE `generative-ai-418805.budget_alert.meta_anomalies`
ADD COLUMN IF NOT EXISTS delivery_status STRING,
ADD COLUMN IF NOT EXISTS total_adsets INTEGER,
ADD COLUMN IF NOT EXISTS active_adsets INTEGER;

-- Create view to easily find zombie campaigns
CREATE OR REPLACE VIEW `generative-ai-418805.budget_alert.meta_zombie_campaigns` AS
WITH latest_campaigns AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
    FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots`
    WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
)
SELECT 
    campaign_id,
    campaign_name,
    account_name,
    budget_amount,
    budget_type,
    delivery_status_simple,
    total_adsets,
    active_adsets,
    adsets_with_active_ads,
    CASE 
        WHEN budget_type = 'daily' THEN budget_amount * 30
        ELSE budget_amount
    END as monthly_budget_at_risk,
    CASE 
        WHEN delivery_status_simple LIKE '🔴%' THEN 'CRITICAL'
        WHEN delivery_status_simple LIKE '🟠%' THEN 'HIGH'
        WHEN delivery_status_simple LIKE '🟡%' THEN 'MEDIUM'
        ELSE 'OK'
    END as risk_level
FROM latest_campaigns
WHERE rn = 1
    AND campaign_status = 'ACTIVE'
    AND delivery_status_simple NOT LIKE '🟢%'
    AND delivery_status_simple NOT LIKE '❓%'
    AND budget_amount > 1000
ORDER BY monthly_budget_at_risk DESC;

-- Summary view for dashboard
CREATE OR REPLACE VIEW `generative-ai-418805.budget_alert.meta_delivery_summary` AS
WITH latest AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
    FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots`
    WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
)
SELECT 
    COUNT(DISTINCT campaign_id) as total_campaigns,
    COUNT(DISTINCT CASE WHEN delivery_status_simple LIKE '🟢%' THEN campaign_id END) as deliverable_campaigns,
    COUNT(DISTINCT CASE WHEN delivery_status_simple LIKE '🔴%' THEN campaign_id END) as no_adsets,
    COUNT(DISTINCT CASE WHEN delivery_status_simple LIKE '🟠%' THEN campaign_id END) as adsets_paused,
    COUNT(DISTINCT CASE WHEN delivery_status_simple LIKE '🟡%' THEN campaign_id END) as no_ads,
    SUM(CASE 
        WHEN delivery_status_simple NOT LIKE '🟢%' AND delivery_status_simple NOT LIKE '❓%'
        THEN budget_amount 
        ELSE 0 
    END) as daily_budget_at_risk,
    COUNT(DISTINCT account_name) as accounts_affected
FROM latest
WHERE rn = 1
    AND campaign_status = 'ACTIVE';