import requests
from logger import logger
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(text):
    """
    Sends a message to the configured Telegram chat.
    If credentials are not present, logs the message instead.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info("=" * 60)
        logger.info("[TELEGRAM ALERT NOT SENT - BOT CREDENTIALS MISSING IN .env]")
        logger.info(f"TEXT:\n{text}")
        logger.info("=" * 60)
        return True

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Clean up standard Markdown to match Telegram's legacy Markdown parser if needed,
    # or let it pass directly. Legacy "Markdown" expects *bold* rather than **bold**,
    # but handles double asterisks as bold in many clients as well. 
    # Let's do a simple clean replacement of double asterisks to single asterisks just in case,
    # and clean up markdown headers.
    cleaned_text = text.replace("**", "*")
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": cleaned_text,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram alert sent successfully.")
            return True
        else:
            # Fallback if markdown parsing failed (e.g. unclosed asterisks)
            logger.warning(f"Telegram Markdown send failed (HTTP {response.status_code}). Retrying as plain text...")
            payload.pop("parse_mode", None)
            payload["text"] = text  # send original text without markdown formatting
            retry_resp = requests.post(url, json=payload, timeout=10)
            if retry_resp.status_code == 200:
                logger.info("Telegram alert sent successfully as plain text.")
                return True
            else:
                logger.error(f"Failed to send Telegram alert: HTTP {retry_resp.status_code} - {retry_resp.text}")
                return False
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")
        return False
