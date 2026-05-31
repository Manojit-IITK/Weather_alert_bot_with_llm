from config import WEATHER_KEYWORDS

def classify_relevance(text):
    """
    Classifies if text is weather-relevant.
    Returns (relevant: bool, score: int).
    A text is relevant if it contains at least 2 weather keywords (case-insensitive).
    """
    if not text or not isinstance(text, str):
        return False, 0
        
    text_lower = text.lower()
    score = 0
    matched_keywords = []
    
    for keyword in WEATHER_KEYWORDS:
        if keyword.lower() in text_lower:
            score += 1
            matched_keywords.append(keyword)
            
    relevant = score >= 2
    return relevant, score
