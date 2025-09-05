# Unified Budget Monitor Dashboard

Multi-platform budget anomaly detection dashboard for Meta Ads and Google Ads campaigns.

## Features

- **Multi-Platform Support**: Monitor both Meta Ads and Google Ads campaigns
- **Real-time Monitoring**: Live data from BigQuery with auto-refresh options
- **Anomaly Detection**: Visual alerts for budget anomalies with severity levels
- **Platform Identification**: Clear visual indicators for Meta vs Google Ads
- **Professional UI**: Dark theme with platform-specific branding

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Credentials**:
   - Ensure `meta.json` (Google Cloud credentials) is in this directory
   - The `.env` file should contain `GCP_PROJECT_ID=generative-ai-418805`
   - Files are already configured if copied from unified parent directory

3. **Run Dashboard**:
   ```bash
   python run_dashboard.py
   ```
   
   Or directly with Streamlit:
   ```bash
   streamlit run dashboard.py --server.port 8501
   ```

4. **Access Dashboard**:
   - Open browser to http://localhost:8501
   - Login credentials: username=`admin`/`viewer`, password=`12345`

## Platform Support

### Meta Ads (Facebook)
- Blue branding and 🔵 indicators
- Queries `meta_campaign_snapshots` and `meta_anomalies` tables

### Google Ads  
- Red/Google branding and 🔴 indicators
- Queries `google_ads_campaign_snapshots` and `google_ads_anomalies` tables

## Dashboard Sections

1. **Active Campaigns**: Overview of all campaigns across platforms
2. **Anomalies**: Budget anomalies with severity levels and platform breakdown
3. **Budget Trends**: Time-series analysis and platform comparisons
4. **Settings**: System configuration and data freshness status

## Authentication

Uses simple hash-based authentication. Default credentials:
- Username: `admin` or `viewer` 
- Password: `12345` (change in production)

Sessions last 24 hours before re-authentication is required.