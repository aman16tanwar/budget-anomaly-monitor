-- BigQuery Schema for Meta Ads Budget Monitoring
-- Dataset: generative-ai-418805.budget_alert

-- Table Naming Convention:
-- All tables are prefixed with 'meta_' to distinguish from future platforms:
-- - meta_* for Facebook/Meta Ads
-- - google_ads_* for Google Ads (future)
-- - dv360_* for Display & Video 360 (future)
-- - linkedin_* for LinkedIn Ads (future)

-- Note: Dataset already created, so we'll create tables directly

-- Table 1: Meta Campaign snapshots (for tracking current state and changes)
CREATE TABLE IF NOT EXISTS `generative-ai-418805.budget_alert.meta_campaign_snapshots` (
  snapshot_id STRING NOT NULL,
  campaign_id STRING NOT NULL,
  account_id STRING NOT NULL,
  account_name STRING,
  campaign_name STRING,
  campaign_status STRING,
  budget_amount NUMERIC,
  budget_type STRING, -- 'daily' or 'lifetime'
  budget_currency STRING,
  previous_budget_amount NUMERIC,
  budget_change_percentage FLOAT64,
  is_new_campaign BOOLEAN,
  created_time TIMESTAMP,
  snapshot_timestamp TIMESTAMP NOT NULL,
  
  -- Additional fields for ML
  objective STRING,
  bid_strategy STRING,
  optimization_goal STRING
)
PARTITION BY DATE(snapshot_timestamp)
OPTIONS(
  description="Hourly snapshots of campaign budgets for change detection"
);

-- Table 2: Meta Ad Set snapshots
CREATE TABLE IF NOT EXISTS `generative-ai-418805.budget_alert.meta_adset_snapshots` (
  snapshot_id STRING NOT NULL,
  adset_id STRING NOT NULL,
  campaign_id STRING NOT NULL,
  account_id STRING NOT NULL,
  account_name STRING,
  adset_name STRING,
  adset_status STRING,
  budget_amount NUMERIC,
  budget_type STRING,
  budget_currency STRING,
  previous_budget_amount NUMERIC,
  budget_change_percentage FLOAT64,
  is_new_adset BOOLEAN,
  created_time TIMESTAMP,
  snapshot_timestamp TIMESTAMP NOT NULL,
  
  -- Additional targeting info for ML
  targeting_countries ARRAY<STRING>,
  targeting_age_min INT64,
  targeting_age_max INT64,
  bid_amount NUMERIC
)
PARTITION BY DATE(snapshot_timestamp)
OPTIONS(
  description="Hourly snapshots of ad set budgets"
);

-- Table 3: Meta Anomalies detected
CREATE TABLE IF NOT EXISTS `generative-ai-418805.budget_alert.meta_anomalies` (
  anomaly_id STRING NOT NULL,
  anomaly_type STRING NOT NULL, -- 'CRITICAL', 'WARNING', 'INFO'
  anomaly_category STRING, -- 'budget_increase', 'new_campaign', 'velocity', 'pattern'
  level STRING NOT NULL, -- 'campaign' or 'adset'
  account_id STRING NOT NULL,
  account_name STRING,
  campaign_id STRING,
  campaign_name STRING,
  adset_id STRING,
  adset_name STRING,
  
  -- Anomaly details
  message STRING NOT NULL,
  current_budget NUMERIC,
  previous_budget NUMERIC,
  budget_increase_percentage FLOAT64,
  risk_score FLOAT64,
  
  -- Context
  detected_at TIMESTAMP NOT NULL,
  created_outside_business_hours BOOLEAN,
  time_since_creation_minutes INT64,
  
  -- Response tracking
  alert_sent BOOLEAN DEFAULT FALSE,
  alert_sent_at TIMESTAMP,
  acknowledged BOOLEAN DEFAULT FALSE,
  acknowledged_by STRING,
  acknowledged_at TIMESTAMP,
  false_positive BOOLEAN DEFAULT FALSE,
  
  -- For ML training
  was_actual_issue BOOLEAN -- For supervised learning
)
PARTITION BY DATE(detected_at)
OPTIONS(
  description="All detected anomalies with response tracking"
);

-- Table 4: Meta Account activity patterns (for ML)
CREATE TABLE IF NOT EXISTS `generative-ai-418805.budget_alert.meta_account_activity` (
  account_id STRING NOT NULL,
  activity_date DATE NOT NULL,
  
  -- Daily aggregates
  total_campaigns INT64,
  new_campaigns_created INT64,
  campaigns_with_budget_changes INT64,
  total_budget_changes INT64,
  
  -- Budget statistics
  total_daily_budget NUMERIC,
  avg_campaign_budget NUMERIC,
  max_campaign_budget NUMERIC,
  total_budget_increase_amount NUMERIC,
  
  -- Time patterns
  earliest_activity_hour INT64,
  latest_activity_hour INT64,
  activities_outside_business_hours INT64,
  
  -- For anomaly detection
  is_weekend BOOLEAN,
  is_holiday BOOLEAN
)
PARTITION BY activity_date
OPTIONS(
  description="Daily account activity patterns for ML training"
);

-- Table 5: Meta Real-time monitoring state
CREATE TABLE IF NOT EXISTS `generative-ai-418805.budget_alert.meta_current_state` (
  entity_id STRING NOT NULL, -- campaign_id or adset_id
  entity_type STRING NOT NULL, -- 'campaign' or 'adset'
  account_id STRING NOT NULL,
  
  -- Current values
  current_budget NUMERIC,
  current_status STRING,
  last_seen_timestamp TIMESTAMP NOT NULL,
  
  -- For quick comparison
  previous_budget NUMERIC,
  previous_status STRING,
  previous_check_timestamp TIMESTAMP,
  
  -- Flags
  is_being_monitored BOOLEAN DEFAULT TRUE,
  has_recent_anomaly BOOLEAN DEFAULT FALSE,
  consecutive_anomaly_count INT64 DEFAULT 0,
  
  PRIMARY KEY (entity_id, entity_type) NOT ENFORCED
)
OPTIONS(
  description="Current state for real-time comparison, updated every check"
);

-- Views for analysis

-- View 1: Recent Meta anomalies summary
CREATE OR REPLACE VIEW `generative-ai-418805.budget_alert.meta_recent_anomalies_view` AS
SELECT 
  DATE(detected_at) as detection_date,
  account_name,
  anomaly_type,
  COUNT(*) as anomaly_count,
  SUM(CAST(acknowledged AS INT64)) as acknowledged_count,
  SUM(CAST(false_positive AS INT64)) as false_positive_count,
  AVG(risk_score) as avg_risk_score
FROM `generative-ai-418805.budget_alert.meta_anomalies`
WHERE detected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY 1, 2, 3
ORDER BY detection_date DESC, anomaly_count DESC;

-- View 2: Meta Budget trend analysis
CREATE OR REPLACE VIEW `generative-ai-418805.budget_alert.meta_budget_trends_view` AS
SELECT 
  account_id,
  campaign_id,
  campaign_name,
  DATE(snapshot_timestamp) as snapshot_date,
  MAX(budget_amount) as max_budget,
  MIN(budget_amount) as min_budget,
  AVG(budget_amount) as avg_budget,
  MAX(budget_change_percentage) as max_change_percentage
FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots`
WHERE snapshot_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY 1, 2, 3, 4
HAVING max_change_percentage > 0
ORDER BY max_change_percentage DESC;

-- Table for Meta ML features (create this after collecting some data)
CREATE OR REPLACE TABLE `generative-ai-418805.budget_alert.meta_ml_features` AS
WITH campaign_history AS (
  SELECT 
    campaign_id,
    account_id,
    -- Time-based features
    EXTRACT(HOUR FROM snapshot_timestamp) as hour_of_day,
    EXTRACT(DAYOFWEEK FROM snapshot_timestamp) as day_of_week,
    
    -- Budget features
    budget_amount,
    LAG(budget_amount, 1) OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp) as prev_budget,
    LAG(budget_amount, 24) OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp) as budget_24h_ago,
    
    -- Change features
    budget_change_percentage,
    COUNT(*) OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp ROWS BETWEEN 23 PRECEDING AND CURRENT ROW) as changes_last_24h,
    
    snapshot_timestamp
  FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots`
  WHERE snapshot_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
)
SELECT 
  *,
  -- Derived features
  CASE WHEN hour_of_day < 8 OR hour_of_day > 18 THEN 1 ELSE 0 END as outside_business_hours,
  CASE WHEN day_of_week IN (1, 7) THEN 1 ELSE 0 END as is_weekend,
  CASE WHEN budget_amount > 10000 THEN 1 ELSE 0 END as high_budget_flag,
  
  -- Rolling statistics
  AVG(budget_amount) OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp ROWS BETWEEN 167 PRECEDING AND CURRENT ROW) as avg_budget_7d,
  STDDEV(budget_amount) OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp ROWS BETWEEN 167 PRECEDING AND CURRENT ROW) as stddev_budget_7d
FROM campaign_history
WHERE prev_budget IS NOT NULL;