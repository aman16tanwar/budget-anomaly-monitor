import requests
import json
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(usecwd=True), override=True)

def test_google_chat_alert():
    """Simple test of Google Chat alert"""
    
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ GOOGLE_CHAT_WEBHOOK_URL not found in .env")
        return
    
    print("✅ Google Chat webhook URL found")
    print(f"🔗 Webhook: {webhook_url[:50]}...")
    
    # Create test alert for Google Ads anomalies
    test_alert = {
        "cards": [{
            "header": {
                "title": "🚨 Google Ads Budget Alert - TEST",
                "subtitle": "31 budget anomalies detected",
                "imageUrl": "https://cdn-icons-png.flaticon.com/512/2920/2920277.png"
            },
            "sections": [{
                "header": "🔴 GOOGLE ADS ALERTS",
                "widgets": [{
                    "textParagraph": {
                        "text": "🆕 **31 NEW high-budget campaigns detected:**<br>" +
                               "💰 **$16,584 CAD** - WR - Search (Ad Grant) - UMS - Florida<br>" +
                               "💰 **$10,000 CAD** - WR - Ad Grant - Parksville - DSA - BC<br>" +
                               "💰 **$8,000 CAD** - WR - Ad Grant - Parksville - General<br>" +
                               "💰 **$7,000 CAD** - WR - BC Parks Foundation - Brand<br>" +
                               "💰 **$7,000 CAD** - WR - BC Parks Foundation - Generic"
                    }
                }]
            }, {
                "header": "📋 ACTION REQUIRED", 
                "widgets": [{
                    "textParagraph": {
                        "text": "**🎯 RECOMMENDED ACTIONS:**<br>" +
                               "• Verify 31 new high-budget campaigns<br>" +
                               "• Check campaign delivery status<br>" +
                               "• Confirm spend authorization with stakeholders"
                    }
                }]
            }]
        }]
    }
    
    try:
        print("📤 Sending test alert to Google Chat...")
        response = requests.post(
            webhook_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_alert),
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Test alert sent successfully!")
            print("💬 Check your Google Chat space for the alert")
            return True
        else:
            print(f"❌ Failed to send alert: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as ex:
        print(f"❌ Error sending alert: {ex}")
        return False

def test_combined_alert():
    """Test combined Meta + Google Ads alert"""
    
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ GOOGLE_CHAT_WEBHOOK_URL not found")
        return
    
    # Combined alert with both platforms
    combined_alert = {
        "cards": [{
            "header": {
                "title": "🚨 Multi-Platform Budget Alert - TEST",
                "subtitle": "32 budget anomalies detected across platforms",
                "imageUrl": "https://cdn-icons-png.flaticon.com/512/2920/2920277.png"
            },
            "sections": [{
                "header": "📊 PLATFORM SUMMARY",
                "widgets": [{
                    "textParagraph": {
                        "text": "🔵 **Meta Ads:** 1 anomaly<br>" +
                               "🔴 **Google Ads:** 31 anomalies<br>" +
                               "<i>Detected at: 2025-09-02 07:04 UTC</i>"
                    }
                }]
            }, {
                "header": "🔵 META ADS ALERTS",
                "widgets": [{
                    "textParagraph": {
                        "text": "🔴 **CRITICAL:** Meta Brand Campaign - Summer 2024<br>" +
                               "💰 Budget: $2,000 → $8,000<br>" +
                               "📈 Increase: 4.0x"
                    }
                }, {
                    "buttons": [{
                        "textButton": {
                            "text": "VIEW IN META ADS MANAGER",
                            "onClick": {
                                "openLink": {
                                    "url": "https://business.facebook.com/adsmanager/manage/campaigns?act=act_12345"
                                }
                            }
                        }
                    }]
                }]
            }, {
                "header": "🔴 GOOGLE ADS ALERTS",
                "widgets": [{
                    "textParagraph": {
                        "text": "🆕 **31 NEW high-budget campaigns:**"
                    }
                }, {
                    "textParagraph": {
                        "text": "💰 **$16,584 CAD** - WR - Search (Ad Grant) - UMS - Florida<br>" +
                               "💰 **$10,000 CAD** - WR - Ad Grant - Search 2020 - Parksville<br>" +
                               "💰 **$8,000 CAD** - WR - Ad Grant - Search 2020 - Parksville<br>" +
                               "💰 **$7,000 CAD** - WR - BC Parks Foundation - Brand<br>" +
                               "💰 **$7,000 CAD** - WR - BC Parks Foundation - Generic"
                    }
                }]
            }, {
                "header": "📋 ACTION REQUIRED",
                "widgets": [{
                    "textParagraph": {
                        "text": "**🎯 RECOMMENDED ACTIONS:**<br>" +
                               "• Review 1 critical Meta budget increase immediately<br>" +
                               "• Verify 31 new high-budget Google Ads campaigns<br>" +
                               "• Check campaign delivery status<br>" +
                               "• Confirm spend authorization with stakeholders"
                    }
                }]
            }]
        }]
    }
    
    try:
        print("\n📤 Sending combined platform alert...")
        response = requests.post(
            webhook_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(combined_alert),
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Combined alert sent successfully!")
            print("💬 Multi-platform alert delivered to Google Chat")
            return True
        else:
            print(f"❌ Failed to send combined alert: {response.status_code}")
            return False
            
    except Exception as ex:
        print(f"❌ Error sending combined alert: {ex}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Google Chat Budget Alerts")
    
    # Test 1: Google Ads only alert
    print("\n=== TEST 1: Google Ads Only Alert ===")
    test_google_chat_alert()
    
    # Test 2: Combined Meta + Google Ads alert  
    print("\n=== TEST 2: Combined Platform Alert ===")
    test_combined_alert()
    
    print("\n✅ Alert testing complete!")