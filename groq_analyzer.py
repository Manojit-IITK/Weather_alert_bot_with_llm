import requests
from logger import logger

def analyze_weather_zones(df, api_key):
    """
    Analyzes the first 50 rows of weather incident data using Groq API
    with the 'openai/gpt-oss-120b' model.
    Categorizes affected areas into Red and Orange zones, providing specific reasons.
    """
    if df.empty:
        return "⚠️ No weather incident records found in the database to analyze."

    # Take the first 30 rows
    df_top = df.head(30)
    
    # Format the data for the LLM prompt (only send source, location, and title)
    records_str = []
    for idx, row in df_top.iterrows():
        title = str(row.get("title", "")).strip()
        location = str(row.get("location", "")).strip()
        source = str(row.get("source", "")).strip()
        
        record_fmt = (
            f"Incident #{idx+1}\n"
            f"Source: {source}\n"
            f"Location: {location}\n"
            f"Title: {title}\n"
            f"----------------------------------------"
        )
        records_str.append(record_fmt)
        
    incidents_payload = "\n".join(records_str)
    
    # Construct prompts
    system_prompt = (
        "You are an expert disaster response and weather analyst for India. "
        "Your task is to analyze the provided weather incident records, extract unique affected areas/cities/districts, "
        "and classify them into Red and Orange zones based on severity."
    )
    
    user_prompt = f"""Below are the 30 most recent weather incident reports collected by our monitoring agent:

{incidents_payload}

Please perform a comprehensive weather severity and impact analysis and format your output in this EXACT structure, with these EXACT headers:

### 📝 Overall Weather Situation Summary
[Provide a clear, high-level paragraph summarizing the general weather conditions, patterns, and primary disruptions currently affecting parts of India based on these reports]

### 🔴 Red Zone (High/Critical Severity Areas)
List all areas classified in the Red Zone (severe flooding, flash floods, landslides, cyclone impacts, total road blockages, or critical transit shutdowns). For each area, use this format:
* **Area Name**: [Area name]
  - **Reason / Why Affected**: [The specific trigger, e.g. cloudburst, severe thunderstorm]
  - **What Is Going To Happen & Consequences**: [Explain the impact, e.g. flight cancellations, train suspensions, high lightning strike hazard]
  - **Expected Timeline**: [The specific time window mentioned in the reports, e.g. "in the next 3 hours", "evening hours"]

### 🟠 Orange Zone (Moderate Severity Areas)
List all areas classified in the Orange Zone (moderate rain, warnings, minor waterlogging, fog delays, or light delays). For each area, use this format:
* **Area Name**: [Area name]
  - **Reason / Why Affected**: [The specific trigger, e.g. moderate thunderstorm, light rain]
  - **What Is Going To Happen & Consequences**: [Explain the impact, e.g. minor traffic delays, warning advisory]
  - **Expected Timeline**: [The time window, e.g. "in next 3 hours", "over the next 24 hours"]
"""

    # Clean the API key to remove whitespace, standard quotes, and smart/curly quotes
    api_key_clean = str(api_key).strip().strip('"').strip("'").strip('“').strip('”').strip('‘').strip('’').strip()

    headers = {
        "Authorization": f"Bearer {api_key_clean}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    logger.info("Sending database analysis completions request to Groq API...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            analysis_text = result["choices"][0]["message"]["content"]
            logger.info("Successfully received analysis from Groq.")
            return analysis_text
        else:
            error_msg = f"Groq API returned HTTP error code {response.status_code}: {response.text}"
            logger.error(error_msg)
            return f"❌ Analysis Failed.\n\n**API Error**: {response.text} (HTTP {response.status_code})"
    except requests.exceptions.Timeout:
        logger.error("Groq API request timed out after 30 seconds.")
        return "❌ Analysis Failed. The connection to the Groq API timed out. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error calling Groq API: {e}")
        return f"❌ Analysis Failed. An unexpected error occurred: {e}"
