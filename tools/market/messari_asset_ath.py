import requests
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

def get_messari_asset_ath(
    ids: Optional[List[str]] = None,
    slugs: Optional[List[str]] = None,
    category: Optional[str] = None,
    sector: Optional[str] = None,
    tags: Optional[List[str]] = None,
    search: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Get All-Time High (ATH) data for specified assets from the Messari API.
    
    Args:
        ids: Optional list of asset IDs
        slugs: Optional list of asset slugs (defaults to bitcoin,ethereum if neither ids nor slugs provided)
        category: Optional filter by asset category
        sector: Optional filter by asset sector
        tags: Optional list of tags to filter by
        search: Optional fuzzy search for assets by name, slug, or symbol
        limit: Maximum number of results to return (default: 20)
        
    Returns:
        JSON string containing list of assets with their ATH data
        
    Raises:
        Exception: If the API response indicates an error
    """
    url = "https://api.messari.io/metrics/v2/assets/ath"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Build query parameters
    params = {"limit": limit}
    if ids:
        params["ids"] = ",".join(ids)
    elif slugs:
        params["slugs"] = ",".join(slugs)
    else:
        params["slugs"] = "bitcoin,ethereum"  # Default value
    
    if category:
        params["category"] = category
    if sector:
        params["sector"] = sector
    if tags:
        params["tags"] = ",".join(tags)
    if search:
        params["search"] = search
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    result = response.json()
    
    # Check for errors
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari asset ath ===")
    print(result.get("data", []))
    print("\n")
    return json.dumps(result.get("data", []))
