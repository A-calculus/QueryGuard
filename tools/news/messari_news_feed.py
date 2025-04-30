import requests
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

def get_messari_news_feed(
    asset_ids: Optional[List[str]] = None,
    source_ids: Optional[List[str]] = None,
    source_types: Optional[List[str]] = None,
    sort: int = 2,
    published_before: Optional[int] = None,
    published_after: Optional[int] = None,
    page: int = 1,
    limit: int = 25
) -> str:
    """
    Get news articles from the Messari API.
    
    Args:
        asset_ids: Optional list of asset IDs to filter by
        source_ids: Optional list of source IDs to filter by
        source_types: Optional list of source types to filter by (News, Blog, Forum)
        sort: Sort by publish time (1 for ascending, 2 for descending)
        published_before: Optional timestamp in milliseconds UTC
        published_after: Optional timestamp in milliseconds UTC
        page: Page number for pagination
        limit: Number of results per page
        
    Returns:
        JSON string containing:
        - data: List of news articles with assets, publish time, source, title, URL, etc.
        - metadata: Pagination info (limit, page, totalRows, totalPages)
        
    Raises:
        Exception: If the API response indicates an error
    """
    url = "https://api.messari.io/news/v1/news/feed"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Build query parameters
    params = {
        "sort": sort,
        "page": page,
        "limit": limit
    }
    
    if asset_ids:
        params["assetIDs[]"] = asset_ids
    if source_ids:
        params["sourceIDs[]"] = source_ids
    if source_types:
        params["sourceTypes[]"] = source_types
    if published_before:
        params["publishedBefore"] = published_before
    if published_after:
        params["publishedAfter"] = published_after
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    result = response.json()
    
    # Check for errors
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari news feed ===")
    print(result.get("data", []))
    print("\n")
    return json.dumps(result.get("data", []))

