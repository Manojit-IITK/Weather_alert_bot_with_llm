import os
import sys
import sqlite3
import pandas as pd
import streamlit as st
import subprocess
from datetime import datetime
import database
import groq_analyzer

# Set up page styling
st.set_page_config(
    page_title="India Weather Incident Monitor",
    page_icon="⛈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling via CSS
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #374151;
        text-align: center;
    }
    .alert-card {
        background-color: #7f1d1d;
        color: #fca5a5;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #b91c1c;
        margin-bottom: 10px;
    }
    .success-card {
        background-color: #064e3b;
        color: #a7f3d0;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #047857;
        margin-bottom: 10px;
    }
    h1, h2, h3 {
        color: #f3f4f6 !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper to fetch coordinates from city_list.csv
@st.cache_data
def load_city_coordinates():
    csv_path = "city_list.csv"
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            # Normalize names to lower case for lookups
            coords = {}
            for _, row in df.iterrows():
                city = str(row["city_name"]).strip().lower()
                coords[city] = (float(row["latitude"]), float(row["longitude"]))
            return coords
        except Exception:
            return {}
    return {}

# Database helper
def load_data_from_db():
    db_path = "incidents.db"
    if not os.path.exists(db_path):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM incidents ORDER BY created_at DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame()

# Grouped alerts helper
def load_alerts_from_csv():
    csv_path = os.path.join("data", "grouped_alerts.csv")
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    try:
        return pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame()

# Main Title & Subheader
st.title("⛈️ Weather Incident Monitoring Agent")
st.markdown("##### Real-time MVP Dashboard for Weather & Urban Disruption Chatter in India")
st.markdown("---")

# Sidebar
st.sidebar.header("Agent Controls")
if st.sidebar.button("🔄 Run Ingestion Pipeline Now", width="stretch"):
    with st.spinner("Executing app.py pipeline..."):
        try:
            # Run the ingestion script in a separate process
            result = subprocess.run([sys.executable, "app.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.sidebar.success("Pipeline executed successfully!")
                # Show log summary in sidebar
                st.sidebar.text_area("Pipeline Logs", result.stdout, height=150)
            else:
                st.sidebar.error("Pipeline run failed.")
                st.sidebar.text_area("Error Logs", result.stderr, height=150)
        except Exception as e:
            st.sidebar.error(f"Execution error: {e}")

if st.sidebar.button("🗑️ Reset Database & Logs", width="stretch"):
    with st.spinner("Resetting database..."):
        try:
            database.reset_database();
            st.sidebar.success("Database and logs reset successfully!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Failed to reset: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### Configured Sources")
st.sidebar.markdown("""
- **RSS Feeds**:
  - Google News (India Heavy Rain)
  - The Hindu
  - Indian Express
  - Times of India
  - NDTV
  - Sachet NDMA
- **Reddit API (r/...)**:
  - india, mumbai, delhi, bangalore, chennai, hyderabad, kolkata, pune
- **Weather API**:
  - Open-Meteo Current Weather
""")

# Load datasets
df_incidents = load_data_from_db()
df_alerts = load_alerts_from_csv()
city_coords = load_city_coordinates()

# Sidebar Navigation & AI API key setup
st.sidebar.markdown("---")
st.sidebar.markdown("### Dashboard Page")
app_page = st.sidebar.radio("Select View:", ["📊 Live Incident Monitor", "🤖 AI Zone Analysis (Groq)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### AI Analyzer Settings")
groq_api_key = st.sidebar.text_input(
    "🔑 Enter Groq API Key",
    type="password",
    help="Provide your Groq API Key to enable severity zone classification."
)

if df_incidents.empty:
    st.warning("⚠️ No data loaded yet. Use the sidebar button to run the Ingestion Pipeline and seed the database!")
    st.stop()

if app_page == "🤖 AI Zone Analysis (Groq)":
    st.subheader("🤖 AI Weather Severity Classification (Groq)")
    st.markdown("""
    This utility uses the **Groq API** with the `openai/gpt-oss-120b` model to evaluate the first 30 incident reports in the database.
    It identifies affected areas in India, groups them into severity zones, and lists detailed explanations for high-risk zones.
    """)
    
    # Initialize session state for AI report
    if "groq_report" not in st.session_state:
        st.session_state.groq_report = None
        
    if not groq_api_key:
        st.warning("🔑 Please enter your **Groq API Key** in the sidebar to enable this analysis.")
        st.session_state.groq_report = None  # Clear past reports if key is cleared
    else:
        st.success("API Key detected. Click below to run AI analysis.")
        if st.button("📊 Run AI Severity Classification", type="primary"):
            with st.spinner("Analyzing top 30 database records with openai/gpt-oss-120b on Groq..."):
                report = groq_analyzer.analyze_weather_zones(df_incidents, groq_api_key)
                st.session_state.groq_report = report
                
        # Persist report rendering
        if st.session_state.groq_report:
            st.markdown("### 📋 AI Classification Report")
            st.markdown(st.session_state.groq_report)
    st.stop()

if app_page == "📊 Live Incident Monitor":
    # 1. Top Level Metrics
    total_records = len(df_incidents)
    
    # Active alerts in last 90 minutes
    active_alerts_count = 0
    recent_alerts_markup = ""
    if not df_alerts.empty:
        try:
            df_alerts["detected_at_dt"] = pd.to_datetime(df_alerts["detected_at"], errors="coerce")
            cutoff = datetime.now() - pd.Timedelta(minutes=90)
            active_alerts = df_alerts[df_alerts["detected_at_dt"] >= cutoff]
            active_alerts_count = len(active_alerts)
            
            if active_alerts_count > 0:
                for _, row in active_alerts.iterrows():
                    recent_alerts_markup += f"""
                    <div class="alert-card">
                        <strong>🚨 CRITICAL SPIKE IN {row['location'].upper()}</strong><br>
                        {row['mentions']} mentions detected. Detected at {row['detected_at']}<br>
                        <em>Top posts: {row['headlines']}</em>
                    </div>
                    """
        except Exception:
            active_alerts_count = len(df_alerts)
            
    # Unpack locations to count occurrences
    location_list = []
    for loc_str in df_incidents["location"].dropna():
        for l in loc_str.split(","):
            l_clean = l.strip()
            if l_clean and l_clean != "India" and l_clean != "Unknown":
                location_list.append(l_clean)
                
    most_affected_city = "N/A"
    if location_list:
        most_affected_city = pd.Series(location_list).value_counts().index[0]
        
    num_clusters = len(df_incidents[df_incidents["cluster_id"] != -1]["cluster_id"].unique())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><h3>📥 Total Ingested</h3><h1>{total_records}</h1><p>Incidents in database</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>🚨 Active Spikes</h3><h1>{active_alerts_count}</h1><p>Locations above threshold</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>📊 Clusters</h3><h1>{num_clusters}</h1><p>Groups of similar events</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><h3>📍 Most Mentioned</h3><h1>{most_affected_city}</h1><p>Primary disruption node</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 2. Alerts & Map Section
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        st.subheader("🚨 Rolling 90-Minute Spike Alerts")
        if active_alerts_count > 0:
            st.markdown(recent_alerts_markup, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-card">
                <strong>✅ All Quiet</strong><br>
                No active location spikes (mentions >= 3) in the last 90 minutes.
            </div>
            """, unsafe_allow_html=True)
            
        # Display alerts table if available
        if not df_alerts.empty:
            st.markdown("##### Historical Spike Logs")
            st.dataframe(df_alerts, width="stretch")

    with right_col:
        st.subheader("📍 Disruption Map (India)")
        # Build coordinates dataframe for map
        map_data = []
        for _, row in df_incidents.iterrows():
            loc_str = row.get("location", "")
            if not loc_str or pd.isna(loc_str):
                continue
            cities = [c.strip() for c in loc_str.split(",") if c.strip()]
            for city in cities:
                city_lower = city.lower()
                if city_lower in city_coords:
                    lat, lon = city_coords[city_lower]
                    map_data.append({"city": city, "latitude": lat, "longitude": lon})
                    
        if map_data:
            df_map = pd.DataFrame(map_data)
            st.map(df_map, latitude="latitude", longitude="longitude", size=20, color="#ff4b4b")
        else:
            st.info("No coordinates matched for recent incidents to display on the map.")

    st.markdown("---")

    # 3. Visual Charts & Analytics
    st.subheader("📊 Ingestion & Source Analytics")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("##### Incident Count by Source")
        source_counts = df_incidents["source"].value_counts()
        st.bar_chart(source_counts, color="#2563eb")
        
    with c2:
        st.markdown("##### Top Disrupted Locations (Mentions)")
        if location_list:
            top_locs = pd.Series(location_list).value_counts().head(10)
            st.bar_chart(top_locs, color="#d97706")
        else:
            st.info("No city locations available for breakdown.")

    st.markdown("---")

    # 4. Interactive Data Viewer & Clustering
    st.subheader("🔍 Search & Filter Raw Incidents")
    
    # Filter controls
    f_source = st.selectbox("Filter by Source", ["All"] + list(df_incidents["source"].unique()))
    f_location = st.text_input("Search Location (e.g. Mumbai)")
    f_search = st.text_input("Search Text Keyword (e.g. waterlogging)")
    
    df_filtered = df_incidents.copy()
    if f_source != "All":
        df_filtered = df_filtered[df_filtered["source"] == f_source]
    if f_location:
        df_filtered = df_filtered[df_filtered["location"].str.contains(f_location, case=False, na=False)]
    if f_search:
        df_filtered = df_filtered[
            df_filtered["title"].str.contains(f_search, case=False, na=False) |
            df_filtered["text"].str.contains(f_search, case=False, na=False)
        ]
        
    st.write(f"Showing {len(df_filtered)} of {len(df_incidents)} records")
    st.dataframe(
        df_filtered[["id", "source", "title", "text", "location", "cluster_id", "created_at"]],
        width="stretch"
    )
    
    # Clustering Details
    st.subheader("🔗 Cluster Explorer (Similar Incident Grouping)")
    grouped_clusters = df_incidents[df_incidents["cluster_id"] != -1].groupby("cluster_id")
    if len(grouped_clusters) > 0:
        for cid, group in grouped_clusters:
            with st.expander(f"📦 Cluster #{cid} ({len(group)} similar items)"):
                st.write(group[["source", "title", "location", "created_at"]])
    else:
        st.info("No incident clusters formed yet. DBSCAN requires at least 2 similar items to form a cluster.")
