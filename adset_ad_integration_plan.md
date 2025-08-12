# Ad Set & Ad Level Integration Plan

## Why This Matters
Without ad set and ad data, you're flying blind. A campaign can have a $50,000 daily budget but spend $0 if all ad sets are paused or have no ads.

## Recommended Approach: Hierarchical Monitoring

### 1. Data Collection Strategy

#### Option A: Full Hierarchy Scan (Comprehensive but Expensive)
```python
for campaign in active_campaigns:
    # Get all ad sets
    for adset in campaign.get_ad_sets():
        # Get all ads
        for ad in adset.get_ads():
            # Store ad data
```
**Pros**: Complete visibility
**Cons**: Many API calls, slower, higher costs

#### Option B: Smart Sampling (Recommended)
```python
# Only deep-dive into high-risk campaigns
for campaign in active_campaigns:
    if campaign.budget > HIGH_THRESHOLD or is_new_campaign:
        # Check delivery capability
        check_adsets_and_ads(campaign)
    else:
        # Just store basic campaign data
        store_campaign_only(campaign)
```

### 2. BigQuery Schema Design

#### Enhanced Tables Structure
```sql
-- 1. Campaign snapshots (existing, add delivery fields)
meta_campaign_snapshots
  + has_active_adsets BOOLEAN
  + active_adsets_count INTEGER
  + deliverable_adsets_count INTEGER
  + delivery_status STRING
  + last_delivery_check TIMESTAMP

-- 2. Ad Set snapshots (new)
meta_adset_snapshots
  - adset_id STRING
  - campaign_id STRING
  - account_id STRING
  - adset_name STRING
  - adset_status STRING
  - effective_status STRING
  - daily_budget NUMERIC
  - lifetime_budget NUMERIC
  - has_active_ads BOOLEAN
  - active_ads_count INTEGER
  - created_time TIMESTAMP
  - snapshot_timestamp TIMESTAMP

-- 3. Ad snapshots (lightweight)
meta_ad_snapshots
  - ad_id STRING
  - adset_id STRING
  - campaign_id STRING
  - ad_name STRING
  - ad_status STRING
  - effective_status STRING
  - approval_status STRING
  - created_time TIMESTAMP
  - snapshot_timestamp TIMESTAMP

-- 4. Delivery status summary (materialized view)
meta_delivery_status_current
  - campaign_id STRING
  - delivery_score FLOAT64 (0-1)
  - can_deliver BOOLEAN
  - issue_type STRING
  - last_checked TIMESTAMP
```

### 3. Efficient Monitoring Logic

```python
class EnhancedMetaMonitor:
    def monitor_with_delivery(self, account):
        campaigns = self.get_active_campaigns(account)
        
        for campaign in campaigns:
            # Always get campaign data
            campaign_data = self.process_campaign(campaign)
            
            # Risk-based deep inspection
            if self.needs_delivery_check(campaign):
                delivery_status = self.check_delivery_hierarchy(campaign)
                campaign_data['delivery_status'] = delivery_status
                
                # Store detailed data only for problematic campaigns
                if delivery_status['has_issues']:
                    self.store_detailed_hierarchy(campaign)
            
            self.store_campaign_snapshot(campaign_data)
    
    def needs_delivery_check(self, campaign):
        """Determine if we need to check delivery status"""
        return any([
            campaign.budget > 5000,  # High budget
            campaign.is_new,         # New campaign
            campaign.last_check_hours > 6,  # Haven't checked recently
            campaign.had_recent_changes  # Budget/status changed
        ])
    
    def check_delivery_hierarchy(self, campaign):
        """Smart delivery checking"""
        adsets = campaign.get_ad_sets(fields=['id', 'effective_status'])
        
        if not adsets:
            return {'status': 'NO_ADSETS', 'has_issues': True}
        
        active_adsets = [a for a in adsets if a['effective_status'] == 'ACTIVE']
        
        if not active_adsets:
            return {'status': 'NO_ACTIVE_ADSETS', 'has_issues': True}
        
        # Sample check - don't need to check EVERY ad
        sample_adset = active_adsets[0]
        ads = sample_adset.get_ads(fields=['effective_status'], limit=10)
        
        active_ads = [a for a in ads if a['effective_status'] == 'ACTIVE']
        
        if not ads:
            return {'status': 'NO_ADS', 'has_issues': True}
        elif not active_ads:
            return {'status': 'ADS_PAUSED', 'has_issues': True}
        
        return {'status': 'ACTIVE', 'has_issues': False}
```

### 4. Query Patterns for Analysis

```sql
-- Find zombie campaigns (high budget, can't deliver)
CREATE OR REPLACE VIEW meta_zombie_campaigns AS
SELECT 
    c.campaign_id,
    c.campaign_name,
    c.account_name,
    c.budget_amount,
    c.budget_type,
    c.delivery_status,
    c.budget_amount * 
        CASE 
            WHEN c.budget_type = 'daily' THEN 30
            ELSE 1
        END as monthly_waste_potential,
    CASE 
        WHEN c.delivery_status = 'NO_ADSETS' THEN 'Campaign has no ad sets'
        WHEN c.delivery_status = 'NO_ACTIVE_ADSETS' THEN 'All ad sets are paused'
        WHEN c.delivery_status = 'NO_ADS' THEN 'Ad sets have no ads'
        WHEN c.delivery_status = 'ADS_PAUSED' THEN 'All ads are paused'
    END as issue_description
FROM meta_campaign_snapshots c
WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
    AND campaign_status = 'ACTIVE'
    AND delivery_status != 'ACTIVE'
    AND budget_amount > 1000
ORDER BY monthly_waste_potential DESC;

-- Delivery health score by account
SELECT 
    account_name,
    COUNT(DISTINCT campaign_id) as total_campaigns,
    COUNT(DISTINCT CASE WHEN delivery_status = 'ACTIVE' THEN campaign_id END) as deliverable_campaigns,
    SUM(CASE WHEN delivery_status != 'ACTIVE' THEN budget_amount ELSE 0 END) as at_risk_budget,
    ROUND(COUNT(DISTINCT CASE WHEN delivery_status = 'ACTIVE' THEN campaign_id END) / COUNT(DISTINCT campaign_id), 2) as health_score
FROM meta_campaign_snapshots
WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
GROUP BY account_name
ORDER BY at_risk_budget DESC;
```

### 5. Cost-Effective Implementation

#### Phase 1: Campaign-Level Indicators (Week 1)
- Add basic delivery flags to campaign snapshots
- Use existing API calls, just add fields
- Minimal cost increase

#### Phase 2: High-Risk Deep Dive (Week 2)
- Only fetch ad set/ad data for:
  - Campaigns > $5,000 daily budget
  - New campaigns (< 24 hours old)
  - Campaigns with recent anomalies
- Store in separate tables

#### Phase 3: Full Hierarchy (Month 2)
- Gradually expand coverage
- Use BigQuery scheduled queries for analysis
- Build ML model to predict delivery issues

### 6. API Rate Limit Management

```python
class RateLimitedFetcher:
    def __init__(self):
        self.calls_per_hour = 200  # Meta's default
        self.call_times = []
    
    def fetch_with_backoff(self, func, *args, **kwargs):
        """Fetch with exponential backoff"""
        for attempt in range(5):
            try:
                self._check_rate_limit()
                result = func(*args, **kwargs)
                self._record_call()
                return result
            except RateLimitError:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
        raise Exception("Rate limit exceeded after retries")
    
    def batch_fetch_adsets(self, campaign_ids):
        """Batch fetch to reduce API calls"""
        # Meta allows up to 50 IDs per request
        for batch in chunks(campaign_ids, 50):
            yield self.fetch_with_backoff(
                AdSet.get_by_ids,
                ids=batch,
                fields=['id', 'campaign_id', 'effective_status']
            )
```

### 7. Storage Optimization

```sql
-- Partition by date and cluster by campaign_id
CREATE TABLE meta_adset_snapshots
PARTITION BY DATE(snapshot_timestamp)
CLUSTER BY campaign_id, account_id
OPTIONS(
    partition_expiration_days=90,  -- Auto-delete old data
    description="Ad set snapshots with automatic expiration"
);

-- Materialized view for current state only
CREATE MATERIALIZED VIEW meta_current_delivery_state AS
SELECT 
    campaign_id,
    MAX(snapshot_timestamp) as last_check,
    ARRAY_AGG(
        STRUCT(adset_id, has_active_ads)
        ORDER BY adset_id
    ) as adsets_status
FROM meta_adset_snapshots
WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
GROUP BY campaign_id;
```

### 8. Alert Priority Matrix

| Budget | Delivery Issue | Priority | Action |
|--------|---------------|----------|---------|
| >$10k | No ad sets | CRITICAL | Immediate alert + auto-pause suggestion |
| >$10k | No ads | CRITICAL | Immediate alert |
| $5-10k | No active ads | HIGH | Alert within 1 hour |
| $1-5k | No active ads | MEDIUM | Daily summary |
| <$1k | Any issue | LOW | Weekly report |

### 9. Dashboard Integration

```python
# Add to dashboard.py
def get_delivery_summary():
    query = """
    SELECT 
        COUNT(DISTINCT campaign_id) as total_campaigns,
        COUNT(DISTINCT CASE WHEN delivery_status = 'ACTIVE' THEN campaign_id END) as active_delivery,
        COUNT(DISTINCT CASE WHEN delivery_status = 'NO_ADSETS' THEN campaign_id END) as no_adsets,
        COUNT(DISTINCT CASE WHEN delivery_status = 'NO_ADS' THEN campaign_id END) as no_ads,
        SUM(CASE WHEN delivery_status != 'ACTIVE' THEN budget_amount ELSE 0 END) as budget_at_risk
    FROM meta_campaign_snapshots
    WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
    """
    return client.query(query).to_dataframe()
```

## Recommended Implementation Order

1. **Start Simple** (Week 1)
   - Add delivery status fields to existing campaign monitoring
   - Basic check: does campaign have > 0 ad sets?
   
2. **Add Intelligence** (Week 2)
   - Implement risk-based deep diving
   - Only check high-budget campaigns fully
   
3. **Scale Gradually** (Month 1)
   - Monitor API usage and costs
   - Adjust thresholds based on findings
   
4. **Optimize** (Month 2)
   - Use BigQuery ML for predictions
   - Implement caching for unchanged data

## Cost Estimate
- Additional API calls: ~20-30% increase
- BigQuery storage: ~2-3x current (still under $100/month)
- Processing time: ~30-40% increase
- ROI: Catching even ONE zombie campaign with $10k/day budget pays for entire system

## Success Metrics
- Zombie campaigns detected per week
- Budget saved from non-delivering campaigns  
- Time to detection (should be < 6 hours)
- False positive rate (should be < 5%)