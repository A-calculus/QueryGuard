import os
import requests
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

class ChatAgent:
    def __init__(self):
        self.headers = {
            "x-messari-api-key": API_KEY,
            "Content-Type": "application/json"
        }
        self.endpoint = "https://api.messari.io/ai/v1/chat/completions"

    async def __call__(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get completion from Messari AI chat endpoint."""
        # Format messages according to Messari API requirements
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        params = {
            "messages": formatted_messagesmessages,
            "verbosity": "verbose",
            "response_format": "plaintext",
            "inline_citations": True,
            "stream": False  # Changed to False to avoid streaming issues
        }
        
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=params
            )
            
            if response.status_code != 200:
                return {
                    "messages": [],
                    "cited_sources": [],
                    "error": f"Messari AI API error: {response.text}"
                }
            
            result = response.json()
            
            # Extract messages and cited sources
            messages = result.get("data", {}).get("messages", [])
            cited_sources = result.get("metadata", {}).get("cited_sources", [])
            
            return {
                "messages": messages,
                "cited_sources": cited_sources
            }
            
        except Exception as e:
            return {
                "messages": [],
                "cited_sources": [],
                "error": str(e)
            }

async def chat_agent(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Factory function to create and use the ChatAgent."""
    agent = ChatAgent()
    response = await agent(messages)
    print("\n=== Chat Agent Response ===")
    print(json.dumps(response, indent=2))
    return response 