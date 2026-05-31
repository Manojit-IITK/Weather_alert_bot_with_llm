import os
import random
from datetime import datetime, timedelta
from logger import logger
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, SUBREDDITS, REDDIT_LIMIT
from classifier import classify_relevance
from locations import extract_locations

# Attempt to import praw
try:
    import praw
except ImportError:
    praw = None

def get_reddit_client():
    """
    Returns a PRAW Reddit client if credentials are configured.
    Returns None otherwise.
    """
    if praw is None:
        logger.warning("PRAW library is not installed.")
        return None
        
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        logger.info("Reddit credentials missing in .env. Reddit source will be skipped.")
        return None
        
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent="weather-incident-agent:v1.0.0 (by /u/anonymous)",
            request_timeout=10
        )
        # Simple read-only check
        reddit.read_only = True
        return reddit
    except Exception as e:
        logger.warning(f"Failed to initialize Reddit client (check credentials): {e}. Skipping Reddit source.")
        return None

def fetch_real_reddit(reddit):
    """
    Fetches real posts from configured subreddits.
    """
    logger.info("Ingesting from Reddit using PRAW API...")
    all_incidents = []
    
    for sub_name in SUBREDDITS:
        try:
            subreddit = reddit.subreddit(sub_name)
            logger.info(f"Fetching posts from r/{sub_name}...")
            
            # Fetch new/hot posts
            posts_fetched = 0
            for submission in subreddit.new(limit=REDDIT_LIMIT):
                title = submission.title
                text = submission.selftext or ""
                full_text = f"{title}. {text}"
                
                # Check weather relevance
                relevant, score = classify_relevance(full_text)
                if not relevant:
                    continue
                    
                # Extract locations
                locations = extract_locations(full_text)
                # If no location is extracted, tag with city from subreddit name if it is in the city list
                if not locations:
                    # e.g., sub_name = 'mumbai' -> 'Mumbai'
                    if sub_name.lower() in ["mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "kolkata", "pune"]:
                        locations = [sub_name.capitalize()]
                    else:
                        locations = ["India"]
                        
                created_at_dt = datetime.fromtimestamp(submission.created_utc)
                
                incident = {
                    "source": f"Reddit (r/{sub_name})",
                    "title": title,
                    "text": text if text else title,
                    "location": ", ".join(locations),
                    "cluster_id": -1,
                    "created_at": created_at_dt.isoformat()
                }
                all_incidents.append(incident)
                posts_fetched += 1
                
            logger.info(f"Processed r/{sub_name}. Found {posts_fetched} relevant weather incidents.")
        except Exception as e:
            logger.error(f"Error fetching from r/{sub_name}: {e}")
            
    return all_incidents

def generate_mock_reddit_data():
    """
    Generates mock weather incidents from Reddit for simulation and testing.
    Specifies a spike (>=15 mentions) in Mumbai within the last 90 minutes
    to verify spike detection, DBSCAN clustering, email alerts, and the dashboard.
    """
    logger.info("Generating simulated Reddit data to verify anomaly/spike detection and clustering...")
    mock_data = []
    now = datetime.now()
    
    # 1. Mumbai Waterlogging Spike (18 posts within the last 60 minutes)
    mumbai_templates = [
        "Massive traffic jam at Andheri subway due to waterlogging.",
        "Sion circle is completely flooded, avoid this route guys!",
        "Heavy rain causing waterlogging in Kurla West, water entering houses.",
        "Waterlogging on SV road in Bandra. Traffic is standing still.",
        "Trains on Central Line running 20 mins late due to waterlogging at Kurla.",
        "Unbelievable rains in Mumbai today, waterlogging everywhere.",
        "Fallen tree near Dadar TT circle. Road blocked, heavy traffic.",
        "Mumbai rain update: Andheri, Kurla, Sion, and Hindmata are waterlogged.",
        "BMC claims to be prepared, but Sion is underwater within 2 hours of heavy rain.",
        "Milan subway is closed due to severe waterlogging.",
        "Stay safe guys, waterlogging reported on Link Road, Malad.",
        "Waterlogging at Hindmata Cinema, traffic diverted to Flyover.",
        "Eastern Express Highway waterlogged near Chembur, huge traffic jam.",
        "Waterlogging at Elphinstone road station, difficult to exit.",
        "King's Circle is flooded, waist-deep water in some parts.",
        "Heavy rain and waterlogging reported near domestic airport road.",
        "Fallen tree blocking the lane near Santacruz West.",
        "Train disruptions on Central and Harbour lines due to track waterlogging at Sion."
    ]
    
    for i, text in enumerate(mumbai_templates):
        # Disperse timestamps in the last 60 minutes
        minutes_ago = random.randint(5, 60)
        post_time = now - timedelta(minutes=minutes_ago)
        
        mock_data.append({
            "source": "Reddit (r/mumbai)",
            "title": f"Mumbai Rain Alert: {text[:40]}...",
            "text": text,
            "location": "Mumbai",
            "cluster_id": -1,
            "created_at": post_time.isoformat()
        })
        
    # 2. Delhi Rain Disruptions (5 posts in the last 90 minutes - below spike threshold)
    delhi_templates = [
        "Waterlogging at Ring Road near WHO building.",
        "Delhi rains: Traffic disruptions near ITO due to waterlogging.",
        "Fallen tree blocks lane near Connaught Place Outer Circle.",
        "Waterlogging under Minto Bridge, road closed.",
        "Heavy rain in Delhi NCR, flight disruptions at IGI airport."
    ]
    for i, text in enumerate(delhi_templates):
        minutes_ago = random.randint(10, 80)
        post_time = now - timedelta(minutes=minutes_ago)
        mock_data.append({
            "source": "Reddit (r/delhi)",
            "title": f"Delhi Rains: {text[:40]}...",
            "text": text,
            "location": "Delhi",
            "cluster_id": -1,
            "created_at": post_time.isoformat()
        })

    # 3. Bengaluru Rain Disruptions (3 posts)
    bengaluru_templates = [
        "Outer Ring Road flooded near EcoSpace, severe traffic block.",
        "Heavy rain causing tree fall in Indiranagar.",
        "Waterlogging in Silk Board junction, Bengaluru traffic back to normal jams."
    ]
    for i, text in enumerate(bengaluru_templates):
        minutes_ago = random.randint(15, 80)
        post_time = now - timedelta(minutes=minutes_ago)
        mock_data.append({
            "source": "Reddit (r/bangalore)",
            "title": f"Bengaluru Rain: {text[:40]}...",
            "text": text,
            "location": "Bangalore",
            "cluster_id": -1,
            "created_at": post_time.isoformat()
        })
        
    return mock_data

def fetch_reddit_data():
    """
    Entry point for Reddit data fetching.
    Returns empty list if credentials are not configured or if fetching fails.
    No simulation fallback is performed.
    """
    reddit_client = get_reddit_client()
    if reddit_client:
        try:
            return fetch_real_reddit(reddit_client)
        except Exception as e:
            logger.error(f"Error fetching real Reddit data: {e}. Skipping Reddit source.")
            return []
    else:
        return []
