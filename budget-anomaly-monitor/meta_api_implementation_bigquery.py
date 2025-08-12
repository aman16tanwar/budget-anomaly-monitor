"""
Meta Ads Budget Anomaly Detection System - BigQuery Version
Monitors ACTIVE campaigns and ad sets, stores data in BigQuery for ML/Analytics

Table Naming Convention:
- All Meta/Facebook related tables are prefixed with 'meta_'
- This allows for future expansion to other platforms like:
  - google_ads_campaign_snapshots
  - dv360_campaign_snapshots
  - etc.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
from google.cloud import bigquery
from google.cloud import secretmanager
import requests
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

class MetaBudgetMonitorBQ:
    def __init__(self, business_id: str, project_id: str, dataset_id: str = "budget_alert"):
        """
        Initialize the Meta Budget Monitor with BigQuery
        
        Args:
            business_id: Meta Business Manager ID
            project_id: Google Cloud Project ID
            dataset_id: BigQuery dataset ID
        """
        self.business_id = business_id
        self.project_id = project_id
        self.dataset_id = dataset_id
        
        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=project_id)
        
        # Ensure dataset exists
        self._ensure_dataset_exists()
        
        # Initialize Meta API
        self._init_meta_api()
        
        # Load configuration
        self.config = self._load_config()
        
    def _ensure_dataset_exists(self):
        """Check if BigQuery dataset exists"""
        dataset_id = f"{self.project_id}.{self.dataset_id}"
        
        try:
            dataset = self.bq_client.get_dataset(dataset_id)
            print(f"✅ Using existing dataset: {self.dataset_id}")
        except Exception as e:
            print(f"Dataset check: {e}")
            # Since the dataset already exists, we'll continue
            print(f"✅ Dataset {self.dataset_id} is ready")
    
    def _init_meta_api(self):
        """Initialize Meta API with credentials from environment or Secret Manager"""
        # Try environment variables first (for local development)
        access_token = os.getenv('META_ACCESS_TOKEN')
        app_secret = os.getenv('META_APP_SECRET')
        app_id = os.getenv('META_APP_ID')
        
        # If not in environment, try Secret Manager (for production)
        if not all([access_token, app_secret, app_id]):
            try:
                client = secretmanager.SecretManagerServiceClient()
                
                if not access_token:
                    access_token_name = f"projects/{self.project_id}/secrets/meta-access-token/versions/latest"
                    response = client.access_secret_version(request={"name": access_token_name})
                    access_token = response.payload.data.decode('UTF-8')
                
                if not app_secret:
                    app_secret_name = f"projects/{self.project_id}/secrets/meta-app-secret/versions/latest"
                    response = client.access_secret_version(request={"name": app_secret_name})
                    app_secret = response.payload.data.decode('UTF-8')
                
                if not app_id:
                    app_id_name = f"projects/{self.project_id}/secrets/meta-app-id/versions/latest"
                    response = client.access_secret_version(request={"name": app_id_name})
                    app_id = response.payload.data.decode('UTF-8')
            except Exception as e:
                print(f"Warning: Could not access Secret Manager: {e}")
        
        if not all([access_token, app_secret, app_id]):
            raise ValueError("Missing Meta API credentials")
            
        FacebookAdsApi.init(app_id, app_secret, access_token)
        
    def _convert_decimal(self, value):
        """Convert Decimal to float for JSON serialization"""
        if isinstance(value, Decimal):
            return float(value)
        return value
    
    def _prepare_for_bigquery(self, data: Dict) -> Dict:
        """Convert all Decimal values and datetime objects in a dictionary for BigQuery"""
        result = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                result[key] = float(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = self._prepare_for_bigquery(value)
            elif isinstance(value, list):
                result[key] = [self._prepare_for_bigquery(item) if isinstance(item, dict) else 
                              self._convert_decimal(item) for item in value]
            else:
                result[key] = value
        return result
    
    def _parse_meta_timestamp(self, timestamp_str: str) -> Optional[str]:
        """Convert Meta timestamp to BigQuery format"""
        if not timestamp_str:
            return None
        try:
            # Parse Meta's timestamp format: 2025-07-08T17:05:44-0700
            from datetime import datetime
            import re
            
            # Remove timezone offset for parsing
            clean_timestamp = re.sub(r'[+-]\d{4}$', '', timestamp_str)
            dt = datetime.strptime(clean_timestamp, '%Y-%m-%dT%H:%M:%S')
            
            # Return in BigQuery format
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Error parsing timestamp {timestamp_str}: {e}")
            return None
    
    def _parse_meta_timestamp_to_datetime(self, timestamp_str: str) -> Optional[datetime]:
        """Convert Meta timestamp to datetime object for comparison"""
        if not timestamp_str:
            return None
        try:
            # Parse Meta's timestamp format: 2025-07-08T17:05:44-0700
            import re
            
            # Remove timezone offset for parsing
            clean_timestamp = re.sub(r'[+-]\d{4}$', '', timestamp_str)
            return datetime.strptime(clean_timestamp, '%Y-%m-%dT%H:%M:%S')
        except Exception as e:
            print(f"Error parsing timestamp to datetime {timestamp_str}: {e}")
            return None
    
    def _load_config(self) -> Dict:
        """Load monitoring configuration"""
        return {
            "thresholds": {
                "budget_increase_warning": float(os.getenv('BUDGET_INCREASE_WARNING', 1.5)),
                "budget_increase_critical": float(os.getenv('BUDGET_INCREASE_CRITICAL', 3.0)),
                "new_campaign_max_budget": float(os.getenv('NEW_CAMPAIGN_MAX_BUDGET', 5000)),
                "new_adset_max_budget": float(os.getenv('NEW_ADSET_MAX_BUDGET', 2000)),
                "daily_spend_velocity": 2.0,
                "delivery_check_threshold": float(os.getenv('DELIVERY_CHECK_THRESHOLD', 5000)),
            },
            "monitoring": {
                "check_interval_minutes": int(os.getenv('CHECK_INTERVAL_MINUTES', 5)),
                "campaign_status_filter": ["ACTIVE"],
                "adset_status_filter": ["ACTIVE"],
            },
            "google_chat": {
                "webhook_url": os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
            },
            "business_hours": {
                "start": int(os.getenv('BUSINESS_HOURS_START', 8)),
                "end": int(os.getenv('BUSINESS_HOURS_END', 18)),
                "timezone": os.getenv('TIMEZONE', 'America/Toronto')
            }
        }
    
    def check_simple_delivery_status(self, campaign_id: str) -> Dict:
        """
        Simple check: Does this campaign have active ad sets with active ads?
        """
        from facebook_business.adobjects.campaign import Campaign
        
        campaign = Campaign(campaign_id)
        
        result = {
            'campaign_id': campaign_id,
            'total_adsets': 0,
            'active_adsets': 0,
            'adsets_with_active_ads': 0,
            'can_deliver': False,
            'status': 'CHECKING'
        }
        
        try:
            # Get all ad sets
            adsets = campaign.get_ad_sets(
                fields=['id', 'name', 'effective_status'],
                params={'limit': 100}
            )
            
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
                        params={'limit': 10}  # Just check first 10 ads
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
            
        except Exception as e:
            result['status'] = f'❌ Error: {str(e)}'
            return result
    
    def get_current_state_from_bq(self, entity_id: str, entity_type: str) -> Optional[Dict]:
        """Get current state from BigQuery for comparison"""
        query = f"""
        SELECT 
            current_budget,
            previous_budget,
            last_seen_timestamp,
            consecutive_anomaly_count
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
            query_job = self.bq_client.query(query, job_config=job_config)
            results = list(query_job)
            if results:
                return dict(results[0])
        except Exception as e:
            print(f"Error querying current state: {e}")
        
        return None
    
    def update_current_state(self, updates: List[Dict]):
        """Update current state in BigQuery using MERGE"""
        if not updates:
            return
            
        # Convert Decimals to floats
        prepared_updates = [self._prepare_for_bigquery(u) for u in updates]
            
        # Create temporary table with updates
        temp_table_id = f"{self.project_id}.{self.dataset_id}.temp_state_updates_{uuid.uuid4().hex[:8]}"
        
        # Insert updates into temp table
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("entity_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("entity_type", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("account_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("current_budget", "NUMERIC"),
                bigquery.SchemaField("current_status", "STRING"),
                bigquery.SchemaField("last_seen_timestamp", "TIMESTAMP"),
                bigquery.SchemaField("previous_budget", "NUMERIC"),
                bigquery.SchemaField("previous_status", "STRING"),
                bigquery.SchemaField("previous_check_timestamp", "TIMESTAMP"),
                bigquery.SchemaField("has_recent_anomaly", "BOOLEAN"),
                bigquery.SchemaField("consecutive_anomaly_count", "INTEGER"),
            ],
            write_disposition="WRITE_TRUNCATE",
        )
        
        try:
            # Load data to temp table
            job = self.bq_client.load_table_from_json(prepared_updates, temp_table_id, job_config=job_config)
            job.result()  # Wait for job to complete
            
            # Merge temp table with current state
            merge_query = f"""
            MERGE `{self.project_id}.{self.dataset_id}.meta_current_state` T
            USING `{temp_table_id}` S
            ON T.entity_id = S.entity_id AND T.entity_type = S.entity_type
            WHEN MATCHED THEN
                UPDATE SET 
                    T.current_budget = S.current_budget,
                    T.current_status = S.current_status,
                    T.last_seen_timestamp = S.last_seen_timestamp,
                    T.previous_budget = S.previous_budget,
                    T.previous_status = S.previous_status,
                    T.previous_check_timestamp = S.previous_check_timestamp,
                    T.has_recent_anomaly = S.has_recent_anomaly,
                    T.consecutive_anomaly_count = S.consecutive_anomaly_count
            WHEN NOT MATCHED THEN
                INSERT (entity_id, entity_type, account_id, current_budget, current_status, 
                       last_seen_timestamp, previous_budget, previous_status, previous_check_timestamp,
                       has_recent_anomaly, consecutive_anomaly_count, is_being_monitored)
                VALUES (S.entity_id, S.entity_type, S.account_id, S.current_budget, S.current_status,
                       S.last_seen_timestamp, S.previous_budget, S.previous_status, S.previous_check_timestamp,
                       S.has_recent_anomaly, S.consecutive_anomaly_count, TRUE)
            """
            
            self.bq_client.query(merge_query).result()
            
            # Clean up temp table
            self.bq_client.delete_table(temp_table_id, not_found_ok=True)
            
        except Exception as e:
            print(f"Error updating current state: {e}")
            # Clean up temp table on error
            self.bq_client.delete_table(temp_table_id, not_found_ok=True)
    
    def insert_campaign_snapshots(self, snapshots: List[Dict]):
        """Insert campaign snapshots into BigQuery"""
        if not snapshots:
            return
            
        table_id = f"{self.project_id}.{self.dataset_id}.meta_campaign_snapshots"
        
        # Convert Decimals to floats
        prepared_snapshots = [self._prepare_for_bigquery(s) for s in snapshots]
        
        try:
            errors = self.bq_client.insert_rows_json(table_id, prepared_snapshots)
            if errors:
                print(f"Error inserting campaign snapshots: {errors}")
            else:
                print(f"✅ Inserted {len(snapshots)} campaign snapshots")
        except Exception as e:
            print(f"Error inserting campaign snapshots: {e}")
    
    def insert_anomalies(self, anomalies: List[Dict]):
        """Insert detected anomalies into BigQuery"""
        if not anomalies:
            return
            
        table_id = f"{self.project_id}.{self.dataset_id}.meta_anomalies"
        
        # Add anomaly_id and timestamps
        for anomaly in anomalies:
            anomaly['anomaly_id'] = str(uuid.uuid4())
            anomaly['detected_at'] = datetime.now().isoformat()
            anomaly['alert_sent'] = False
            anomaly['acknowledged'] = False
            anomaly['false_positive'] = False
        
        try:
            errors = self.bq_client.insert_rows_json(table_id, anomalies)
            if errors:
                print(f"Error inserting anomalies: {errors}")
            else:
                print(f"✅ Inserted {len(anomalies)} anomalies")
        except Exception as e:
            print(f"Error inserting anomalies: {e}")
    
    def get_active_accounts(self) -> List[AdAccount]:
        """Get all ad accounts under the Business Manager"""
        business = Business(self.business_id)
        
        accounts = business.get_owned_ad_accounts(
            fields=[
                'id',
                'name', 
                'account_status',
                'spend_cap',
                'amount_spent',
                'currency'
            ]
        )
        
        # Filter for active accounts only
        active_accounts = []
        for account in accounts:
            if account.get('account_status') == 1:  # 1 = ACTIVE
                active_accounts.append(account)
                
        print(f"Found {len(active_accounts)} active accounts under Business ID {self.business_id}")
        return active_accounts
    
    def monitor_active_campaigns(self, account: AdAccount) -> List[Dict]:
        """Monitor only ACTIVE campaigns in the account"""
        anomalies = []
        snapshots = []
        state_updates = []
        
        # Get ACTIVE campaigns only
        campaigns = account.get_campaigns(
            fields=[
                'id',
                'name',
                'status',
                'daily_budget',
                'lifetime_budget',
                'created_time',
                'updated_time',
                'start_time',
                'stop_time',
                'objective',
                'bid_strategy'
            ],
            params={
                'effective_status': ['ACTIVE'],
                'limit': 500
            }
        )
        
        current_timestamp = datetime.now()
        
        for campaign in campaigns:
            campaign_id = campaign.get('id')
            
            # Check if campaign has ended
            stop_time = campaign.get('stop_time')
            if stop_time:
                # Parse stop time
                stop_datetime = self._parse_meta_timestamp_to_datetime(stop_time)
                if stop_datetime and stop_datetime < current_timestamp:
                    # Campaign has ended, skip it
                    print(f"Skipping ended campaign: {campaign.get('name')} (ended {stop_time})")
                    continue
            
            # Get historical data from BigQuery
            previous_state = self.get_current_state_from_bq(campaign_id, 'campaign')
            
            # Determine budget
            current_budget = campaign.get('daily_budget') or campaign.get('lifetime_budget', 0)
            if current_budget:
                current_budget = float(current_budget) / 100  # Convert from cents
            
            # Create snapshot for BigQuery
            snapshot = {
                'snapshot_id': str(uuid.uuid4()),
                'campaign_id': campaign_id,
                'account_id': account.get('id'),
                'account_name': account.get('name'),
                'campaign_name': campaign.get('name'),
                'campaign_status': campaign.get('status'),
                'budget_amount': current_budget,
                'budget_type': 'daily' if campaign.get('daily_budget') else 'lifetime',
                'budget_currency': account.get('currency', 'USD'),
                'previous_budget_amount': previous_state['current_budget'] if previous_state else None,
                'budget_change_percentage': 0,
                'is_new_campaign': previous_state is None,
                'created_time': self._parse_meta_timestamp(campaign.get('created_time')),
                'snapshot_timestamp': current_timestamp.isoformat(),
                'objective': campaign.get('objective'),
                'bid_strategy': campaign.get('bid_strategy'),
                'start_time': self._parse_meta_timestamp(campaign.get('start_time')),
                'stop_time': self._parse_meta_timestamp(campaign.get('stop_time')),
                # Initialize delivery fields
                'total_adsets': 0,
                'active_adsets': 0,
                'adsets_with_active_ads': 0,
                'delivery_status_simple': '❓ Not checked'
            }
            
            # Check if campaign hasn't started yet
            start_time = campaign.get('start_time')
            if start_time:
                start_datetime = self._parse_meta_timestamp_to_datetime(start_time)
                if start_datetime and start_datetime > current_timestamp:
                    snapshot['delivery_status_simple'] = '⏰ Not started'
                    snapshot['is_future_campaign'] = True
            
            # Check delivery status for high budget campaigns (skip if not started)
            if current_budget >= self.config['thresholds']['delivery_check_threshold'] and not snapshot.get('is_future_campaign'):
                try:
                    delivery_status = self.check_simple_delivery_status(campaign_id)
                    snapshot.update({
                        'total_adsets': delivery_status['total_adsets'],
                        'active_adsets': delivery_status['active_adsets'],
                        'adsets_with_active_ads': delivery_status['adsets_with_active_ads'],
                        'delivery_status_simple': delivery_status['status']
                    })
                    
                    # Add zombie campaign anomaly if can't deliver
                    if not delivery_status['can_deliver']:
                        anomalies.append({
                            'anomaly_type': 'CRITICAL',
                            'anomaly_category': 'zombie_campaign',
                            'level': 'campaign',
                            'account_id': account.get('id'),
                            'account_name': account.get('name'),
                            'campaign_id': campaign_id,
                            'campaign_name': campaign.get('name'),
                            'message': f'Campaign cannot deliver: {delivery_status["status"]}',
                            'current_budget': current_budget,
                            'risk_score': 0.8,
                            'delivery_status': delivery_status['status'],
                            'total_adsets': delivery_status['total_adsets'],
                            'active_adsets': delivery_status['active_adsets']
                        })
                except Exception as e:
                    print(f"Error checking delivery for campaign {campaign_id}: {e}")
                    snapshot['delivery_status_simple'] = '❓ Check failed'
            
            # Check for anomalies
            if previous_state is None:
                # New campaign
                created_time_str = campaign.get('created_time')
                # Parse timestamp with timezone
                import re
                clean_timestamp = re.sub(r'[+-]\d{4}$', '', created_time_str)
                created_time = datetime.strptime(clean_timestamp, '%Y-%m-%dT%H:%M:%S')
                time_since_creation = datetime.now() - created_time
                
                if time_since_creation < timedelta(hours=1):
                    if current_budget > self.config['thresholds']['new_campaign_max_budget']:
                        anomalies.append({
                            'anomaly_type': 'CRITICAL',
                            'anomaly_category': 'new_campaign',
                            'level': 'campaign',
                            'account_id': account.get('id'),
                            'account_name': account.get('name'),
                            'campaign_id': campaign_id,
                            'campaign_name': campaign.get('name'),
                            'message': f'New campaign with unusually high budget: ${current_budget:,.2f} CAD',
                            'current_budget': current_budget,
                            'risk_score': 0.9,
                            'created_outside_business_hours': created_time.hour < self.config['business_hours']['start'] or created_time.hour > self.config['business_hours']['end'],
                            'time_since_creation_minutes': int(time_since_creation.total_seconds() / 60)
                        })
            else:
                # Existing campaign - check for budget changes
                previous_budget = self._convert_decimal(previous_state.get('current_budget', 0))
                
                if current_budget and previous_budget and current_budget != previous_budget:
                    increase_ratio = current_budget / previous_budget if previous_budget > 0 else float('inf')
                    snapshot['budget_change_percentage'] = (increase_ratio - 1) * 100
                    
                    if increase_ratio >= self.config['thresholds']['budget_increase_critical']:
                        anomalies.append({
                            'anomaly_type': 'CRITICAL',
                            'anomaly_category': 'budget_increase',
                            'level': 'campaign',
                            'account_id': account.get('id'),
                            'account_name': account.get('name'),
                            'campaign_id': campaign_id,
                            'campaign_name': campaign.get('name'),
                            'message': f'Budget increased by {((increase_ratio - 1) * 100):.0f}%',
                            'current_budget': current_budget,
                            'previous_budget': previous_budget,
                            'budget_increase_percentage': (increase_ratio - 1) * 100,
                            'risk_score': 0.8,
                            'created_outside_business_hours': datetime.now().hour < self.config['business_hours']['start'] or datetime.now().hour > self.config['business_hours']['end']
                        })
            
            # Prepare state update
            state_updates.append({
                'entity_id': campaign_id,
                'entity_type': 'campaign',
                'account_id': account.get('id'),
                'current_budget': current_budget,
                'current_status': campaign.get('status'),
                'last_seen_timestamp': current_timestamp.isoformat(),
                'previous_budget': previous_state['current_budget'] if previous_state else current_budget,
                'previous_status': campaign.get('status'),
                'previous_check_timestamp': previous_state['last_seen_timestamp'] if previous_state else current_timestamp.isoformat(),
                'has_recent_anomaly': len([a for a in anomalies if a['campaign_id'] == campaign_id]) > 0,
                'consecutive_anomaly_count': (previous_state['consecutive_anomaly_count'] + 1 if previous_state and len([a for a in anomalies if a['campaign_id'] == campaign_id]) > 0 else 0) if previous_state else 0
            })
            
            snapshots.append(snapshot)
        
        # Insert data into BigQuery
        self.insert_campaign_snapshots(snapshots)
        self.update_current_state(state_updates)
        
        return anomalies
    
    def send_google_chat_alert(self, anomalies: List[Dict]):
        """Send alerts to Google Chat Space"""
        if not anomalies:
            return
        
        webhook_url = self.config['google_chat']['webhook_url']
        if not webhook_url:
            print("❌ Google Chat webhook URL not configured")
            return
        
        # Group anomalies by severity
        critical_anomalies = [a for a in anomalies if a['anomaly_type'] == 'CRITICAL']
        warning_anomalies = [a for a in anomalies if a['anomaly_type'] == 'WARNING']
        
        # Create card message
        card = {
            "cards": [{
                "header": {
                    "title": "🚨 Meta Ads Budget Alert",
                    "subtitle": f"Detected {len(anomalies)} anomalies",
                    "imageUrl": "https://www.facebook.com/images/fb_icon_325x325.png"
                },
                "sections": []
            }]
        }
        
        # Add critical anomalies section
        if critical_anomalies:
            critical_section = {
                "header": "⛔ CRITICAL ALERTS",
                "widgets": []
            }
            
            for anomaly in critical_anomalies[:3]:
                widget = {
                    "keyValue": {
                        "topLabel": f"{anomaly['level'].upper()}: {anomaly.get('campaign_name') or anomaly.get('adset_name')}",
                        "content": anomaly['message'],
                        "contentMultiline": True,
                        "button": {
                            "textButton": {
                                "text": "VIEW IN ADS MANAGER",
                                "onClick": {
                                    "openLink": {
                                        "url": f"https://business.facebook.com/adsmanager/manage/campaigns?act={anomaly['account_id']}"
                                    }
                                }
                            }
                        }
                    }
                }
                critical_section["widgets"].append(widget)
            
            card["cards"][0]["sections"].append(critical_section)
        
        # Add ML insights section
        insights_section = {
            "widgets": [{
                "textParagraph": {
                    "text": f"💡 <b>Insights:</b> Anomalies detected during {'business hours' if datetime.now().hour >= self.config['business_hours']['start'] and datetime.now().hour <= self.config['business_hours']['end'] else 'off-hours'}. Data stored in BigQuery for ML analysis."
                }
            }]
        }
        card["cards"][0]["sections"].append(insights_section)
        
        # Send to Google Chat
        try:
            response = requests.post(webhook_url, json=card)
            if response.status_code == 200:
                print(f"✅ Alert sent to Google Chat")
                # Mark anomalies as alert_sent in BigQuery
                self._mark_alerts_sent(anomalies)
            else:
                print(f"❌ Failed to send Google Chat alert: {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending Google Chat alert: {e}")
    
    def _mark_alerts_sent(self, anomalies: List[Dict]):
        """Update BigQuery to mark alerts as sent"""
        if not anomalies:
            return
            
        anomaly_ids = [a['anomaly_id'] for a in anomalies if 'anomaly_id' in a]
        if not anomaly_ids:
            return
            
        query = f"""
        UPDATE `{self.project_id}.{self.dataset_id}.meta_anomalies`
        SET alert_sent = TRUE,
            alert_sent_at = CURRENT_TIMESTAMP()
        WHERE anomaly_id IN UNNEST(@anomaly_ids)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("anomaly_ids", "STRING", anomaly_ids),
            ]
        )
        
        try:
            self.bq_client.query(query, job_config=job_config).result()
        except Exception as e:
            print(f"Error marking alerts as sent: {e}")
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        print(f"Starting monitoring cycle for Business ID: {self.business_id}")
        all_anomalies = []
        
        try:
            # Get all active accounts
            active_accounts = self.get_active_accounts()
            
            for account in active_accounts:
                print(f"Checking account: {account.get('name')} ({account.get('id')})")
                
                # Monitor active campaigns
                campaign_anomalies = self.monitor_active_campaigns(account)
                all_anomalies.extend(campaign_anomalies)
                
                # TODO: Add ad set monitoring
            
            # Insert anomalies to BigQuery
            if all_anomalies:
                self.insert_anomalies(all_anomalies)
                self.send_google_chat_alert(all_anomalies)
            
            # Update account activity patterns for ML
            self._update_account_activity()
            
            print(f"✅ Monitoring cycle complete. Found {len(all_anomalies)} anomalies.")
            
        except Exception as e:
            print(f"❌ Error during monitoring cycle: {str(e)}")
            raise e
    
    def _update_account_activity(self):
        """Update daily account activity patterns for ML training"""
        query = f"""
        INSERT INTO `{self.project_id}.{self.dataset_id}.meta_account_activity`
        SELECT 
            account_id,
            CURRENT_DATE() as activity_date,
            COUNT(DISTINCT campaign_id) as total_campaigns,
            SUM(CAST(is_new_campaign AS INT64)) as new_campaigns_created,
            COUNT(DISTINCT CASE WHEN budget_change_percentage > 0 THEN campaign_id END) as campaigns_with_budget_changes,
            SUM(CASE WHEN budget_change_percentage > 0 THEN 1 ELSE 0 END) as total_budget_changes,
            SUM(CASE WHEN budget_type = 'daily' THEN budget_amount ELSE 0 END) as total_daily_budget,
            AVG(budget_amount) as avg_campaign_budget,
            MAX(budget_amount) as max_campaign_budget,
            SUM(CASE WHEN budget_change_percentage > 0 THEN budget_amount - previous_budget_amount ELSE 0 END) as total_budget_increase_amount,
            MIN(EXTRACT(HOUR FROM snapshot_timestamp)) as earliest_activity_hour,
            MAX(EXTRACT(HOUR FROM snapshot_timestamp)) as latest_activity_hour,
            SUM(CASE WHEN EXTRACT(HOUR FROM snapshot_timestamp) < 8 OR EXTRACT(HOUR FROM snapshot_timestamp) > 18 THEN 1 ELSE 0 END) as activities_outside_business_hours,
            EXTRACT(DAYOFWEEK FROM CURRENT_DATE()) IN (1, 7) as is_weekend,
            FALSE as is_holiday  -- TODO: Add holiday calendar
        FROM `{self.project_id}.{self.dataset_id}.meta_campaign_snapshots`
        WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
        GROUP BY account_id
        """
        
        try:
            self.bq_client.query(query).result()
            print("✅ Updated account activity patterns")
        except Exception as e:
            print(f"Error updating account activity: {e}")


# Cloud Function entry point for BigQuery version
def monitor_meta_budgets_bq(request):
    """
    Cloud Function to monitor Meta budgets using BigQuery
    """
    business_id = os.getenv('META_BUSINESS_ID', request.args.get('business_id'))
    project_id = os.getenv('GCP_PROJECT')
    
    if not business_id:
        return {'error': 'No business_id provided'}, 400
    
    # Initialize and run monitor
    monitor = MetaBudgetMonitorBQ(business_id, project_id)
    monitor.run_monitoring_cycle()
    
    return {'status': 'success', 'business_id': business_id}