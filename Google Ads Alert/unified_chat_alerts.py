import requests
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)
logger = logging.getLogger(__name__)

class UnifiedBudgetAlerts:
    """Unified alert system for both Meta Ads and Google Ads budget anomalies"""
    
    def __init__(self):
        self.google_chat_webhook = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
        if not self.google_chat_webhook:
            logger.warning("Google Chat webhook URL not configured")
    
    def send_combined_alert(self, meta_anomalies: List[Dict] = None, google_ads_anomalies: List[Dict] = None):
        """Send unified alert combining both Meta and Google Ads anomalies"""
        
        if not self.google_chat_webhook:
            logger.error("Cannot send alerts: Google Chat webhook URL not configured")
            return False
        
        # Filter out empty lists
        meta_anomalies = meta_anomalies or []
        google_ads_anomalies = google_ads_anomalies or []
        
        # Skip if no anomalies to report
        if not meta_anomalies and not google_ads_anomalies:
            logger.info("No anomalies to report")
            return True
        
        try:
            # Build unified Google Chat card
            card = self._build_unified_chat_card(meta_anomalies, google_ads_anomalies)
            
            # Send to Google Chat
            response = requests.post(
                self.google_chat_webhook,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(card),
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent unified alert: {len(meta_anomalies)} Meta + {len(google_ads_anomalies)} Google Ads anomalies")
                return True
            else:
                logger.error(f"Failed to send alert: {response.status_code} - {response.text}")
                return False
                
        except Exception as ex:
            logger.error(f"Error sending unified alert: {ex}")
            return False
    
    def _build_unified_chat_card(self, meta_anomalies: List[Dict], google_ads_anomalies: List[Dict]) -> Dict:
        """Build unified Google Chat card with both platform anomalies"""
        
        total_anomalies = len(meta_anomalies) + len(google_ads_anomalies)
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        # Main card structure
        card = {
            "cards": [{
                "header": {
                    "title": "🚨 Multi-Platform Budget Alert",
                    "subtitle": f"Detected {total_anomalies} budget anomalies across platforms",
                    "imageUrl": "https://cdn-icons-png.flaticon.com/512/2920/2920277.png"  # Alert icon
                },
                "sections": []
            }]
        }
        
        sections = card["cards"][0]["sections"]
        
        # Summary section
        platform_summary = []
        if meta_anomalies:
            platform_summary.append(f"🔵 **Meta Ads:** {len(meta_anomalies)} anomalies")
        if google_ads_anomalies:
            platform_summary.append(f"🔴 **Google Ads:** {len(google_ads_anomalies)} anomalies")
        
        sections.append({
            "header": "📊 PLATFORM SUMMARY",
            "widgets": [{
                "textParagraph": {
                    "text": "<br>".join(platform_summary) + f"<br><i>Detected at: {current_time}</i>"
                }
            }]
        })
        
        # Meta Ads section
        if meta_anomalies:
            sections.append(self._build_meta_ads_section(meta_anomalies))
        
        # Google Ads section  
        if google_ads_anomalies:
            sections.append(self._build_google_ads_section(google_ads_anomalies))
        
        # Action items section
        sections.append(self._build_action_section(meta_anomalies, google_ads_anomalies))
        
        return card
    
    def _build_meta_ads_section(self, anomalies: List[Dict]) -> Dict:
        """Build Meta Ads section of the alert"""
        
        # Group by severity
        critical_anomalies = [a for a in anomalies if 'critical' in a.get('anomaly_category', '').lower()]
        warning_anomalies = [a for a in anomalies if 'warning' in a.get('anomaly_category', '').lower()]
        new_campaign_anomalies = [a for a in anomalies if 'new_campaign' in a.get('anomaly_category', '')]
        
        widgets = []
        
        # Critical alerts
        if critical_anomalies:
            for anomaly in critical_anomalies[:3]:  # Show max 3
                widgets.append({
                    "textParagraph": {
                        "text": f"🔴 **CRITICAL:** {anomaly.get('campaign_name', 'Unknown Campaign')}<br>" +
                               f"💰 Budget: ${anomaly.get('previous_budget', 0):,.0f} → ${anomaly.get('current_budget', 0):,.0f}<br>" +
                               f"📈 Increase: {anomaly.get('increase_ratio', 1):.1f}x"
                    }
                })
                
                # Add Ads Manager button
                if anomaly.get('account_id'):
                    widgets.append({
                        "buttons": [{
                            "textButton": {
                                "text": "VIEW IN META ADS MANAGER",
                                "onClick": {
                                    "openLink": {
                                        "url": f"https://business.facebook.com/adsmanager/manage/campaigns?act={anomaly['account_id']}"
                                    }
                                }
                            }
                        }]
                    })
        
        # Warning alerts (summarized)
        if warning_anomalies:
            widgets.append({
                "textParagraph": {
                    "text": f"🟡 **{len(warning_anomalies)} WARNING alerts** - Budget increases 1.5x-3x"
                }
            })
        
        # New campaign alerts (summarized)
        if new_campaign_anomalies:
            high_budget_campaigns = [a for a in new_campaign_anomalies if a.get('current_budget', 0) >= 5000]
            widgets.append({
                "textParagraph": {
                    "text": f"🆕 **{len(new_campaign_anomalies)} NEW high-budget campaigns** (≥$5,000)"
                }
            })
        
        return {
            "header": "🔵 META ADS ALERTS",
            "widgets": widgets
        }
    
    def _build_google_ads_section(self, anomalies: List[Dict]) -> Dict:
        """Build Google Ads section of the alert"""
        
        # Group by severity
        critical_anomalies = [a for a in anomalies if 'critical' in a.get('anomaly_category', '').lower()]
        warning_anomalies = [a for a in anomalies if 'warning' in a.get('anomaly_category', '').lower()]  
        new_campaign_anomalies = [a for a in anomalies if 'new_campaign' in a.get('anomaly_category', '')]
        
        widgets = []
        
        # Critical alerts
        if critical_anomalies:
            for anomaly in critical_anomalies[:3]:  # Show max 3
                widgets.append({
                    "textParagraph": {
                        "text": f"🔴 **CRITICAL:** {anomaly.get('campaign_name', 'Unknown Campaign')}<br>" +
                               f"💰 Budget: ${anomaly.get('previous_budget', 0):,.0f} → ${anomaly.get('current_budget', 0):,.0f}<br>" +
                               f"📈 Increase: {anomaly.get('increase_ratio', 1):.1f}x"
                    }
                })
                
                # Add Google Ads button
                if anomaly.get('account_id'):
                    widgets.append({
                        "buttons": [{
                            "textButton": {
                                "text": "VIEW IN GOOGLE ADS",
                                "onClick": {
                                    "openLink": {
                                        "url": f"https://ads.google.com/aw/campaigns?ocid={anomaly['account_id']}"
                                    }
                                }
                            }
                        }]
                    })
        
        # Warning alerts (summarized)
        if warning_anomalies:
            widgets.append({
                "textParagraph": {
                    "text": f"🟡 **{len(warning_anomalies)} WARNING alerts** - Budget increases 1.5x-3x"
                }
            })
        
        # New campaign alerts (show top high-budget ones)
        if new_campaign_anomalies:
            # Sort by budget and show top 5
            sorted_campaigns = sorted(new_campaign_anomalies, key=lambda x: x.get('current_budget', 0), reverse=True)
            
            widgets.append({
                "textParagraph": {
                    "text": f"🆕 **{len(new_campaign_anomalies)} NEW high-budget campaigns:**"
                }
            })
            
            for campaign in sorted_campaigns[:5]:  # Show top 5
                budget = campaign.get('current_budget', 0)
                currency = campaign.get('currency', 'CAD')
                name = campaign.get('campaign_name', 'Unknown Campaign')
                # Truncate long campaign names
                display_name = (name[:50] + '...') if len(name) > 50 else name
                
                widgets.append({
                    "textParagraph": {
                        "text": f"💰 **${budget:,.0f} {currency}** - {display_name}"
                    }
                })
        
        return {
            "header": "🔴 GOOGLE ADS ALERTS", 
            "widgets": widgets
        }
    
    def _build_action_section(self, meta_anomalies: List[Dict], google_ads_anomalies: List[Dict]) -> Dict:
        """Build action items section"""
        
        widgets = []
        
        # Quick stats
        total_critical = len([a for a in (meta_anomalies + google_ads_anomalies) 
                             if 'critical' in a.get('anomaly_category', '').lower()])
        
        total_new_campaigns = len([a for a in (meta_anomalies + google_ads_anomalies)
                                  if 'new_campaign' in a.get('anomaly_category', '')])
        
        action_text = "**🎯 RECOMMENDED ACTIONS:**<br>"
        
        if total_critical > 0:
            action_text += f"• Review {total_critical} critical budget increases immediately<br>"
        
        if total_new_campaigns > 0:
            action_text += f"• Verify {total_new_campaigns} new high-budget campaigns<br>"
        
        action_text += "• Check campaign delivery status<br>"
        action_text += "• Confirm spend authorization with stakeholders"
        
        widgets.append({
            "textParagraph": {
                "text": action_text
            }
        })
        
        # Dashboard link
        widgets.append({
            "buttons": [{
                "textButton": {
                    "text": "🔍 VIEW FULL DASHBOARD",
                    "onClick": {
                        "openLink": {
                            "url": "https://your-dashboard-url.com"  # Update with actual dashboard URL
                        }
                    }
                }
            }]
        })
        
        return {
            "header": "📋 ACTION REQUIRED",
            "widgets": widgets
        }

def test_unified_alerts():
    """Test the unified alert system with sample data"""
    
    # Sample Meta anomalies
    meta_anomalies = [
        {
            "anomaly_category": "budget_increase_critical",
            "campaign_name": "Meta Campaign A", 
            "previous_budget": 1000,
            "current_budget": 4000,
            "increase_ratio": 4.0,
            "account_id": "123456789"
        }
    ]
    
    # Sample Google Ads anomalies
    google_ads_anomalies = [
        {
            "anomaly_category": "new_campaign",
            "campaign_name": "WR - BC Parks Foundation - Search Ad Grant 2024-2025",
            "current_budget": 7000,
            "currency": "CAD",
            "account_id": "987654321"
        },
        {
            "anomaly_category": "budget_increase_warning", 
            "campaign_name": "Google Ads Campaign B",
            "previous_budget": 2000,
            "current_budget": 3500, 
            "increase_ratio": 1.75,
            "account_id": "555666777"
        }
    ]
    
    # Send unified alert
    alert_system = UnifiedBudgetAlerts()
    success = alert_system.send_combined_alert(meta_anomalies, google_ads_anomalies)
    
    if success:
        print("✅ Test unified alert sent successfully!")
    else:
        print("❌ Failed to send test alert")

if __name__ == "__main__":
    test_unified_alerts()