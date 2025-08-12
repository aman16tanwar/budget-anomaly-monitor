import os
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

# Check if webhook URL is loaded
webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
print(f"Webhook URL loaded: {'Yes' if webhook_url else 'No'}")
if webhook_url:
    print(f"URL starts with: {webhook_url[:50]}...")
    print(f"Full URL length: {len(webhook_url)} characters")
else:
    print("❌ GOOGLE_CHAT_WEBHOOK_URL not found in .env file")

# Test sending a message
if webhook_url:
    import requests
    import json
    
    test_message = {
        "text": "🧪 Test notification from Budget Anomaly Monitor"
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=test_message,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✅ Test message sent successfully!")
        else:
            print(f"❌ Failed to send message. Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")