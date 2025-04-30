import requests
from typing import List, Dict, Optional, Union
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

def get_messari_signal_topics(
    sort: str = "trending",
    classes: Optional[List[str]] = None,
    asset_ids: Optional[List[str]] = None,
    page: int = 1,
    limit: int = 10
) -> str:
    """
    Get a list of topics sorted by specified ranking algorithm.
    
    Args:
        sort: Sorting algorithm ("trending", "new", or "top")
        classes: List of classes to filter topics
        asset_ids: List of asset IDs to filter topics
        page: Page number for pagination
        limit: Number of results per page
        
    Returns:
        String containing:
        - data: Array of topic objects including:
            - id: Topic ID
            - name: Topic name
            - slug: Topic slug
            - rank: Topic rank
            - mindshareScore: Mindshare score
            - mindshareMomentumScore: Mindshare momentum score
            - postVolume: Number of posts
            - tweetVolume: Number of tweets
            - assetCount: Number of assets
            
    Raises:
        Exception: If the API response indicates an error
    """
    url = "https://api.messari.io/signal/v0/topics/global/current"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    params = {
        "sort": sort,
        "page": page,
        "limit": limit
    }
    
    if classes:
        params["classes"] = ",".join(classes)
    if asset_ids:
        params["assetIDs"] = ",".join(asset_ids)
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari signal topics ===")
    print(result.get("data", [])[:20])
    print("\n")
    return json.dumps({
        "data": result.get("data", [])[:20],
        "metadata": result.get("metadata", {})
    })

def get_messari_signal_topics_daily(
    start_time: str,
    end_time: str
) -> str:
    """
    Get historical data on topics over a specified time range.
    
    Args:
        start_time: Start time in RFC3339 format (e.g., 2023-06-03T00:00:00Z)
        end_time: End time in RFC3339 format (e.g., 2023-06-03T00:00:00Z)
        
    Returns:
        String containing historical topic data
        
    Raises:
        Exception: If the API response indicates an error
    """
    url = "https://api.messari.io/signal/v0/topics/global/daily"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    params = {
        "start": start_time,
        "end": end_time
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari signal topics daily ===")
    print(result.get("data", []).get("points", [])[:12])
    print("\n")
    return json.dumps({
        "points": result.get("data", []).get("points", [])[:12],
        "metadata": result.get("metadata", [])
    })

def get_messari_signal_topic_classes() -> str:
    """
    Get a list of available classes for filtering topics.
    
    Returns:
        String containing available topic classes
        
    Raises:
        Exception: If the API response indicates an error
    """
    url = "https://api.messari.io/signal/v0/topics/classes"
    
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
    
    print("=== messari signal topic classes ===")
    print(result.get("data", []))
    print("\n")
    return json.dumps(result.get("data", []))

