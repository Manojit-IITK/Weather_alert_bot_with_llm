import feedparser
import time
from datetime import datetime
from logger import logger
from config import RSS_FEEDS
from classifier import classify_relevance
from locations import extract_locations

def parse_rss_date(entry):
    """
    Tries to parse the publication date of an RSS entry.
    Falls back to current datetime.
    """
    for date_key in ["published_parsed", "updated_parsed", "created_parsed"]:
        parsed_struct = entry.get(date_key)
        if parsed_struct:
            try:
                # Convert time struct to datetime
                dt = datetime(*parsed_struct[:6])
                return dt.isoformat()
            except Exception:
                pass
                
    # Fallback to string parse if struct is not available
    for date_key in ["published", "updated", "created"]:
        date_str = entry.get(date_key)
        if date_str:
            try:
                # Try some common RSS date formats
                # e.g., 'Wed, 27 May 2026 12:00:00 GMT'
                dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                return dt.isoformat()
            except Exception:
                pass
                
    return datetime.now().isoformat()

def fetch_rss_feeds():
    """
    Fetches all configured RSS feeds, parses entries, 
    filters for weather relevance, and extracts locations.
    Returns a list of incident dictionaries.
    """
    all_incidents = []
    
    for feed_name, url in RSS_FEEDS.items():
        logger.info(f"Fetching RSS feed: {feed_name} from {url}")
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed {feed_name}")
                continue
                
            feed_incidents_count = 0
            for entry in feed.entries:
                title = entry.get("title", "")
                # Summary or description
                summary = entry.get("summary", "") or entry.get("description", "")
                
                # Combine title and summary for analysis
                full_text = f"{title}. {summary}"
                
                # Check weather relevance: Sachet alerts are relevant by definition
                if feed_name == "Sachet NDMA":
                    relevant = True
                else:
                    relevant, score = classify_relevance(full_text)
                if not relevant:
                    continue
                    
                # Extract locations
                locations = extract_locations(full_text)
                if not locations:
                    # Optional: default to "India" or skip. Project.md says "Match against predefined India city list"
                    # If we don't match any specific city in India, we can label it as "India" or skip.
                    # Since it is a weather incident *in India* and we want to monitor specific local incidents,
                    # we can tag it as "India" or leave it empty/skip. Let's tag it as "India" or "Unknown"
                    # so that it gets processed, or just skip if we only care about specific city spikes.
                    # Let's tag it as "India" if no specific city is matched, or keep it empty. 
                    # Actually, keeping it as "India" is a nice fallback.
                    loc_str = "India"
                else:
                    loc_str = ", ".join(locations)
                    
                published_iso = parse_rss_date(entry)
                
                incident = {
                    "source": feed_name,
                    "title": title,
                    "text": summary,
                    "location": loc_str,
                    "cluster_id": -1,
                    "created_at": published_iso
                }
                all_incidents.append(incident)
                feed_incidents_count += 1
                
            logger.info(f"Processed RSS feed {feed_name}. Found {feed_incidents_count} relevant weather incidents.")
        except Exception as e:
            logger.error(f"Error fetching/parsing RSS feed {feed_name}: {e}")
            
    return all_incidents
if __name__ == "__main__":
    # Test RSS feeds fetching
    import json
    results = fetch_rss_feeds()
    print(f"Fetched {len(results)} incidents")
    print(json.dumps(results[:3], indent=2))
