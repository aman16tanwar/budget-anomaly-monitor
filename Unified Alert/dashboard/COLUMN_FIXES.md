# Column Name Fixes for Unified Dashboard

## Issue Summary
The unified dashboard was failing because Meta Ads and Google Ads tables use different column names in BigQuery.

## Column Name Differences Between Platforms

### Campaign Snapshots Tables

| Column Purpose | Meta Ads Table | Google Ads Table |
|---|---|---|
| Currency | `budget_currency` | `currency` |
| Status | `campaign_status` | `status` |
| Timestamp | `snapshot_timestamp` | `snapshot_time` |
| Created Date | `created_time` | `created_date` |

### Anomalies Tables

| Column Purpose | Meta Ads Table | Google Ads Table |
|---|---|---|
| Increase Ratio | `budget_increase_percentage` | `increase_ratio` |
| Detection Time | `detected_at` | `detected_time` |
| Business Hours | `created_outside_business_hours` (BOOLEAN) | `business_hours_context` (STRING) |

## Fixes Applied

### 1. Campaign Queries
```sql
-- Meta Ads Query
SELECT 
    budget_currency as currency,
    campaign_status as status,
    snapshot_timestamp,
    created_time as created_date
FROM meta_campaign_snapshots

-- Google Ads Query  
SELECT 
    currency,
    status,
    snapshot_time as snapshot_timestamp,
    created_date
FROM google_ads_campaign_snapshots
```

### 2. Anomalies Queries
```sql
-- Meta Ads Query
SELECT 
    budget_increase_percentage as increase_ratio,
    detected_at,
    CASE WHEN created_outside_business_hours THEN 'Outside Business Hours' 
         ELSE 'Business Hours' END as business_hours_context
FROM meta_anomalies

-- Google Ads Query
SELECT 
    increase_ratio,
    detected_time as detected_at,
    business_hours_context
FROM google_ads_anomalies
```

### 3. Data Freshness Query
```sql
-- Uses snapshot_timestamp for Meta, snapshot_time for Google Ads
SELECT MAX(snapshot_timestamp) FROM meta_campaign_snapshots
UNION ALL  
SELECT MAX(snapshot_time) FROM google_ads_campaign_snapshots
```

## Column Mapping Summary

### Campaign Tables
- **currency**: `budget_currency` (Meta) → `currency` (Google) 
- **status**: `campaign_status` (Meta) → `status` (Google)
- **timestamp**: `snapshot_timestamp` (Meta) → `snapshot_time` (Google)
- **created_date**: `created_time` (Meta) → `created_date` (Google)

### Anomalies Tables  
- **increase_ratio**: `budget_increase_percentage` (Meta) → `increase_ratio` (Google)
- **detection_time**: `detected_at` (Meta) → `detected_time` (Google)
- **business_hours**: `created_outside_business_hours` BOOLEAN (Meta) → `business_hours_context` STRING (Google)

## Result
All queries now use the correct platform-specific column names while normalizing them to common column names in the unified dataframe for consistent dashboard functionality.