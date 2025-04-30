import requests
from typing import List, Dict, Optional, Union
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

def get_messari_signal_assets(
    page: int = 1,
    limit: int = 20
) -> Dict:
    """
    Get a list of assets sorted by mindshare.
    
    Args:
        page: Page number for pagination
        limit: Number of results per page
        
    Returns:
        Dict containing:
        - data: List of assets with mindshare data
        - metadata: Pagination info
        
    Raises:
        Exception: If the API response indicates an error
    """
    url = "https://api.messari.io/signal/v0/assets"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    params = {
        "page": page,
        "limit": limit
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari signal assets ===")
    print(result.get("data", []))
    print("\n")
    return json.dumps(result.get("data", []))

def get_messari_signal_asset_by_id(
    asset_id: str
) -> str:
    """
    Get a specific asset by its ID or slug.
    
    Args:
        asset_id: The ID or slug of the asset to retrieve
        
    Returns:
        String containing:
        - data: Asset details including:
            - id: Asset ID
            - name: Asset name
            - symbol: Asset symbol
            - slug: Asset slug
            - mindshare: Mindshare data including rank, scores, and changes
            - sentiment: Sentiment data including scores and post percentages
            
    Raises:
        Exception: If the API response indicates an error
    """
    url = f"https://api.messari.io/signal/v0/assets/{asset_id}"
    
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
    
    print("=== messari signal asset by id ===")
    print(result.get("data", []))
    print("\n")
    return json.dumps(result.get("data", []))

def get_messari_signal_asset_mindshare(
    asset_id: str
) -> str:
    """
    Get a specific asset's mindshare over time.
    
    Args:
        asset_id: The ID or slug of the asset
        
    Returns:
        String containing:
        - data: Time series data including:
            - points: Array of [timestamp, rank, percentage, score]
            - metadata: Point schemas and granularity info
            
    Raises:
        Exception: If the API response indicates an error
    """
    url = f"https://api.messari.io/signal/v0/assets/{asset_id}/time-series/mindshare"
    
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

    points = result.get("data", {}).get("points", [])
    pointSchemas = result.get("metadata", {})
    
    print("=== messari signal asset mindshare ===")
    print(points)
    print("\n")
    return json.dumps({"points": points, "pointSchemas": pointSchemas})

