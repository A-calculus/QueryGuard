import requests
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

def get_messari_news_assets(
    name_or_symbol: Optional[str] = None,
    page: int = 1,
    limit: int = 20
) -> str:
    """
    Get a list of assets that have been tagged in news articles.
    
    Args:
        name_or_symbol: Optional case-sensitive text to search by asset name or symbol
        page: Page number for pagination
        limit: Number of results per page
        
    Returns:
        JSON string containing:
        - data: List of assets with id, name, slug, and symbol
        - metadata: Pagination info (limit, page, totalRows, totalPages)
        
    Raises:
        Exception: If the API response indicates an error
    """
    url = "https://api.messari.io/news/v1/news/assets"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Build query parameters
    params = {
        "page": page,
        "limit": limit
    }
    
    if name_or_symbol:
        params["nameOrSymbol"] = name_or_symbol
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    result = response.json()
    
    # Check for errors
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari news assets ===")
    print(result.get("data", []))
    print("\n")
    return json.dumps(result.get("data", []))

