#!/usr/bin/env python3
"""
Web wrapper for Meta Ads Budget Monitoring
Provides HTTP endpoint for Cloud Run Service
"""
from flask import Flask, jsonify
import os
import threading
from datetime import datetime
from cloud_run_job import main as run_monitor

app = Flask(__name__)

# Track last run time
last_run = None
is_running = False

@app.route('/')
def index():
    return jsonify({
        "service": "Meta Ads Budget Monitor",
        "status": "healthy",
        "last_run": last_run.isoformat() if last_run else None
    })

@app.route('/run')
def trigger_monitor():
    global last_run, is_running
    
    if is_running:
        return jsonify({
            "status": "already_running",
            "message": "Monitor is already running"
        }), 429
    
    # Run monitor in background thread
    def run_async():
        global is_running, last_run
        is_running = True
        try:
            run_monitor()
            last_run = datetime.now()
        finally:
            is_running = False
    
    thread = threading.Thread(target=run_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "triggered",
        "message": "Budget monitor started"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)