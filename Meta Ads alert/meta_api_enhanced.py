"""
Enhanced Meta API implementation with delivery status checking
"""

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad

def check_campaign_delivery_status(account: AdAccount, campaign_id: str) -> dict:
    """
    Check if a campaign can actually deliver ads
    Returns detailed delivery status
    """
    campaign = Campaign(campaign_id)
    
    # Get ad sets for this campaign
    adsets = campaign.get_ad_sets(
        fields=['id', 'name', 'status', 'effective_status'],
        params={'limit': 100}
    )
    
    active_adsets = []
    paused_adsets = []
    
    for adset in adsets:
        if adset.get('effective_status') == 'ACTIVE':
            active_adsets.append(adset)
        else:
            paused_adsets.append(adset)
    
    # Check ads in active ad sets
    deliverable_adsets = []
    adsets_without_ads = []
    adsets_with_issues = []
    
    for adset in active_adsets:
        ads = adset.get_ads(
            fields=['id', 'name', 'status', 'effective_status'],
            params={'limit': 100}
        )
        
        active_ads = [ad for ad in ads if ad.get('effective_status') == 'ACTIVE']
        
        if len(list(ads)) == 0:
            adsets_without_ads.append(adset)
        elif len(active_ads) == 0:
            adsets_with_issues.append({
                'adset': adset,
                'total_ads': len(list(ads)),
                'active_ads': 0
            })
        else:
            deliverable_adsets.append({
                'adset': adset,
                'active_ads': len(active_ads)
            })
    
    # Determine overall status
    if len(active_adsets) == 0:
        status = 'NO_ACTIVE_ADSETS'
        status_emoji = '🔴'
        risk_level = 'HIGH'
    elif len(deliverable_adsets) == 0:
        if len(adsets_without_ads) > 0:
            status = 'NO_ADS'
            status_emoji = '🟠'
            risk_level = 'MEDIUM'
        else:
            status = 'ADS_PAUSED'
            status_emoji = '🟡'
            risk_level = 'MEDIUM'
    else:
        status = 'ACTIVE'
        status_emoji = '🟢'
        risk_level = 'LOW'
    
    return {
        'campaign_id': campaign_id,
        'delivery_status': status,
        'status_emoji': status_emoji,
        'risk_level': risk_level,
        'total_adsets': len(list(adsets)),
        'active_adsets': len(active_adsets),
        'paused_adsets': len(paused_adsets),
        'deliverable_adsets': len(deliverable_adsets),
        'adsets_without_ads': len(adsets_without_ads),
        'adsets_with_issues': len(adsets_with_issues),
        'can_deliver': len(deliverable_adsets) > 0,
        'details': {
            'active_adsets': [{'id': a.get('id'), 'name': a.get('name')} for a in active_adsets],
            'adsets_without_ads': [{'id': a.get('id'), 'name': a.get('name')} for a in adsets_without_ads],
            'adsets_with_issues': adsets_with_issues
        }
    }


def get_enhanced_campaign_data(account: AdAccount, campaign_id: str) -> dict:
    """
    Get campaign data with delivery status
    """
    # Get basic campaign info
    campaign = Campaign(campaign_id)
    campaign_data = campaign.api_get(
        fields=[
            'id', 'name', 'status', 'daily_budget', 
            'lifetime_budget', 'created_time', 'objective'
        ]
    )
    
    # Get delivery status
    delivery_status = check_campaign_delivery_status(account, campaign_id)
    
    # Combine data
    enhanced_data = {
        **campaign_data,
        'delivery_check': delivery_status
    }
    
    return enhanced_data


# SQL to add delivery status columns to BigQuery table
ENHANCED_SCHEMA_SQL = """
-- Add delivery status columns to campaign snapshots table
ALTER TABLE `generative-ai-418805.budget_alert.meta_campaign_snapshots`
ADD COLUMN IF NOT EXISTS delivery_status STRING,
ADD COLUMN IF NOT EXISTS active_adsets_count INTEGER,
ADD COLUMN IF NOT EXISTS deliverable_adsets_count INTEGER,
ADD COLUMN IF NOT EXISTS can_deliver BOOLEAN,
ADD COLUMN IF NOT EXISTS delivery_risk_level STRING;

-- Create new table for ad set snapshots with delivery info
CREATE TABLE IF NOT EXISTS `generative-ai-418805.budget_alert.meta_adset_delivery_status` (
  snapshot_id STRING NOT NULL,
  campaign_id STRING NOT NULL,
  adset_id STRING NOT NULL,
  adset_name STRING,
  adset_status STRING,
  has_active_ads BOOLEAN,
  active_ads_count INTEGER,
  total_ads_count INTEGER,
  snapshot_timestamp TIMESTAMP NOT NULL
)
PARTITION BY DATE(snapshot_timestamp)
OPTIONS(
  description="Ad set delivery status for monitoring zombie campaigns"
);

-- Create view for campaigns with delivery issues
CREATE OR REPLACE VIEW `generative-ai-418805.budget_alert.meta_campaigns_delivery_issues` AS
SELECT 
  c.campaign_id,
  c.campaign_name,
  c.account_name,
  c.budget_amount,
  c.budget_type,
  c.delivery_status,
  c.active_adsets_count,
  c.deliverable_adsets_count,
  CASE 
    WHEN c.delivery_status = 'NO_ACTIVE_ADSETS' THEN '🔴 No active ad sets'
    WHEN c.delivery_status = 'NO_ADS' THEN '🟠 Ad sets have no ads'
    WHEN c.delivery_status = 'ADS_PAUSED' THEN '🟡 All ads paused'
    ELSE '🟢 Active'
  END as delivery_message,
  c.budget_amount * 
    CASE 
      WHEN c.delivery_status IN ('NO_ACTIVE_ADSETS', 'NO_ADS') THEN 1.0
      ELSE 0.0
    END as wasted_budget_risk
FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots` c
WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
  AND c.campaign_status = 'ACTIVE'
  AND c.delivery_status IN ('NO_ACTIVE_ADSETS', 'NO_ADS', 'ADS_PAUSED')
ORDER BY wasted_budget_risk DESC;
"""


# Function to generate delivery status summary
def get_delivery_status_display(delivery_check: dict) -> str:
    """
    Generate a user-friendly delivery status display
    """
    status = delivery_check['delivery_status']
    emoji = delivery_check['status_emoji']
    
    if status == 'NO_ACTIVE_ADSETS':
        return f"{emoji} No active ad sets"
    elif status == 'NO_ADS':
        return f"{emoji} Ad sets need ads"
    elif status == 'ADS_PAUSED':
        return f"{emoji} All ads paused"
    elif status == 'ACTIVE':
        active = delivery_check['deliverable_adsets']
        total = delivery_check['total_adsets']
        return f"{emoji} Active ({active}/{total} ad sets)"
    else:
        return f"{emoji} Unknown"


# Example alert message for zombie campaigns
def create_zombie_campaign_alert(campaign_name: str, budget: float, issue: str) -> str:
    """
    Create alert message for campaigns that can't deliver
    """
    return f"""
🧟 **Zombie Campaign Alert**
Campaign: {campaign_name}
Daily Budget: ${budget:,.2f}
Issue: {issue}
Action Required: This campaign has budget allocated but cannot deliver ads!
"""