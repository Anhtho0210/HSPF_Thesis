import time
from langgraph.graph import StateGraph, END

# --- Import shared state ---
from models import AgentState

# --- Import nodes from Agent 1 ---
from Agent1 import (
    parse_profile_node, 
    conversational_chat_node, 
    wrap_up_chat_node, 
    check_for_completion
)

# --- Import nodes from Agent 3 ---
from Agent3 import (
    agent_3_filter_node,
    agent_3_rank_node
)


# --- 1. BUILD THE MASTER WORKFLOW ---
def build_master_workflow():
    workflow = StateGraph(AgentState)
    
    # Add Agent 1 Nodes
    workflow.add_node("parsing", parse_profile_node)
    workflow.add_node("chat", conversational_chat_node)
    workflow.add_node("wrap_up", wrap_up_chat_node)
    
    # Add Agent 3 Nodes
    workflow.add_node("agent_3_filter", agent_3_filter_node)
    workflow.add_node("agent_3_rank", agent_3_rank_node)

    workflow.set_entry_point("parsing")

    # Connect Agent 1 (Intake)
    workflow.add_conditional_edges(
        "parsing",
        check_for_completion,
        {
            "chat": "chat",
            "wrap_up": "wrap_up",
            "matching": "agent_3_filter"  # --- This connects Agent 1 to Agent 3 ---
        }
    )
    
    # Agent 1 chat loops (pause for input)
    workflow.add_edge("chat", END)
    workflow.add_edge("wrap_up", END)
    
    # Connect Agent 3 (Filter -> Rank)
    workflow.add_edge("agent_3_filter", "agent_3_rank")
    
    # Agent 3's final step is the end of the graph
    workflow.add_edge("agent_3_rank", END)

    return workflow.compile()


# --- 2. EXECUTION ---
if __name__ == "__main__":
    
    # Compile the full graph
    app = build_master_workflow()

    # --- Define Initial State ---
    initial_raw_input = (
        "Hi, I'm Anny Tran from Vietnam. I have a 4-year IT degree with a 7.0/10.0 GPA (min pass 5.0), "
        "and 210 ECTS. I got a 7.0 on my IELTS. I have 3 years of work experience. "
        "I'm interested in Machine Learning, AI, and Information Systems. "
        "I'd prefer Munich or Berlin and want tuition under 1000 EUR."
    )
    
    current_state: AgentState = {
        "user_intent": initial_raw_input,
        "latest_response": initial_raw_input,
        "ai_response": None,
        "user_profile": None,
        # Init Agent 3 keys
        "program_catalog": [], 
        "eligible_programs": [], 
        "ranked_programs": []
    }
    
    print("\n--- 🚀 Starting Full Agentic Workflow (Agent 1 + Agent 3) ---")
    
    # --- Main Loop ---
    while True:
        try:
            # Run the graph from the current state
            next_state = app.invoke(current_state)
            
            # Update current state
            current_state.update(next_state)

        except Exception as e:
            print(f"\n[ERROR] Graph execution failed: {e}. Exiting.")
            break

        # Check for AI Question (Pause point for Agent 1)
        ai_q = current_state.get("ai_response")

        if ai_q:
            print("-" * 50)
            print(f"AI Assistant: {ai_q}")
            user_response = input("You: ")
            print("-" * 50)
            
            # Update state with new input
            current_state["user_intent"] += " " + user_response
            current_state["latest_response"] = user_response
            current_state["ai_response"] = None
            
        else:
            # No AI question, means the graph finished (hit an END)
            break

    # --- Final Output ---
    print("\n" + "=" * 50)
    print("--- ✅ WORKFLOW COMPLETE! ---")
    print("=" * 50)
    
    final_ranked_list = current_state.get("ranked_programs")
    
    if final_ranked_list:
        print(f"\n--- Final Top 5 Ranked & Eligible Programs ---")
        for i, program in enumerate(final_ranked_list[:5]):
            print(f"{i+1}. {program['name']} (Score: {program['relevance_score']:.2f})")
    else:
        print("No eligible programs were found that match your profile.")