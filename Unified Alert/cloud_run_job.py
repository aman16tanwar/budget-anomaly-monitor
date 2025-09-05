#!/usr/bin/env python3
"""
Cloud Run Job script for Meta Ads Budget Monitoring
This script runs once when triggered by Cloud Scheduler
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from meta_api_implementation_bigquery import MetaBudgetMonitorBQ

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main function for Cloud Run Job"""
    start_time = datetime.now()
    logger.info(f"🚀 Starting Meta Ads Budget Monitoring Job at {start_time}")
    
    try:
        # Get configuration from environment
        business_id = os.getenv('META_BUSINESS_ID')
        project_id = os.getenv('GCP_PROJECT_ID')
        
        if not business_id:
            logger.error("❌ META_BUSINESS_ID not set in environment variables")
            sys.exit(1)
            
        if not project_id:
            logger.error("❌ GCP_PROJECT_ID not set in environment variables")
            sys.exit(1)
        
        # Log configuration
        logger.info(f"📊 Configuration:")
        logger.info(f"  - Business ID: {business_id}")
        logger.info(f"  - Project ID: {project_id}")
        logger.info(f"  - Dataset: budget_alert")
        logger.info(f"  - Check Interval: {os.getenv('CHECK_INTERVAL_MINUTES', 5)} minutes")
        
        # Initialize monitor
        logger.info("🔍 Initializing Meta Budget Monitor...")
        monitor = MetaBudgetMonitorBQ(business_id, project_id)
        
        # Run monitoring cycle
        logger.info("🔄 Starting monitoring cycle...")
        monitor.run_monitoring_cycle()
        
        # Calculate execution time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Monitoring job completed successfully!")
        logger.info(f"⏱️  Total execution time: {duration:.2f} seconds")
        
        # Exit with success code
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Critical error during monitoring: {str(e)}")
        logger.exception("Full traceback:")
        
        # Exit with error code
        sys.exit(1)

if __name__ == "__main__":
    main()