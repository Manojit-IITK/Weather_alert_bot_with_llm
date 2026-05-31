import os
import sys
import pandas as pd
from datetime import datetime
from logger import logger
from config import RAW_DATA_PATH, GROUPED_DATA_PATH, SPIKE_THRESHOLD, SPIKE_WINDOW_MINUTES
import database
import feeds
import reddit_ingest
import grouping
import anomaly
import locations
import weather_api
import summarizer
import alerts
import telegram_alerts

def ensure_directories():
    """Ensure data and logs directories exist."""
    for path in [RAW_DATA_PATH, GROUPED_DATA_PATH]:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

def append_to_csv(df, file_path):
    """Appends data to a CSV file, avoiding duplicates."""
    if df.empty:
        return
        
    if os.path.exists(file_path):
        try:
            df_existing = pd.read_csv(file_path, encoding="utf-8")
            # Combine
            df_combined = pd.concat([df_existing, df], ignore_index=True)
            # Remove duplicates by title, source, created_at
            df_combined = df_combined.drop_duplicates(subset=["title", "source", "created_at"], keep="last")
            df_combined.to_csv(file_path, index=False, encoding="utf-8")
            logger.info(f"Appended records to {file_path}. Total rows now: {len(df_combined)}")
        except Exception as e:
            logger.error(f"Error appending to CSV {file_path}: {e}")
            df.to_csv(file_path, index=False, encoding="utf-8")
    else:
        df.to_csv(file_path, index=False, encoding="utf-8")
        logger.info(f"Created CSV {file_path} with {len(df)} records.")

def save_triggered_alert_to_csv(alert_dict):
    """Saves a triggered spike alert into the grouped alerts CSV."""
    df_alert = pd.DataFrame([{
        "location": alert_dict["location"],
        "mentions": alert_dict["mentions"],
        "detected_at": alert_dict["detected_at"],
        "headlines": "; ".join([inc.get("title", "") for inc in alert_dict["incidents"][:3]])
    }])
    
    file_path = GROUPED_DATA_PATH
    if os.path.exists(file_path):
        try:
            df_existing = pd.read_csv(file_path, encoding="utf-8")
            df_combined = pd.concat([df_existing, df_alert], ignore_index=True)
            df_combined.to_csv(file_path, index=False, encoding="utf-8")
        except Exception as e:
            logger.error(f"Error saving alert to CSV: {e}")
            df_alert.to_csv(file_path, index=False, encoding="utf-8")
    else:
        df_alert.to_csv(file_path, index=False, encoding="utf-8")
    logger.info(f"Logged spike alert to {file_path}")

def run_pipeline():
    logger.info("Starting Weather Incident Monitoring Ingestion Pipeline...")
    ensure_directories()
    
    # 1. Ingest RSS News feeds
    rss_incidents = feeds.fetch_rss_feeds()
    
    # 2. Ingest Reddit posts
    reddit_incidents = reddit_ingest.fetch_reddit_data()
    
    # Combine incidents
    all_incidents = rss_incidents + reddit_incidents
    logger.info(f"Total raw incidents ingested: {len(all_incidents)}")
    
    if not all_incidents:
        logger.info("No weather-relevant incidents found in this run.")
        return
        
    df_new = pd.DataFrame(all_incidents)
    
    # 3. Classify and group similar posts using TF-IDF and DBSCAN
    df_new = grouping.group_incidents(df_new)
    
    # 4. Save to CSV (Raw & Cluster assigned)
    append_to_csv(df_new, RAW_DATA_PATH)
    
    # 5. Store in SQLite
    new_incidents_list = df_new.to_dict(orient="records")
    database.save_incidents(new_incidents_list)
    
    # 6. Fetch recent incidents from SQLite to perform rolling Spike Detection (90 mins window)
    df_recent = database.fetch_all_incidents(limit=2000) # Fetch recent ones
    spikes = anomaly.detect_spikes(df_recent)
    
    logger.info(f"Spike detection completed. Triggered {len(spikes)} alerts.")
    
    # 7. Enrich spikes with weather data, generate summaries and send alerts
    for spike in spikes:
        loc = spike["location"]
        mentions = spike["mentions"]
        incidents = spike["incidents"]
        
        # Query Open Meteo API for weather data
        lat, lon = locations.get_city_coords(loc)
        weather_info = None
        if lat is not None and lon is not None:
            logger.info(f"Fetching Open-Meteo weather details for {loc} ({lat}, {lon}) to enrich alert...")
            weather_info = weather_api.fetch_weather(lat, lon)
            
        # Generate summary
        summary_text = summarizer.generate_summary(loc, mentions, incidents, weather_info)
        
        # Send Email Alert
        subject = f"WEATHER ALERT: Severe Chatter Detected in {loc}"
        alerts.send_email_alert(subject, summary_text)
        
        # Send Telegram Alert
        telegram_alerts.send_telegram_message(f"*ALERT: Severe Weather Chatter*\n\n{summary_text}")
        
        # Save alert metadata to CSV
        save_triggered_alert_to_csv(spike)
        
    logger.info("Pipeline run finished successfully.")

if __name__ == "__main__":
    # Initialize DB schema
    database.init_db()
    
    # If run with '--loop', it runs every 10 minutes (or we can use standard scheduler)
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        import time
        import schedule
        
        logger.info("Running in scheduler mode. Running pipeline every 10 minutes...")
        # Run immediately first
        run_pipeline()
        
        schedule.every(10).minutes.do(run_pipeline)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
    else:
        # One-shot execution
        run_pipeline()
