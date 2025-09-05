from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import secretmanager
import os
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv, find_dotenv
import logging
from typing import List, Dict, Any
import pytz
from unified_chat_alerts import UnifiedBudgetAlerts

load_dotenv(find_dotenv(usecwd=True), override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleAdsBudgetMonitor:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "generative-ai-418805")
        self.dataset_id = "budget_alert"
        self.manager_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "9820928751")
        
        # Initialize Google Ads client
        self.google_ads_client = self._setup_google_ads_client()
        
        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=self.project_id)
        
        # Initialize unified alert system
        self.alert_system = UnifiedBudgetAlerts()
        
        # Budget thresholds (matching Meta implementation)
        self.budget_increase_warning = float(os.getenv("BUDGET_INCREASE_WARNING", "1.5"))
        self.budget_increase_critical = float(os.getenv("BUDGET_INCREASE_CRITICAL", "3.0"))
        self.new_campaign_max_budget = float(os.getenv("NEW_CAMPAIGN_MAX_BUDGET", "5000"))
        
        # Create tables if they don't exist
        self._ensure_tables_exist()
        
    def _setup_google_ads_client(self) -> GoogleAdsClient:
        """Initialize Google Ads client with credentials"""
        config = {
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "login_customer_id": self.manager_customer_id,
            "use_proto_plus": True,
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
        }
        return GoogleAdsClient.load_from_dict(config)
    
    def _ensure_tables_exist(self):
        """Create BigQuery tables if they don't exist (matching Meta structure)"""
        
        # Google Ads Campaign Snapshots table
        snapshots_schema = [
            bigquery.SchemaField("account_id", "STRING"),
            bigquery.SchemaField("campaign_id", "STRING"),
            bigquery.SchemaField("campaign_name", "STRING"),
            bigquery.SchemaField("budget_amount", "FLOAT64"),
            bigquery.SchemaField("currency", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("delivery_method", "STRING"),
            bigquery.SchemaField("snapshot_time", "TIMESTAMP"),
            bigquery.SchemaField("created_date", "DATE"),
            bigquery.SchemaField("business_hours_flag", "BOOLEAN"),
        ]
        
        # Google Ads Anomalies table  
        anomalies_schema = [
            bigquery.SchemaField("anomaly_id", "STRING"),
            bigquery.SchemaField("account_id", "STRING"),
            bigquery.SchemaField("campaign_id", "STRING"),
            bigquery.SchemaField("campaign_name", "STRING"),
            bigquery.SchemaField("anomaly_category", "STRING"),
            bigquery.SchemaField("previous_budget", "FLOAT64"),
            bigquery.SchemaField("current_budget", "FLOAT64"),
            bigquery.SchemaField("increase_ratio", "FLOAT64"),
            bigquery.SchemaField("risk_score", "FLOAT64"),
            bigquery.SchemaField("detected_time", "TIMESTAMP"),
            bigquery.SchemaField("business_hours_context", "STRING"),
            bigquery.SchemaField("acknowledged", "BOOLEAN"),
            bigquery.SchemaField("acknowledged_by", "STRING"),
            bigquery.SchemaField("acknowledged_at", "TIMESTAMP"),
            bigquery.SchemaField("alert_sent", "BOOLEAN"),
            bigquery.SchemaField("alert_sent_at", "TIMESTAMP"),
        ]
        
        # Google Ads Current State table
        current_state_schema = [
            bigquery.SchemaField("account_id", "STRING"),
            bigquery.SchemaField("campaign_id", "STRING"),
            bigquery.SchemaField("campaign_name", "STRING"),
            bigquery.SchemaField("current_budget", "FLOAT64"),
            bigquery.SchemaField("currency", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("last_updated", "TIMESTAMP"),
        ]
        
        tables_to_create = [
            ("google_ads_campaign_snapshots", snapshots_schema),
            ("google_ads_anomalies", anomalies_schema),
            ("google_ads_current_state", current_state_schema),
        ]
        
        for table_name, schema in tables_to_create:
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            
            try:
                self.bq_client.get_table(table_id)
                logger.info(f"Table {table_name} already exists")
            except Exception:
                table = bigquery.Table(table_id, schema=schema)
                
                # Add partitioning for snapshots table
                if "snapshots" in table_name:
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field="snapshot_time"
                    )
                
                table = self.bq_client.create_table(table)
                logger.info(f"Created table {table_name}")
    
    def get_active_accounts(self) -> List[str]:
        """Get list of active customer accounts from manager account"""
        try:
            ga_service = self.google_ads_client.get_service("GoogleAdsService")
            query = """
                SELECT customer_client.client_customer,
                       customer_client.id,
                       customer_client.status,
                       customer_client.descriptive_name
                FROM customer_client 
                WHERE customer_client.level >= 1 
                  AND customer_client.status = 'ENABLED'
                ORDER BY customer_client.descriptive_name
            """
            
            response = ga_service.search_stream(customer_id=self.manager_customer_id, query=query)
            active_accounts = []
            
            for chunk in response:
                for row in chunk.results:
                    customer_client = row.customer_client
                    if customer_client.status.name == "ENABLED":
                        active_accounts.append(str(customer_client.id))
            
            logger.info(f"Found {len(active_accounts)} active accounts")
            return active_accounts
            
        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error getting accounts: {ex}")
            return []
    
    def fetch_campaign_budgets(self, customer_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch campaign budget data for all active accounts"""
        all_campaigns = []
        ga_service = self.google_ads_client.get_service("GoogleAdsService")
        
        # Query to get campaign budget information
        query = """
            SELECT 
                customer.id,
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.start_date,
                campaign_budget.id,
                campaign_budget.amount_micros,
                campaign_budget.delivery_method,
                customer.currency_code
            FROM campaign
            WHERE campaign.status IN ('ENABLED', 'PAUSED')
        """
        
        for customer_id in customer_ids:
            try:
                response = ga_service.search_stream(customer_id=customer_id, query=query)
                
                for chunk in response:
                    for row in chunk.results:
                        campaign = row.campaign
                        campaign_budget = row.campaign_budget
                        customer = row.customer
                        
                        # Convert micros to dollars
                        budget_amount = campaign_budget.amount_micros / 1_000_000 if campaign_budget.amount_micros else 0.0
                        
                        campaign_data = {
                            "account_id": str(customer.id),
                            "campaign_id": str(campaign.id),
                            "campaign_name": campaign.name,
                            "budget_amount": budget_amount,
                            "currency": customer.currency_code,
                            "status": campaign.status.name,
                            "delivery_method": campaign_budget.delivery_method.name,
                            "created_date": campaign.start_date,
                            "snapshot_time": datetime.now(timezone.utc),
                            "business_hours_flag": self._is_business_hours()
                        }
                        
                        all_campaigns.append(campaign_data)
                        
            except GoogleAdsException as ex:
                logger.error(f"Error fetching campaigns for customer {customer_id}: {ex}")
                continue
        
        logger.info(f"Fetched {len(all_campaigns)} campaigns")
        return all_campaigns
    
    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours (8 AM - 6 PM PST)"""
        pst = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(pst)
        hour = current_time.hour
        return 8 <= hour < 18
    
    def get_current_state(self) -> Dict[str, Dict]:
        """Get current state of campaigns from BigQuery"""
        query = f"""
            SELECT account_id, campaign_id, campaign_name, current_budget, currency, status
            FROM `{self.project_id}.{self.dataset_id}.google_ads_current_state`
        """
        
        try:
            df = pd.read_gbq(query, project_id=self.project_id)
            current_state = {}
            
            for _, row in df.iterrows():
                key = f"{row['account_id']}_{row['campaign_id']}"
                current_state[key] = {
                    'account_id': row['account_id'],
                    'campaign_id': row['campaign_id'],
                    'campaign_name': row['campaign_name'],
                    'current_budget': row['current_budget'],
                    'currency': row['currency'],
                    'status': row['status']
                }
            
            return current_state
            
        except Exception as ex:
            logger.error(f"Error getting current state: {ex}")
            return {}
    
    def detect_budget_anomalies(self, campaigns: List[Dict], current_state: Dict) -> List[Dict]:
        """Detect budget anomalies using same logic as Meta implementation"""
        anomalies = []
        current_time = datetime.now(timezone.utc)
        
        for campaign in campaigns:
            account_id = campaign['account_id']
            campaign_id = campaign['campaign_id']
            current_budget = campaign['budget_amount']
            
            state_key = f"{account_id}_{campaign_id}"
            
            # Check for new campaigns with high budget
            if state_key not in current_state:
                if current_budget >= self.new_campaign_max_budget:
                    anomaly_id = f"google_ads_new_{account_id}_{campaign_id}_{int(current_time.timestamp())}"
                    
                    anomalies.append({
                        'anomaly_id': anomaly_id,
                        'account_id': account_id,
                        'campaign_id': campaign_id,
                        'campaign_name': campaign['campaign_name'],
                        'anomaly_category': 'new_campaign',
                        'previous_budget': 0.0,
                        'current_budget': current_budget,
                        'increase_ratio': float('inf'),
                        'risk_score': 0.8,
                        'detected_time': current_time,
                        'business_hours_context': 'business_hours' if campaign['business_hours_flag'] else 'after_hours',
                        'acknowledged': False,
                        'alert_sent': False
                    })
            else:
                # Check for budget increases
                previous_budget = current_state[state_key]['current_budget']
                
                if previous_budget > 0 and current_budget > previous_budget:
                    increase_ratio = current_budget / previous_budget
                    
                    if increase_ratio >= self.budget_increase_warning:
                        anomaly_category = 'budget_increase_critical' if increase_ratio >= self.budget_increase_critical else 'budget_increase_warning'
                        risk_score = 0.8 if increase_ratio >= self.budget_increase_critical else 0.5
                        
                        anomaly_id = f"google_ads_budget_{account_id}_{campaign_id}_{int(current_time.timestamp())}"
                        
                        anomalies.append({
                            'anomaly_id': anomaly_id,
                            'account_id': account_id,
                            'campaign_id': campaign_id,
                            'campaign_name': campaign['campaign_name'],
                            'anomaly_category': anomaly_category,
                            'previous_budget': previous_budget,
                            'current_budget': current_budget,
                            'increase_ratio': increase_ratio,
                            'risk_score': risk_score,
                            'detected_time': current_time,
                            'business_hours_context': 'business_hours' if campaign['business_hours_flag'] else 'after_hours',
                            'acknowledged': False,
                            'alert_sent': False
                        })
        
        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies
    
    def update_bigquery_tables(self, campaigns: List[Dict], anomalies: List[Dict]):
        """Update BigQuery tables with new data"""
        
        # Update snapshots table
        if campaigns:
            snapshots_df = pd.DataFrame(campaigns)
            snapshots_df.to_gbq(
                f"{self.dataset_id}.google_ads_campaign_snapshots",
                project_id=self.project_id,
                if_exists='append'
            )
            logger.info(f"Updated snapshots table with {len(campaigns)} campaigns")
        
        # Update anomalies table
        if anomalies:
            anomalies_df = pd.DataFrame(anomalies)
            anomalies_df.to_gbq(
                f"{self.dataset_id}.google_ads_anomalies",
                project_id=self.project_id,
                if_exists='append'
            )
            logger.info(f"Updated anomalies table with {len(anomalies)} anomalies")
        
        # Update current state table
        if campaigns:
            current_state_data = []
            for campaign in campaigns:
                current_state_data.append({
                    'account_id': campaign['account_id'],
                    'campaign_id': campaign['campaign_id'],
                    'campaign_name': campaign['campaign_name'],
                    'current_budget': campaign['budget_amount'],
                    'currency': campaign['currency'],
                    'status': campaign['status'],
                    'last_updated': datetime.now(timezone.utc)
                })
            
            # Use MERGE operation to update existing records or insert new ones
            current_state_df = pd.DataFrame(current_state_data)
            current_state_df.to_gbq(
                f"{self.dataset_id}.google_ads_current_state",
                project_id=self.project_id,
                if_exists='replace'  # Replace entire table for current state
            )
            logger.info(f"Updated current state table with {len(current_state_data)} campaigns")
    
    def run_monitoring_cycle(self):
        """Run complete monitoring cycle"""
        logger.info("Starting Google Ads budget monitoring cycle")
        
        try:
            # Get active accounts
            active_accounts = self.get_active_accounts()
            if not active_accounts:
                logger.warning("No active accounts found")
                return []
            
            # Fetch campaign budgets
            campaigns = self.fetch_campaign_budgets(active_accounts)
            if not campaigns:
                logger.warning("No campaigns found")
                return []
            
            # Get current state
            current_state = self.get_current_state()
            
            # Detect anomalies
            anomalies = self.detect_budget_anomalies(campaigns, current_state)
            
            # Update BigQuery tables
            self.update_bigquery_tables(campaigns, anomalies)
            
            # Send alerts if anomalies found
            if anomalies:
                logger.info(f"Sending Google Chat alerts for {len(anomalies)} anomalies")
                self.alert_system.send_combined_alert(google_ads_anomalies=anomalies)
            
            logger.info(f"Monitoring cycle complete: {len(campaigns)} campaigns, {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as ex:
            logger.error(f"Error in monitoring cycle: {ex}")
            raise

if __name__ == "__main__":
    monitor = GoogleAdsBudgetMonitor()
    anomalies = monitor.run_monitoring_cycle()
    
    if anomalies:
        print(f"Found {len(anomalies)} anomalies:")
        for anomaly in anomalies:
            print(f"- {anomaly['anomaly_category']}: {anomaly['campaign_name']} ({anomaly['current_budget']} {anomaly.get('currency', 'CAD')})")
    else:
        print("No anomalies detected")