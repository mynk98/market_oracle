import os
import json
import datetime
import subprocess
from duckduckgo_search import DDGS

# --- Configuration (Relative Paths) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
NEWS_DIR = os.path.join(BASE_DIR, "data/news_archive")

def fetch_and_save_news(query, category):
    print(f"[*] Searching {category} news: {query}")
    results = []
    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.news(query, max_results=10))
            for r in search_results:
                results.append({
                    "title": r.get('title'),
                    "snippet": r.get('body'),
                    "source": r.get('source'),
                    "date": r.get('date'),
                    "url": r.get('url')
                })
    except Exception as e:
        print(f"Error fetching {category}: {e}")
        return []
    return results

def run_sentiment_pipeline():
    os.makedirs(NEWS_DIR, exist_ok=True)
    topics = {
        "finance": "Indian stock market NSE BSE news today",
        "international": "global geopolitical events market impact",
        "tech": "AI tech industry trends February 2026",
        "commodities": "silver prices MCX news India"
    }
    
    news_report = {"timestamp": datetime.datetime.now().isoformat(), "categories": {}}
    for cat, query in topics.items():
        news_report["categories"][cat] = fetch_and_save_news(query, cat)
        
    filename = f"news_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(NEWS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(news_report, f, indent=2)
        
    latest_path = os.path.join(BASE_DIR, "data/latest_news.json")
    with open(latest_path, "w") as f:
        json.dump(news_report, f, indent=2)
        
    print(f"[*] News archived to {filepath}")
    return news_report

if __name__ == "__main__":
    run_sentiment_pipeline()
