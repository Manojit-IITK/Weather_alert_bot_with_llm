from datetime import datetime, timedelta
import pandas as pd
from logger import logger
from config import SPIKE_THRESHOLD, SPIKE_WINDOW_MINUTES

def detect_spikes(df_incidents):
    """
    Detects spike alerts based on the count of mentions per location in the last 90 minutes.
    df_incidents: DataFrame containing all incidents.
    Returns a list of dictionaries, where each dict represents a triggered spike:
      {'location': str, 'mentions': int, 'incidents': list}
    """
    if df_incidents.empty:
        return []

    # Filter incidents from the last 90 minutes
    now = datetime.now()
    cutoff_time = now - timedelta(minutes=SPIKE_WINDOW_MINUTES)
    
    # Ensure created_at is parsed as datetime
    try:
        # SQLite stores as string, pandas can parse it
        df_incidents = df_incidents.copy()
        df_incidents["created_at_dt"] = pd.to_datetime(df_incidents["created_at"], errors="coerce")
        df_recent = df_incidents[df_incidents["created_at_dt"] >= cutoff_time]
    except Exception as e:
        logger.error(f"Error parsing created_at datetimes: {e}")
        # Fallback to simple filtering if datetime conversion fails
        df_recent = df_incidents.copy()

    # Count mentions per location. Since locations can be comma-separated, we split them.
    location_counts = {}
    location_incidents = {}
    
    for _, row in df_recent.iterrows():
        loc_str = row.get("location", "")
        if not loc_str or pd.isna(loc_str):
            continue
            
        # Locations are stored as comma-separated values (e.g., "Mumbai, Pune")
        locations = [l.strip() for l in loc_str.split(",") if l.strip()]
        for loc in locations:
            location_counts[loc] = location_counts.get(loc, 0) + 1
            if loc not in location_incidents:
                location_incidents[loc] = []
            location_incidents[loc].append(row.to_dict())

    triggered_spikes = []
    for loc, count in location_counts.items():
        if count >= SPIKE_THRESHOLD:
            logger.warning(f"SPIKE DETECTED: Location '{loc}' has {count} mentions in the last {SPIKE_WINDOW_MINUTES} minutes (threshold: {SPIKE_THRESHOLD})!")
            triggered_spikes.append({
                "location": loc,
                "mentions": count,
                "incidents": location_incidents[loc],
                "detected_at": now.isoformat()
            })
            
    return triggered_spikes
