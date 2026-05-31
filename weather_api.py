import requests
from logger import logger
from config import OPEN_METEO_BASE_URL

def fetch_weather(lat, lon):
    """
    Fetches current weather for given latitude and longitude from Open-Meteo.
    Returns a dict with temperature, precipitation, wind_speed, and weather_desc,
    or None if the request fails.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation,wind_speed_10m,weather_code",
        "timezone": "Asia/Kolkata"
    }
    
    try:
        response = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            
            # Open-Meteo WMO weather codes mapped to descriptions
            wmo_codes = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
                77: "Snow grains",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                85: "Slight snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            
            weather_code = current.get("weather_code", -1)
            weather_desc = wmo_codes.get(weather_code, f"Unknown ({weather_code})")
            
            weather_info = {
                "temperature": current.get("temperature_2m"),
                "precipitation": current.get("precipitation"),
                "wind_speed": current.get("wind_speed_10m"),
                "description": weather_desc,
                "fetched_at": current.get("time")
            }
            return weather_info
        else:
            logger.warning(f"Open-Meteo API returned status code {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching weather data from Open-Meteo: {e}")
        return None
