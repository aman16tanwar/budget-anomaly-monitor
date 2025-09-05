from unified_chat_alerts import UnifiedBudgetAlerts
from datetime import datetime, timezone
import os

# Test the unified alert system with real Google Ads data
def test_with_real_data():
    """Test unified alerts with actual Google Ads anomalies detected earlier"""
    
    print("🔍 Testing Unified Budget Alert System")
    
    # Sample of the 31 Google Ads anomalies we detected earlier
    google_ads_anomalies = [
        {
            "anomaly_id": "google_ads_new_5121268068_21737028066_1725246258",
            "account_id": "5121268068", 
            "campaign_id": "21737028066",
            "campaign_name": "WR - BC Parks Foundation - Search Ad Grant 2024-2025 - Google Search - BC - Brand",
            "anomaly_category": "new_campaign",
            "previous_budget": 0.0,
            "current_budget": 7000.0,
            "increase_ratio": float('inf'),
            "currency": "CAD"
        },
        {
            "anomaly_id": "google_ads_new_6069257040_21395154775_1725246258",
            "account_id": "6069257040",
            "campaign_id": "21395154775", 
            "campaign_name": "WR - Ad Grant - Search 2020 - 2021 - Parksville - General - Canada",
            "anomaly_category": "new_campaign",
            "previous_budget": 0.0,
            "current_budget": 8000.0,
            "increase_ratio": float('inf'),
            "currency": "CAD"
        },
        {
            "anomaly_id": "google_ads_new_2246822346_21664976354_1725246258",
            "account_id": "2246822346",
            "campaign_id": "21664976354",
            "campaign_name": "WR - Search (Ad Grant) - UMS - Florida", 
            "anomaly_category": "new_campaign",
            "previous_budget": 0.0,
            "current_budget": 16583.98,
            "increase_ratio": float('inf'),
            "currency": "CAD"
        },
        {
            "anomaly_id": "google_ads_new_7164713350_21395154215_1725246258",
            "account_id": "7164713350",
            "campaign_id": "21395154215",
            "campaign_name": "WR - Ad Grant - Search 2020/21 - Desktop - Parksville - DSA - BC",
            "anomaly_category": "new_campaign", 
            "previous_budget": 0.0,
            "current_budget": 10000.0,
            "increase_ratio": float('inf'),
            "currency": "CAD"
        }
    ]
    
    # Sample Meta anomalies (for testing combined alerts)
    meta_anomalies = [
        {
            "anomaly_id": "meta_budget_12345_67890_1725246258",
            "account_id": "act_12345",
            "campaign_id": "67890",
            "campaign_name": "Meta Brand Campaign - Summer 2024",
            "anomaly_category": "budget_increase_critical",
            "previous_budget": 2000.0,
            "current_budget": 8000.0, 
            "increase_ratio": 4.0,
            "currency": "CAD"
        }
    ]
    
    # Initialize alert system
    alert_system = UnifiedBudgetAlerts()
    
    # Check if webhook is configured
    if not alert_system.google_chat_webhook:
        print("❌ Google Chat webhook URL not configured")
        print("💡 Please set GOOGLE_CHAT_WEBHOOK_URL environment variable")
        return
    
    print(f"✅ Google Chat webhook configured")
    print(f"📊 Test data: {len(google_ads_anomalies)} Google Ads + {len(meta_anomalies)} Meta anomalies")
    
    # Send combined alert
    print("📤 Sending unified alert to Google Chat...")
    success = alert_system.send_combined_alert(
        meta_anomalies=meta_anomalies,
        google_ads_anomalies=google_ads_anomalies
    )
    
    if success:
        print("✅ Unified alert sent successfully!")
        print("💬 Check your Google Chat space for the multi-platform budget alert")
        
        print("\n📋 Alert Summary:")
        print(f"   🔵 Meta Ads: {len(meta_anomalies)} anomalies")
        print(f"   🔴 Google Ads: {len(google_ads_anomalies)} anomalies") 
        print(f"   💰 Highest Google Ads budget: ${max(a['current_budget'] for a in google_ads_anomalies):,.2f}")
        print(f"   📈 Meta budget increase: {meta_anomalies[0]['increase_ratio']:.1f}x")
        
    else:
        print("❌ Failed to send unified alert")
        print("🔍 Check webhook URL and network connectivity")

def test_google_ads_only():
    """Test Google Ads only alerts"""
    
    print("\n🔍 Testing Google Ads Only Alert")
    
    # Just Google Ads anomalies
    google_ads_anomalies = [
        {
            "campaign_name": "WR - BC Parks Foundation - Brand Campaign",
            "anomaly_category": "new_campaign",
            "current_budget": 7000.0,
            "currency": "CAD",
            "account_id": "5121268068"
        },
        {
            "campaign_name": "WR - Tourism Parksville - DSA",
            "anomaly_category": "new_campaign", 
            "current_budget": 10000.0,
            "currency": "CAD",
            "account_id": "7164713350"
        }
    ]
    
    alert_system = UnifiedBudgetAlerts()
    success = alert_system.send_combined_alert(google_ads_anomalies=google_ads_anomalies)
    
    if success:
        print("✅ Google Ads only alert sent successfully!")
    else:
        print("❌ Failed to send Google Ads alert")

if __name__ == "__main__":
    # Test combined alerts
    test_with_real_data()
    
    # Test Google Ads only
    test_google_ads_only()