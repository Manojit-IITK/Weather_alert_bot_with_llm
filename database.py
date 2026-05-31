import os
import sqlite3
import pandas as pd
from datetime import datetime
from logger import logger
from config import DB_PATH, RAW_DATA_PATH, GROUPED_DATA_PATH

def get_connection():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            text TEXT,
            location TEXT,
            cluster_id INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def save_incidents(incidents_list):
    """
    Saves a list of dictionaries as incidents in the DB.
    Each dictionary should have keys: source, title, text, location, cluster_id, created_at.
    """
    if not incidents_list:
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    inserted_count = 0
    for inc in incidents_list:
        # Format created_at to ISO string if it is a datetime object
        created_at_val = inc.get("created_at")
        if isinstance(created_at_val, datetime):
            created_at_val = created_at_val.isoformat()
        elif not created_at_val:
            created_at_val = datetime.now().isoformat()
            
        cursor.execute("""
            INSERT INTO incidents (source, title, text, location, cluster_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            inc.get("source", ""),
            inc.get("title", ""),
            inc.get("text", ""),
            inc.get("location", ""),
            inc.get("cluster_id", -1),
            created_at_val
        ))
        inserted_count += 1
        
    conn.commit()
    conn.close()
    logger.info(f"Saved {inserted_count} records to database.")

def fetch_all_incidents(limit=1000):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM incidents ORDER BY created_at DESC LIMIT {limit}", conn)
    conn.close()
    return df

def fetch_incidents_in_window(minutes=90):
    """
    Fetches incidents from the last N minutes.
    """
    conn = get_connection()
    # Using sqlite datetime function
    # Note: SQLite stores datetime strings. If stored in ISO format, we can query them.
    query = """
        SELECT * FROM incidents 
        WHERE datetime(created_at) >= datetime('now', ?)
    """
    # -N minutes format for SQLite
    df = pd.read_sql_query(query, conn, params=(f"-{minutes} minutes",))
    conn.close()
    return df

def reset_database():
    """
    Resets the database by dropping and recreating the incidents table,
    and deleting the CSV logs.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS incidents")
        conn.commit()
        conn.close()
        logger.info("Dropped incidents table.")
    except Exception as e:
        logger.error(f"Error dropping table: {e}")
        
    init_db()
    
    # Also delete CSV files to clear all data
    for file_path in [RAW_DATA_PATH, GROUPED_DATA_PATH]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted data file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")

