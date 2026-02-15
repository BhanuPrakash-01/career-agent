# backend/services/search.py
from typing import List, Dict, Any
from supabase import Client
from .embedding import get_embedding

async def search_similar_experience(
    query: str, 
    supabase_client: Client, 
    profile_id: str,
    threshold: float = 0.5, 
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    1. Embeds the user's query (e.g., a Job Description requirement).
    2. Calls the Supabase RPC function 'match_experience_items'.
    3. Returns the most relevant past experiences.
    """
    
    # A. Convert query text to numbers
    query_vector = get_embedding(query)
    
    if not query_vector:
        return []

    # B. Call the Database Function (RPC)
    try:
        response = supabase_client.rpc(
            "match_experience_items", 
            {
                "query_embedding": query_vector,
                "match_threshold": threshold,
                "match_count": limit,
                "filter_profile_id": profile_id
            }
        ).execute()
        
        return response.data

    except Exception as e:
        print(f"Search Error: {e}")
        return []