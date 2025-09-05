#!/usr/bin/env python3
"""
Test script to send dummy Google Ads and Meta Ads alerts to Google Chat
This helps visualize how the alerts will look in the chat space
"""
import os
import sys
from datetime import datetime, timezone

# Load environment variables manually
def load_env_manually():
    """Load environment variables from .env file"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value
    except Exception as e:
        print(f"Error loading .env: {e}")

# Load environment
load_env_manually()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from unified_chat_alerts import UnifiedBudgetAlerts
except ImportError:
    print("❌ Cannot import unified_chat_alerts. Please ensure the module is available.")
    sys.exit(1)

def create_dummy_meta_anomalies():
    """Create realistic Meta Ads dummy anomalies"""
    current_time = datetime.now(timezone.utc)
    
    return [
        {
            'anomaly_id': 'meta_new_123_456_1693934400',
            'account_id': '523709941772517',
            'campaign_id': '23851234567890',
            'adset_id': '23851234567891',
            'campaign_name': 'Summer Sale - Retargeting Campaign',
            'adset_name': 'US Warm Audience - Age 25-45',
            'anomaly_category': 'new_adset',
            'previous_budget': 0.0,
            'current_budget': 250.0,
            'currency': 'CAD',
            'increase_ratio': float('inf'),
            'risk_score': 0.8,
            'detected_time': current_time,
            'business_hours_context': 'after_hours',
            'acknowledged': False,
            'alert_sent': False
        },
        {
            'anomaly_id': 'meta_budget_123_789_1693934500',
            'account_id': '523709941772517',
            'campaign_id': '23851234567892',
            'adset_id': '23851234567893',
            'campaign_name': 'Q4 Holiday Promotions',
            'adset_name': 'Canada Lookalike - Purchase Intent',
            'anomaly_category': 'budget_increase_critical',
            'previous_budget': 150.0,
            'current_budget': 600.0,
            'currency': 'CAD',
            'increase_ratio': 4.0,
            'risk_score': 0.9,
            'detected_time': current_time,
            'business_hours_context': 'business_hours',
            'acknowledged': False,
            'alert_sent': False
        },
        {
            'anomaly_id': 'meta_budget_123_101112_1693934600',
            'account_id': '523709941772517', 
            'campaign_id': '23851234567894',
            'adset_id': '23851234567895',
            'campaign_name': 'Back to School - Electronics',
            'adset_name': 'Mobile Users - Interest Targeting',
            'anomaly_category': 'budget_increase_warning',
            'previous_budget': 100.0,
            'current_budget': 200.0,
            'currency': 'CAD',
            'increase_ratio': 2.0,
            'risk_score': 0.6,
            'detected_time': current_time,
            'business_hours_context': 'business_hours',
            'acknowledged': False,
            'alert_sent': False
        }
    ]

def create_dummy_google_ads_anomalies():
    """Create realistic Google Ads dummy anomalies with smart thresholds"""
    current_time = datetime.now(timezone.utc)
    
    return [
        {
            'anomaly_id': 'google_ads_new_1234567890_9876543210_1693934700',
            'account_id': '1234567890',
            'campaign_id': '9876543210',
            'campaign_name': 'WR - Search (Ad Grant) - UMS - Florida',
            'anomaly_category': 'new_campaign',
            'previous_budget': 0.0,
            'current_budget': 200.0,
            'budget_type': 'STANDARD',
            'currency': 'CAD',
            'increase_ratio': float('inf'),
            'monthly_impact': 6000.0,
            'impact_level': 'MEDIUM',
            'smart_threshold_used': 'New Campaign Threshold: $165/day',
            'risk_score': 0.7,
            'detected_time': current_time,
            'business_hours_context': 'after_hours',
            'acknowledged': False,
            'alert_sent': False
        },
        {
            'anomaly_id': 'google_ads_budget_1234567891_9876543211_1693934800',
            'account_id': '1234567891',
            'campaign_id': '9876543211', 
            'campaign_name': 'WR - Display Campaign - Canada Targeting',
            'anomaly_category': 'budget_increase_critical',
            'previous_budget': 1500.0,
            'current_budget': 3000.0,
            'budget_type': 'STANDARD',
            'currency': 'CAD',
            'increase_ratio': 2.0,
            'monthly_impact': 45000.0,
            'impact_level': 'HIGH',
            'smart_threshold_used': 'Warning: 1.5x, Critical: 2.0x',
            'risk_score': 0.9,
            'detected_time': current_time,
            'business_hours_context': 'business_hours',
            'acknowledged': False,
            'alert_sent': False
        },
        {
            'anomaly_id': 'google_ads_budget_1234567892_9876543212_1693934900',
            'account_id': '1234567892',
            'campaign_id': '9876543212',
            'campaign_name': 'Brand Defense - Competitor Keywords',
            'anomaly_category': 'budget_increase_warning',
            'previous_budget': 500.0,
            'current_budget': 1200.0,
            'budget_type': 'STANDARD',
            'currency': 'CAD',
            'increase_ratio': 2.4,
            'monthly_impact': 21000.0,
            'impact_level': 'HIGH',
            'smart_threshold_used': 'Warning: 2.0x, Critical: 3.0x',
            'risk_score': 0.8,
            'detected_time': current_time,
            'business_hours_context': 'after_hours',
            'acknowledged': False,
            'alert_sent': False
        },
        {
            'anomaly_id': 'google_ads_budget_1234567893_9876543213_1693935000',
            'account_id': '1234567893',
            'campaign_id': '9876543213',
            'campaign_name': 'Shopping Campaign - Product Feed',
            'anomaly_category': 'budget_increase_warning',
            'previous_budget': 75.0,
            'current_budget': 225.0,
            'budget_type': 'STANDARD',
            'currency': 'CAD',
            'increase_ratio': 3.0,
            'monthly_impact': 4500.0,
            'impact_level': 'MEDIUM',
            'smart_threshold_used': 'Warning: 3.0x, Critical: 5.0x',
            'risk_score': 0.6,
            'detected_time': current_time,
            'business_hours_context': 'business_hours',
            'acknowledged': False,
            'alert_sent': False
        }
    ]

def test_meta_only_alert():
    """Test Meta Ads only alert"""
    print("📱 Testing Meta Ads Only Alert...")
    
    alert_system = UnifiedBudgetAlerts()
    meta_anomalies = create_dummy_meta_anomalies()
    
    success = alert_system.send_combined_alert(meta_anomalies=meta_anomalies)
    
    if success:
        print(f"✅ Meta Ads alert sent successfully! ({len(meta_anomalies)} anomalies)")
    else:
        print("❌ Failed to send Meta Ads alert")
    
    return success

def test_google_ads_only_alert():
    """Test Google Ads only alert"""
    print("\n🔍 Testing Google Ads Only Alert...")
    
    alert_system = UnifiedBudgetAlerts()
    google_ads_anomalies = create_dummy_google_ads_anomalies()
    
    success = alert_system.send_combined_alert(google_ads_anomalies=google_ads_anomalies)
    
    if success:
        print(f"✅ Google Ads alert sent successfully! ({len(google_ads_anomalies)} anomalies)")
    else:
        print("❌ Failed to send Google Ads alert")
    
    return success

def test_unified_alert():
    """Test unified alert with both platforms"""
    print("\n🚀 Testing Unified Multi-Platform Alert...")
    
    alert_system = UnifiedBudgetAlerts()
    meta_anomalies = create_dummy_meta_anomalies()
    google_ads_anomalies = create_dummy_google_ads_anomalies()
    
    success = alert_system.send_combined_alert(
        meta_anomalies=meta_anomalies,
        google_ads_anomalies=google_ads_anomalies
    )
    
    if success:
        print(f"✅ Unified alert sent successfully! ({len(meta_anomalies)} Meta + {len(google_ads_anomalies)} Google Ads anomalies)")
    else:
        print("❌ Failed to send unified alert")
    
    return success

def test_single_high_impact_alert():
    """Test single high-impact alert"""
    print("\n💰 Testing Single High-Impact Alert...")
    
    alert_system = UnifiedBudgetAlerts()
    
    # Create a single high-impact Google Ads anomaly
    high_impact_anomaly = [{
        'anomaly_id': 'google_ads_budget_critical_test',
        'account_id': '9999999999',
        'campaign_id': '8888888888',
        'campaign_name': 'URGENT: Enterprise Campaign - Black Friday',
        'anomaly_category': 'budget_increase_critical',
        'previous_budget': 5000.0,
        'current_budget': 15000.0,
        'budget_type': 'STANDARD',
        'currency': 'CAD',
        'increase_ratio': 3.0,
        'monthly_impact': 300000.0,  # $300K monthly impact!
        'impact_level': 'HIGH',
        'smart_threshold_used': 'Warning: 1.5x, Critical: 2.0x',
        'risk_score': 0.95,
        'detected_time': datetime.now(timezone.utc),
        'business_hours_context': 'after_hours',
        'acknowledged': False,
        'alert_sent': False
    }]
    
    success = alert_system.send_combined_alert(google_ads_anomalies=high_impact_anomaly)
    
    if success:
        print("✅ High-impact alert sent successfully!")
    else:
        print("❌ Failed to send high-impact alert")
    
    return success

def main():
    """Run alert tests"""
    print("🚀 Testing Google Chat Alert Messages")
    print("=" * 60)
    
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    if not webhook_url:
        print("❌ GOOGLE_CHAT_WEBHOOK_URL not found in environment variables")
        print("Please ensure your .env file contains the webhook URL")
        return False
    
    print(f"✅ Using webhook: {webhook_url[:50]}...")
    print("\nSending test alerts to your Google Chat space...")
    print("Check your chat space to see how the messages look!")
    
    # Run tests with delays between them
    results = {}
    
    try:
        results['Meta Only'] = test_meta_only_alert()
        
        import time
        time.sleep(2)  # Small delay between alerts
        
        results['Google Ads Only'] = test_google_ads_only_alert()
        
        time.sleep(2)
        
        results['Unified Alert'] = test_unified_alert()
        
        time.sleep(2)
        
        results['High Impact'] = test_single_high_impact_alert()
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 ALERT TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ SENT" if result else "❌ FAILED"
        print(f"{status} {test_name} Alert")
    
    print(f"\nAlerts Sent: {passed}/{total}")
    
    if passed > 0:
        print(f"\n🎉 {passed} alert(s) sent to Google Chat!")
        print("📱 Check your Google Chat space to see how they look.")
        print("💡 You can now review the message formatting and adjust if needed.")
    else:
        print("\n❌ No alerts were sent successfully.")
        print("🔧 Please check your webhook URL and network connection.")
    
    return passed > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)