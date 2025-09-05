"""
Meta Ads Budget Anomaly Detection API - Cloud Run Version
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from meta_api_implementation_bigquery import MetaBudgetMonitorBQ

# Load environment variables
load_dotenv()

# Store monitoring status
monitoring_status = {
    "last_run": None,
    "is_running": False,
    "last_anomalies_count": 0,
    "total_runs": 0,
    "errors": []
}

# Request/Response Models
class MonitoringRequest(BaseModel):
    business_id: Optional[str] = None
    force_run: bool = False

class MonitoringResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None

class WebhookRequest(BaseModel):
    action: str
    parameters: Dict

# Initialize FastAPI app
app = FastAPI(
    title="Meta Ads Budget Anomaly Detection",
    description="Real-time monitoring system for Meta Ads budget anomalies",
    version="1.0.0"
)

async def run_monitoring(business_id: str = None) -> Dict:
    """Run the monitoring cycle"""
    global monitoring_status
    
    if monitoring_status["is_running"]:
        return {
            "status": "already_running",
            "message": "Monitoring cycle is already in progress"
        }
    
    monitoring_status["is_running"] = True
    monitoring_status["last_run"] = datetime.now().isoformat()
    
    try:
        # Use business_id from env if not provided
        if not business_id:
            business_id = os.getenv('META_BUSINESS_ID')
            
        if not business_id:
            raise ValueError("No business_id provided and META_BUSINESS_ID not set in environment")
        
        # Initialize monitor
        project_id = os.getenv('GCP_PROJECT_ID')
        monitor = MetaBudgetMonitorBQ(business_id, project_id)
        
        # Run monitoring
        print(f"🔍 Running monitoring for Business ID: {business_id}")
        monitor.run_monitoring_cycle()
        
        monitoring_status["total_runs"] += 1
        monitoring_status["is_running"] = False
        
        return {
            "status": "success",
            "business_id": business_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        monitoring_status["is_running"] = False
        error_info = {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        monitoring_status["errors"].append(error_info)
        
        # Keep only last 10 errors
        if len(monitoring_status["errors"]) > 10:
            monitoring_status["errors"] = monitoring_status["errors"][-10:]
        
        print(f"❌ Error during monitoring: {str(e)}")
        raise e

# API Routes

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Meta Ads Budget Monitor",
        "status": "healthy",
        "version": "1.0.0",
        "monitoring_status": monitoring_status
    }

@app.post("/monitor", response_model=MonitoringResponse)
async def trigger_monitoring(
    request: MonitoringRequest,
    background_tasks: BackgroundTasks
):
    """Manually trigger monitoring cycle"""
    try:
        if request.force_run or not monitoring_status["is_running"]:
            # Run monitoring in background
            background_tasks.add_task(run_monitoring, request.business_id)
            
            return MonitoringResponse(
                status="triggered",
                message="Monitoring cycle has been triggered",
                data={
                    "business_id": request.business_id or os.getenv('META_BUSINESS_ID'),
                    "triggered_at": datetime.now().isoformat()
                }
            )
        else:
            return MonitoringResponse(
                status="already_running",
                message="Monitoring cycle is already in progress",
                data=monitoring_status
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get current monitoring status"""
    return {
        "monitoring_status": monitoring_status,
        "config": {
            "business_id": os.getenv('META_BUSINESS_ID'),
            "check_interval_minutes": os.getenv('CHECK_INTERVAL_MINUTES', 5),
            "thresholds": {
                "budget_increase_warning": float(os.getenv('BUDGET_INCREASE_WARNING', 1.5)),
                "budget_increase_critical": float(os.getenv('BUDGET_INCREASE_CRITICAL', 3.0)),
                "new_campaign_max_budget": float(os.getenv('NEW_CAMPAIGN_MAX_BUDGET', 5000)),
                "new_adset_max_budget": float(os.getenv('NEW_ADSET_MAX_BUDGET', 2000))
            }
        }
    }

@app.post("/webhook/google-chat")
async def handle_google_chat_webhook(request: Request):
    """Handle Google Chat webhook callbacks (e.g., acknowledge button)"""
    try:
        body = await request.json()
        
        # Handle different action types
        if body.get("type") == "CARD_CLICKED":
            action = body.get("action", {})
            action_name = action.get("actionMethodName")
            
            if action_name == "acknowledge_alert":
                # Handle alert acknowledgment
                parameters = action.get("parameters", [])
                alert_ids = []
                for param in parameters:
                    if param.get("key") == "alert_ids":
                        alert_ids = json.loads(param.get("value", "[]"))
                
                # TODO: Update Firestore to mark alerts as acknowledged
                
                return {
                    "actionResponse": {
                        "type": "UPDATE_MESSAGE"
                    },
                    "cards": [{
                        "header": {
                            "title": "✅ Alert Acknowledged",
                            "subtitle": f"Acknowledged {len(alert_ids)} alerts"
                        },
                        "sections": [{
                            "widgets": [{
                                "textParagraph": {
                                    "text": f"Alerts have been acknowledged by {body.get('user', {}).get('displayName', 'Unknown')}"
                                }
                            }]
                        }]
                    }]
                }
            
            elif action_name == "pause_campaign":
                # Handle campaign pause request
                # TODO: Implement campaign pausing logic
                return {
                    "text": "Campaign pause functionality not yet implemented"
                }
        
        return {"text": "Unknown action"}
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return {"text": f"Error processing request: {str(e)}"}

@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check Meta API connectivity
    try:
        # Simple check - verify env vars are set
        if os.getenv('META_ACCESS_TOKEN') and os.getenv('META_BUSINESS_ID'):
            health_status["checks"]["meta_api"] = "configured"
        else:
            health_status["checks"]["meta_api"] = "not_configured"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["meta_api"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check BigQuery connectivity
    try:
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.getenv('GCP_PROJECT_ID'):
            health_status["checks"]["bigquery"] = "configured"
        else:
            health_status["checks"]["bigquery"] = "not_configured"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["bigquery"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check recent errors
    recent_errors = len([e for e in monitoring_status["errors"] 
                        if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(hours=1)])
    health_status["checks"]["recent_errors"] = recent_errors
    
    if recent_errors > 5:
        health_status["status"] = "degraded"
    
    return health_status

@app.post("/test-alert")
async def test_alert():
    """Send a test alert to Google Chat"""
    try:
        from meta_api_implementation_bigquery import MetaBudgetMonitorBQ
        
        # Create test anomaly
        test_anomaly = [{
            'type': 'WARNING',
            'level': 'campaign',
            'account_id': 'act_123456789',
            'account_name': 'Test Account',
            'campaign_id': 'test_campaign_123',
            'campaign_name': 'Test Campaign',
            'message': 'This is a test alert from the monitoring system',
            'current_budget': 1000,
            'previous_budget': 500,
            'increase_percentage': 100,
            'risk_score': 0.5
        }]
        
        # Initialize monitor and send alert
        project_id = os.getenv('GCP_PROJECT_ID')
        business_id = os.getenv('META_BUSINESS_ID')
        monitor = MetaBudgetMonitorBQ(business_id, project_id)
        monitor.send_google_chat_alert(test_anomaly)
        
        return {
            "status": "success",
            "message": "Test alert sent to Google Chat"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test alert: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)