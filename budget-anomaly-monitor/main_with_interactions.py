"""
Combined Cloud Function for Budget Monitoring and Google Chat Interactions
Handles both scheduled monitoring and interactive button clicks
"""

import os
import json
from datetime import datetime
from google.cloud import bigquery
from meta_api_implementation_bigquery import MetaBudgetMonitorBQ, monitor_meta_budgets_bq

def main(request):
    """
    Single Cloud Function that handles both:
    1. Scheduled monitoring (Cloud Scheduler)
    2. Google Chat interactive button clicks
    """
    
    # Check if this is a Google Chat interaction
    request_json = request.get_json(silent=True)
    
    # Google Chat interactions have an 'action' field
    if request_json and 'action' in request_json:
        return handle_chat_interaction(request)
    else:
        # This is a scheduled monitoring request
        return monitor_meta_budgets_bq(request)


def handle_chat_interaction(request):
    """Handle Google Chat interactive button clicks"""
    try:
        request_json = request.get_json(silent=True)
        
        # Extract action data
        action = request_json.get('action', {})
        action_method = action.get('actionMethodName', '')
        parameters = action.get('parameters', [])
        user = request_json.get('user', {})
        
        # Get user information
        user_name = user.get('displayName', 'Unknown User')
        user_email = user.get('email', 'unknown@email.com')
        
        # Extract parameters
        anomaly_ids = []
        acknowledged = False
        
        for param in parameters:
            if param.get('key') == 'anomaly_ids':
                anomaly_ids = json.loads(param.get('value', '[]'))
            elif param.get('key') == 'acknowledged':
                acknowledged = param.get('value', 'false').lower() == 'true'
        
        if not anomaly_ids:
            return {'text': '❌ No anomaly IDs provided'}, 400
        
        # Initialize BigQuery client
        project_id = os.getenv('GCP_PROJECT', 'generative-ai-418805')
        dataset_id = 'budget_alert'
        bq_client = bigquery.Client(project=project_id)
        
        # Update anomalies in BigQuery
        if action_method == 'acknowledge_anomaly':
            update_query = f"""
            UPDATE `{project_id}.{dataset_id}.meta_anomalies`
            SET 
                acknowledged = @acknowledged,
                acknowledged_by = @acknowledged_by,
                acknowledged_at = CURRENT_TIMESTAMP(),
                acknowledgment_note = @note
            WHERE anomaly_id IN UNNEST(@anomaly_ids)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("anomaly_ids", "STRING", anomaly_ids),
                    bigquery.ScalarQueryParameter("acknowledged", "BOOLEAN", acknowledged),
                    bigquery.ScalarQueryParameter("acknowledged_by", "STRING", user_email),
                    bigquery.ScalarQueryParameter("note", "STRING", 
                        f"Acknowledged via Google Chat by {user_name}" if acknowledged 
                        else f"Marked as false positive by {user_name}")
                ]
            )
            
            try:
                query_job = bq_client.query(update_query, job_config=job_config)
                query_job.result()  # Wait for the query to complete
                
                # Return success message
                if acknowledged:
                    return {
                        'text': f'✅ Alert acknowledged by {user_name}. This budget increase has been marked as legitimate.',
                        'thread': request_json.get('message', {}).get('thread', {})
                    }
                else:
                    return {
                        'text': f'✅ Alert marked as false positive by {user_name}. Future alerts for this specific budget amount will be suppressed.',
                        'thread': request_json.get('message', {}).get('thread', {})
                    }
                    
            except Exception as e:
                print(f"Error updating anomalies: {e}")
                return {
                    'text': f'❌ Failed to update anomaly: {str(e)}',
                    'thread': request_json.get('message', {}).get('thread', {})
                }, 500
        
        else:
            return {
                'text': f'❌ Unknown action: {action_method}',
                'thread': request_json.get('message', {}).get('thread', {})
            }, 400
            
    except Exception as e:
        print(f"Error handling chat interaction: {e}")
        return {'text': f'❌ Error: {str(e)}'}, 500