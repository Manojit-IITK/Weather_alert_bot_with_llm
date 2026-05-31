import os
import pandas as pd
import spacy
from logger import logger

# Load city list
CITY_FILE = "city_list.csv"
cities_db = {}
if os.path.exists(CITY_FILE):
    try:
        df_cities = pd.read_csv(CITY_FILE)
        # Store as dict: lowercase_name -> (original_name, lat, lon)
        for _, row in df_cities.iterrows():
            city_name = str(row["city_name"]).strip()
            cities_db[city_name.lower()] = {
                "name": city_name,
                "lat": float(row["latitude"]),
                "lon": float(row["longitude"])
            }
        logger.info(f"Loaded {len(cities_db)} cities from {CITY_FILE}")
    except Exception as e:
        logger.error(f"Error loading {CITY_FILE}: {e}")
else:
    logger.warning(f"{CITY_FILE} not found. Location matching will be limited.")

# Load spaCy model
nlp = None
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy en_core_web_sm model loaded successfully.")
except Exception as e:
    logger.warning(f"Failed to load spaCy model en_core_web_sm ({e}). Location extraction will fall back to keyword search.")

def extract_locations(text):
    """
    Extracts Indian cities from the text.
    First uses spaCy GPE/LOC entities, then matches them against city_list.csv.
    If spaCy fails to load, falls back to direct keyword searching.
    """
    if not text or not isinstance(text, str):
        return []

    matched_cities = set()
    
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"]:
                    ent_clean = ent.text.strip().lower()
                    if ent_clean in cities_db:
                        matched_cities.add(cities_db[ent_clean]["name"])
        except Exception as e:
            logger.error(f"Error in spaCy extraction: {e}")
            
    # Fallback / Backup check: Check all city names directly in the text to capture missed locations
    # (or if spaCy failed to load)
    text_lower = text.lower()
    for city_lower, city_info in cities_db.items():
        # Use word boundaries or simple substring search
        # Simple substring search is usually fine for these specific Indian cities, 
        # but let's make sure it's not a substring of another word (like 'uri' in 'during').
        # We can do a basic check:
        if city_lower in text_lower:
            # Check word boundary to avoid partial match (like 'pune' in 'punishment' or 'delhi' in 'delhimits' etc)
            idx = text_lower.find(city_lower)
            while idx != -1:
                # Check character before and after
                before_ok = (idx == 0 or not text_lower[idx-1].isalnum())
                after_ok = (idx + len(city_lower) == len(text_lower) or not text_lower[idx + len(city_lower)].isalnum())
                if before_ok and after_ok:
                    matched_cities.add(city_info["name"])
                    break
                idx = text_lower.find(city_lower, idx + 1)
                
    return list(matched_cities)

def get_city_coords(city_name):
    """
    Returns latitude and longitude for a city name (case-insensitive).
    Returns (None, None) if not found.
    """
    info = cities_db.get(city_name.lower())
    if info:
        return info["lat"], info["lon"]
    return None, None
