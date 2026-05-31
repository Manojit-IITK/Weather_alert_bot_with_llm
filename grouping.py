import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from logger import logger

def group_incidents(df):
    """
    Groups similar incidents using TF-IDF and DBSCAN.
    Expects a DataFrame with 'title' and 'text' columns.
    Adds a 'cluster_id' column to the DataFrame.
    """
    if df.empty:
        return df
        
    if "cluster_id" not in df.columns:
        df["cluster_id"] = -1
        
    # We need at least 2 samples to cluster with DBSCAN min_samples=2
    if len(df) < 2:
        df["cluster_id"] = -1
        return df

    try:
        # Combine title and text for vectorization
        corpus = []
        for _, row in df.iterrows():
            title = str(row.get("title", ""))
            text = str(row.get("text", ""))
            corpus.append(f"{title} {text}".strip())

        # Check if there's any non-empty content to vectorize
        if not any(corpus):
            df["cluster_id"] = -1
            return df
            
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # Fit DBSCAN
        db = DBSCAN(eps=0.7, min_samples=2, metric="cosine")
        db.fit(tfidf_matrix)
        
        # Assign cluster labels (-1 is noise, 0, 1, 2... are clusters)
        df["cluster_id"] = db.labels_
        
        cluster_count = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
        noise_count = list(db.labels_).count(-1)
        logger.info(f"Grouped incidents. Formed {cluster_count} clusters (Noise/Outliers: {noise_count}).")
        
    except Exception as e:
        logger.error(f"Error during similarity grouping: {e}")
        df["cluster_id"] = -1
        
    return df
