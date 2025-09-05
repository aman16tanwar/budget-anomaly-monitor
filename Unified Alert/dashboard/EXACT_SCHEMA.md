# Exact BigQuery Schema Column Names

## Meta Campaign Snapshots (`meta_campaign_snapshots`)

**Based on**: `/mnt/c/Users/Aman Tanwar/Downloads/AI/Budget Anomaly/bigquery_schema.sql` lines 14-38

**Actual columns**:
- `snapshot_id` (STRING)
- `campaign_id` (STRING) 
- `account_id` (STRING)
- `account_name` (STRING)
- `campaign_name` (STRING)
- `campaign_status` (STRING) ← **NOT** `status`
- `budget_amount` (NUMERIC)
- `budget_type` (STRING)
- `budget_currency` (STRING) ← **NOT** `currency`
- `previous_budget_amount` (NUMERIC)
- `budget_change_percentage` (FLOAT64)
- `is_new_campaign` (BOOLEAN)
- `created_time` (TIMESTAMP) ← **NOT** `created_date`
- `snapshot_timestamp` (TIMESTAMP)
- `objective` (STRING)
- `bid_strategy` (STRING)
- `optimization_goal` (STRING)

**❌ DOES NOT HAVE**: `business_hours_flag`

---

## Google Ads Campaign Snapshots (`google_ads_campaign_snapshots`)

**Based on**: `/mnt/c/Users/Aman Tanwar/Downloads/AI/Budget Anomaly/unified/google_ads_budget_monitor.py` lines 60-71

**Actual columns**:
- `account_id` (STRING)
- `campaign_id` (STRING)
- `campaign_name` (STRING)
- `budget_amount` (FLOAT64)
- `currency` (STRING) ← **NOT** `budget_currency`
- `status` (STRING) ← **NOT** `campaign_status`
- `delivery_method` (STRING)
- `snapshot_time` (TIMESTAMP) ← **NOT** `snapshot_timestamp`
- `created_date` (DATE) ← **NOT** `created_time`
- `business_hours_flag` (BOOLEAN) ← **EXISTS**

---

## Meta Anomalies (`meta_anomalies`)

**Based on**: `/mnt/c/Users/Aman Tanwar/Downloads/AI/Budget Anomaly/bigquery_schema.sql` lines 70-108

**Actual columns**:
- `anomaly_id` (STRING)
- `anomaly_type` (STRING)
- `anomaly_category` (STRING)
- `level` (STRING)
- `account_id` (STRING)
- `account_name` (STRING)
- `campaign_id` (STRING)
- `campaign_name` (STRING)
- `adset_id` (STRING)
- `adset_name` (STRING)
- `message` (STRING)
- `current_budget` (NUMERIC)
- `previous_budget` (NUMERIC)
- `budget_increase_percentage` (FLOAT64) ← **NOT** `increase_ratio`
- `risk_score` (FLOAT64)
- `detected_at` (TIMESTAMP)
- `created_outside_business_hours` (BOOLEAN) ← **NOT** `business_hours_context`
- `time_since_creation_minutes` (INT64)
- `alert_sent` (BOOLEAN)
- `alert_sent_at` (TIMESTAMP)
- `acknowledged` (BOOLEAN)
- `acknowledged_by` (STRING)
- `acknowledged_at` (TIMESTAMP)
- `false_positive` (BOOLEAN)
- `was_actual_issue` (BOOLEAN)

---

## Google Ads Anomalies (`google_ads_anomalies`)

**Based on**: `/mnt/c/Users/Aman Tanwar/Downloads/AI/Budget Anomaly/unified/google_ads_budget_monitor.py` lines 74-91

**Actual columns**:
- `anomaly_id` (STRING)
- `account_id` (STRING)
- `campaign_id` (STRING)
- `campaign_name` (STRING)
- `anomaly_category` (STRING)
- `previous_budget` (FLOAT64)
- `current_budget` (FLOAT64)
- `increase_ratio` (FLOAT64) ← **NOT** `budget_increase_percentage`
- `risk_score` (FLOAT64)
- `detected_time` (TIMESTAMP) ← **NOT** `detected_at`
- `business_hours_context` (STRING) ← **NOT** `created_outside_business_hours`
- `acknowledged` (BOOLEAN)
- `acknowledged_by` (STRING)
- `acknowledged_at` (TIMESTAMP)
- `alert_sent` (BOOLEAN)
- `alert_sent_at` (TIMESTAMP)

---

## Dashboard Query Fixes Applied

### Campaign Queries:
```sql
-- Meta: Uses FALSE as business_hours_flag (column doesn't exist)
-- Google: Uses actual business_hours_flag column
```

### Key Differences Summary:
1. **Meta campaigns**: NO `business_hours_flag` → Use `FALSE as business_hours_flag`
2. **Google campaigns**: HAS `business_hours_flag` → Use normally
3. **Meta anomalies**: Uses `created_outside_business_hours` BOOLEAN
4. **Google anomalies**: Uses `business_hours_context` STRING
5. **Timestamp naming**: Meta uses `_timestamp`, Google uses `_time`
6. **Currency naming**: Meta uses `budget_currency`, Google uses `currency`
7. **Status naming**: Meta uses `campaign_status`, Google uses `status`