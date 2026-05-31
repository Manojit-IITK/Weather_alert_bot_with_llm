import os
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

WEATHER_KEYWORDS = [
    "flood",
    "flooding",
    "waterlogging",
    "heavy rain",
    "cyclone",
    "storm",
    "landslide",
    "fog",
    "tree fall",
    "inundation",
    "road blockage",
    "airport disruption",
    "train disruption",
    "rain"
]

RSS_FEEDS = {
    "Google News": "https://news.google.com/rss/search?q=india+heavy+rain",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/section/india/feed/",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "Sachet NDMA": "https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml"
}

SUBREDDITS = [
    "india",
    "mumbai",
    "delhi",
    "bangalore",
    "chennai",
    "hyderabad",
    "kolkata",
    "pune"
]

REDDIT_LIMIT = 50

DB_PATH = os.getenv("DB_PATH", "incidents.db")
RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", os.path.join("data", "raw_articles.csv"))
GROUPED_DATA_PATH = os.getenv("GROUPED_DATA_PATH", os.path.join("data", "grouped_alerts.csv"))

# Anomaly/Spike thresholds
SPIKE_THRESHOLD = 3
SPIKE_WINDOW_MINUTES = 90

# Open-Meteo endpoint (coordinates can be resolved per city)
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
# Default recipient if none specified
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT", EMAIL_USER)

# Telegram credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GROQ_API_KEY_ENV = os.getenv("GROQ_API_KEY", "")
