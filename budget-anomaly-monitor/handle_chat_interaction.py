"""
Google Chat Interaction Handler for Budget Anomaly Acknowledgments
Handles button clicks from Google Chat interactive cards
"""

import os
import json
from datetime import datetime
from google.cloud import bigquery
from flask import Request, jsonify

def handle_chat_interaction(request: Request):
    """
    Cloud Function to handle Google Chat interactive button clicks
    
    This function processes acknowledgment buttons from budget alerts
    """
    try:
        # Parse the request from Google Chat
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return jsonify({'text': 'Invalid request'}), 400
        
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
            return jsonify({'text': '❌ No anomaly IDs provided'}), 400
        
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
                    return jsonify({
                        'text': f'✅ {len(anomaly_ids)} anomalies acknowledged by {user_name}',
                        'thread': request_json.get('message', {}).get('thread', {})
                    })
                else:
                    return jsonify({
                        'text': f'✅ {len(anomaly_ids)} anomalies marked as false positive by {user_name}',
                        'thread': request_json.get('message', {}).get('thread', {})
                    })
                    
            except Exception as e:
                print(f"Error updating anomalies: {e}")
                return jsonify({
                    'text': f'❌ Failed to update anomalies: {str(e)}',
                    'thread': request_json.get('message', {}).get('thread', {})
                }), 500
        
        # Handle view details action
        elif action_method == 'view_details':
            # Query anomaly details
            query = f"""
            SELECT 
                anomaly_id,
                campaign_name,
                account_name,
                anomaly_category,
                message,
                current_budget,
                previous_budget,
                detected_at,
                acknowledged,
                acknowledged_by,
                acknowledged_at
            FROM `{project_id}.{dataset_id}.meta_anomalies`
            WHERE anomaly_id IN UNNEST(@anomaly_ids)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("anomaly_ids", "STRING", anomaly_ids),
                ]
            )
            
            try:
                query_job = bq_client.query(query, job_config=job_config)
                results = list(query_job)
                
                if results:
                    details_text = "📊 **Anomaly Details:**\n\n"
                    for row in results:
                        details_text += f"**Campaign:** {row['campaign_name']}\n"
                        details_text += f"**Account:** {row['account_name']}\n"
                        details_text += f"**Type:** {row['anomaly_category']}\n"
                        details_text += f"**Message:** {row['message']}\n"
                        details_text += f"**Current Budget:** ${row['current_budget']:,.2f}\n"
                        if row['previous_budget']:
                            details_text += f"**Previous Budget:** ${row['previous_budget']:,.2f}\n"
                        details_text += f"**Detected:** {row['detected_at']}\n"
                        if row['acknowledged']:
                            details_text += f"**Acknowledged by:** {row['acknowledged_by']} at {row['acknowledged_at']}\n"
                        details_text += "\n---\n\n"
                    
                    return jsonify({
                        'text': details_text,
                        'thread': request_json.get('message', {}).get('thread', {})
                    })
                else:
                    return jsonify({
                        'text': '❌ No anomaly details found',
                        'thread': request_json.get('message', {}).get('thread', {})
                    })
                    
            except Exception as e:
                print(f"Error querying anomaly details: {e}")
                return jsonify({
                    'text': f'❌ Failed to retrieve details: {str(e)}',
                    'thread': request_json.get('message', {}).get('thread', {})
                }), 500
        
        else:
            return jsonify({
                'text': f'❌ Unknown action: {action_method}',
                'thread': request_json.get('message', {}).get('thread', {})
            }), 400
            
    except Exception as e:
        print(f"Error handling chat interaction: {e}")
        return jsonify({'text': f'❌ Error: {str(e)}'}), 500