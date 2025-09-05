"""
Unified Multi-Platform Budget Monitoring Dashboard
Real-time monitoring and analytics for Meta Ads and Google Ads campaigns
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import base64
import contextlib
import pytz
from PIL import Image

# Load environment variables
load_dotenv()

# Page configuration - MUST BE FIRST
page_icon = "💰"  # Multi-platform icon
favicon_path = os.path.join(os.path.dirname(__file__), "favicon.png")
if os.path.exists(favicon_path):
    page_icon = favicon_path

st.set_page_config(
    page_title="Unified Budget Monitor - Meta & Google Ads",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force dark theme
st.markdown("""
<style>
/* Force dark theme globally */
.stApp {
    background-color: #0e1117 !important;
    color: #fafafa !important;
}
</style>
""", unsafe_allow_html=True)

# Custom CSS for dark theme with blue accents - EXACT Original Meta Production Style
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* AGGRESSIVE Reset and base styles - FORCE DARK MODE */
    .stApp {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }
    
    /* Force all main content to be dark */
    .main {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }
    
    /* Force all containers to be dark */
    .block-container {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }
    
    /* Force all elements to have visible text */
    .stMarkdown, .stText, p, span, div {
        color: #fafafa !important;
    }
    
    /* Override Streamlit's default white backgrounds */
    .element-container {
        background-color: transparent !important;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove top padding/margin from Streamlit app */
    .main > div {
        padding-top: 0rem !important;
    }
    
    .stApp > div > div {
        padding-top: 0rem !important;
    }
    
    /* Remove default Streamlit header space */
    .stApp [data-testid="stToolbar"] {
        display: none !important;
    }
    
    .stApp [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Custom header styling - Professional layout */
    .dashboard-header {
        background: linear-gradient(90deg, #1a1f2e 0%, #0e1117 100%);
        padding: 1.25rem 2rem;
        margin: -1rem -1rem 1.5rem -1rem;
        border-bottom: 2px solid #4da3ff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .dashboard-header-left {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    
    .dashboard-logo {
        height: 45px;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
    }
    
    .dashboard-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.02em;
    }
    
    .dashboard-subtitle {
        font-size: 0.9rem;
        color: #94a3b8;
        margin: 0;
        font-family: 'Inter', sans-serif;
    }
    
    .dashboard-header-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.25rem;
    }
    
    .last-updated {
        font-size: 0.8rem;
        color: #64748b;
        font-family: 'Inter', sans-serif;
    }
    
    .update-time {
        font-size: 1rem;
        color: #4da3ff;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #1a1f2e;
        border: 1px solid #2d3748;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        border-color: #4da3ff;
        box-shadow: 0 6px 12px rgba(77, 163, 255, 0.2);
        transform: translateY(-2px);
    }
    
    div[data-testid="metric-container"] > label {
        color: #94a3b8 !important;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.875rem;
        letter-spacing: 0.05em;
    }
    
    div[data-testid="metric-container"] [data-testid="metric-value"] {
        color: #4da3ff !important;
        font-weight: 700;
        font-size: 2rem;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1a1f2e;
        border-right: 1px solid #2d3748;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #1a1f2e;
        padding-top: 2rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        border-bottom: 2px solid #2d3748;
        padding-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #94a3b8;
        border: none;
        font-weight: 500;
        font-size: 1rem;
        padding: 0.75rem 1.5rem;
        border-radius: 8px 8px 0 0;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #4da3ff;
        background-color: rgba(77, 163, 255, 0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4da3ff !important;
        color: white !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #4da3ff;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
    }
    
    .stButton > button:hover {
        background-color: #2d8ff0;
        box-shadow: 0 4px 12px rgba(77, 163, 255, 0.3);
        transform: translateY(-1px);
    }
    
    /* Input field styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div,
    .stDateInput > div > div > input {
        background-color: #2d3748;
        border: 1px solid #4a5568;
        color: #fafafa;
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #4da3ff;
        box-shadow: 0 0 0 1px #4da3ff;
    }
    
    /* AGGRESSIVE DataFrame styling - FORCE DARK MODE */
    .dataframe {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
        border: none !important;
    }
    
    .dataframe thead tr th {
        background-color: #2d3748 !important;
        color: #4da3ff !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 1rem 0.5rem !important;
        border-bottom: 2px solid #4a5568 !important;
    }
    
    .dataframe tbody tr {
        border-bottom: 1px solid #2d3748 !important;
        background-color: #1a1f2e !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: rgba(77, 163, 255, 0.05) !important;
    }
    
    .dataframe tbody tr td {
        padding: 0.75rem 0.5rem !important;
        color: #fafafa !important;
        background-color: #1a1f2e !important;
    }
    
    /* FORCE Streamlit dataframe dark mode - AGGRESSIVE OVERRIDES */
    [data-testid="stDataFrame"] {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    [data-testid="stDataFrame"] > div {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    [data-testid="stDataFrame"] iframe {
        background-color: #1a1f2e !important;
    }
    
    /* Additional AGGRESSIVE table styling fixes */
    .stDataFrame {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    .stDataFrame table {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    .stDataFrame table tbody tr {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    .stDataFrame table tbody tr td {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    .stDataFrame table thead tr th {
        background-color: #2d3748 !important;
        color: #4da3ff !important;
    }
    
    /* Force all text elements to be visible */
    .stDataFrame * {
        color: #fafafa !important;
        background-color: #1a1f2e !important;
    }
    
    /* Override any white backgrounds */
    div[data-testid="stDataFrame"] div {
        background-color: #1a1f2e !important;
    }
    
    div[data-testid="stDataFrame"] table {
        background-color: #1a1f2e !important;
    }
    
    /* More specific overrides for stubborn elements */
    .element-container div[data-testid="stDataFrame"] {
        background-color: #1a1f2e !important;
    }
    
    .stDataFrame > div > div > div > div {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    /* Ultimate override - target the actual data cells */
    [data-testid="stDataFrame"] [role="gridcell"] {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    [data-testid="stDataFrame"] [role="columnheader"] {
        background-color: #2d3748 !important;
        color: #4da3ff !important;
    }
    
    /* Force override any inline styles */
    [data-testid="stDataFrame"] * {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    [data-testid="stDataFrame"] th {
        background-color: #2d3748 !important;
        color: #4da3ff !important;
    }
    
    /* CRITICAL: Force all table text to be white */
    table, table * {
        color: #fafafa !important;
        background-color: #1a1f2e !important;
    }
    
    table th, table th * {
        color: #4da3ff !important;
        background-color: #2d3748 !important;
    }
    
    /* Override any Streamlit default table styles */
    .stDataFrame table {
        color: #fafafa !important;
        background-color: #1a1f2e !important;
    }
    
    .stDataFrame table td {
        color: #fafafa !important;
        background-color: #1a1f2e !important;
    }
    
    .stDataFrame table th {
        color: #4da3ff !important;
        background-color: #2d3748 !important;
    }
    
    /* st.table() styling for dark mode */
    .stTable {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
    }
    
    .stTable table {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
        border: none !important;
    }
    
    .stTable table thead tr th {
        background-color: #2d3748 !important;
        color: #4da3ff !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
        padding: 1rem 0.5rem !important;
        border-bottom: 2px solid #4a5568 !important;
    }
    
    .stTable table tbody tr {
        background-color: #1a1f2e !important;
        border-bottom: 1px solid #2d3748 !important;
    }
    
    .stTable table tbody tr:hover {
        background-color: rgba(77, 163, 255, 0.05) !important;
    }
    
    .stTable table tbody tr td {
        background-color: #1a1f2e !important;
        color: #fafafa !important;
        padding: 0.75rem 0.5rem !important;
    }
    
    /* High budget highlighting */
    .high-budget-tag {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 0.5rem;
    }
    
    .very-high-budget-tag {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 0.5rem;
    }
    
    .budget-warning {
        color: #f59e0b !important;
        font-weight: 600;
    }
    
    .budget-critical {
        color: #ef4444 !important;
        font-weight: 700;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(77, 163, 255, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(77, 163, 255, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(77, 163, 255, 0);
        }
    }
    
    /* Apply animations to elements */
    div[data-testid="metric-container"] {
        animation: fadeIn 0.6s ease-out;
        animation-fill-mode: both;
    }
    
    div[data-testid="metric-container"]:nth-child(1) {
        animation-delay: 0.1s;
    }
    
    div[data-testid="metric-container"]:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    div[data-testid="metric-container"]:nth-child(3) {
        animation-delay: 0.3s;
    }
    
    div[data-testid="metric-container"]:nth-child(4) {
        animation-delay: 0.4s;
    }
    
    .stTabs {
        animation: fadeIn 0.8s ease-out;
    }
    
    .dataframe {
        animation: fadeIn 1s ease-out;
    }
    
    .stButton > button {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Smooth transitions for all interactive elements */
    * {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1f2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4a5568;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4da3ff;
    }
    
</style>
""", unsafe_allow_html=True)

# Initialize BigQuery client
def init_bigquery():
    """Initialize BigQuery client with proper credentials"""
    project_id = os.getenv('GCP_PROJECT_ID', 'generative-ai-418805')
    
    # Set up credentials path
    credentials_path = os.path.join(os.path.dirname(__file__), 'meta.json')
    if os.path.exists(credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    client = bigquery.Client(project=project_id)
    return client, project_id

client, project_id = init_bigquery()
dataset_id = "budget_alert"

# Get latest data timestamp
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_latest_data_timestamp():
    """Get the most recent snapshot timestamp from BigQuery"""
    try:
        query = f"""
        SELECT MAX(snapshot_timestamp) as latest_timestamp
        FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
        """
        result = client.query(query).to_dataframe()
        if not result.empty and result['latest_timestamp'].iloc[0] is not None:
            timestamp = result['latest_timestamp'].iloc[0]
            # Convert to regular datetime if it's a BigQuery timestamp
            if hasattr(timestamp, 'to_pydatetime'):
                return timestamp.to_pydatetime()
            return timestamp
    except Exception as e:
        st.warning(f"Could not fetch data timestamp: {str(e)}")
    return datetime.now()  # Fallback to current time

# Custom spinner with loader GIF
@contextlib.contextmanager
def custom_spinner(message="Loading..."):
    """Display a custom spinner with the loader GIF"""
    placeholder = st.empty()
    
    try:
        placeholder.info(f"🔄 {message}")
        yield
    finally:
        placeholder.empty()

# Header with logo support - Professional version
def display_header():
    # Get actual data timestamp
    data_timestamp = get_latest_data_timestamp()
    
    # Convert UTC timestamp from BigQuery to PST for display
    if isinstance(data_timestamp, (datetime, pd.Timestamp)):
        # Convert to datetime if it's a pandas Timestamp
        if isinstance(data_timestamp, pd.Timestamp):
            data_timestamp = data_timestamp.to_pydatetime()
        
        # BigQuery returns UTC timestamps as timezone-naive, so we need to localize
        if data_timestamp.tzinfo is None:
            # Localize as UTC first
            utc = pytz.UTC
            data_timestamp = utc.localize(data_timestamp)
        
        # Convert to PST
        pst = pytz.timezone('America/Los_Angeles')
        data_timestamp_pst = data_timestamp.astimezone(pst)
        
        # Format the PST time
        formatted_time = data_timestamp_pst.strftime('%I:%M %p PST')
        
        # Calculate how long ago using PST times
        now_pst = datetime.now(pst)
        time_diff = now_pst - data_timestamp_pst
        minutes_ago = int(time_diff.total_seconds() / 60)
        
        if minutes_ago < 1:
            time_ago = "just now"
        elif minutes_ago == 1:
            time_ago = "1 minute ago"
        elif minutes_ago < 60:
            time_ago = f"{minutes_ago} minutes ago"
        else:
            hours_ago = minutes_ago // 60
            time_ago = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"
    else:
        formatted_time = datetime.now().strftime('%I:%M %p PST')
        time_ago = ""
    
    # Default header without logo
    header_html = f"""
    <div class="dashboard-header">
        <div class="dashboard-header-left">
            <div style="font-size: 2.5rem;">💰</div>
            <div>
                <h1 class="dashboard-title">Unified Budget Monitor</h1>
                <div class="dashboard-subtitle">Multi-Platform Budget Tracking & Analytics</div>
            </div>
        </div>
        <div class="dashboard-header-right" style="display: flex; align-items: center; gap: 1rem;">
            <div>
                <div class="last-updated">Data updated</div>
                <div class="update-time">{formatted_time}</div>
                {f'<div style="font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">{time_ago}</div>' if time_ago else ''}
            </div>
        </div>
    </div>
    """
    
    # Try to load logo if it exists
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
            header_html = f"""
            <div class="dashboard-header">
                <div class="dashboard-header-left">
                    <img src="data:image/png;base64,{logo_data}" class="dashboard-logo" alt="Logo">
                    <div>
                        <h1 class="dashboard-title">Unified Budget Monitor</h1>
                        <div class="dashboard-subtitle">Multi-Platform Budget Tracking & Analytics</div>
                    </div>
                </div>
                <div class="dashboard-header-right" style="display: flex; align-items: center; gap: 1rem;">
                    <div>
                        <div class="last-updated">Data updated</div>
                        <div class="update-time">{formatted_time}</div>
                        {f'<div style="font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">{time_ago}</div>' if time_ago else ''}
                    </div>
                </div>
            </div>
            """
        except:
            pass
    
    st.markdown(header_html, unsafe_allow_html=True)

# Display header first
display_header()

# Initialize help modal state
if 'show_help' not in st.session_state:
    st.session_state.show_help = False

# Add help button right after header
col1, col2, col3 = st.columns([6, 3, 1])
with col3:
    if st.button("❓", key="help_button", help="View documentation", type="secondary"):
        st.session_state.show_help = not st.session_state.show_help

# Cache for accounts data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_accounts():
    """Get all unique account IDs from both platforms"""
    try:
        accounts = []
        
        # Get Meta accounts
        try:
            meta_query = f"""
            SELECT DISTINCT account_id, account_name, COUNT(*) as campaign_count
            FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
            WHERE DATE(snapshot_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY account_id, account_name
            ORDER BY account_name
            """
            meta_accounts = client.query(meta_query).to_dataframe()
            
            if not meta_accounts.empty:
                st.info(f"Found {len(meta_accounts)} Meta Ads accounts")  # Debug info
                for _, row in meta_accounts.iterrows():
                    account_name = row.get('account_name', row['account_id'])
                    accounts.append({
                        'id': str(row['account_id']),
                        'display': f"🔵 {account_name} ({row['account_id']}) - {row['campaign_count']} campaigns",
                        'platform': 'Meta Ads'
                    })
            else:
                st.warning("No Meta Ads accounts found in recent data")
        except Exception as e:
            st.warning(f"Could not load Meta accounts: {str(e)}")
            st.write("**Debug - Meta Query:**")
            st.code(f"""
            SELECT DISTINCT account_id, account_name, COUNT(*) as campaign_count
            FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
            WHERE DATE(snapshot_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY account_id, account_name
            ORDER BY account_name
            """)
        
        # Get Google accounts - check multiple possible table configurations
        google_table_found = False
        for table_suffix in ['google_ads_campaign_snapshots']:
            try:
                # Test if table exists first
                test_query = f"""
                SELECT COUNT(*) as total_rows
                FROM `{project_id}.{dataset_id}.{table_suffix}`
                LIMIT 1
                """
                test_result = client.query(test_query).to_dataframe()
                
                if not test_result.empty:
                    st.info(f"✅ Found Google Ads table: {table_suffix} ({test_result.iloc[0]['total_rows']} total rows)")
                    
                    # First, let's see how many total accounts exist in google_ads table
                    total_accounts_query = f"""
                    SELECT COUNT(*) as total_google_accounts
                    FROM `{project_id}.{dataset_id}.google_ads`
                    """
                    total_accounts_result = client.query(total_accounts_query).to_dataframe()
                    if not total_accounts_result.empty:
                        st.info(f"📊 Total Google Ads accounts in google_ads table: {total_accounts_result.iloc[0]['total_google_accounts']}")
                    
                    # Also check how many unique account_ids are in the campaigns table  
                    unique_campaign_accounts_query = f"""
                    SELECT COUNT(DISTINCT account_id) as unique_account_ids
                    FROM `{project_id}.{dataset_id}.{table_suffix}`
                    """
                    unique_accounts_result = client.query(unique_campaign_accounts_query).to_dataframe()
                    if not unique_accounts_result.empty:
                        st.info(f"📊 Unique account IDs in {table_suffix}: {unique_accounts_result.iloc[0]['unique_account_ids']}")
                    
                    # Use the google_ads table directly for account names
                    
                    # Use the google_ads table to get ALL account names (remove date and count restrictions)
                    google_query = f"""
                    WITH all_campaign_accounts AS (
                        SELECT DISTINCT account_id, COUNT(*) as campaign_count
                        FROM `{project_id}.{dataset_id}.{table_suffix}`
                        GROUP BY account_id  -- Remove date filter to get ALL accounts
                    )
                    SELECT 
                        CAST(ga.id AS STRING) as account_id,
                        ga.descriptive_name as account_name,
                        COALESCE(ca.campaign_count, 0) as campaign_count,
                        ga.status as account_status
                    FROM `{project_id}.{dataset_id}.google_ads` ga
                    LEFT JOIN all_campaign_accounts ca ON CAST(ga.id AS STRING) = ca.account_id
                    WHERE ca.campaign_count > 0 OR ga.status = 'ENABLED'  -- Show accounts with campaigns OR enabled accounts
                    ORDER BY ga.descriptive_name
                    LIMIT 200  -- Increased limit
                    """
                    
                    google_accounts = client.query(google_query).to_dataframe()
                    
                    if not google_accounts.empty:
                        st.info(f"✅ Found {len(google_accounts)} Google Ads accounts with names")
                        
                        # Debug info about account distribution
                        with_campaigns = len(google_accounts[google_accounts['campaign_count'] > 0])
                        without_campaigns = len(google_accounts[google_accounts['campaign_count'] == 0])
                        
                        st.write(f"**Account breakdown:**")
                        st.write(f"- {with_campaigns} accounts with campaigns")
                        st.write(f"- {without_campaigns} accounts without campaigns (but enabled)")
                        
                        # Show top 5 accounts for verification
                        st.write(f"**Sample accounts found:**")
                        for i, (_, row) in enumerate(google_accounts.head().iterrows()):
                            st.write(f"- {row.get('account_name', 'No name')} ({row['account_id']}) - {row.get('campaign_count', 0)} campaigns")
                        
                        for _, row in google_accounts.iterrows():
                            account_name = row.get('account_name', '').strip()
                            account_id = str(row['account_id'])
                            campaign_count = row.get('campaign_count', 0)
                            
                            # Create display name with proper account name from google_ads table
                            if account_name and account_name != account_id:
                                display_name = f"🔴 {account_name} ({account_id}) - {campaign_count} campaigns"
                            else:
                                # Fallback if descriptive_name is empty
                                display_name = f"🔴 Google Ads {account_id} - {campaign_count} campaigns"
                            
                            accounts.append({
                                'id': account_id,
                                'display': display_name,
                                'platform': 'Google Ads'
                            })
                        google_table_found = True
                        break
                    else:
                        st.warning(f"Table {table_suffix} exists but no recent accounts found")
                        
            except Exception as e:
                st.warning(f"Table {table_suffix} not found or error: {str(e)}")
                continue
        
        if not google_table_found:
            st.warning("⚠️ Google Ads tables not found - The monitoring job may not have run yet")
            st.write("**Next Steps:**")
            st.write("1. Run the Google Ads monitoring job to create and populate tables:")
            st.code("python3 google_ads_main.py", language="bash")
            st.write("2. Or run the unified monitoring job:")
            st.code("python3 unified_budget_monitoring_job.py", language="bash")
            st.write("**Expected table names:**")
            st.write("- google_ads_campaign_snapshots (main campaigns data)")
            st.write("- google_ads (accounts/customers data)")
            st.write("- google_ads_current_state (current state tracking)")
        
        # Always show available tables to find accounts/customers table
        try:
            st.write("### 🔍 Checking for Google Ads accounts/customers tables...")
            tables_query = f"""
            SELECT table_name 
            FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
            WHERE table_name LIKE '%google%' OR table_name LIKE '%ads%' OR table_name LIKE '%customer%' OR table_name LIKE '%account%'
            ORDER BY table_name
            """
            available_tables = client.query(tables_query).to_dataframe()
            if not available_tables.empty:
                st.write("**Available tables that might contain account names:**")
                for _, table in available_tables.iterrows():
                    st.write(f"- {table['table_name']}")
                    
                # Check for common account table patterns
                account_table_candidates = [
                    'google_ads_current_state',  # This looks promising!
                    'google_ads',  # This too!
                    'google_ads_customers',
                    'google_ads_accounts', 
                    'googleads_customers',
                    'googleads_accounts',
                    'google_customers',
                    'google_accounts'
                ]
                
                for candidate_table in account_table_candidates:
                    if candidate_table in available_tables['table_name'].values:
                        st.info(f"🎯 Found potential accounts table: {candidate_table}")
                        
                        # Check its schema
                        try:
                            schema_query = f"""
                            SELECT column_name, data_type
                            FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
                            WHERE table_name = '{candidate_table}'
                            ORDER BY column_name
                            """
                            account_schema = client.query(schema_query).to_dataframe()
                            st.write(f"**Columns in {candidate_table}:**")
                            for _, col in account_schema.iterrows():
                                st.write(f"- {col['column_name']} ({col['data_type']})")
                                
                            # Sample data
                            sample_query = f"""
                            SELECT * FROM `{project_id}.{dataset_id}.{candidate_table}` LIMIT 3
                            """
                            sample_accounts = client.query(sample_query).to_dataframe()
                            if not sample_accounts.empty:
                                st.write(f"**Sample data from {candidate_table}:**")
                                st.dataframe(sample_accounts.head(3))
                        except Exception as e:
                            st.write(f"Error checking {candidate_table}: {e}")
                            
            else:
                st.write("No Google/Ads tables found")
        except Exception as e:
            st.write(f"Error checking tables: {e}")
        
        # Summary of what was found
        meta_accounts_count = len([acc for acc in accounts if acc['platform'] == 'Meta Ads'])
        google_accounts_count = len([acc for acc in accounts if acc['platform'] == 'Google Ads'])
        
        st.success(f"✅ Account Loading Complete: {meta_accounts_count} Meta Ads + {google_accounts_count} Google Ads = {len(accounts)} total accounts")
        
        return accounts
        
    except Exception as e:
        st.error(f"Error fetching accounts: {str(e)}")
        return []

# Get unified campaigns data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_unified_campaigns(days=7, selected_account_ids=None, platform_filter=None):
    """Get campaigns from both Meta and Google Ads with account filtering"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    all_campaigns = []
    
    # Meta Ads query
    if not platform_filter or 'Meta Ads' in platform_filter:
        try:
            meta_where = f"DATE(snapshot_timestamp) >= '{start_date.strftime('%Y-%m-%d')}'" 
            if selected_account_ids:
                account_list = "', '".join(selected_account_ids)
                meta_where += f" AND account_id IN ('{account_list}')"
                
            meta_query = f"""
            WITH latest AS (
                SELECT 
                    'Meta Ads' as platform,
                    account_id,
                    account_name,
                    campaign_id,
                    campaign_name,
                    CAST(budget_amount AS FLOAT64) as budget_amount,
                    budget_currency as currency,
                    campaign_status as status,
                    budget_type,
                    objective,
                    created_time,
                    start_time,
                    stop_time,
                    delivery_status_simple as delivery_status,
                    snapshot_timestamp,
                    ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
                FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
                WHERE {meta_where} AND campaign_status = 'ACTIVE'
            )
            SELECT 
                platform,
                account_id,
                account_name,
                campaign_id,
                campaign_name,
                budget_amount,
                currency,
                status,
                budget_type,
                objective,
                created_time,
                start_time,
                stop_time,
                delivery_status,
                snapshot_timestamp
            FROM latest
            WHERE rn = 1
            ORDER BY budget_amount DESC
            LIMIT 1000
            """
            
            meta_df = client.query(meta_query).to_dataframe()
            if not meta_df.empty:
                all_campaigns.append(meta_df)
                
        except Exception as e:
            st.warning(f"Could not load Meta Ads data: {str(e)}")
    
    # Google Ads query
    if not platform_filter or 'Google Ads' in platform_filter:
        try:
            google_where = f"DATE(snapshot_time) >= '{start_date.strftime('%Y-%m-%d')}'"
            if selected_account_ids:
                account_list = "', '".join(selected_account_ids)
                google_where += f" AND account_id IN ('{account_list}')"
                
            google_query = f"""
            WITH latest AS (
                SELECT 
                    'Google Ads' as platform,
                    account_id,
                    account_id as account_name,  -- Google Ads doesn't have account_name, use account_id
                    campaign_id,
                    campaign_name,
                    CAST(budget_amount AS FLOAT64) as budget_amount,
                    currency,
                    status,
                    'daily' as budget_type,  -- Google Ads uses daily budgets
                    'CONVERSIONS' as objective,  -- Google Ads default objective
                    created_date as created_time,
                    created_date as start_time,  -- Use created_date as start_time
                    NULL as stop_time,  -- Google Ads doesn't have stop_time
                    'ACTIVE' as delivery_status,  -- Default delivery status
                    snapshot_time as snapshot_timestamp,
                    business_hours_flag,
                    ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_time DESC) as rn
                FROM `{project_id}.{dataset_id}.google_ads_campaign_snapshots`
                WHERE {google_where} AND status = 'ENABLED'
            )
            SELECT 
                platform,
                account_id,
                account_name,
                campaign_id,
                campaign_name,
                budget_amount,
                currency,
                status,
                budget_type,
                objective,
                created_time,
                start_time,
                stop_time,
                delivery_status,
                snapshot_timestamp
            FROM latest
            WHERE rn = 1
            ORDER BY budget_amount DESC
            LIMIT 1000
            """
            
            google_df = client.query(google_query).to_dataframe()
            if not google_df.empty:
                all_campaigns.append(google_df)
                
        except Exception as e:
            st.warning(f"Could not load Google Ads data: {str(e)}")
    
    # Combine dataframes
    if all_campaigns:
        combined_df = pd.concat(all_campaigns, ignore_index=True)
        # Ensure consistent data types
        combined_df['budget_amount'] = pd.to_numeric(combined_df['budget_amount'], errors='coerce').fillna(0)
        combined_df['snapshot_timestamp'] = pd.to_datetime(combined_df['snapshot_timestamp'], errors='coerce')
        return combined_df
    else:
        return pd.DataFrame()

# Sidebar filters
with st.sidebar:
    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        try:
            st.image(logo_path, width=200)
        except:
            st.markdown("### 💰 Unified Budget Monitor")
    else:
        st.markdown("### 💰 Unified Budget Monitor")
        
    st.markdown("### 📊 Dashboard Controls")
    
    # Date range selector
    days = st.selectbox(
        "📅 Time Range",
        options=[1, 3, 7, 14, 30],
        index=2,
        format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}"
    )
    
    # Platform filter
    platform_filter = st.multiselect(
        "🎯 Platforms",
        options=["Meta Ads", "Google Ads"],
        default=["Meta Ads", "Google Ads"]
    )
    
    # Account filter
    with custom_spinner("Loading accounts..."):
        all_accounts_data = get_all_accounts()
        
    if all_accounts_data:
        # Display names for selection
        account_options = [acc['display'] for acc in all_accounts_data]
        
        selected_accounts_display = st.multiselect(
            "🏢 Filter by Accounts",
            options=account_options,
            default=account_options[:5] if len(account_options) > 5 else account_options
        )
        
        # Extract account IDs
        selected_account_ids = []
        for display_name in selected_accounts_display:
            matching_account = next((acc for acc in all_accounts_data if acc['display'] == display_name), None)
            if matching_account:
                selected_account_ids.append(matching_account['id'])
    else:
        selected_account_ids = None
        st.warning("No accounts found")
    
    # Budget filters (like production dashboard)
    st.markdown("### 🎯 Budget Filters")
    show_normal_budget = st.checkbox("✅ Normal Budget (Daily: <$500, Lifetime: <$15K)", value=True)
    show_high_budget = st.checkbox("⚠️ HIGH Budget (Daily: $500-1.9K, Lifetime: $15K-49K)", value=True)
    show_very_high_budget = st.checkbox("🚨 VERY HIGH Budget (Daily: $2K+, Lifetime: $50K+)", value=True)
    
    # Auto refresh
    auto_refresh = st.checkbox("🔄 Auto Refresh (30s)", value=False)
    if auto_refresh:
        st.rerun()

# Fetch data with error handling
try:
    with custom_spinner("Loading unified data..."):
        campaigns_df = get_unified_campaigns(
            days=days, 
            selected_account_ids=selected_account_ids, 
            platform_filter=platform_filter
        )
    
    # Apply budget filters (same logic as production dashboard)
    if not campaigns_df.empty:
        # Budget thresholds
        # Updated thresholds to match new risk calculation
        # For filtering, we'll use daily budget thresholds as baseline
        high_budget_threshold = 500   # Daily: $500+, Lifetime: $15K+
        very_high_budget_threshold = 2000  # Daily: $2K+, Lifetime: $50K+
        
        # Create budget-type aware filter conditions
        filter_conditions = []
        
        def create_budget_filter(budget_level):
            """Create filter condition based on budget level and type"""
            def budget_filter_func(row):
                budget = row.get('budget_amount', 0)
                budget_type = row.get('budget_type', 'daily')
                
                if pd.isna(budget) or budget == 0:
                    return budget_level == 'normal'
                
                if budget_type == 'daily':
                    if budget_level == 'normal':
                        return budget < 500
                    elif budget_level == 'high':
                        return 500 <= budget < 2000
                    elif budget_level == 'very_high':
                        return budget >= 2000
                else:  # lifetime
                    if budget_level == 'normal':
                        return budget < 15000
                    elif budget_level == 'high':
                        return 15000 <= budget < 50000
                    elif budget_level == 'very_high':
                        return budget >= 50000
                return False
            
            return campaigns_df.apply(budget_filter_func, axis=1)
        
        if show_normal_budget:
            filter_conditions.append(create_budget_filter('normal'))
        if show_high_budget:
            filter_conditions.append(create_budget_filter('high'))
        if show_very_high_budget:
            filter_conditions.append(create_budget_filter('very_high'))
        
        # Apply filters if any are selected
        if filter_conditions:
            # Combine all conditions with OR
            combined_filter = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined_filter = combined_filter | condition
            campaigns_df = campaigns_df[combined_filter]
        else:
            # If no filters selected, show empty dataframe
            campaigns_df = campaigns_df.iloc[0:0]
    
    # Debug info for troubleshooting
    if campaigns_df.empty:
        if not show_normal_budget and not show_high_budget and not show_very_high_budget:
            st.warning("⚠️ No budget filters selected. Please select at least one filter to view campaigns.")
        else:
            st.warning(f"⚠️ No campaigns found for selected filters:")
            st.write(f"- Days: {days}")
            st.write(f"- Platforms: {platform_filter}")
            st.write(f"- Selected accounts: {len(selected_account_ids) if selected_account_ids else 0}")
            st.write(f"- Budget filters: {[f for f, selected in [('Normal', show_normal_budget), ('HIGH', show_high_budget), ('VERY HIGH', show_very_high_budget)] if selected]}")
    else:
        st.success(f"✅ Loaded {len(campaigns_df):,} campaigns from {campaigns_df['platform'].nunique()} platforms")
        
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.write("**Debug Info:**")
    st.write(f"- Selected account IDs: {selected_account_ids}")
    st.write(f"- Platform filter: {platform_filter}")
    campaigns_df = pd.DataFrame()

# Main metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_campaigns = len(campaigns_df) if not campaigns_df.empty else 0
    st.metric(
        label="🎯 Total Campaigns",
        value=f"{total_campaigns:,}"
    )

with col2:
    try:
        if not campaigns_df.empty and 'budget_amount' in campaigns_df.columns:
            total_budget = float(campaigns_df['budget_amount'].fillna(0).sum())
        else:
            total_budget = 0
    except:
        total_budget = 0
        
    st.metric(
        label="💰 Total Budget",
        value=f"${total_budget:,.0f}",
        delta="CAD + USD"
    )

with col3:
    total_accounts = len(selected_account_ids) if selected_account_ids else 0
    st.metric(
        label="🏢 Active Accounts",
        value=f"{total_accounts:,}",
        delta=f"{len(platform_filter)} platforms"
    )
    
with col4:
    if not campaigns_df.empty:
        meta_count = len(campaigns_df[campaigns_df['platform'] == 'Meta Ads'])
        google_count = len(campaigns_df[campaigns_df['platform'] == 'Google Ads'])
    else:
        meta_count = google_count = 0
        
    st.metric(
        label="🔵🔴 Platform Split",
        value=f"{meta_count + google_count}",
        delta=f"M:{meta_count} G:{google_count}"
    )

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Active Campaigns", "📈 Budget Trends", "⚙️ Settings"])

with tab1:
    st.subheader("🎯 Active Campaigns - Multi-Platform View")
    
    # Debug section
    with st.expander("🔍 Debug Info", expanded=False):
        st.write(f"**Data shape:** {campaigns_df.shape if not campaigns_df.empty else 'Empty'}")
        if not campaigns_df.empty:
            st.write(f"**Columns:** {list(campaigns_df.columns)}")
            st.write(f"**Sample data:**")
            st.dataframe(campaigns_df.head(3), height=150)
    
    if not campaigns_df.empty:
        # Format display data
        display_df = campaigns_df.copy()
        
        # Format columns exactly like production dashboard
        try:
            # Budget thresholds (same as production)
            high_budget_threshold = 1000
            very_high_budget_threshold = 5000
            
            # 1. Platform with icons
            if 'platform' in display_df.columns:
                display_df['Platform'] = display_df['platform'].apply(lambda x: 
                    f"🔵 {x}" if x == "Meta Ads" else f"🔴 {x}"
                )
            
            # 2. Account name (or account ID for Google Ads)
            display_df['Account'] = display_df['account_name'].fillna(display_df['account_id'])
            
            # 3. Campaign name (keep as is)
            display_df['Campaign'] = display_df['campaign_name']
            
            # 4. Budget formatting
            if 'budget_amount' in display_df.columns:
                display_df['Budget'] = display_df['budget_amount'].apply(
                    lambda x: f"${float(x):,.0f}" if pd.notna(x) and x != 0 else "$0"
                )
            
            # 5. Smart Risk Level based on budget type and amount
            def calculate_smart_risk(row):
                budget = row.get('budget_amount', 0)
                budget_type = row.get('budget_type', 'daily')
                
                if pd.isna(budget) or budget == 0:
                    return '✅ Normal'
                
                # Different thresholds for daily vs lifetime budgets
                if budget_type == 'daily':
                    # Daily budget thresholds
                    if budget >= 2000:  # $2K+ daily = $60K+ monthly
                        return '🚨 VERY HIGH'
                    elif budget >= 500:  # $500+ daily = $15K+ monthly  
                        return '⚠️ HIGH'
                    else:
                        return '✅ Normal'
                else:  # lifetime budget
                    # Lifetime budget thresholds (more conservative)
                    if budget >= 50000:  # $50K+ lifetime
                        return '🚨 VERY HIGH'
                    elif budget >= 15000:  # $15K+ lifetime
                        return '⚠️ HIGH'  
                    else:
                        return '✅ Normal'
            
            display_df['Risk Level'] = display_df.apply(calculate_smart_risk, axis=1)
            
            # 6. Delivery status
            display_df['Delivery'] = display_df['delivery_status'].fillna('Active')
            
            # 7. Budget Type
            display_df['Type'] = display_df['budget_type'].fillna('daily')
            
            # 8. Objective
            display_df['Objective'] = display_df['objective'].fillna('CONVERSIONS')
            
            # 9. Created date formatting
            display_df['Created'] = pd.to_datetime(display_df['created_time'], errors='coerce').dt.strftime('%Y-%m-%d')
            display_df['Created'] = display_df['Created'].fillna('Unknown')
            
            # 10. Start date formatting  
            display_df['Start Date'] = pd.to_datetime(display_df['start_time'], errors='coerce').dt.strftime('%Y-%m-%d')
            display_df['Start Date'] = display_df['Start Date'].fillna('Not Set')
            
            # 11. End date formatting
            display_df['End Date'] = pd.to_datetime(display_df['stop_time'], errors='coerce').dt.strftime('%Y-%m-%d')
            display_df['End Date'] = display_df['End Date'].fillna('Ongoing')
            
            # 12. Days Active calculation (like production)
            try:
                created_times = pd.to_datetime(display_df['created_time'], errors='coerce')
                if created_times.dt.tz is not None:
                    created_times = created_times.dt.tz_localize(None)
                display_df['Days Active'] = (datetime.now() - created_times).dt.days
                display_df['Days Active'] = display_df['Days Active'].fillna(0).astype(int)
            except:
                display_df['Days Active'] = 0
            
            # Select columns in EXACT order as production dashboard
            available_cols = ['Platform', 'Account', 'Campaign', 'Budget', 'Risk Level', 
                            'Delivery', 'Type', 'Objective', 'Created', 'Start Date', 'End Date', 'Days Active']
            display_columns = [col for col in available_cols if col in display_df.columns]
            
            # Sort by budget amount by default (descending) - same as production
            display_df = display_df.sort_values('budget_amount', ascending=False)
            
            st.write(f"**Displaying {len(display_df)} campaigns** (sorted by budget, highest first):")
            
            # Professional Pagination System
            try:
                st.markdown("### 📊 Campaign Data")
                
                total_campaigns = len(display_df)
                
                # Page size selector
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    items_per_page = st.selectbox(
                        "📄 Items per page:",
                        options=[10, 25, 50, 100],
                        index=2,  # Default to 50
                        key="items_per_page"
                    )
                
                # Initialize page number in session state
                if 'current_page' not in st.session_state:
                    st.session_state.current_page = 1
                
                # Calculate pagination
                total_pages = (total_campaigns - 1) // items_per_page + 1
                current_page = st.session_state.current_page
                
                # Ensure current page is valid
                if current_page > total_pages:
                    st.session_state.current_page = total_pages
                    current_page = total_pages
                elif current_page < 1:
                    st.session_state.current_page = 1
                    current_page = 1
                
                # Calculate start and end indices
                start_idx = (current_page - 1) * items_per_page
                end_idx = min(start_idx + items_per_page, total_campaigns)
                
                # Page info
                with col2:
                    st.write(f"**Page {current_page} of {total_pages}**")
                with col3:
                    st.write(f"Showing {start_idx + 1}-{end_idx} of {total_campaigns:,} campaigns")
                
                # Navigation buttons
                nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([1, 1, 1, 1, 1, 1])
                
                with nav_col1:
                    if st.button("⏮️ First", disabled=(current_page <= 1), key="first_page"):
                        st.session_state.current_page = 1
                        st.rerun()
                
                with nav_col2:
                    if st.button("◀️ Previous", disabled=(current_page <= 1), key="prev_page"):
                        st.session_state.current_page = max(1, current_page - 1)
                        st.rerun()
                
                with nav_col3:
                    # Jump to page input
                    jump_page = st.number_input(
                        "Go to page:",
                        min_value=1,
                        max_value=total_pages,
                        value=current_page,
                        key="jump_page"
                    )
                
                with nav_col4:
                    if st.button("🎯 Go", key="go_page"):
                        st.session_state.current_page = jump_page
                        st.rerun()
                
                with nav_col5:
                    if st.button("▶️ Next", disabled=(current_page >= total_pages), key="next_page"):
                        st.session_state.current_page = min(total_pages, current_page + 1)
                        st.rerun()
                
                with nav_col6:
                    if st.button("⏭️ Last", disabled=(current_page >= total_pages), key="last_page"):
                        st.session_state.current_page = total_pages
                        st.rerun()
                
                # Display current page data
                display_data = display_df[display_columns].iloc[start_idx:end_idx]
                st.table(display_data)
                
                # Show page numbers at bottom for easy navigation
                if total_pages > 1:
                    st.markdown("---")
                    page_cols = st.columns(min(total_pages, 10))  # Show max 10 page numbers
                    
                    # Show page numbers around current page
                    start_page = max(1, current_page - 4)
                    end_page = min(total_pages, start_page + 9)
                    
                    if end_page - start_page < 9 and start_page > 1:
                        start_page = max(1, end_page - 9)
                    
                    for i, page_num in enumerate(range(start_page, end_page + 1)):
                        if i < len(page_cols):
                            with page_cols[i]:
                                if page_num == current_page:
                                    st.markdown(f"**🔵 {page_num}**")
                                else:
                                    if st.button(f"{page_num}", key=f"page_{page_num}"):
                                        st.session_state.current_page = page_num
                                        st.rerun()
                
            except Exception as e:
                st.error(f"Table display error: {str(e)}")
                st.write("**Fallback - Raw Data:**")
                st.write(display_df[display_columns].to_dict('records')[:10])
            
            # Platform breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                if 'Meta Ads' in platform_filter:
                    meta_campaigns = campaigns_df[campaigns_df['platform'] == 'Meta Ads']
                    if not meta_campaigns.empty:
                        st.markdown("### 🔵 Meta Ads Summary")
                        try:
                            meta_summary = meta_campaigns.groupby('status').agg({
                                'campaign_id': 'count',
                                'budget_amount': 'sum'
                            }).round(0)
                            meta_summary.columns = ['Campaign Count', 'Total Budget']
                            st.table(meta_summary)  # Use st.table instead of st.dataframe
                        except Exception:
                            st.write(f"Meta campaigns: {len(meta_campaigns)}")
            
            with col2:
                if 'Google Ads' in platform_filter:
                    google_campaigns = campaigns_df[campaigns_df['platform'] == 'Google Ads']
                    if not google_campaigns.empty:
                        st.markdown("### 🔴 Google Ads Summary")
                        try:
                            google_summary = google_campaigns.groupby('status').agg({
                                'campaign_id': 'count',
                                'budget_amount': 'sum'
                            }).round(0)
                            google_summary.columns = ['Campaign Count', 'Total Budget']
                            st.table(google_summary)  # Use st.table instead of st.dataframe
                        except Exception:
                            st.write(f"Google campaigns: {len(google_campaigns)}")
                            
        except Exception as e:
            st.error(f"Error formatting display: {str(e)}")
            st.dataframe(campaigns_df.head(), use_container_width=True)
    else:
        st.info("🔍 No campaign data found for the selected time range and platforms.")
        
with tab2:
    st.subheader("📈 Budget Trends - Multi-Platform Analysis")
    
    if not campaigns_df.empty:
        try:
            # Budget trends over time
            trends_df = campaigns_df.copy()
            trends_df['budget_amount'] = pd.to_numeric(trends_df['budget_amount'], errors='coerce').fillna(0)
            trends_df['date'] = pd.to_datetime(trends_df['snapshot_timestamp'], errors='coerce').dt.date
            
            if not trends_df['date'].isna().all():
                daily_budgets = trends_df.groupby(['date', 'platform'])['budget_amount'].sum().reset_index()
                
                if not daily_budgets.empty:
                    fig = px.line(
                        daily_budgets, 
                        x='date', 
                        y='budget_amount', 
                        color='platform',
                        title='Daily Budget Trends by Platform',
                        labels={'budget_amount': 'Total Budget ($)', 'date': 'Date'},
                        color_discrete_map={'Meta Ads': '#1877F2', 'Google Ads': '#4285F4'}
                    )
                    fig.update_layout(
                        height=400,
                        plot_bgcolor='#1a1f2e',
                        paper_bgcolor='#1a1f2e',
                        font_color='#fafafa'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No trend data available")
            else:
                st.info("No date data available for trends")
        except Exception as e:
            st.error(f"Error creating trends: {str(e)}")
    else:
        st.info("🔍 No budget trend data available.")
        
with tab3:
    st.subheader("⚙️ System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 Configuration")
        st.info(f"**Project ID:** {project_id}")
        st.info(f"**Dataset:** {dataset_id}")
        st.info("**Timezone:** America/Los_Angeles")
        
    with col2:
        st.markdown("### 📊 Data Summary")
        if not campaigns_df.empty:
            st.write(f"**Total Campaigns:** {len(campaigns_df):,}")
            meta_campaigns = campaigns_df[campaigns_df['platform'] == 'Meta Ads']
            google_campaigns = campaigns_df[campaigns_df['platform'] == 'Google Ads']
            st.write(f"**Meta Ads:** {len(meta_campaigns):,}")
            st.write(f"**Google Ads:** {len(google_campaigns):,}")
            
            # Calculate date range for display
            end_date_display = datetime.now()
            start_date_display = end_date_display - timedelta(days=days)
            st.write(f"**Date Range:** {start_date_display.strftime('%Y-%m-%d')} to {end_date_display.strftime('%Y-%m-%d')}")
        else:
            st.info("No data loaded")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; opacity: 0.7; padding: 1rem;">
    💰 Unified Budget Monitor • Multi-Platform Anomaly Detection • Powered by BigQuery
</div>
""", unsafe_allow_html=True)