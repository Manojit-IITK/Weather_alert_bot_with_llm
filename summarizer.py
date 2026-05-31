def generate_summary(location, mentions, incidents=None, weather_info=None):
    """
    Generates a weather alert summary.
    Includes the mandatory template and enriches it with details if available.
    """
    # Mandatory template format
    base_summary = (
        f"High chatter detected regarding severe weather activity in {location}\n\n"
        f"{mentions} mentions detected across Reddit and RSS feeds."
    )
    
    # Enrichment
    enrichment_parts = []
    
    # Add Weather information if available
    if weather_info:
        temp = weather_info.get("temperature")
        precip = weather_info.get("precipitation")
        wind = weather_info.get("wind_speed")
        desc = weather_info.get("description")
        
        weather_str = "Current Weather Conditions from Open-Meteo:\n"
        if desc:
            weather_str += f"- Status: {desc}\n"
        if temp is not None:
            weather_str += f"- Temperature: {temp}°C\n"
        if precip is not None:
            weather_str += f"- Precipitation: {precip} mm\n"
        if wind is not None:
            weather_str += f"- Wind Speed: {wind} km/h\n"
        enrichment_parts.append(weather_str)
        
    # Add Top Articles / Headlines if available
    if incidents:
        headlines_str = "Recent Headlines / Posts:\n"
        # Get up to 3 distinct headlines
        seen_titles = set()
        count = 0
        for inc in incidents:
            title = inc.get("title", "").strip()
            if title and title not in seen_titles:
                headlines_str += f"- [{inc.get('source', 'Unknown')}] {title}\n"
                seen_titles.add(title)
                count += 1
                if count >= 3:
                    break
        if count > 0:
            enrichment_parts.append(headlines_str)
            
    # Combine everything
    full_summary = base_summary
    if enrichment_parts:
        full_summary += "\n\n" + "\n\n".join(enrichment_parts)
        
    return full_summary
