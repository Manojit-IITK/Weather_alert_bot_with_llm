# Weather Incident Monitoring Agent — Build Specification

## Objective

Build a rapid MVP (single-machine, Python-based) that detects unusual weather-related incident chatter in India.

The system should identify:

- heavy rainfall
- flooding
- waterlogging
- inundation
- cyclones
- high winds
- fallen trees
- fog disruptions
- storm damage
- landslides
- urban flooding
- road blockages
- train disruptions
- airport disruptions caused by weather

This is an MVP and must be buildable in under 1 hour.

---

# Hard Constraints

DO NOT USE:

- scraping
- Selenium
- Playwright
- BeautifulSoup scraping
- snscrape
- browser automation
- unofficial APIs
- paid APIs
- Kafka
- Docker
- Kubernetes
- distributed systems

ONLY USE:

- RSS feeds
- Official APIs
- Public JSON endpoints
- Reddit API (PRAW)
- Free sources

Language:

- Python only

Goal:

- runnable immediately
- minimal setup
- local execution only

---

# Functional Requirements

The system must:

### Input Sources

Collect data from:

1. RSS News feeds
2. Reddit API
3. Weather APIs
4. Government/weather feeds if available

---

### Processing

Pipeline:

1. Ingest content
2. Clean text
3. Classify weather relevance
4. Extract locations
5. Group similar posts
6. Detect spikes
7. Generate summaries
8. Send alerts

---

### Output

Example:

High chatter detected regarding severe waterlogging in Mumbai (Andheri, Sion, Kurla). 55 mentions detected across Reddit and news feeds within 90 minutes.

---

# Data Sources

## RSS News Sources

Use RSS only.

RSS sources:

Google News RSS

https://news.google.com/rss/search?q=india+heavy+rain

The Hindu

https://www.thehindu.com/news/national/feeder/default.rss

Indian Express

https://indianexpress.com/section/india/feed/

Times Of India

https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms

NDTV

https://feeds.feedburner.com/ndtvnews-top-stories

Hindustan Times RSS

India Today RSS

Deccan Herald RSS

Regional RSS sources where available

Do not scrape article pages.

---

## Reddit

Use official API only:

Library:

praw

Monitor:

- r/india
- r/mumbai
- r/delhi
- r/bangalore
- r/chennai
- r/hyderabad
- r/kolkata
- r/pune

Retrieve:

- new posts
- recent posts

Limit:

50 posts/subreddit

---

## Weather APIs

Use:

Open Meteo

https://api.open-meteo.com/

Use weather API only as confidence boosting.

Not primary signal.

---

# Architecture

```text
RSS + Reddit + Weather API
            ↓
       Ingestion Layer
            ↓
Text Cleaning + NLP
            ↓
Relevance Classification
            ↓
Location Extraction
            ↓
Similarity Grouping
            ↓
Spike Detection
            ↓
Summary Generation
            ↓
Email Alerts
            ↓
SQLite Persistence
            ↓
Streamlit Dashboard
```

---

# Folder Structure

```text
weather_incident_agent/

├── app.py
├── dashboard.py
├── requirements.txt
├── .env
├── config.py
├── database.py
├── logger.py
├── feeds.py
├── reddit_ingest.py
├── weather_api.py
├── classifier.py
├── locations.py
├── grouping.py
├── anomaly.py
├── summarizer.py
├── alerts.py
├── utils.py
├── city_list.csv
├── incidents.db
│
├── logs/
│   └── app.log
│
└── data/
    ├── raw_articles.csv
    └── grouped_alerts.csv
```

---

# Dependencies

Create:

requirements.txt

Content:

```txt
pandas
numpy
requests
feedparser
praw
python-dotenv
scikit-learn
spacy
streamlit
schedule
sqlalchemy
```

---

# NLP Requirements

Use lightweight NLP only.

Relevance classification:

Method:

- keyword scoring
- TF-IDF similarity
- cosine similarity

Avoid:

- large LLMs

Optional:

- HuggingFace zero-shot classification

---

# Keywords

Use:

```python
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
"train disruption"

]
```

---

# Relevance Logic

Simple score:

```python
score=0

for keyword in WEATHER_KEYWORDS:
    if keyword in text:
        score+=1

relevant=score>=2
```

---

# Location Extraction

Use:

spaCy:

```python
en_core_web_sm
```

Approach:

1. Extract entities:

- GPE
- LOC

2. Match against predefined India city list

Return:

```python
["Mumbai","Pune"]
```

---

# Group Similar Content

Use:

TF-IDF:

```python
TfidfVectorizer
```

Then:

```python
DBSCAN
```

Parameters:

```python
eps=.7
min_samples=2
metric="cosine"
```

Output:

```python
cluster_id
```

---

# Spike Detection

Method:

Rolling threshold

Logic:

```python
mentions>=15
```

Window:

```python
90 minutes
```

Return:

Triggered alerts

---

# Summary Generator

Template:

```python
High chatter detected regarding severe weather activity in {location}

{mentions} mentions detected across Reddit and RSS feeds.
```

---

# Email Alerting

Use:

```python
smtplib
```

SMTP:

Gmail SMTP

Required:

App password

Environment variables:

```env
EMAIL_USER=
EMAIL_PASSWORD=
```

---

# Database

Use:

SQLite

Table:

incidents

Fields:

```text
id
source
title
text
location
cluster_id
created_at
```

---

# Logging

Log file:

```text
logs/app.log
```

Format:

```text
timestamp
level
message
```

Example:

```text
2026-05-27 10:21 INFO Fetched 400 records
2026-05-27 10:22 INFO Relevant records 88
2026-05-27 10:23 INFO Alerts triggered 3
```

---

# Dashboard

Build:

Streamlit dashboard

Features:

1. Incident table
2. Alert summaries
3. Source counts
4. Mention counts
5. Location grouping

Run:

```bash
streamlit run dashboard.py
```

---

# Persistence

Save:

Raw:

```text
data/raw_articles.csv
```

Grouped:

```text
data/grouped_alerts.csv
```

Database:

```text
incidents.db
```

---

# Required .env

Create:

```env
REDDIT_CLIENT_ID=

REDDIT_CLIENT_SECRET=

EMAIL_USER=

EMAIL_PASSWORD=
```

---

# Setup Commands

```bash
mkdir weather_incident_agent

cd weather_incident_agent

python -m venv venv


# Windows

venv\Scripts\activate


# Linux/Mac

source venv/bin/activate


pip install -r requirements.txt


python -m spacy download en_core_web_sm


python app.py


streamlit run dashboard.py
```

---

# Acceptance Criteria

The build is successful only if:

✓ Pulls RSS data

✓ Pulls Reddit data

✓ Pulls weather API data

✓ Filters irrelevant content

✓ Extracts locations

✓ Groups related incidents

✓ Detects spikes

✓ Generates summaries

✓ Sends email alerts

✓ Stores data in SQLite

✓ Exports CSV

✓ Displays dashboard

✓ Logs events

---

# Future Improvements (not MVP)

Optional future enhancements:

- GDELT API
- IMD bulletins
- sentence-transformers
- MiniLM embeddings
- rolling averages
- better anomaly detection
- cron scheduling
- confidence scoring
- map visualization