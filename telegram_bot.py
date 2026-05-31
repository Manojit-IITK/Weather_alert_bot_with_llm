import os
import sys
import time
import requests
import subprocess
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import other scripts in directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import logger
from config import TELEGRAM_BOT_TOKEN, DB_PATH, GROQ_API_KEY_ENV
import database
import anomaly
import groq_analyzer

# Reload env just in case
load_dotenv()

BOT_TOKEN = TELEGRAM_BOT_TOKEN

def send_raw_message(chat_id, text, parse_mode="Markdown"):
    """Sends a raw message to a specific chat_id."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Clean up double asterisks to single asterisks for legacy Telegram Markdown parser
    if parse_mode == "Markdown":
        text = text.replace("**", "*")
        
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
        
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            # Fallback if markdown parsing fails
            logger.warning(f"Telegram Markdown send failed (HTTP {res.status_code}). Retrying as plain text...")
            payload.pop("parse_mode", None)
            requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")

def send_split_message(chat_id, text, parse_mode="Markdown"):
    """Splits messages exceeding Telegram's 4096-character limit."""
    LIMIT = 4000
    while len(text) > LIMIT:
        part = text[:LIMIT]
        last_nl = part.rfind("\n")
        if last_nl != -1:
            part = text[:last_nl]
            text = text[last_nl:]
        else:
            text = text[LIMIT:]
        send_raw_message(chat_id, part, parse_mode)
        time.sleep(0.5)
    send_raw_message(chat_id, text, parse_mode)

def handle_start(chat_id):
    welcome_msg = (
        "⛈️ *Welcome to the Weather Incident Monitoring Agent Bot!*\n\n"
        "I monitor real-time weather alerts and news disruptions in India.\n\n"
        "*Available Commands:*\n"
        "🔄 /update - Run ingestion pipeline to fetch new database records.\n"
        "📢 /alerts - View active rolling 90-minute city spikes.\n"
        "🤖 /analyze - Run Groq AI classification on the top 30 records (Red/Orange severity zones).\n"
        "📊 /status - View database statistics & sources.\n"
        "ℹ️ /help - Show this guide."
    )
    send_raw_message(chat_id, welcome_msg)

def handle_alerts(chat_id):
    try:
        # Fetch all incidents from DB
        df_incidents = database.fetch_all_incidents(limit=2000)
        if df_incidents.empty:
            send_raw_message(chat_id, "⚠️ No data found in the incidents database.")
            return
            
        spikes = anomaly.detect_spikes(df_incidents)
        if not spikes:
            send_raw_message(
                chat_id, 
                "✅ *All Quiet*\n\nNo active location spikes (mentions >= 3) detected in the last 90 minutes."
            )
            return
            
        alert_msg = "*🚨 Active Rolling 90-Minute Spike Alerts:*\n\n"
        for idx, spike in enumerate(spikes):
            loc = spike["location"]
            mentions = spike["mentions"]
            alert_msg += f"{idx+1}. *{loc}*: {mentions} mentions in last 90 minutes.\n"
        send_raw_message(chat_id, alert_msg)
    except Exception as e:
        logger.error(f"Error handling /alerts: {e}")
        send_raw_message(chat_id, f"❌ Failed to query alerts: {e}")

def handle_status(chat_id):
    try:
        df = database.fetch_all_incidents(limit=5000)
        if df.empty:
            send_raw_message(chat_id, "📊 *Database Status:*\n\nDatabase is currently empty (0 records).")
            return
            
        total_rows = len(df)
        sources = df["source"].value_counts()
        
        sources_str = ""
        for src, count in sources.items():
            sources_str += f"- {src}: {count} records\n"
            
        # Count locations (excluding generic "India")
        loc_series = df["location"].dropna()
        locations = set()
        for l_str in loc_series:
            for item in l_str.split(","):
                item_clean = item.strip()
                if item_clean and item_clean not in ["India", "Unknown"]:
                    locations.add(item_clean)
                    
        status_msg = (
            f"📊 *Weather Monitoring Agent Status*\n\n"
            f"- *Total Records Ingested*: {total_rows}\n"
            f"- *Unique Cities Tracked*: {len(locations)}\n"
            f"- *Last Ingested Date*: {df.iloc[0].get('created_at', 'N/A')}\n\n"
            f"*Source Distribution:*\n{sources_str}"
        )
        send_raw_message(chat_id, status_msg)
    except Exception as e:
        logger.error(f"Error handling /status: {e}")
        send_raw_message(chat_id, f"❌ Failed to fetch status: {e}")

def handle_update(chat_id):
    send_raw_message(
        chat_id, 
        "🔄 *Executing Ingestion Pipeline...* Ingesting live RSS feeds and weather forecasts. Please wait a few seconds."
    )
    try:
        python_exe = sys.executable
        app_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
        
        # Run app.py in a subprocess
        result = subprocess.run([python_exe, app_py], capture_output=True, text=True, timeout=90)
        
        if result.returncode == 0:
            summary = "✅ *Ingestion Pipeline Completed Successfully!*\n\n"
            # Parse metrics from stdout
            ingested_line = ""
            spike_line = ""
            for line in result.stdout.split("\n"):
                if "Total raw incidents ingested" in line:
                    ingested_line = f"📥 {line.split('INFO')[-1].strip()}"
                if "Spike detection completed" in line:
                    spike_line = f"🚨 {line.split('INFO')[-1].strip()}"
            
            if ingested_line:
                summary += ingested_line + "\n"
            if spike_line:
                summary += spike_line + "\n"
                
            summary += "\nDatabase is now up to date. You can run `/status` or `/alerts` to see the new data."
            send_raw_message(chat_id, summary)
        else:
            logger.error(f"Ingestion failed from Bot command: {result.stderr}")
            send_raw_message(
                chat_id, 
                f"❌ *Pipeline execution failed.*\n\nError details:\n`{result.stderr[:400]}`"
            )
    except Exception as e:
        logger.error(f"Error running pipeline from Bot: {e}")
        send_raw_message(chat_id, f"❌ *Failed to trigger pipeline:* {e}")

def handle_analyze(chat_id):
    # Fetch default Groq key from environment
    groq_api_key = os.getenv("GROQ_API_KEY", "") or GROQ_API_KEY_ENV
    
    if not groq_api_key:
        err_msg = (
            "🔑 *Configuration Required*\n\n"
            "Groq API Key is missing in the environment. Please edit the `.env` file and set:\n"
            "`GROQ_API_KEY=your_key_here`"
        )
        send_raw_message(chat_id, err_msg)
        return
        
    send_raw_message(chat_id, "🤖 *Requesting AI Severity Zone Classification...* Please wait.")
    
    try:
        df = database.fetch_all_incidents(limit=100)
        if df.empty:
            send_raw_message(chat_id, "⚠️ Database is empty. Please run ingestion to fetch records first.")
            return
            
        # Run classification
        analysis_report = groq_analyzer.analyze_weather_zones(df, groq_api_key)
        
        report_msg = (
            f"🤖 *AI Zone Severity Report*\n"
            f"Analyzed top 30 database records using model `openai/gpt-oss-120b`.\n\n"
            f"{analysis_report}"
        )
        send_split_message(chat_id, report_msg)
    except Exception as e:
        logger.error(f"Error handling /analyze: {e}")
        send_raw_message(chat_id, f"❌ AI Analysis failed: {e}")

def process_command(chat_id, cmd):
    """Routes the command string to the correct handler."""
    cmd = cmd.lower().strip()
    
    if cmd.startswith("/start"):
        handle_start(chat_id)
    elif cmd.startswith("/update"):
        handle_update(chat_id)
    elif cmd.startswith("/alerts"):
        handle_alerts(chat_id)
    elif cmd.startswith("/status"):
        handle_status(chat_id)
    elif cmd.startswith("/analyze"):
        handle_analyze(chat_id)
    elif cmd.startswith("/help"):
        handle_start(chat_id)
    else:
        # Unknown command
        send_raw_message(
            chat_id, 
            "🤔 Unknown command. Type /help to see available actions."
        )

def main_polling_loop():
    logger.info("Initializing Telegram Bot...")
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing in .env! Cannot start bot listener.")
        print("Error: TELEGRAM_BOT_TOKEN is missing in .env. Exiting.")
        return

    logger.info("Telegram Bot started. Polling for messages...")
    print("Telegram Bot listener started. Press Ctrl+C to stop.")
    
    last_update_id = 0
    # Warm up: fetch updates once to discard past messages (only process new messages)
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=10"
        res = requests.get(url, timeout=5).json()
        if res.get("ok") and res.get("result"):
            last_update_id = res["result"][-1]["update_id"]
            logger.info(f"Warmed up. Cleared past updates up to ID: {last_update_id}")
    except Exception as e:
        logger.warning(f"Bot warm up failed: {e}. Polling will start from beginning.")

    # Main infinite polling loop
    while True:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
        try:
            response = requests.get(url, timeout=35)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    results = data.get("result", [])
                    for update in results:
                        last_update_id = update["update_id"]
                        
                        message = update.get("message", {})
                        chat = message.get("chat", {})
                        chat_id = chat.get("id")
                        text = message.get("text", "")
                        
                        if chat_id and text:
                            user = chat.get("username", "user")
                            logger.info(f"Bot received command: '{text}' from {user} (ID: {chat_id})")
                            process_command(chat_id, text)
            else:
                logger.error(f"Telegram getUpdates returned error: HTTP {response.status_code} - {response.text}")
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            # Network issue, sleep a bit and retry
            logger.warning(f"Telegram Bot network connection lost: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error in Bot loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Ensure DB exists
    database.init_db()
    
    try:
        main_polling_loop()
    except KeyboardInterrupt:
        logger.info("Telegram Bot stopped by user.")
        print("\nTelegram Bot listener stopped.")
