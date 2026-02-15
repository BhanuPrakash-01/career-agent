# backend/agent/graph.py
from langgraph.graph import StateGraph, END
from .state import ResumeGraphState
from .nodes import analyst_node, writer_node, critic_node # Import the real logic

# --- Routing Logic ---

def should_continue(state: ResumeGraphState):
    """
    If the Critic approves, we stop.
    If the Critic rejects, we go back to the Writer.
    Safety: If we have revised 3 times, we force stop to prevent infinite loops.
    """
    if state["is_approved"]:
        return END
    
    if state["revision_count"] >= 3:
        print("--- Max revisions reached. Stopping. ---")
        return END
        
    return "writer"

# --- Build the Graph ---

workflow = StateGraph(ResumeGraphState)

# Add nodes
workflow.add_node("analyst", analyst_node)
workflow.add_node("writer", writer_node)
workflow.add_node("critic", critic_node)

# Add edges
workflow.set_entry_point("analyst")
workflow.add_edge("analyst", "writer")
workflow.add_edge("writer", "critic")

# Conditional edge loop
workflow.add_conditional_edges(
    "critic",
    should_continue,
    {
        "writer": "writer",
        END: END
    }
)

# Compile
resume_builder_app = workflow.compile()