# backend/agent/state.py
from typing import TypedDict, List, Dict, Any

class ResumeGraphState(TypedDict):
    """
    This is the data structure passed between our LangGraph agents.
    """
    job_description: str         # Input: What the user pasted
    retrieved_experience: str    # Input: The RAG data we fetched from Supabase

    # NEW: Store the full profile (Education, Contact info) here
    user_profile: str
    
    extracted_requirements: List[str] # Output from Analyst Agent
    draft_resume: str            # Output from Writer Agent
    
    critic_feedback: str         # Output from Critic Agent
    revision_count: int          # To prevent infinite loops
    is_approved: bool            # Conditional flag: True = done, False = rewrite