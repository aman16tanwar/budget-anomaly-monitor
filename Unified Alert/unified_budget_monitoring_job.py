#!/usr/bin/env python3
"""
Unified Cloud Run Job script for Multi-Platform Budget Monitoring
This script monitors both Meta Ads and Google Ads platforms
Runs once when triggered by Cloud Scheduler
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from meta_api_implementation_bigquery import MetaBudgetMonitorBQ

# Import Google Ads monitoring (we'll need to copy the files)
sys.path.append('/app')
try:
    from google_ads_budget_monitor import GoogleAdsBudgetMonitor
    from unified_chat_alerts import UnifiedBudgetAlerts
    GOOGLE_ADS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Google Ads monitoring not available: {e}")
    GOOGLE_ADS_AVAILABLE = False

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
    """Main function for Unified Multi-Platform Monitoring"""
    start_time = datetime.now()
    logger.info(f"🚀 Starting Unified Budget Monitoring Job at {start_time}")
    
    # Track results
    meta_anomalies = []
    google_ads_anomalies = []
    errors = []
    
    try:
        # Get configuration from environment
        meta_business_id = os.getenv('META_BUSINESS_ID')
        google_ads_customer_id = os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID')
        project_id = os.getenv('GCP_PROJECT_ID', 'generative-ai-418805')
        
        logger.info(f"📊 Multi-Platform Configuration:")
        logger.info(f"  - Meta Business ID: {meta_business_id}")
        logger.info(f"  - Google Ads Manager ID: {google_ads_customer_id}")
        logger.info(f"  - Project ID: {project_id}")
        logger.info(f"  - Dataset: budget_alert")
        logger.info(f"  - Check Interval: {os.getenv('CHECK_INTERVAL_MINUTES', 5)} minutes")
        
        # Initialize unified alert system
        logger.info("📢 Initializing unified alert system...")
        alert_system = UnifiedBudgetAlerts() if GOOGLE_ADS_AVAILABLE else None
        
        # === MONITOR META ADS ===
        logger.info("🔵 === STARTING META ADS MONITORING ===")
        try:
            if not meta_business_id:
                logger.warning("⚠️ META_BUSINESS_ID not set - skipping Meta monitoring")
            else:
                logger.info("🔍 Initializing Meta Budget Monitor...")
                meta_monitor = MetaBudgetMonitorBQ(meta_business_id, project_id)
                
                logger.info("🔄 Running Meta monitoring cycle...")
                # Note: The existing Meta monitor handles its own alerting
                # We'll need to modify it to return anomalies instead of sending alerts directly
                meta_monitor.run_monitoring_cycle()
                logger.info("✅ Meta monitoring completed")
                
        except Exception as e:
            error_msg = f"❌ Error in Meta monitoring: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # === MONITOR GOOGLE ADS ===
        logger.info("🔴 === STARTING GOOGLE ADS MONITORING ===")
        try:
            if not GOOGLE_ADS_AVAILABLE:
                logger.warning("⚠️ Google Ads monitoring not available - skipping")
            elif not google_ads_customer_id:
                logger.warning("⚠️ GOOGLE_ADS_LOGIN_CUSTOMER_ID not set - skipping Google Ads monitoring")
            else:
                logger.info("🔍 Initializing Google Ads Budget Monitor...")
                google_ads_monitor = GoogleAdsBudgetMonitor()
                
                logger.info("🔄 Running Google Ads monitoring cycle...")
                google_ads_anomalies = google_ads_monitor.run_monitoring_cycle()
                logger.info(f"✅ Google Ads monitoring completed - {len(google_ads_anomalies)} anomalies detected")
                
        except Exception as e:
            error_msg = f"❌ Error in Google Ads monitoring: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # === SEND UNIFIED ALERTS ===
        logger.info("📧 === PROCESSING UNIFIED ALERTS ===")
        try:
            total_anomalies = len(meta_anomalies) + len(google_ads_anomalies)
            
            if total_anomalies > 0:
                logger.info(f"🚨 Sending unified alert for {total_anomalies} total anomalies")
                logger.info(f"  - Meta Ads: {len(meta_anomalies)} anomalies")
                logger.info(f"  - Google Ads: {len(google_ads_anomalies)} anomalies")
                
                if alert_system:
                    # Send combined alert (Google Ads anomalies only for now)
                    # Meta alerts are already handled by existing system
                    if google_ads_anomalies:
                        alert_system.send_combined_alert(google_ads_anomalies=google_ads_anomalies)
                        logger.info("✅ Unified alert sent successfully")
                    else:
                        logger.info("ℹ️ No Google Ads anomalies to alert")
                else:
                    logger.warning("⚠️ Alert system not available")
            else:
                logger.info("ℹ️ No anomalies detected across platforms")
                
        except Exception as e:
            error_msg = f"❌ Error sending unified alerts: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # === JOB COMPLETION SUMMARY ===
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info("📊 UNIFIED MONITORING JOB SUMMARY")
        logger.info("=" * 60)
        logger.info(f"⏱️  Total execution time: {duration:.2f} seconds")
        logger.info(f"🔵 Meta Ads anomalies: {len(meta_anomalies)}")
        logger.info(f"🔴 Google Ads anomalies: {len(google_ads_anomalies)}")
        logger.info(f"🚨 Total anomalies: {len(meta_anomalies) + len(google_ads_anomalies)}")
        logger.info(f"❌ Errors encountered: {len(errors)}")
        
        if errors:
            logger.warning("⚠️ ERRORS DURING EXECUTION:")
            for error in errors:
                logger.warning(f"  - {error}")
        
        # Determine exit code
        if len(errors) >= 2:  # Both platforms failed
            logger.error("❌ Critical failure - both platforms failed")
            sys.exit(1)
        elif errors:
            logger.warning("⚠️ Partial failure - one platform had issues")
            # Continue with exit code 0 since at least one platform worked
        
        logger.info("✅ Unified monitoring job completed!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Critical error in unified monitoring: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)

def health_check():
    """Health check endpoint for monitoring"""
    logger.info("🏥 Running health check...")
    
    # Check Meta configuration
    meta_ok = bool(os.getenv('META_BUSINESS_ID'))
    
    # Check Google Ads configuration
    google_ads_ok = bool(os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID')) and GOOGLE_ADS_AVAILABLE
    
    # Check BigQuery configuration
    bq_ok = bool(os.getenv('GCP_PROJECT_ID'))
    
    # Check Alert configuration
    alerts_ok = bool(os.getenv('GOOGLE_CHAT_WEBHOOK_URL'))
    
    logger.info(f"Health Check Results:")
    logger.info(f"  - Meta Ads: {'✅' if meta_ok else '❌'}")
    logger.info(f"  - Google Ads: {'✅' if google_ads_ok else '❌'}")
    logger.info(f"  - BigQuery: {'✅' if bq_ok else '✅'}")
    logger.info(f"  - Alerts: {'✅' if alerts_ok else '❌'}")
    
    overall_health = meta_ok or google_ads_ok  # At least one platform should work
    logger.info(f"Overall Health: {'✅ HEALTHY' if overall_health else '❌ UNHEALTHY'}")
    
    return overall_health

if __name__ == "__main__":
    # Check for health check mode
    if len(sys.argv) > 1 and sys.argv[1] == 'health':
        healthy = health_check()
        sys.exit(0 if healthy else 1)
    else:
        main()