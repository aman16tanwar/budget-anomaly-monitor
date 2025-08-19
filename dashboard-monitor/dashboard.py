"""
Meta Ads Budget Monitoring Dashboard
Real-time monitoring and analytics for Meta advertising campaigns
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

# Load environment variables
load_dotenv()

# Page configuration - MUST BE FIRST
# Load favicon if exists
page_icon = "💰"  # Default emoji
favicon_path = os.path.join(os.path.dirname(__file__), "favicon.png")
if os.path.exists(favicon_path):
    page_icon = favicon_path

st.set_page_config(
    page_title="Meta Ads Budget Monitor",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme with blue accents
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Reset and base styles */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
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
    
    /* DataFrame styling */
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
    }
    
    .dataframe tbody tr:hover {
        background-color: rgba(77, 163, 255, 0.05) !important;
    }
    
    .dataframe tbody tr td {
        padding: 0.75rem 0.5rem !important;
        color: #fafafa !important;
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
    
    /* Alert boxes */
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-family: 'Inter', sans-serif;
    }
    
    .alert-critical {
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-left: 4px solid #ef4444;
    }
    
    .alert-warning {
        background-color: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-left: 4px solid #f59e0b;
    }
    
    .alert-info {
        background-color: rgba(77, 163, 255, 0.1);
        border: 1px solid rgba(77, 163, 255, 0.3);
        border-left: 4px solid #4da3ff;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #1a1f2e;
        border: 1px solid #2d3748;
        border-radius: 8px;
        color: #4da3ff !important;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #2d3748;
        border-color: #4da3ff;
    }
    
    /* Plotly chart styling */
    .js-plotly-plot {
        background-color: transparent !important;
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
    
    /* Success message styling */
    .success-message {
        background-color: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 8px;
        color: #22c55e;
        font-weight: 500;
    }
    
    /* Make sidebar toggle arrow more visible */
    button[kind="header"] {
        background-color: #4da3ff !important;
        color: white !important;
        border-radius: 50% !important;
        width: 2.5rem !important;
        height: 2.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    button[kind="header"]:hover {
        background-color: #2d8ff0 !important;
        transform: scale(1.1) !important;
        box-shadow: 0 4px 12px rgba(77, 163, 255, 0.4) !important;
    }
    
    /* Style the arrow icon itself */
    button[kind="header"] svg {
        width: 1.25rem !important;
        height: 1.25rem !important;
        color: white !important;
    }
    
    /* Position adjustment for better visibility */
    .stApp > header {
        background-color: transparent !important;
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
    
    /* Loading shimmer effect */
    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }
    
    .loading-skeleton {
        background: linear-gradient(90deg, #1a1f2e 25%, #2d3748 50%, #1a1f2e 75%);
        background-size: 1000px 100%;
        animation: shimmer 2s infinite;
        border-radius: 8px;
        height: 100%;
        width: 100%;
    }
    
    /* Number counter animation class */
    .counting {
        font-variant-numeric: tabular-nums;
        animation: pulse 2s ease-out;
    }
    
    /* CSS Loading spinner fallback */
    .loading-spinner {
        width: 60px;
        height: 60px;
        border: 4px solid #2d3748;
        border-top: 4px solid #4da3ff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Help button styling */
    .help-button {
        background-color: #2d3748;
        color: #94a3b8;
        border: 1px solid #4a5568;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1.1rem;
        font-weight: 600;
        margin-left: 1rem;
    }
    
    .help-button:hover {
        background-color: #4da3ff;
        color: white;
        border-color: #4da3ff;
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(77, 163, 255, 0.3);
    }
    
    /* Help modal styling */
    .help-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(4px);
        z-index: 99999;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        animation: fadeIn 0.3s ease-out;
    }
    
    .help-modal {
        background: #1a1f2e;
        border: 2px solid #4da3ff;
        border-radius: 16px;
        width: 100%;
        max-width: 800px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        animation: slideIn 0.3s ease-out;
    }
    
    .help-modal-header {
        background: linear-gradient(90deg, #1a1f2e 0%, #0e1117 100%);
        padding: 2rem;
        border-bottom: 2px solid #2d3748;
        position: sticky;
        top: 0;
        z-index: 10;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .help-modal-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #4da3ff;
        margin: 0;
    }
    
    .help-modal-close {
        background: #2d3748;
        color: #94a3b8;
        border: none;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1.25rem;
    }
    
    .help-modal-close:hover {
        background: #ef4444;
        color: white;
        transform: rotate(90deg);
    }
    
    .help-modal-content {
        padding: 2rem;
    }
    
    .help-section {
        margin-bottom: 2rem;
        padding: 1.5rem;
        background: #0e1117;
        border-radius: 12px;
        border: 1px solid #2d3748;
    }
    
    .help-section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #4da3ff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .help-section-content {
        color: #cbd5e1;
        line-height: 1.6;
    }
    
    .help-term {
        font-weight: 600;
        color: #4da3ff;
        margin-top: 0.75rem;
    }
    
    .help-definition {
        margin-left: 1rem;
        color: #94a3b8;
    }
    
    .help-metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .help-metric-item {
        background: #1a1f2e;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2d3748;
    }
    
    .help-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
</style>
""", unsafe_allow_html=True)

# Add JavaScript for number counting animation
st.markdown("""
<script>
// Number counting animation
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value.toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            element.textContent = end.toLocaleString();
        }
    };
    window.requestAnimationFrame(step);
}

// Apply to all metric values when page loads
document.addEventListener('DOMContentLoaded', function() {
    const metricElements = document.querySelectorAll('[data-testid="metric-value"]');
    metricElements.forEach((element) => {
        const finalValue = parseInt(element.textContent.replace(/[^0-9]/g, ''));
        if (!isNaN(finalValue)) {
            element.classList.add('counting');
            animateValue(element, 0, finalValue, 1500);
        }
    });
});

</script>
""", unsafe_allow_html=True)

# Initialize BigQuery client
@st.cache_resource
def init_bigquery():
    project_id = os.getenv('GCP_PROJECT_ID', 'generative-ai-418805')
    return bigquery.Client(project=project_id), project_id

# Skeleton loader component with custom loader GIF
def show_skeleton_loader(type="metric", count=1):
    """Display skeleton loaders for different component types"""
    # Try to load the custom loader GIF
    loader_html = ""
    loader_path = os.path.join(os.path.dirname(__file__), "loader.gif")
    if os.path.exists(loader_path):
        try:
            with open(loader_path, "rb") as f:
                loader_data = base64.b64encode(f.read()).decode()
            loader_html = f'<img src="data:image/gif;base64,{loader_data}" style="width: 60px; height: 60px;">'
        except:
            loader_html = '<div class="loading-spinner"></div>'
    else:
        loader_html = '<div class="loading-spinner"></div>'
    
    if type == "metric":
        cols = st.columns(count)
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"""
                <div style="height: 100px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: center;">
                    {loader_html}
                </div>
                """, unsafe_allow_html=True)
    elif type == "table":
        st.markdown(f"""
        <div style="height: 400px; margin: 1rem 0; display: flex; align-items: center; justify-content: center;">
            {loader_html}
        </div>
        """, unsafe_allow_html=True)
    elif type == "chart":
        st.markdown(f"""
        <div style="height: 400px; margin: 1rem 0; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
            {loader_html}
        </div>
        """, unsafe_allow_html=True)

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
    loader_path = os.path.join(os.path.dirname(__file__), "loader.gif")
    placeholder = st.empty()
    
    try:
        if os.path.exists(loader_path):
            with open(loader_path, "rb") as f:
                loader_data = base64.b64encode(f.read()).decode()
            
            placeholder.markdown(f"""
            <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
                        background: rgba(14, 17, 23, 0.8); z-index: 99999;">
                <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                            text-align: center;">
                    <img src="data:image/gif;base64,{loader_data}" style="width: 150px; height: 150px;">
                    <div style="color: #4da3ff; font-weight: 600; font-size: 1.25rem; margin-top: 1rem;">{message}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            placeholder.info(f"🔄 {message}")
        
        yield
    finally:
        placeholder.empty()

# Header with logo support - Professional version
def display_header():
    # Get actual data timestamp
    data_timestamp = get_latest_data_timestamp()
    
    # Format the timestamp (data is already in PST, even though BigQuery thinks it's UTC)
    if isinstance(data_timestamp, (datetime, pd.Timestamp)):
        # The timestamp is already PST time, just display it as such
        formatted_time = data_timestamp.strftime('%I:%M %p PST')
        
        # Calculate how long ago
        # Handle both timezone-aware and timezone-naive timestamps
        if isinstance(data_timestamp, pd.Timestamp):
            # Convert pandas Timestamp to naive datetime
            data_timestamp = data_timestamp.to_pydatetime()
            if data_timestamp.tzinfo is not None:
                data_timestamp = data_timestamp.replace(tzinfo=None)
        elif hasattr(data_timestamp, 'tzinfo') and data_timestamp.tzinfo is not None:
            # Regular datetime with timezone
            data_timestamp = data_timestamp.replace(tzinfo=None)
        
        now_pst = datetime.now()  # Local time is PST
        time_diff = now_pst - data_timestamp
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
                <h1 class="dashboard-title">Meta Ads Budget Monitor</h1>
                <div class="dashboard-subtitle">Real-time campaign budget tracking & analytics</div>
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
                        <h1 class="dashboard-title">Meta Ads Budget Monitor</h1>
                        <div class="dashboard-subtitle">Real-time campaign budget tracking & analytics</div>
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


# Display header
display_header()

# Initialize help modal state
if 'show_help' not in st.session_state:
    st.session_state.show_help = False

# Add help button right after header
col1, col2, col3 = st.columns([6, 3, 1])
with col3:
    if st.button("❓", key="help_button", help="View documentation", type="secondary"):
        st.session_state.show_help = not st.session_state.show_help

# Show help modal if active
if st.session_state.show_help:
    # Create modal-like container
    with st.container():
        st.markdown("---")
        st.markdown("## 📚 Help & Documentation")
        
        # Create tabs for different help sections
        help_tabs = st.tabs(["🧟 Zombie Campaigns", "💰 Budget Thresholds", "📊 Metrics", "🚨 Anomalies", "💡 Tips"])
        
        with help_tabs[0]:
            st.markdown("### What are Zombie Campaigns?")
            st.info("Zombie campaigns are active campaigns with allocated budgets that cannot deliver ads effectively. They consume budget allocation without generating results.")
            
            st.markdown("**Common causes:**")
            st.markdown("""
            - No active ad sets in the campaign
            - Ad sets exist but are paused  
            - Ad sets have no ads
            - All ads are paused or disapproved
            - Technical issues preventing delivery
            """)
        
        with help_tabs[1]:
            st.markdown("### Budget Thresholds")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.success("**💵 Normal Budget (Green)**  \nCampaigns with daily budgets below the HIGH threshold. These are considered standard spend levels.")
            with col2:
                st.warning("**⚠️ HIGH Budget (Orange)**  \nCampaigns exceeding the first threshold but below the VERY HIGH threshold. Requires monitoring.")
            with col3:
                st.error("**🚨 VERY HIGH Budget (Red)**  \nCampaigns exceeding the maximum threshold. These need immediate attention to prevent overspending.")
        
        with help_tabs[2]:
            st.markdown("### Key Metrics Explained")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**👥 Total Accounts**")
                st.caption("Number of unique Meta ad accounts being monitored")
                
                st.markdown("**🎯 Active Campaigns**")
                st.caption("Campaigns currently in ACTIVE status with allocated budgets")
                
            with col2:
                st.markdown("**💵 Total Daily Budget**")
                st.caption("Sum of all daily budgets across active campaigns")
                
                st.markdown("**⚠️ High Budget Campaigns**")
                st.caption("Count of campaigns exceeding the HIGH threshold")
        
        with help_tabs[3]:
            st.markdown("### Anomaly Detection")
            
            st.error("**CRITICAL Anomalies**  \nMajor budget changes or issues requiring immediate action (e.g., 200%+ budget increase)")
            st.warning("**WARNING Anomalies**  \nModerate changes that should be reviewed (e.g., 50-200% budget increase)")
            st.info("**Risk Score**  \nA numerical score (0-10) indicating the severity of the anomaly. Higher scores = higher risk.")
            
            st.markdown("### Delivery Status Indicators")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("🟢 **Green Status** - Campaign is delivering normally")
                st.markdown("🟡 **Yellow Status** - Some delivery issues")
            with col2:
                st.markdown("🟠 **Orange Status** - Significant delivery problems")
                st.markdown("🔴 **Red Status** - Critical issue, cannot deliver")
        
        with help_tabs[4]:
            st.markdown("### Tips & Best Practices")
            st.markdown("""
            - ✅ Review zombie campaigns daily to avoid wasted budget allocation
            - ✅ Set appropriate budget thresholds based on your typical spend levels
            - ✅ Investigate anomalies promptly to catch accidental budget changes
            - ✅ Use filters to focus on specific accounts or budget ranges
            - ✅ Monitor the "Days Active" metric to identify long-running high-budget campaigns
            """)
        
        # Add close button
        st.markdown("---")
        if st.button("✕ Close Help", key="close_help", type="primary"):
            st.session_state.show_help = False
            st.rerun()

# Sidebar configuration
with st.sidebar:
    
    st.markdown("### 🔍 Filters")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=7),
            max_value=datetime.now().date()
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
    
    # Account selection
    try:
        accounts_query = f"""
        SELECT DISTINCT account_name
        FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
        WHERE DATE(snapshot_timestamp) BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY account_name
        """
        accounts_df = client.query(accounts_query).to_dataframe()
        
        selected_accounts = st.multiselect(
            "Select Accounts",
            options=accounts_df['account_name'].tolist(),
            help="Leave empty to view all accounts"
        )
    except:
        selected_accounts = []
        st.info("No account data available")
    
    # Budget threshold
    min_budget = st.slider(
        "Minimum Daily Budget ($)",
        min_value=0,
        max_value=10000,
        value=100,
        step=50,
        help="Filter campaigns by minimum daily budget"
    )
    
    st.markdown("---")
    
    # Budget alert thresholds
    st.markdown("### ⚠️ Alert Thresholds")
    col1, col2 = st.columns(2)
    with col1:
        high_budget_threshold = st.number_input(
            "High Budget ($)",
            min_value=1000,
            max_value=50000,
            value=5000,
            step=1000,
            help="Campaigns above this will be highlighted in orange"
        )
    with col2:
        very_high_budget_threshold = st.number_input(
            "Very High Budget ($)",
            min_value=2000,
            max_value=100000,
            value=10000,
            step=1000,
            help="Campaigns above this will be highlighted in red"
        )
    
    st.markdown("---")
    
    # Campaign filtering options
    st.markdown("### 🎯 Campaign Filters")
    col1, col2 = st.columns(2)
    with col1:
        show_high_budget = st.checkbox(
            "Show HIGH budget",
            value=True,
            help=f"${high_budget_threshold:,.0f} - ${very_high_budget_threshold:,.0f}"
        )
    with col2:
        show_very_high_budget = st.checkbox(
            "Show VERY HIGH budget",
            value=True,
            help=f"Above ${very_high_budget_threshold:,.0f}"
        )
    
    show_normal_budget = st.checkbox(
        "Show Normal budget",
        value=True,
        help=f"Below ${high_budget_threshold:,.0f}"
    )
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Build filter clause
account_filter = ""
if selected_accounts:
    accounts_str = ', '.join([f"'{acc}'" for acc in selected_accounts])
    account_filter = f"AND account_name IN ({accounts_str})"

# Main content area - Summary metrics
# Initialize session state for loading
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

col1, col2, col3, col4 = st.columns(4)

try:
    # Get summary metrics
    with custom_spinner("Loading dashboard metrics..."):
        metrics_query = f"""
    WITH latest AS (
        SELECT 
            campaign_id,
            account_name,
            budget_amount,
            budget_type,
            ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
        FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
        WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
        {account_filter}
    )
    SELECT 
        COUNT(DISTINCT account_name) as total_accounts,
        COUNT(DISTINCT campaign_id) as total_campaigns,
        SUM(CASE WHEN budget_type = 'daily' THEN budget_amount ELSE 0 END) as total_daily_budget,
        SUM(CASE WHEN budget_type = 'lifetime' THEN budget_amount ELSE 0 END) as total_lifetime_budget,
        COUNT(DISTINCT CASE WHEN budget_type = 'daily' THEN campaign_id END) as daily_campaigns,
        COUNT(DISTINCT CASE WHEN budget_type = 'lifetime' THEN campaign_id END) as lifetime_campaigns,
        COUNT(DISTINCT CASE WHEN budget_amount >= {high_budget_threshold} THEN campaign_id END) as high_budget_campaigns
    FROM latest
    WHERE rn = 1
    """
    
        metrics = client.query(metrics_query).to_dataframe().iloc[0]
    
    with col1:
        total_accounts = metrics.get('total_accounts', 0) or 0
        st.metric("Total Accounts", f"{int(total_accounts):,}")
    
    with col2:
        total_campaigns = metrics.get('total_campaigns', 0) or 0
        st.metric("Active Campaigns", f"{int(total_campaigns):,}")
    
    with col3:
        total_lifetime_budget = metrics.get('total_lifetime_budget', 0) or 0
        if total_lifetime_budget > 0:
            # Show combined view if there are lifetime budgets
            daily_budget = metrics.get('total_daily_budget', 0) or 0
            lifetime_budget = metrics.get('total_lifetime_budget', 0) or 0
            daily_count = int(metrics.get('daily_campaigns', 0) or 0)
            lifetime_count = int(metrics.get('lifetime_campaigns', 0) or 0)
            
            st.metric(
                "Total Budgets", 
                f"${daily_budget:,.0f} / ${lifetime_budget:,.0f}",
                delta=f"{daily_count} daily, {lifetime_count} lifetime",
                help="Daily Budget / Lifetime Budget"
            )
        else:
            # Show only daily budget if no lifetime budgets
            total_daily_budget = metrics.get('total_daily_budget', 0) or 0
            st.metric("Total Daily Budget", f"${total_daily_budget:,.0f}")
    
    with col4:
        high_budget_campaigns = metrics.get('high_budget_campaigns', 0) or 0
        st.metric("High Budget Campaigns", f"{int(high_budget_campaigns):,}")
except Exception as e:
    st.error(f"Error loading metrics: {str(e)}")

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["💰 Active Campaigns", "📈 Budget Trends", "🚨 Anomalies", "🧟 Delivery Issues"])

# Tab 1: Active Campaigns
with tab1:
    st.markdown("### Active Campaigns by Account")
    
    # Budget level legend
    st.markdown("""
    <div style="display: flex; gap: 2rem; margin-bottom: 1rem; padding: 0.75rem; background-color: #1a1f2e; border-radius: 8px;">
        <div>💵 <strong>Normal Budget</strong>: Below ${:,.0f}</div>
        <div>⚠️ <span class="high-budget-tag">HIGH</span>: ${:,.0f} - ${:,.0f}</div>
        <div>🚨 <span class="very-high-budget-tag">VERY HIGH</span>: Above ${:,.0f}</div>
    </div>
    """.format(high_budget_threshold, high_budget_threshold, very_high_budget_threshold, very_high_budget_threshold), unsafe_allow_html=True)
    
    # View toggle
    col1, col2 = st.columns([1, 4])
    with col1:
        view_mode = st.radio(
            "View Mode",
            ["Grouped by Account", "Unified Table"],
            help="Choose how to display campaigns"
        )
    
    # Show filter status if active
    active_filters = []
    if show_normal_budget:
        active_filters.append("Normal")
    if show_high_budget:
        active_filters.append("HIGH")
    if show_very_high_budget:
        active_filters.append("VERY HIGH")
    
    if active_filters and len(active_filters) < 3:
        st.info(f"🔍 **Filter Active:** Showing {', '.join(active_filters)} budget campaigns")
    elif not active_filters:
        st.warning("⚠️ No budget filters selected. Please select at least one filter to view campaigns.")
    
    try:
        with custom_spinner("Loading campaign data..."):
            campaigns_query = f"""
        WITH latest AS (
            SELECT 
                account_name,
                campaign_id,
                campaign_name,
                budget_amount,
                budget_type,
                objective,
                created_time,
                start_time,
                stop_time,
                delivery_status_simple,
                total_adsets,
                active_adsets,
                adsets_with_active_ads,
                ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
            FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
            WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
            AND budget_amount >= {min_budget}
            {account_filter}
        )
        SELECT 
            account_name,
            campaign_name,
            budget_amount,
            budget_type,
            objective,
            created_time,
            start_time,
            stop_time,
            delivery_status_simple,
            total_adsets,
            active_adsets,
            adsets_with_active_ads
        FROM latest 
        WHERE rn = 1
        ORDER BY account_name, budget_amount DESC
        """
        
            campaigns_df = client.query(campaigns_query).to_dataframe()
            import time
            time.sleep(0.5)  # Brief delay to show loader
        
        # Apply budget filters if selected
        if len(campaigns_df) > 0:
            # Create filter conditions based on checkboxes
            filter_conditions = []
            
            if show_normal_budget:
                filter_conditions.append(campaigns_df['budget_amount'] < high_budget_threshold)
            
            if show_high_budget:
                filter_conditions.append(
                    (campaigns_df['budget_amount'] >= high_budget_threshold) & 
                    (campaigns_df['budget_amount'] < very_high_budget_threshold)
                )
            
            if show_very_high_budget:
                filter_conditions.append(campaigns_df['budget_amount'] >= very_high_budget_threshold)
            
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
        
        if len(campaigns_df) > 0:
            if view_mode == "Unified Table":
                # Unified view - all campaigns in one table
                st.markdown("### All Campaigns - Sortable by Any Column")
                
                # Prepare display dataframe
                display_df = campaigns_df.copy()
                
                # Add status column based on budget amount
                display_df['status'] = display_df['budget_amount'].apply(
                    lambda x: '🚨 VERY HIGH' if x >= very_high_budget_threshold 
                    else '⚠️ HIGH' if x >= high_budget_threshold 
                    else '✅ Normal'
                )
                
                # Format created date
                display_df['created_date'] = pd.to_datetime(display_df['created_time'], errors='coerce').dt.strftime('%Y-%m-%d')
                display_df['created_date'] = display_df['created_date'].fillna('Unknown')
                
                # Format start date
                display_df['start_date'] = pd.to_datetime(display_df['start_time'], errors='coerce').dt.strftime('%Y-%m-%d')
                display_df['start_date'] = display_df['start_date'].fillna('Not Set')
                
                # Format end date
                display_df['end_date'] = pd.to_datetime(display_df['stop_time'], errors='coerce').dt.strftime('%Y-%m-%d')
                display_df['end_date'] = display_df['end_date'].fillna('Ongoing')
                
                # Calculate days active
                try:
                    created_times = pd.to_datetime(display_df['created_time'], errors='coerce')
                    if created_times.dt.tz is not None:
                        created_times = created_times.dt.tz_localize(None)
                    display_df['days_active'] = (datetime.now() - created_times).dt.days
                    display_df['days_active'] = display_df['days_active'].fillna(0).astype(int)
                except:
                    display_df['days_active'] = 0
                
                # Select and reorder columns - keep budget_amount for sorting
                display_df = display_df[['account_name', 'campaign_name', 'budget_amount', 
                                       'status', 'delivery_status_simple', 'budget_type', 'objective', 
                                       'created_date', 'start_date', 'end_date', 'days_active']]
                
                # Rename columns for display
                display_df.columns = ['Account', 'Campaign', 'Budget', 'Risk Level', 
                                    'Delivery', 'Type', 'Objective', 'Created', 'Start Date', 'End Date', 'Days Active']
                
                # Sort by budget amount by default (descending)
                display_df = display_df.sort_values('Budget', ascending=False)
                
                # Display with enhanced styling
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Account": st.column_config.TextColumn(
                            "Account",
                            help="Account name",
                            width="medium"
                        ),
                        "Campaign": st.column_config.TextColumn(
                            "Campaign",
                            help="Campaign name",
                            width="medium"
                        ),
                        "Budget": st.column_config.NumberColumn(
                            "Budget",
                            help="Daily budget amount - Click column header to sort",
                            format="$%.2f"
                        ),
                        "Risk Level": st.column_config.TextColumn(
                            "Risk Level",
                            help="Budget risk level based on thresholds"
                        ),
                        "Delivery": st.column_config.TextColumn(
                            "Delivery",
                            help="Campaign delivery status"
                        ),
                        "Type": st.column_config.TextColumn(
                            "Type",
                            help="Budget type (daily/lifetime)"
                        ),
                        "Created": st.column_config.TextColumn(
                            "Created",
                            help="Date when campaign was created in Meta Ads"
                        ),
                        "Start Date": st.column_config.TextColumn(
                            "Start Date",
                            help="Scheduled start date for the campaign"
                        ),
                        "End Date": st.column_config.TextColumn(
                            "End Date",
                            help="Scheduled end date for the campaign (Ongoing if no end date set)"
                        ),
                        "Days Active": st.column_config.NumberColumn(
                            "Days Active",
                            help="Number of days since campaign was created"
                        )
                    },
                    height=600  # Fixed height for better scrolling
                )
                
                # Summary stats
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Campaigns", len(display_df))
                with col2:
                    st.metric("Total Daily Budget", f"${campaigns_df['budget_amount'].sum():,.2f}")
                with col3:
                    high_risk = len(display_df[display_df['Risk Level'].str.contains('HIGH')])
                    st.metric("High Risk Campaigns", high_risk)
                with col4:
                    avg_days = display_df['Days Active'].mean()
                    st.metric("Avg Days Active", f"{avg_days:.0f}")
                    
            else:
                # Grouped view - original implementation
                # Group by account
                for account in campaigns_df['account_name'].unique():
                    account_data = campaigns_df[campaigns_df['account_name'] == account]
                    daily_budget = account_data[account_data['budget_type'] == 'daily']['budget_amount'].sum()
                    
                    # Count high budget campaigns in this account
                    high_budget_count = len(account_data[account_data['budget_amount'] >= high_budget_threshold])
                    very_high_budget_count = len(account_data[account_data['budget_amount'] >= very_high_budget_threshold])
                    
                    # Create expander header with warning indicators
                    header = f"**{account}** - {len(account_data)} campaigns - Daily: ${daily_budget:,.2f}"
                    if very_high_budget_count > 0:
                        header += f" 🚨 ({very_high_budget_count} very high)"
                    elif high_budget_count > 0:
                        header += f" ⚠️ ({high_budget_count} high)"
                    
                    with st.expander(header, expanded=(high_budget_count > 0)):
                        # Format display with enhanced columns
                        display_df = account_data[['campaign_name', 'budget_amount', 'budget_type', 'objective', 'created_time', 'start_time', 'stop_time']].copy()
                    
                        # Add status column based on budget amount
                        display_df['status'] = display_df['budget_amount'].apply(
                        lambda x: '🚨 VERY HIGH' if x >= very_high_budget_threshold 
                        else '⚠️ HIGH' if x >= high_budget_threshold 
                        else '✅ Normal'
                        )
                        
                        # Format columns
                        display_df['budget_display'] = display_df['budget_amount'].apply(lambda x: f"${x:,.2f}")
                    
                        # Format created date
                        display_df['created_date'] = pd.to_datetime(display_df['created_time'], errors='coerce').dt.strftime('%Y-%m-%d')
                        display_df['created_date'] = display_df['created_date'].fillna('Unknown')
                        
                        # Format start date
                        display_df['start_date'] = pd.to_datetime(display_df['start_time'], errors='coerce').dt.strftime('%Y-%m-%d')
                        display_df['start_date'] = display_df['start_date'].fillna('Not Set')
                        
                        # Format end date
                        display_df['end_date'] = pd.to_datetime(display_df['stop_time'], errors='coerce').dt.strftime('%Y-%m-%d')
                        display_df['end_date'] = display_df['end_date'].fillna('Ongoing')
                    
                        # Calculate days active - handle timezone
                        try:
                            # Convert created_time to timezone-naive for calculation
                            created_times = pd.to_datetime(display_df['created_time'], errors='coerce')
                            if created_times.dt.tz is not None:
                                created_times = created_times.dt.tz_localize(None)
                            display_df['days_active'] = (datetime.now() - created_times).dt.days
                            display_df['days_active'] = display_df['days_active'].fillna(0).astype(int)
                        except:
                            display_df['days_active'] = 0
                    
                        # Get delivery status from data if available
                        if 'delivery_status_simple' in account_data.columns:
                            display_df['delivery_status'] = account_data['delivery_status_simple']
                        else:
                            # Fallback if column doesn't exist yet
                            display_df['delivery_status'] = display_df['budget_amount'].apply(
                                lambda x: '⚠️ Check delivery' if x >= high_budget_threshold else '✓ Check delivery'
                            )
                    
                        # Reorder and rename columns
                        display_df = display_df[['campaign_name', 'budget_display', 'status', 'delivery_status', 'budget_type', 'objective', 'created_date', 'start_date', 'end_date', 'days_active']]
                        display_df.columns = ['Campaign', 'Budget', 'Risk Level', 'Delivery', 'Type', 'Objective', 'Created', 'Start Date', 'End Date', 'Days Active']
                    
                        # Display with custom styling
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Budget": st.column_config.TextColumn(
                                    "Budget",
                                    help="Daily budget amount"
                                ),
                                "Status": st.column_config.TextColumn(
                                    "Status",
                                    help="Budget risk level"
                                )
                            }
                        )
        else:
            if not active_filters:
                st.info("Please select at least one budget filter to view campaigns.")
            else:
                filter_text = " or ".join(active_filters)
                st.info(f"No {filter_text} budget campaigns found matching your criteria.")
    except Exception as e:
        st.error(f"Error loading campaigns: {str(e)}")

# Tab 2: Budget Trends
with tab2:
    st.markdown("### Budget Trends Analysis")
    
    try:
        # Get budget type distribution first
        budget_type_query = f"""
        WITH latest AS (
            SELECT 
                campaign_id,
                budget_type,
                budget_amount,
                ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
            FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
            WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
            {account_filter}
        )
        SELECT 
            budget_type,
            COUNT(DISTINCT campaign_id) as campaign_count,
            SUM(budget_amount) as total_budget
        FROM latest
        WHERE rn = 1
        GROUP BY budget_type
        """
        
        budget_types_df = client.query(budget_type_query).to_dataframe()
        
        # Show budget type summary
        col1, col2, col3 = st.columns(3)
        
        daily_campaigns = budget_types_df[budget_types_df['budget_type'] == 'daily']['campaign_count'].sum() if len(budget_types_df[budget_types_df['budget_type'] == 'daily']) > 0 else 0
        lifetime_campaigns = budget_types_df[budget_types_df['budget_type'] == 'lifetime']['campaign_count'].sum() if len(budget_types_df[budget_types_df['budget_type'] == 'lifetime']) > 0 else 0
        daily_budget_total = budget_types_df[budget_types_df['budget_type'] == 'daily']['total_budget'].sum() if len(budget_types_df[budget_types_df['budget_type'] == 'daily']) > 0 else 0
        lifetime_budget_total = budget_types_df[budget_types_df['budget_type'] == 'lifetime']['total_budget'].sum() if len(budget_types_df[budget_types_df['budget_type'] == 'lifetime']) > 0 else 0
        
        with col1:
            st.metric("Daily Budget Campaigns", f"{int(daily_campaigns):,}", 
                     delta=f"${daily_budget_total:,.0f} total daily spend")
        with col2:
            st.metric("Lifetime Budget Campaigns", f"{int(lifetime_campaigns):,}", 
                     delta=f"${lifetime_budget_total:,.0f} total allocation")
        with col3:
            # Calculate effective daily spend from lifetime budgets
            effective_daily = lifetime_budget_total / 30 if lifetime_budget_total > 0 else 0  # Assuming 30-day average
            st.metric("Est. Combined Daily Spend", f"${(daily_budget_total + effective_daily):,.0f}",
                     help="Daily budgets + (Lifetime budgets ÷ 30 days)")
        
        st.markdown("---")
        
        # Combined budget trends
        st.markdown("#### Budget Trends Over Time")
        
        trends_query = f"""
        SELECT 
            DATE(snapshot_timestamp) as date,
            SUM(CASE WHEN budget_type = 'daily' THEN budget_amount ELSE 0 END) as total_daily_budget,
            SUM(CASE WHEN budget_type = 'lifetime' THEN budget_amount ELSE 0 END) as total_lifetime_budget,
            COUNT(DISTINCT CASE WHEN budget_type = 'daily' THEN campaign_id END) as daily_campaign_count,
            COUNT(DISTINCT CASE WHEN budget_type = 'lifetime' THEN campaign_id END) as lifetime_campaign_count
        FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
        WHERE DATE(snapshot_timestamp) BETWEEN '{start_date}' AND '{end_date}'
        {account_filter}
        GROUP BY date
        ORDER BY date
        """
        
        trends_df = client.query(trends_query).to_dataframe()
        
        if len(trends_df) > 0:
            # Create dual-axis trend chart
            fig = go.Figure()
            
            # Daily budget on primary y-axis
            fig.add_trace(go.Scatter(
                x=trends_df['date'],
                y=trends_df['total_daily_budget'],
                mode='lines+markers',
                name='Total Daily Budget',
                line=dict(color='#4da3ff', width=3),
                marker=dict(size=8, color='#4da3ff'),
                hovertemplate='Date: %{x}<br>Daily Budget: $%{y:,.0f}<br>Campaigns: %{customdata}<extra></extra>',
                customdata=trends_df['daily_campaign_count'],
                yaxis='y'
            ))
            
            # Lifetime budget on secondary y-axis
            fig.add_trace(go.Scatter(
                x=trends_df['date'],
                y=trends_df['total_lifetime_budget'],
                mode='lines+markers',
                name='Total Lifetime Budget',
                line=dict(color='#ff6b6b', width=3),
                marker=dict(size=8, color='#ff6b6b'),
                hovertemplate='Date: %{x}<br>Lifetime Budget: $%{y:,.0f}<br>Campaigns: %{customdata}<extra></extra>',
                customdata=trends_df['lifetime_campaign_count'],
                yaxis='y2'
            ))
            
            fig.update_layout(
                title="Daily & Lifetime Budget Trends",
                xaxis_title="Date",
                yaxis=dict(
                    title="Total Daily Budget ($)",
                    titlefont=dict(color="#4da3ff"),
                    tickfont=dict(color="#4da3ff")
                ),
                yaxis2=dict(
                    title="Total Lifetime Budget ($)",
                    titlefont=dict(color="#ff6b6b"),
                    tickfont=dict(color="#ff6b6b"),
                    overlaying='y',
                    side='right'
                ),
                template="plotly_dark",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#fafafa'),
                title_font=dict(size=20, color='#4da3ff'),
                hovermode='x unified',
                margin=dict(l=0, r=60, t=40, b=0),
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(0,0,0,0.5)"
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No budget data found in the selected period")
        
        # Lifetime budget analysis (different visualization)
        st.markdown("#### Lifetime Budget Campaigns - Analysis")
        
        lifetime_query = f"""
        WITH latest AS (
            SELECT 
                campaign_id,
                campaign_name,
                account_name,
                budget_amount,
                created_time,
                start_time,
                stop_time,
                ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
            FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
            WHERE budget_type = 'lifetime'
            AND DATE(snapshot_timestamp) = CURRENT_DATE()
            {account_filter}
        )
        SELECT 
            campaign_id,
            campaign_name,
            account_name,
            budget_amount,
            created_time,
            start_time,
            stop_time,
            CASE 
                WHEN stop_time IS NOT NULL THEN DATE_DIFF(DATE(stop_time), DATE(start_time), DAY)
                ELSE DATE_DIFF(CURRENT_DATE(), DATE(start_time), DAY)
            END as campaign_duration_days
        FROM latest
        WHERE rn = 1
        ORDER BY budget_amount DESC
        LIMIT 20
        """
        
        lifetime_df = client.query(lifetime_query).to_dataframe()
        
        if len(lifetime_df) > 0:
            # Calculate effective daily budget for lifetime campaigns
            lifetime_df['effective_daily_budget'] = lifetime_df.apply(
                lambda row: row['budget_amount'] / max(row['campaign_duration_days'], 1) if row['campaign_duration_days'] > 0 else row['budget_amount'] / 30,
                axis=1
            )
            
            # Show top lifetime budget campaigns with their effective daily spend
            fig2 = go.Figure()
            
            # Bar chart showing lifetime budgets and effective daily
            fig2.add_trace(go.Bar(
                x=lifetime_df['campaign_name'][:10],
                y=lifetime_df['budget_amount'][:10],
                name='Lifetime Budget',
                marker_color='#ff6b6b',
                hovertemplate='%{x}<br>Lifetime: $%{y:,.0f}<extra></extra>'
            ))
            
            fig2.add_trace(go.Bar(
                x=lifetime_df['campaign_name'][:10],
                y=lifetime_df['effective_daily_budget'][:10],
                name='Effective Daily',
                marker_color='#4da3ff',
                hovertemplate='%{x}<br>Daily: $%{y:,.0f}<extra></extra>',
                yaxis='y2'
            ))
            
            fig2.update_layout(
                title="Top 10 Lifetime Budget Campaigns",
                xaxis_title="Campaign",
                yaxis_title="Lifetime Budget ($)",
                yaxis2=dict(
                    title="Effective Daily Budget ($)",
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                template="plotly_dark",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#fafafa'),
                title_font=dict(size=20, color='#4da3ff'),
                margin=dict(l=0, r=60, t=40, b=100),
                xaxis={'tickangle': -45},
                hovermode='x unified',
                barmode='group',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(0,0,0,0.5)"
                )
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
        else:
            st.info("No lifetime budget campaigns found")
            
        # Top accounts summary
        if not selected_accounts:
            st.markdown("### Top 10 Accounts by Budget Type")
            
            top_accounts_query = f"""
            WITH latest AS (
                SELECT 
                    account_name,
                    campaign_id,
                    budget_amount,
                    budget_type,
                    ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
                FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
                WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
            )
            SELECT 
                account_name,
                SUM(CASE WHEN budget_type = 'daily' THEN budget_amount ELSE 0 END) as daily_budget,
                SUM(CASE WHEN budget_type = 'lifetime' THEN budget_amount ELSE 0 END) as lifetime_budget,
                COUNT(DISTINCT CASE WHEN budget_type = 'daily' THEN campaign_id END) as daily_campaigns,
                COUNT(DISTINCT CASE WHEN budget_type = 'lifetime' THEN campaign_id END) as lifetime_campaigns
            FROM latest
            WHERE rn = 1
            GROUP BY account_name
            ORDER BY (daily_budget + lifetime_budget/30) DESC
            LIMIT 10
            """
            
            top_df = client.query(top_accounts_query).to_dataframe()
            
            if len(top_df) > 0:
                # Create stacked bar chart
                fig3 = go.Figure()
                
                fig3.add_trace(go.Bar(
                    y=top_df['account_name'],
                    x=top_df['daily_budget'],
                    name='Daily Budget',
                    orientation='h',
                    marker_color='#4da3ff',
                    hovertemplate='%{y}<br>Daily: $%{x:,.0f}<br>Campaigns: %{customdata}<extra></extra>',
                    customdata=top_df['daily_campaigns']
                ))
                
                fig3.add_trace(go.Bar(
                    y=top_df['account_name'],
                    x=top_df['lifetime_budget']/30,  # Show as daily equivalent
                    name='Lifetime (÷30)',
                    orientation='h',
                    marker_color='#ff6b6b',
                    hovertemplate='%{y}<br>Lifetime÷30: $%{x:,.0f}<br>Total Lifetime: $%{customdata:,.0f}<extra></extra>',
                    customdata=top_df['lifetime_budget']
                ))
                
                fig3.update_layout(
                    title="Top Accounts by Estimated Daily Spend",
                    xaxis_title="Estimated Daily Spend ($)",
                    yaxis_title="Account",
                    template="plotly_dark",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#fafafa'),
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis=dict(gridcolor='#2d3748'),
                    yaxis=dict(gridcolor='#2d3748'),
                    barmode='stack',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="right",
                        x=0.99,
                        bgcolor="rgba(0,0,0,0.5)"
                    )
                )
                
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No trend data available for the selected period")
    except Exception as e:
        st.error(f"Error loading trends: {str(e)}")

# Tab 3: Anomalies
with tab3:
    st.markdown("### Anomaly Detection History")
    
    try:
        anomalies_query = f"""
        SELECT 
            detected_at,
            anomaly_type,
            account_name,
            campaign_name,
            message,
            current_budget,
            risk_score
        FROM `{project_id}.{dataset_id}.meta_anomalies`
        WHERE DATE(detected_at) BETWEEN '{start_date}' AND '{end_date}'
        {account_filter}
        ORDER BY detected_at DESC
        LIMIT 50
        """
        
        anomalies_df = client.query(anomalies_query).to_dataframe()
        
        if len(anomalies_df) > 0:
            # Anomaly statistics
            col1, col2, col3 = st.columns(3)
            
            critical_count = len(anomalies_df[anomalies_df['anomaly_type'] == 'CRITICAL'])
            warning_count = len(anomalies_df[anomalies_df['anomaly_type'] == 'WARNING'])
            avg_risk = anomalies_df['risk_score'].mean()
            
            with col1:
                st.metric("Critical Alerts", critical_count)
            
            with col2:
                st.metric("Warning Alerts", warning_count)
            
            with col3:
                st.metric("Avg Risk Score", f"{avg_risk:.1f}")
            
            st.markdown("---")
            
            # Display anomalies
            for _, anomaly in anomalies_df.iterrows():
                alert_class = "alert-critical" if anomaly['anomaly_type'] == 'CRITICAL' else "alert-warning"
                
                st.markdown(f"""
                <div class="alert-box {alert_class}">
                    <strong>{anomaly['anomaly_type']}</strong> - {anomaly['account_name']} - {anomaly['campaign_name']}<br>
                    <span style="color: #94a3b8;">{anomaly['message']}</span><br>
                    <small style="color: #64748b;">Detected: {anomaly['detected_at'].strftime('%Y-%m-%d %H:%M')} | Risk Score: {anomaly['risk_score']:.1f}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-message">
                ✅ No anomalies detected in the selected period!
            </div>
            """, unsafe_allow_html=True)
    except:
        st.info("Anomaly data will appear here once the monitoring system detects any budget anomalies.")

# Tab 4: Delivery Issues
with tab4:
    st.markdown("### 🧟 Potential Zombie Campaigns")
    st.markdown("""
    These campaigns have budgets allocated but may not be able to deliver ads due to:
    - No active ad sets
    - Ad sets without ads
    - All ads paused or disapproved
    """)
    
    # Zombie campaign detection info box
    st.info("""
    **💡 Why this matters:** Zombie campaigns waste budget allocation and may indicate:
    - Incomplete campaign setup
    - Forgotten campaigns
    - Technical issues preventing delivery
    """)
    
    # Show campaigns with delivery issues
    try:
        zombie_query = f"""
        WITH latest AS (
            SELECT 
                account_name,
                campaign_id,
                campaign_name,
                budget_amount,
                budget_type,
                created_time,
                delivery_status_simple,
                total_adsets,
                active_adsets,
                adsets_with_active_ads,
                ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY snapshot_timestamp DESC) as rn
            FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
            WHERE DATE(snapshot_timestamp) = CURRENT_DATE()
            AND campaign_status = 'ACTIVE'
            {account_filter}
        )
        SELECT * FROM latest 
        WHERE rn = 1
            AND delivery_status_simple NOT LIKE '🟢%'
            AND delivery_status_simple NOT LIKE '❓%'
            AND budget_amount >= {min_budget}
        ORDER BY budget_amount DESC
        LIMIT 50
        """
        
        zombie_df = client.query(zombie_query).to_dataframe()
        
        if len(zombie_df) > 0:
            # Group by issue type
            critical_zombies = zombie_df[zombie_df['delivery_status_simple'].str.contains('🔴')]
            warning_zombies = zombie_df[zombie_df['delivery_status_simple'].str.contains('🟠')]
            medium_zombies = zombie_df[zombie_df['delivery_status_simple'].str.contains('🟡')]
            
            total_daily_waste = zombie_df[zombie_df['budget_type'] == 'daily']['budget_amount'].sum()
            
            st.error(f"🧟 Found {len(zombie_df)} zombie campaigns with ${total_daily_waste:,.2f} daily budget at risk!")
            
            # Display by severity
            if len(critical_zombies) > 0:
                st.markdown("### 🔴 Critical - No Ad Sets")
                for _, campaign in critical_zombies.iterrows():
                    st.markdown(f"""
                    <div class="alert-box alert-critical">
                        <strong>{campaign['campaign_name']}</strong> - {campaign['account_name']}<br>
                        <span style="color: #ef4444; font-weight: bold;">Budget: ${campaign['budget_amount']:,.2f} {campaign['budget_type']}</span><br>
                        <span style="color: #94a3b8;">{campaign['delivery_status_simple']} | {campaign['total_adsets']} total ad sets</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            if len(warning_zombies) > 0:
                st.markdown("### 🟠 High Risk - Ad Sets Paused")
                for _, campaign in warning_zombies.iterrows():
                    st.markdown(f"""
                    <div class="alert-box alert-warning">
                        <strong>{campaign['campaign_name']}</strong> - {campaign['account_name']}<br>
                        <span style="color: #f59e0b; font-weight: bold;">Budget: ${campaign['budget_amount']:,.2f} {campaign['budget_type']}</span><br>
                        <span style="color: #94a3b8;">{campaign['delivery_status_simple']} | {campaign['active_adsets']}/{campaign['total_adsets']} ad sets active</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            if len(medium_zombies) > 0:
                st.markdown("### 🟡 Medium Risk - No Active Ads")
                for _, campaign in medium_zombies.iterrows():
                    st.markdown(f"""
                    <div class="alert-box alert-info">
                        <strong>{campaign['campaign_name']}</strong> - {campaign['account_name']}<br>
                        <span style="color: #4da3ff; font-weight: bold;">Budget: ${campaign['budget_amount']:,.2f} {campaign['budget_type']}</span><br>
                        <span style="color: #94a3b8;">{campaign['delivery_status_simple']} | {campaign['adsets_with_active_ads']}/{campaign['active_adsets']} ad sets have ads</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Recommendations
            st.markdown("### 📋 Recommended Actions")
            st.markdown("""
            1. **Check Ad Sets**: Verify each campaign has at least one active ad set
            2. **Check Ads**: Ensure active ad sets contain approved, active ads
            3. **Review Delivery**: Check delivery insights in Meta Ads Manager
            4. **Pause if Needed**: Pause campaigns that shouldn't be running
            """)
        else:
            st.success("✅ No high-budget campaigns detected that might have delivery issues!")
            
    except Exception as e:
        st.info("""
        Delivery status monitoring will be available once we integrate ad set and ad level data.
        For now, please manually verify that high-budget campaigns have:
        - Active ad sets
        - Active ads within those ad sets
        """)

# Compact footer
st.markdown(
    f"""<div style='color: #64748b; font-size: 0.75rem; text-align: center; margin-top: 2rem; padding: 0.5rem 0; border-top: 1px solid #2d3748;'>
    BigQuery: {project_id}.{dataset_id} • Auto-refresh: 5 min
    </div>""",
    unsafe_allow_html=True
)