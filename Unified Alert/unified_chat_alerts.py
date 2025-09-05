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
        """Send unified alert with separate, properly branded cards for each platform"""
        
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
            # Send separate professional cards for each platform
            success = True
            
            # Send Meta Ads alert with Facebook branding
            if meta_anomalies:
                meta_card = self._build_meta_ads_card(meta_anomalies)
                response = requests.post(
                    self.google_chat_webhook,
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(meta_card),
                    timeout=30
                )
                if response.status_code != 200:
                    logger.error(f"Failed to send Meta alert: {response.status_code}")
                    success = False
            
            # Send Google Ads alert with Google Ads branding  
            if google_ads_anomalies:
                google_card = self._build_google_ads_card(google_ads_anomalies)
                response = requests.post(
                    self.google_chat_webhook,
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(google_card),
                    timeout=30
                )
                if response.status_code != 200:
                    logger.error(f"Failed to send Google Ads alert: {response.status_code}")
                    success = False
            
            if success:
                logger.info(f"Successfully sent alerts: {len(meta_anomalies)} Meta + {len(google_ads_anomalies)} Google Ads anomalies")
            
            return success
                
        except Exception as ex:
            logger.error(f"Error sending alerts: {ex}")
            return False
    
    def _build_unified_chat_card(self, meta_anomalies: List[Dict], google_ads_anomalies: List[Dict]) -> Dict:
        """Build unified Google Chat card with both platform anomalies - matching Meta's polished UI"""
        
        total_anomalies = len(meta_anomalies) + len(google_ads_anomalies)
        
        # Use professional platform-specific logo or multi-platform icon
        header_image = "https://www.facebook.com/images/fb_icon_325x325.png" if meta_anomalies and not google_ads_anomalies \
                      else "https://developers.google.com/ads/images/branding/googleads/googleads-logo-horizontal-color.png" if google_ads_anomalies and not meta_anomalies \
                      else "https://www.facebook.com/images/fb_icon_325x325.png"  # Default to Facebook icon for multi-platform
        
        # Main card structure with professional styling (matching Meta's design)
        card = {
            "cards": [{
                "header": {
                    "title": "🚨 Multi-Platform Budget Alert",
                    "subtitle": f"Detected {total_anomalies} budget anomalies across advertising platforms",
                    "imageUrl": header_image
                },
                "sections": []
            }]
        }
        
        sections = card["cards"][0]["sections"]
        
        # Summary section
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
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
        
        # Insights section (matching Meta's design)
        sections.append(self._build_insights_section())
        
        # Action items section
        sections.append(self._build_action_section(meta_anomalies, google_ads_anomalies))
        
        return card
    
    def _build_insights_section(self) -> Dict:
        """Build insights section matching Meta's design"""
        import pytz
        
        # Get current time in PST (matching Meta's timezone)
        pst = pytz.timezone('America/Los_Angeles')
        current_time_pst = datetime.now(pst)
        is_business_hours = 8 <= current_time_pst.hour <= 18
        is_morning_reminder = 8 <= current_time_pst.hour <= 10
        
        # Build insights text matching Meta's format
        insights_text = f"💡 <b>Insights:</b> Anomalies detected during {'business hours' if is_business_hours else 'off-hours'}."
        
        if is_morning_reminder:
            insights_text += "\n🌅 <b>Morning Reminder:</b> This may include unacknowledged alerts from yesterday."
        else:
            insights_text += "\n⏰ <b>Note:</b> Duplicate alerts are suppressed for 24 hours. Unacknowledged alerts will be reminded at 9 AM PST."
        
        return {
            "widgets": [{
                "textParagraph": {
                    "text": insights_text
                }
            }]
        }
    
    def _build_meta_ads_section(self, anomalies: List[Dict]) -> Dict:
        """Build Meta Ads section matching original Meta alert design"""
        
        # Group by severity (matching Meta's approach)
        critical_anomalies = [a for a in anomalies if a.get('anomaly_type') == 'CRITICAL' or 'critical' in a.get('anomaly_category', '').lower()]
        warning_anomalies = [a for a in anomalies if a.get('anomaly_type') == 'WARNING' or 'warning' in a.get('anomaly_category', '').lower()]
        new_campaign_anomalies = [a for a in anomalies if 'new_campaign' in a.get('anomaly_category', '')]
        
        widgets = []
        
        # Critical alerts section (matching Meta's ⛔ CRITICAL ALERTS design)
        if critical_anomalies:
            for anomaly in critical_anomalies[:3]:  # Show max 3, same as Meta
                # Text widget matching Meta's format
                # Build message text properly
                default_message = f"Budget increased from ${anomaly.get('previous_budget', 0):,.0f} to ${anomaly.get('current_budget', 0):,.0f}"
                message_text = anomaly.get('message', default_message)
                
                text_widget = {
                    "textParagraph": {
                        "text": f"<b>{anomaly.get('account_name', 'Unknown Account')}</b><br>" +
                               f"<b>{anomaly.get('level', 'CAMPAIGN').upper()}:</b> {anomaly.get('campaign_name', 'Unknown Campaign')}<br>" +
                               f"🔴 {message_text}"
                    }
                }
                widgets.append(text_widget)
                
                # Button widget matching Meta's design
                button_widget = {
                    "buttons": [{
                        "textButton": {
                            "text": "VIEW IN ADS MANAGER",
                            "onClick": {
                                "openLink": {
                                    "url": f"https://business.facebook.com/adsmanager/manage/campaigns?act={anomaly.get('account_id', '')}"
                                }
                            }
                        }
                    }]
                }
                widgets.append(button_widget)
        
        # Warning alerts (summarized)
        if warning_anomalies:
            widgets.append({
                "textParagraph": {
                    "text": f"🟡 **{len(warning_anomalies)} WARNING alerts** - Budget increases 1.5x-3x"
                }
            })
        
        # New campaign alerts (summarized)
        if new_campaign_anomalies:
            widgets.append({
                "textParagraph": {
                    "text": f"🆕 **{len(new_campaign_anomalies)} NEW high-budget campaigns** (≥$5,000)"
                }
            })
        
        return {
            "header": "⛔ CRITICAL ALERTS" if critical_anomalies else "🔵 META ADS ALERTS",
            "widgets": widgets
        }
    
    def _build_google_ads_section(self, anomalies: List[Dict]) -> Dict:
        """Build Google Ads section matching Meta's professional design"""
        
        # Group by severity
        critical_anomalies = [a for a in anomalies if 'critical' in a.get('anomaly_category', '').lower()]
        warning_anomalies = [a for a in anomalies if 'warning' in a.get('anomaly_category', '').lower()]  
        new_campaign_anomalies = [a for a in anomalies if 'new_campaign' in a.get('anomaly_category', '')]
        
        widgets = []
        
        # Critical alerts (matching Meta's format)
        if critical_anomalies:
            for anomaly in critical_anomalies[:3]:  # Show max 3, same as Meta
                # Text widget matching Meta's professional format
                text_widget = {
                    "textParagraph": {
                        "text": f"<b>Google Ads Account: {anomaly.get('account_id', 'Unknown Account')}</b><br>" +
                               f"<b>CAMPAIGN:</b> {anomaly.get('campaign_name', 'Unknown Campaign')}<br>" +
                               f"🔴 Budget increased from ${anomaly.get('previous_budget', 0):,.0f} to ${anomaly.get('current_budget', 0):,.0f} ({anomaly.get('increase_ratio', 1):.1f}x increase)"
                    }
                }
                widgets.append(text_widget)
                
                # Button widget matching Meta's style
                button_widget = {
                    "buttons": [{
                        "textButton": {
                            "text": "VIEW IN GOOGLE ADS",
                            "onClick": {
                                "openLink": {
                                    "url": f"https://ads.google.com/aw/campaigns?ocid={anomaly.get('account_id', '')}"
                                }
                            }
                        }
                    }]
                }
                widgets.append(button_widget)
        
        # New campaign alerts (detailed like Meta's approach)
        if new_campaign_anomalies:
            # Sort by budget and show top 3 detailed, then summarize others
            sorted_campaigns = sorted(new_campaign_anomalies, key=lambda x: x.get('current_budget', 0), reverse=True)
            
            for campaign in sorted_campaigns[:3]:  # Show top 3 in detail
                budget = campaign.get('current_budget', 0)
                currency = campaign.get('currency', 'CAD')
                name = campaign.get('campaign_name', 'Unknown Campaign')
                account_id = campaign.get('account_id', 'Unknown Account')
                
                # Text widget with detailed info
                text_widget = {
                    "textParagraph": {
                        "text": f"<b>Google Ads Account: {account_id}</b><br>" +
                               f"<b>NEW CAMPAIGN:</b> {name}<br>" +
                               f"🆕 New high-budget campaign created with ${budget:,.0f} {currency} budget"
                    }
                }
                widgets.append(text_widget)
                
                # Button widget
                button_widget = {
                    "buttons": [{
                        "textButton": {
                            "text": "VIEW IN GOOGLE ADS",
                            "onClick": {
                                "openLink": {
                                    "url": f"https://ads.google.com/aw/campaigns?ocid={account_id}"
                                }
                            }
                        }
                    }]
                }
                widgets.append(button_widget)
            
            # Summarize remaining campaigns if more than 3
            if len(sorted_campaigns) > 3:
                remaining = len(sorted_campaigns) - 3
                widgets.append({
                    "textParagraph": {
                        "text": f"🆕 **+{remaining} additional NEW high-budget campaigns** (see dashboard for details)"
                    }
                })
        
        # Warning alerts (summarized)
        if warning_anomalies:
            widgets.append({
                "textParagraph": {
                    "text": f"🟡 **{len(warning_anomalies)} WARNING alerts** - Budget increases 1.5x-3x"
                }
            })
        
        # Determine section header based on content
        if critical_anomalies:
            section_header = "⛔ GOOGLE ADS CRITICAL ALERTS"
        elif new_campaign_anomalies:
            section_header = "🆕 GOOGLE ADS NEW CAMPAIGNS"
        else:
            section_header = "🔴 GOOGLE ADS ALERTS"
        
        return {
            "header": section_header,
            "widgets": widgets
        }
    
    def _build_meta_ads_card(self, anomalies: List[Dict]) -> Dict:
        """Build Meta Ads card exactly matching original Meta alert design"""
        
        # Group by severity (matching Meta's approach)
        critical_anomalies = [a for a in anomalies if a.get('anomaly_type') == 'CRITICAL' or 'critical' in a.get('anomaly_category', '').lower()]
        warning_anomalies = [a for a in anomalies if a.get('anomaly_type') == 'WARNING' or 'warning' in a.get('anomaly_category', '').lower()]
        
        # Create card matching Meta's exact design
        card = {
            "cards": [{
                "header": {
                    "title": "🚨 Meta Ads Budget Alert",
                    "subtitle": f"Detected {len(anomalies)} budget anomalies",
                    "imageUrl": "https://www.facebook.com/images/fb_icon_325x325.png"
                },
                "sections": []
            }]
        }
        
        sections = card["cards"][0]["sections"]
        
        # Add critical anomalies section (matching original Meta design)
        if critical_anomalies:
            critical_section = {
                "header": "⛔ CRITICAL ALERTS",
                "widgets": []
            }
            
            for anomaly in critical_anomalies[:3]:  # Show max 3, same as original
                # Build message text properly
                default_message = f"Budget increased from ${anomaly.get('previous_budget', 0):,.0f} to ${anomaly.get('current_budget', 0):,.0f}"
                message_text = anomaly.get('message', default_message)
                
                # Text widget matching Meta's exact format
                text_widget = {
                    "textParagraph": {
                        "text": f"<b>{anomaly.get('account_name', 'Unknown Account')}</b><br>" +
                               f"<b>{anomaly.get('level', 'CAMPAIGN').upper()}:</b> {anomaly.get('campaign_name', 'Unknown Campaign')}<br>" +
                               f"🔴 {message_text}"
                    }
                }
                critical_section["widgets"].append(text_widget)
                
                # Button widget matching Meta's exact design
                button_widget = {
                    "buttons": [{
                        "textButton": {
                            "text": "VIEW IN ADS MANAGER",
                            "onClick": {
                                "openLink": {
                                    "url": f"https://business.facebook.com/adsmanager/manage/campaigns?act={anomaly.get('account_id', '')}"
                                }
                            }
                        }
                    }]
                }
                critical_section["widgets"].append(button_widget)
            
            sections.append(critical_section)
        
        # Add insights section (matching Meta's design)
        sections.append(self._build_insights_section())
        
        return card
    
    def _build_google_ads_card(self, anomalies: List[Dict]) -> Dict:
        """Build Google Ads card with proper Google Ads branding and professional design"""
        
        # Group by severity
        critical_anomalies = [a for a in anomalies if 'critical' in a.get('anomaly_category', '').lower()]
        new_campaign_anomalies = [a for a in anomalies if 'new_campaign' in a.get('anomaly_category', '')]
        
        # Create card with Google Ads branding
        card = {
            "cards": [{
                "header": {
                    "title": "🚨 Google Ads Budget Alert", 
                    "subtitle": f"Detected {len(anomalies)} budget anomalies",
                    "imageUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Google_Ads_logo.svg/512px-Google_Ads_logo.svg.png"
                },
                "sections": []
            }]
        }
        
        sections = card["cards"][0]["sections"]
        
        # Add critical anomalies section
        if critical_anomalies:
            critical_section = {
                "header": "⛔ CRITICAL ALERTS",
                "widgets": []
            }
            
            for anomaly in critical_anomalies[:3]:  # Show max 3
                # Text widget matching Meta's format but for Google Ads
                text_widget = {
                    "textParagraph": {
                        "text": f"<b>Google Ads Account: {anomaly.get('account_id', 'Unknown Account')}</b><br>" +
                               f"<b>CAMPAIGN:</b> {anomaly.get('campaign_name', 'Unknown Campaign')}<br>" +
                               f"🔴 Budget increased from ${anomaly.get('previous_budget', 0):,.0f} to ${anomaly.get('current_budget', 0):,.0f} ({anomaly.get('increase_ratio', 1):.1f}x increase)"
                    }
                }
                critical_section["widgets"].append(text_widget)
                
                # Button widget
                button_widget = {
                    "buttons": [{
                        "textButton": {
                            "text": "VIEW IN GOOGLE ADS",
                            "onClick": {
                                "openLink": {
                                    "url": f"https://ads.google.com/aw/campaigns?ocid={anomaly.get('account_id', '')}"
                                }
                            }
                        }
                    }]
                }
                critical_section["widgets"].append(button_widget)
            
            sections.append(critical_section)
        
        # Add new campaigns section
        if new_campaign_anomalies:
            new_section = {
                "header": "🆕 NEW HIGH-BUDGET CAMPAIGNS",
                "widgets": []
            }
            
            # Sort by budget and show top 3 detailed
            sorted_campaigns = sorted(new_campaign_anomalies, key=lambda x: x.get('current_budget', 0), reverse=True)
            
            for campaign in sorted_campaigns[:3]:  # Show top 3 in detail
                budget = campaign.get('current_budget', 0)
                currency = campaign.get('currency', 'CAD')
                name = campaign.get('campaign_name', 'Unknown Campaign')
                account_id = campaign.get('account_id', 'Unknown Account')
                
                # Text widget with detailed info
                text_widget = {
                    "textParagraph": {
                        "text": f"<b>Google Ads Account: {account_id}</b><br>" +
                               f"<b>NEW CAMPAIGN:</b> {name}<br>" +
                               f"🆕 New high-budget campaign created with ${budget:,.0f} {currency} budget"
                    }
                }
                new_section["widgets"].append(text_widget)
                
                # Button widget
                button_widget = {
                    "buttons": [{
                        "textButton": {
                            "text": "VIEW IN GOOGLE ADS",
                            "onClick": {
                                "openLink": {
                                    "url": f"https://ads.google.com/aw/campaigns?ocid={account_id}"
                                }
                            }
                        }
                    }]
                }
                new_section["widgets"].append(button_widget)
            
            # Summarize remaining campaigns if more than 3
            if len(sorted_campaigns) > 3:
                remaining = len(sorted_campaigns) - 3
                new_section["widgets"].append({
                    "textParagraph": {
                        "text": f"🆕 **+{remaining} additional NEW high-budget campaigns** (see dashboard for details)"
                    }
                })
            
            sections.append(new_section)
        
        # Add insights section
        sections.append(self._build_insights_section())
        
        return card
    
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