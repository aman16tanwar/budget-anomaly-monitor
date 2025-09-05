"""
Direct monitoring script - runs without the API server
"""
import os
from dotenv import load_dotenv
from meta_api_implementation_bigquery import MetaBudgetMonitorBQ

# Load environment variables
load_dotenv()

def run_direct_monitoring():
    """Run monitoring directly without API"""
    print("🚀 Starting Meta Ads Budget Monitoring (Direct Mode)...")
    
    # Get configuration from environment
    business_id = os.getenv('META_BUSINESS_ID')
    project_id = os.getenv('GCP_PROJECT_ID')
    
    if not business_id:
        print("❌ Error: META_BUSINESS_ID not set in .env file")
        return
        
    if not project_id:
        print("❌ Error: GCP_PROJECT_ID not set in .env file")
        return
    
    print(f"📊 Business ID: {business_id}")
    print(f"📊 Project ID: {project_id}")
    print(f"📊 Dataset: budget_alert")
    
    try:
        # Initialize monitor
        print("\n🔍 Initializing Meta Budget Monitor...")
        monitor = MetaBudgetMonitorBQ(business_id, project_id)
        
        # Run monitoring cycle
        print("\n🔄 Running monitoring cycle...")
        monitor.run_monitoring_cycle()
        
        print("\n✅ Monitoring complete! Check your Google Chat for any alerts.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_direct_monitoring()