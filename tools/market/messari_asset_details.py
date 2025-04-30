import requests
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

def get_messari_asset_details(
    ids: Optional[List[str]] = None,
    slugs: Optional[List[str]] = None
) -> str:
    """
    Get detailed information about specific assets from the Messari API.
    
    Args:
        ids: Optional list of asset IDs
        slugs: Optional list of asset slugs (defaults to bitcoin,ethereum if neither ids nor slugs provided)
        
    Returns:
        JSON string containing list of asset details including market data, qualitative information, supply information, ATH, and ROI
        
    Raises:
        Exception: If the API response indicates an error
    """
    url = "https://api.messari.io/metrics/v2/assets/details"
    
    headers = {
        "x-messari-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Build query parameters
    params = {}
    if ids:
        params["ids"] = ",".join(ids)
    elif slugs:
        params["slugs"] = ",".join(slugs)
    else:
        params["slugs"] = "bitcoin,ethereum"  # Default value
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    result = response.json()
    
    # Check for errors
    if result.get("error") is not None:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"API Error: {error_msg}")
    
    print("=== messari asset details ===")
    print(result.get("data", []))
    print("\n")
    return json.dumps(result.get("data", []))

