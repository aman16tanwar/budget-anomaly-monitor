#!/usr/bin/env python3
"""
Run script for Unified Budget Monitor Dashboard
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    print("🚀 Starting Unified Budget Monitor Dashboard...")
    print(f"📁 Working directory: {dashboard_dir}")
    print("🌐 Dashboard will be available at: http://localhost:8501")
    print("---")
    
    # Set up environment variables
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(dashboard_dir / 'meta.json')
    os.environ['GCP_PROJECT_ID'] = 'generative-ai-418805'
    
    # Check if credentials file exists
    creds_path = dashboard_dir / 'meta.json'
    if not creds_path.exists():
        print("❌ Error: meta.json credentials file not found!")
        print("📋 Please copy your Google Cloud credentials file to:")
        print(f"   {creds_path}")
        sys.exit(1)
    
    print("✅ Google Cloud credentials found")
    print("📊 Loading unified dashboard...")
    
    try:
        # Run streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.port", "8501"]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()