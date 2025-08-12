"""
Simple delivery status check - just ad set and ad status
"""

from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

def get_simple_delivery_status(campaign_id: str) -> dict:
    """
    Simple check: Does this campaign have active ad sets with active ads?
    """
    campaign = Campaign(campaign_id)
    
    # Get all ad sets
    adsets = campaign.get_ad_sets(
        fields=['id', 'name', 'effective_status'],
        params={'limit': 100}
    )
    
    result = {
        'campaign_id': campaign_id,
        'total_adsets': 0,
        'active_adsets': 0,
        'adsets_with_active_ads': 0,
        'can_deliver': False,
        'status': 'CHECKING'
    }
    
    adset_list = list(adsets)
    result['total_adsets'] = len(adset_list)
    
    # No ad sets = can't deliver
    if result['total_adsets'] == 0:
        result['status'] = '🔴 No ad sets'
        return result
    
    # Check each ad set
    for adset in adset_list:
        if adset.get('effective_status') == 'ACTIVE':
            result['active_adsets'] += 1
            
            # Check if this ad set has active ads
            ads = adset.get_ads(
                fields=['effective_status'],
                params={'limit': 50}
            )
            
            active_ads = [ad for ad in ads if ad.get('effective_status') == 'ACTIVE']
            if active_ads:
                result['adsets_with_active_ads'] += 1
    
    # Determine overall status
    if result['active_adsets'] == 0:
        result['status'] = '🟠 All ad sets paused'
    elif result['adsets_with_active_ads'] == 0:
        result['status'] = '🟡 No active ads'
    else:
        result['status'] = '🟢 Active'
        result['can_deliver'] = True
    
    return result


# Simple BigQuery schema additions
SIMPLE_DELIVERY_SCHEMA = """
-- Just add these columns to campaign snapshots
ALTER TABLE `generative-ai-418805.budget_alert.meta_campaign_snapshots`
ADD COLUMN IF NOT EXISTS total_adsets INTEGER,
ADD COLUMN IF NOT EXISTS active_adsets INTEGER,
ADD COLUMN IF NOT EXISTS adsets_with_active_ads INTEGER,
ADD COLUMN IF NOT EXISTS delivery_status_simple STRING;

-- Simple view to find problem campaigns
CREATE OR REPLACE VIEW `generative-ai-418805.budget_alert.meta_delivery_issues_simple` AS
SELECT 
    campaign_id,
    campaign_name,
    account_name,
    budget_amount,
    budget_type,
    total_adsets,
    active_adsets,
    adsets_with_active_ads,
    delivery_status_simple,
    CASE 
        WHEN delivery_status_simple LIKE '🔴%' THEN 'CRITICAL - No ad sets'
        WHEN delivery_status_simple LIKE '🟠%' THEN 'HIGH - Ad sets paused'
        WHEN delivery_status_simple LIKE '🟡%' THEN 'MEDIUM - No active ads'
        ELSE 'OK'
    END as issue_severity,
    budget_amount * CASE WHEN budget_type = 'daily' THEN 30 ELSE 1 END as monthly_budget_at_risk
FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots`
WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
    AND campaign_status = 'ACTIVE'
    AND delivery_status_simple NOT LIKE '🟢%'
    AND budget_amount > 1000
ORDER BY monthly_budget_at_risk DESC;
"""


# Integration into existing monitor
def enhance_campaign_snapshot_with_delivery(campaign_data: dict, campaign_id: str) -> dict:
    """
    Add delivery status to existing campaign snapshot
    """
    try:
        delivery = get_simple_delivery_status(campaign_id)
        
        campaign_data.update({
            'total_adsets': delivery['total_adsets'],
            'active_adsets': delivery['active_adsets'],
            'adsets_with_active_ads': delivery['adsets_with_active_ads'],
            'delivery_status_simple': delivery['status']
        })
        
        # Flag as anomaly if high budget and can't deliver
        if not delivery['can_deliver'] and campaign_data.get('budget_amount', 0) > 5000:
            return {
                'has_delivery_issue': True,
                'issue_type': delivery['status'],
                'wasted_budget': campaign_data.get('budget_amount', 0)
            }
    except Exception as e:
        campaign_data['delivery_status_simple'] = f'❓ Check failed: {str(e)}'
    
    return campaign_data


# Simple alert for zombie campaigns
def create_zombie_alert(campaign_name: str, budget: float, issue: str) -> str:
    """Create simple alert message"""
    if '🔴' in issue:
        emoji = '🚨'
        severity = 'CRITICAL'
    elif '🟠' in issue:
        emoji = '⚠️'
        severity = 'WARNING'
    else:
        emoji = '⚡'
        severity = 'NOTICE'
    
    return f"""
{emoji} **{severity}: Zombie Campaign Detected**
Campaign: {campaign_name}
Budget: ${budget:,.2f}
Issue: {issue}
Action: This campaign has budget but cannot deliver ads!
"""


# Dashboard query for summary
DELIVERY_SUMMARY_QUERY = """
SELECT 
    COUNT(*) as total_campaigns,
    COUNT(CASE WHEN delivery_status_simple LIKE '🟢%' THEN 1 END) as active_delivery,
    COUNT(CASE WHEN delivery_status_simple LIKE '🔴%' THEN 1 END) as no_adsets,
    COUNT(CASE WHEN delivery_status_simple LIKE '🟠%' THEN 1 END) as paused_adsets,
    COUNT(CASE WHEN delivery_status_simple LIKE '🟡%' THEN 1 END) as no_active_ads,
    SUM(CASE 
        WHEN delivery_status_simple NOT LIKE '🟢%' 
        THEN budget_amount 
        ELSE 0 
    END) as daily_budget_at_risk
FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots`
WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
    AND campaign_status = 'ACTIVE'
"""