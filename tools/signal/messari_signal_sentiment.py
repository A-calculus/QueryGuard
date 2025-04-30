import requests
from typing import List, Dict, Optional, Union
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

def get_messari_signal_asset_sentiment(
    asset_id: str
) -> str:
    """
    Get sentiment data for a specific asset.
    
    Args:
        asset_id: The ID or slug of the asset
        
    Returns:
        String containing:
        - data: Asset sentiment data including:
            - id: Asset ID
            - name: Asset name
            - symbol: Asset symbol
            - slug: Asset slug
            - rank: Sentiment rank
            - sentimentScore: Sentiment score
            - sentimentMomentumScore: Sentiment momentum score
            - positivePostPercent: Percentage of positive posts
            - negativePostPercent: Percentage of negative posts
            - neutralPostPercent: Percentage of neutral posts
            - tweetVolume: Number of tweets
            
    Raises:
        Exception: If the API response indicates an error
    """
    url = f"https://api.messari.io/signal/v0/sentiment/assets/{asset_id}"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari signal asset sentiment ===")
    print(result.get("data", []))
    print("\n")
    return json.dumps(result.get("data", []))

def get_messari_signal_asset_sentiment_time_series(
    asset_id: str,
    granularity: str = "1h"
) -> str:
    """
    Get sentiment data for a specific asset over time.
    
    Args:
        asset_id: The ID or slug of the asset
        granularity: Time granularity ("1h" for hourly, "1d" for daily)
        
    Returns:
        String containing:
        - data: Time series data including:
            - points: Array of [timestamp, sentimentScore, sentimentRank, momentumScore, 
                              positivePostPercent, negativePostPercent, neutralPostPercent, 
                              tweetVolume]
            - metadata: Point schemas and granularity info
            
    Raises:
        Exception: If the API response indicates an error
    """
    url = f"https://api.messari.io/signal/v0/sentiment/assets/{asset_id}/time-series/{granularity}"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari signal asset sentiment time series ===")
    print(result.get("data", {}).get("points", [])[:100])
    print("\n")
    return json.dumps({"points": result.get("data", {}).get("points", [])[:100], "metadata": result.get("metadata", [])})

