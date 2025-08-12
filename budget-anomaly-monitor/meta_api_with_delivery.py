"""
Enhanced Meta API implementation with ad set and ad level monitoring
Optimized for performance and cost efficiency
"""

import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
from decimal import Decimal

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from google.cloud import bigquery
import requests


class MetaBudgetMonitorWithDelivery:
    """Enhanced monitor with delivery status checking"""
    
    def __init__(self, business_id: str, project_id: str):
        self.business_id = business_id
        self.project_id = project_id
        self.dataset_id = "budget_alert"
        
        # Initialize Meta API
        FacebookAdsApi.init(
            app_id=os.getenv('META_APP_ID'),
            app_secret=os.getenv('META_APP_SECRET'),
            access_token=os.getenv('META_ACCESS_TOKEN')
        )
        
        # Initialize BigQuery
        self.bq_client = bigquery.Client(project=project_id)
        
        # Configuration with delivery thresholds
        self.config = {
            'thresholds': {
                'high_budget_daily': 5000,
                'medium_budget_daily': 1000,
                'always_check_delivery_above': 10000,  # Always check delivery for campaigns above this
                'delivery_check_hours': 6,  # Check delivery every 6 hours
            },
            'api_limits': {
                'calls_per_hour': 200,
                'batch_size': 50,
            }
        }
        
        self.api_calls = []
    
    def should_check_delivery(self, campaign_data: Dict, previous_state: Optional[Dict]) -> bool:
        """Determine if we should check delivery status for this campaign"""
        budget = campaign_data.get('daily_budget', 0) or campaign_data.get('lifetime_budget', 0)
        if budget:
            budget = float(budget) / 100  # Convert from cents
        
        # Always check high budget campaigns
        if budget >= self.config['thresholds']['always_check_delivery_above']:
            return True
        
        # Check new campaigns
        if not previous_state:
            return True
        
        # Check if it's been a while since last check
        if previous_state and 'last_delivery_check' in previous_state:
            last_check = datetime.fromisoformat(previous_state['last_delivery_check'])
            if datetime.now() - last_check > timedelta(hours=self.config['thresholds']['delivery_check_hours']):
                return True
        
        # Check if budget recently increased significantly
        if previous_state and previous_state.get('current_budget'):
            previous_budget = float(previous_state['current_budget'])
            if previous_budget > 0 and budget / previous_budget > 1.5:
                return True
        
        return False
    
    def check_campaign_delivery_status(self, campaign_id: str) -> Dict:
        """
        Efficiently check if a campaign can deliver ads
        Returns delivery status with minimal API calls
        """
        delivery_result = {
            'campaign_id': campaign_id,
            'checked_at': datetime.now().isoformat(),
            'can_deliver': False,
            'delivery_status': 'UNKNOWN',
            'active_adsets_count': 0,
            'deliverable_adsets_count': 0,
            'total_adsets': 0,
            'issue_details': []
        }
        
        try:
            # Get ad sets for this campaign (limit to reduce API calls)
            campaign = Campaign(campaign_id)
            adsets = list(campaign.get_ad_sets(
                fields=['id', 'name', 'effective_status', 'status'],
                params={'limit': 100}  # Most campaigns have < 100 ad sets
            ))
            
            delivery_result['total_adsets'] = len(adsets)
            
            if not adsets:
                delivery_result['delivery_status'] = 'NO_ADSETS'
                delivery_result['issue_details'].append('Campaign has no ad sets')
                return delivery_result
            
            # Count active ad sets
            active_adsets = [a for a in adsets if a.get('effective_status') == 'ACTIVE']
            delivery_result['active_adsets_count'] = len(active_adsets)
            
            if not active_adsets:
                delivery_result['delivery_status'] = 'NO_ACTIVE_ADSETS'
                delivery_result['issue_details'].append(f'All {len(adsets)} ad sets are paused or archived')
                return delivery_result
            
            # For efficiency, sample check ads (check first few active ad sets)
            sample_size = min(3, len(active_adsets))  # Check up to 3 ad sets
            deliverable_count = 0
            
            for adset in active_adsets[:sample_size]:
                # Check if ad set has active ads
                ads = list(adset.get_ads(
                    fields=['effective_status'],
                    params={'limit': 10}  # Just need to know if any exist
                ))
                
                if not ads:
                    delivery_result['issue_details'].append(f'Ad set "{adset.get("name")}" has no ads')
                else:
                    active_ads = [a for a in ads if a.get('effective_status') == 'ACTIVE']
                    if active_ads:
                        deliverable_count += 1
                    else:
                        delivery_result['issue_details'].append(f'Ad set "{adset.get("name")}" has {len(ads)} ads but none are active')
            
            # Extrapolate based on sample
            estimated_deliverable = int((deliverable_count / sample_size) * len(active_adsets))
            delivery_result['deliverable_adsets_count'] = estimated_deliverable
            
            if deliverable_count == 0:
                delivery_result['delivery_status'] = 'NO_DELIVERABLE_ADSETS'
                delivery_result['issue_details'].append('Checked ad sets have no active ads')
            elif deliverable_count < sample_size:
                delivery_result['delivery_status'] = 'PARTIALLY_DELIVERABLE'
                delivery_result['can_deliver'] = True
                delivery_result['issue_details'].append(f'Some ad sets may not have active ads')
            else:
                delivery_result['delivery_status'] = 'ACTIVE'
                delivery_result['can_deliver'] = True
            
            return delivery_result
            
        except Exception as e:
            delivery_result['delivery_status'] = 'CHECK_ERROR'
            delivery_result['issue_details'].append(f'Error checking delivery: {str(e)}')
            return delivery_result
    
    def monitor_campaigns_with_delivery(self, account: AdAccount) -> List[Dict]:
        """Monitor campaigns with smart delivery checking"""
        anomalies = []
        snapshots = []
        adset_snapshots = []
        
        # Get active campaigns
        campaigns = account.get_campaigns(
            fields=[
                'id', 'name', 'status', 'daily_budget', 
                'lifetime_budget', 'created_time', 'objective'
            ],
            params={'effective_status': ['ACTIVE'], 'limit': 500}
        )
        
        current_timestamp = datetime.now()
        
        for campaign in campaigns:
            campaign_id = campaign.get('id')
            
            # Get previous state
            previous_state = self.get_current_state_from_bq(campaign_id, 'campaign')
            
            # Process campaign data
            campaign_data = self.process_campaign_data(campaign, account, previous_state)
            
            # Check if we should inspect delivery
            if self.should_check_delivery(campaign, previous_state):
                delivery_status = self.check_campaign_delivery_status(campaign_id)
                
                # Update campaign data with delivery info
                campaign_data.update({
                    'delivery_status': delivery_status['delivery_status'],
                    'can_deliver': delivery_status['can_deliver'],
                    'active_adsets_count': delivery_status['active_adsets_count'],
                    'deliverable_adsets_count': delivery_status['deliverable_adsets_count'],
                    'last_delivery_check': delivery_status['checked_at']
                })
                
                # Check for zombie campaign anomaly
                if not delivery_status['can_deliver'] and campaign_data['budget_amount'] > self.config['thresholds']['medium_budget_daily']:
                    anomaly = {
                        'anomaly_type': 'CRITICAL',
                        'anomaly_category': 'zombie_campaign',
                        'level': 'campaign',
                        'account_id': account.get('id'),
                        'account_name': account.get('name'),
                        'campaign_id': campaign_id,
                        'campaign_name': campaign.get('name'),
                        'message': f'Campaign cannot deliver: {delivery_status["delivery_status"]}',
                        'current_budget': campaign_data['budget_amount'],
                        'delivery_issues': delivery_status['issue_details'],
                        'risk_score': min(0.9, campaign_data['budget_amount'] / 10000),  # Higher budget = higher risk
                        'potential_daily_waste': campaign_data['budget_amount'] if campaign_data['budget_type'] == 'daily' else 0
                    }
                    anomalies.append(anomaly)
                
                # Store ad set snapshots if we found issues
                if delivery_status['issue_details']:
                    self.store_delivery_diagnostics(campaign_id, delivery_status)
            
            snapshots.append(campaign_data)
        
        # Batch insert data
        self.insert_campaign_snapshots(snapshots)
        
        return anomalies
    
    def process_campaign_data(self, campaign: Campaign, account: AdAccount, previous_state: Optional[Dict]) -> Dict:
        """Process campaign data with delivery fields"""
        campaign_id = campaign.get('id')
        
        # Get budget
        current_budget = campaign.get('daily_budget') or campaign.get('lifetime_budget', 0)
        if current_budget:
            current_budget = float(current_budget) / 100
        
        # Base campaign data
        data = {
            'snapshot_id': str(uuid.uuid4()),
            'campaign_id': campaign_id,
            'account_id': account.get('id'),
            'account_name': account.get('name'),
            'campaign_name': campaign.get('name'),
            'campaign_status': campaign.get('status'),
            'budget_amount': current_budget,
            'budget_type': 'daily' if campaign.get('daily_budget') else 'lifetime',
            'budget_currency': account.get('currency', 'USD'),
            'created_time': self._parse_meta_timestamp(campaign.get('created_time')),
            'snapshot_timestamp': datetime.now().isoformat(),
            'objective': campaign.get('objective'),
            'is_new_campaign': previous_state is None,
            'previous_budget_amount': previous_state.get('current_budget') if previous_state else None,
            # Delivery fields (will be updated if checked)
            'delivery_status': previous_state.get('delivery_status', 'NOT_CHECKED') if previous_state else 'NOT_CHECKED',
            'can_deliver': previous_state.get('can_deliver', True) if previous_state else True,
            'active_adsets_count': previous_state.get('active_adsets_count', 0) if previous_state else 0,
            'deliverable_adsets_count': previous_state.get('deliverable_adsets_count', 0) if previous_state else 0,
            'last_delivery_check': previous_state.get('last_delivery_check') if previous_state else None
        }
        
        # Calculate budget change
        if previous_state and previous_state.get('current_budget'):
            prev_budget = float(previous_state['current_budget'])
            if prev_budget > 0:
                data['budget_change_percentage'] = ((current_budget - prev_budget) / prev_budget) * 100
        
        return data
    
    def store_delivery_diagnostics(self, campaign_id: str, delivery_status: Dict):
        """Store detailed delivery diagnostics for problematic campaigns"""
        table_id = f"{self.project_id}.{self.dataset_id}.meta_delivery_diagnostics"
        
        diagnostic_record = {
            'diagnostic_id': str(uuid.uuid4()),
            'campaign_id': campaign_id,
            'checked_at': delivery_status['checked_at'],
            'delivery_status': delivery_status['delivery_status'],
            'can_deliver': delivery_status['can_deliver'],
            'total_adsets': delivery_status['total_adsets'],
            'active_adsets': delivery_status['active_adsets_count'],
            'deliverable_adsets': delivery_status['deliverable_adsets_count'],
            'issues': ', '.join(delivery_status['issue_details']),
            'issue_count': len(delivery_status['issue_details'])
        }
        
        try:
            errors = self.bq_client.insert_rows_json(table_id, [diagnostic_record])
            if errors:
                print(f"Error storing diagnostics: {errors}")
        except Exception as e:
            print(f"Error storing diagnostics: {e}")
    
    def create_enhanced_alert_message(self, anomalies: List[Dict]) -> Dict:
        """Create enhanced alert with delivery issues highlighted"""
        # Separate zombie campaigns from other anomalies
        zombie_campaigns = [a for a in anomalies if a.get('anomaly_category') == 'zombie_campaign']
        other_anomalies = [a for a in anomalies if a.get('anomaly_category') != 'zombie_campaign']
        
        card = {
            "cards": [{
                "header": {
                    "title": "🚨 Meta Ads Budget Alert",
                    "subtitle": f"Detected {len(anomalies)} issues requiring attention"
                },
                "sections": []
            }]
        }
        
        # Zombie campaigns section (highest priority)
        if zombie_campaigns:
            zombie_section = {
                "header": "🧟 ZOMBIE CAMPAIGNS - CANNOT DELIVER ADS",
                "widgets": []
            }
            
            total_waste = sum(z.get('potential_daily_waste', 0) for z in zombie_campaigns)
            
            # Summary widget
            zombie_section["widgets"].append({
                "textParagraph": {
                    "text": f"<b>Found {len(zombie_campaigns)} campaigns with ${total_waste:,.2f} daily budget at risk!</b>"
                }
            })
            
            # Individual zombies
            for zombie in zombie_campaigns[:3]:  # Show top 3
                widget = {
                    "keyValue": {
                        "topLabel": zombie['campaign_name'],
                        "content": f"${zombie['current_budget']:,.2f} daily - {zombie['message']}",
                        "contentMultiline": True,
                        "bottomLabel": f"Issues: {', '.join(zombie.get('delivery_issues', []))[:100]}..."
                    }
                }
                zombie_section["widgets"].append(widget)
            
            card["cards"][0]["sections"].append(zombie_section)
        
        # Other critical anomalies
        if other_anomalies:
            critical = [a for a in other_anomalies if a['anomaly_type'] == 'CRITICAL']
            if critical:
                critical_section = {
                    "header": "⛔ OTHER CRITICAL ALERTS",
                    "widgets": []
                }
                
                for anomaly in critical[:3]:
                    widget = {
                        "keyValue": {
                            "topLabel": f"{anomaly['anomaly_category'].replace('_', ' ').title()}",
                            "content": f"{anomaly['campaign_name']}: {anomaly['message']}",
                            "bottomLabel": f"Account: {anomaly['account_name']}"
                        }
                    }
                    critical_section["widgets"].append(widget)
                
                card["cards"][0]["sections"].append(critical_section)
        
        return card
    
    def get_current_state_from_bq(self, entity_id: str, entity_type: str) -> Optional[Dict]:
        """Get current state with delivery info"""
        query = f"""
        SELECT 
            entity_id,
            current_budget,
            current_status,
            last_seen_timestamp,
            has_recent_anomaly,
            delivery_status,
            can_deliver,
            active_adsets_count,
            deliverable_adsets_count,
            last_delivery_check
        FROM `{self.project_id}.{self.dataset_id}.meta_current_state`
        WHERE entity_id = @entity_id
        AND entity_type = @entity_type
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("entity_id", "STRING", entity_id),
                bigquery.ScalarQueryParameter("entity_type", "STRING", entity_type),
            ]
        )
        
        try:
            results = self.bq_client.query(query, job_config=job_config).to_dataframe()
            if len(results) > 0:
                return results.iloc[0].to_dict()
        except:
            pass
        
        return None
    
    def _parse_meta_timestamp(self, timestamp_str: str) -> Optional[str]:
        """Parse Meta timestamp to BigQuery format"""
        if not timestamp_str:
            return None
        
        try:
            # Remove timezone offset
            import re
            clean_timestamp = re.sub(r'[+-]\d{4}$', '', timestamp_str)
            dt = datetime.strptime(clean_timestamp, '%Y-%m-%dT%H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None


# Enhanced BigQuery schema
ENHANCED_SCHEMA_SQL = """
-- Add delivery columns to campaign snapshots
ALTER TABLE `generative-ai-418805.budget_alert.meta_campaign_snapshots`
ADD COLUMN IF NOT EXISTS delivery_status STRING,
ADD COLUMN IF NOT EXISTS can_deliver BOOLEAN,
ADD COLUMN IF NOT EXISTS active_adsets_count INTEGER,
ADD COLUMN IF NOT EXISTS deliverable_adsets_count INTEGER,
ADD COLUMN IF NOT EXISTS last_delivery_check TIMESTAMP;

-- Create delivery diagnostics table
CREATE TABLE IF NOT EXISTS `generative-ai-418805.budget_alert.meta_delivery_diagnostics` (
  diagnostic_id STRING NOT NULL,
  campaign_id STRING NOT NULL,
  checked_at TIMESTAMP NOT NULL,
  delivery_status STRING,
  can_deliver BOOLEAN,
  total_adsets INTEGER,
  active_adsets INTEGER,
  deliverable_adsets INTEGER,
  issues STRING,
  issue_count INTEGER
)
PARTITION BY DATE(checked_at)
OPTIONS(
  description="Detailed delivery diagnostics for campaigns with issues"
);

-- Update current state table
ALTER TABLE `generative-ai-418805.budget_alert.meta_current_state`
ADD COLUMN IF NOT EXISTS delivery_status STRING,
ADD COLUMN IF NOT EXISTS can_deliver BOOLEAN,
ADD COLUMN IF NOT EXISTS active_adsets_count INTEGER,
ADD COLUMN IF NOT EXISTS deliverable_adsets_count INTEGER,
ADD COLUMN IF NOT EXISTS last_delivery_check TIMESTAMP;

-- Create view for zombie campaigns
CREATE OR REPLACE VIEW `generative-ai-418805.budget_alert.meta_zombie_campaigns_view` AS
SELECT 
    c.campaign_id,
    c.campaign_name,
    c.account_name,
    c.budget_amount,
    c.budget_type,
    c.delivery_status,
    c.active_adsets_count,
    c.deliverable_adsets_count,
    c.last_delivery_check,
    CASE 
        WHEN c.budget_type = 'daily' THEN c.budget_amount * 30
        ELSE c.budget_amount
    END as monthly_waste_risk,
    d.issues as delivery_issues
FROM `generative-ai-418805.budget_alert.meta_campaign_snapshots` c
LEFT JOIN `generative-ai-418805.budget_alert.meta_delivery_diagnostics` d
    ON c.campaign_id = d.campaign_id
    AND DATE(c.snapshot_timestamp) = DATE(d.checked_at)
WHERE DATE(c.snapshot_timestamp) = CURRENT_DATE()
    AND c.campaign_status = 'ACTIVE'
    AND c.can_deliver = FALSE
    AND c.budget_amount > 500
ORDER BY monthly_waste_risk DESC;
"""