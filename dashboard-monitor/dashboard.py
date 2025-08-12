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

# Load environment variables
load_dotenv()

# Page configuration - MUST BE FIRST
st.set_page_config(
    page_title="Meta Ads Budget Monitor",
    page_icon="💰",
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
    
    /* Custom header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #1a1f2e 0%, #0e1117 100%);
        padding: 2rem;
        margin: -1rem -1rem 2rem -1rem;
        border-bottom: 2px solid #4da3ff;
        text-align: center;
    }
    
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4da3ff;
        margin: 0;
        font-family: 'Inter', sans-serif;
    }
    
    .dashboard-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-top: 0.5rem;
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
</style>
""", unsafe_allow_html=True)

# Initialize BigQuery client
@st.cache_resource
def init_bigquery():
    project_id = os.getenv('GCP_PROJECT_ID', 'generative-ai-418805')
    return bigquery.Client(project=project_id), project_id

client, project_id = init_bigquery()
dataset_id = "budget_alert"

# Header with logo support
def display_header():
    header_html = """
    <div class="dashboard-header">
        <h1 class="dashboard-title">💰 Meta Ads Budget Monitor</h1>
        <p class="dashboard-subtitle">Real-time monitoring and analytics for Meta advertising campaigns</p>
    </div>
    """
    
    # Try to load logo if it exists
    if os.path.exists("logo.png"):
        try:
            with open("logo.png", "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
            header_html = f"""
            <div class="dashboard-header">
                <img src="data:image/png;base64,{logo_data}" style="height: 60px; margin-bottom: 1rem;">
                <h1 class="dashboard-title">Meta Ads Budget Monitor</h1>
                <p class="dashboard-subtitle">Real-time monitoring and analytics for Meta advertising campaigns</p>
            </div>
            """
        except:
            pass
    
    st.markdown(header_html, unsafe_allow_html=True)

# Display header
display_header()

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
col1, col2, col3, col4 = st.columns(4)

try:
    # Get summary metrics
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
        st.metric("Total Accounts", f"{int(metrics['total_accounts']):,}")
    
    with col2:
        st.metric("Active Campaigns", f"{int(metrics['total_campaigns']):,}")
    
    with col3:
        if metrics['total_lifetime_budget'] > 0:
            # Show combined view if there are lifetime budgets
            daily_budget = metrics['total_daily_budget']
            lifetime_budget = metrics['total_lifetime_budget']
            daily_count = int(metrics['daily_campaigns'])
            lifetime_count = int(metrics['lifetime_campaigns'])
            
            st.metric(
                "Total Budgets", 
                f"${daily_budget:,.0f} / ${lifetime_budget:,.0f}",
                delta=f"{daily_count} daily, {lifetime_count} lifetime",
                help="Daily Budget / Lifetime Budget"
            )
        else:
            # Show only daily budget if no lifetime budgets
            st.metric("Total Daily Budget", f"${metrics['total_daily_budget']:,.0f}")
    
    with col4:
        st.metric("High Budget Campaigns", f"{int(metrics['high_budget_campaigns']):,}")
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
        # Daily budget trend
        trends_query = f"""
        SELECT 
            DATE(snapshot_timestamp) as date,
            SUM(CASE WHEN budget_type = 'daily' THEN budget_amount ELSE 0 END) as total_daily_budget,
            COUNT(DISTINCT campaign_id) as campaign_count
        FROM `{project_id}.{dataset_id}.meta_campaign_snapshots`
        WHERE DATE(snapshot_timestamp) BETWEEN '{start_date}' AND '{end_date}'
        {account_filter}
        GROUP BY date
        ORDER BY date
        """
        
        trends_df = client.query(trends_query).to_dataframe()
        
        if len(trends_df) > 0:
            # Create trend chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=trends_df['date'],
                y=trends_df['total_daily_budget'],
                mode='lines+markers',
                name='Total Daily Budget',
                line=dict(color='#4da3ff', width=3),
                marker=dict(size=8, color='#4da3ff'),
                hovertemplate='Date: %{x}<br>Budget: $%{y:,.0f}<extra></extra>'
            ))
            
            fig.update_layout(
                title="Daily Budget Trend",
                xaxis_title="Date",
                yaxis_title="Total Daily Budget ($)",
                template="plotly_dark",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#fafafa'),
                title_font=dict(size=20, color='#4da3ff'),
                hovermode='x unified',
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Top accounts by budget
            if not selected_accounts:
                st.markdown("### Top 10 Accounts by Budget")
                
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
                    SUM(CASE WHEN budget_type = 'daily' THEN budget_amount ELSE 0 END) as total_budget
                FROM latest
                WHERE rn = 1
                GROUP BY account_name
                ORDER BY total_budget DESC
                LIMIT 10
                """
                
                top_df = client.query(top_accounts_query).to_dataframe()
                
                fig2 = px.bar(
                    top_df,
                    x='total_budget',
                    y='account_name',
                    orientation='h',
                    labels={'total_budget': 'Total Daily Budget ($)', 'account_name': 'Account'},
                    color_discrete_sequence=['#4da3ff']
                )
                
                fig2.update_layout(
                    template="plotly_dark",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#fafafa'),
                    showlegend=False,
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(gridcolor='#2d3748'),
                    yaxis=dict(gridcolor='#2d3748')
                )
                
                st.plotly_chart(fig2, use_container_width=True)
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

# Footer
st.markdown("---")
st.markdown(
    f"""<center style='color: #64748b; font-size: 0.875rem;'>
    Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
    Data source: BigQuery `{project_id}.{dataset_id}` | 
    Auto-refresh every 5 minutes
    </center>""",
    unsafe_allow_html=True
)