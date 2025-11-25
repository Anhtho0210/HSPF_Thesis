import time
import os
from langgraph.graph import StateGraph, END
from reportlab.pdfgen import canvas

# --- Import shared state ---
from models import AgentState

# --- Import nodes from Agent 1 ---
from Agent1 import (
    parse_profile_node, 
    conversational_chat_node, 
    wrap_up_chat_node, 
    check_for_completion,
    get_missing_fields,
    get_desirable_missing_fields
)
# --- Import nodes from Agent 3 ---
from Agent3 import agent_3_filter_node

# --- 1. BUILD THE MASTER WORKFLOW ---
def build_master_workflow():
    workflow = StateGraph(AgentState)
    
    # Add Agent 1 Nodes
    workflow.add_node("parsing", parse_profile_node)
    workflow.add_node("chat", conversational_chat_node)
    workflow.add_node("wrap_up", wrap_up_chat_node)
    
    # Add Agent 3 Nodes
    # Note: We merged filtering & ranking into ONE node in Agent3.py
    workflow.add_node("agent_3_filter", agent_3_filter_node)

    workflow.set_entry_point("parsing")

    # Connect Agent 1 (Intake)
    workflow.add_conditional_edges(
        "parsing",
        check_for_completion,
        {
            "chat": "chat",
            "wrap_up": "wrap_up",
            "matching": "agent_3_filter"  # Connects to Agent 3
        }
    )
    
    # Agent 1 chat loops (pause for input)
    workflow.add_edge("chat", END)
    workflow.add_edge("wrap_up", END)
    
    # Connect Agent 3 to End
    workflow.add_edge("agent_3_filter", END)

    return workflow.compile()


# --- 2. EXECUTION ---
if __name__ == "__main__":
    
    # 1. Prepare Data
    pdf_filename = "Transcrip_Of_Record.pdf"
    app = build_master_workflow()
 
    # --- Define Initial State ---
    # Note: We intentionally leave some fields vague to test Agent 1's questions
    initial_raw_input = (
        "Hi, I'm Anny from Vietnam. Here is my transcript. "
        "I want to study Data Science."
        # "I have IELTS 7.0" <-- Commented out to force Agent 1 to ask!
    )
    
    current_state = {
        "user_intent": "Hi, I'm Anny. I want to study data science.",
        "pdf_path": pdf_filename, 
        "user_profile": None,
        "program_catalog": [], 
        "eligible_programs": [], 
        "ranked_programs": [] # <--- This empty list causes the bug if checked too early!
    }
    
    print("\n--- 🚀 Starting Full Agentic Workflow ---")
    
    while True:
        try:
            # Run the graph
            print(f"\n[System] Invoking Graph...")
            next_state = app.invoke(current_state, {"recursion_limit": 20})
            
            # --- DEBUG: See what came back ---
            print(f"[DEBUG] Next State Keys: {list(next_state.keys())}")
            if "ai_response" in next_state:
                print(f"[DEBUG] AI Response Content: {str(next_state['ai_response'])[:50]}...")
            else:
                print("[DEBUG] AI Response is MISSING in next_state")
            # ---------------------------------

            # Update current state with the new values
            current_state.update(next_state)

            # --- CHECK 1: SUCCESS (Found Programs) ---
            if current_state.get("eligible_programs"):
                print("\n✅ Matching complete. Found eligible programs.")
                break 

            # --- CHECK 2: PAUSE FOR CHAT (Missing Info) ---
            ai_q = current_state.get("ai_response")
            
            # Check if ai_q is valid text
            if ai_q and isinstance(ai_q, str) and len(ai_q.strip()) > 0:
                print("\n" + "-" * 50)
                print(f"🤖 AI Assistant: {ai_q}")
                print("-" * 50)
                
                user_response = input("👤 You: ")
                
                # Update State & Restart Loop
                current_state["user_intent"] += f" \nUser: {user_response}"
                current_state["ai_response"] = None # Clear flag so it runs again
                continue 

            # --- CHECK 3: FAILURE ---
            profile = current_state.get("user_profile")
            missing = get_missing_fields(profile) if profile else ["Profile Missing"]

            if not missing:
                print("\n❌ Agent 3 ran, but no programs matched your hard filters.")
                break
            else:
                # If we are here, it means ai_q was None/Empty, but we are still missing info
                print(f"\n[DEBUG] Stuck loop details:")
                print(f"  - Missing Fields: {missing}")
                print(f"  - AI Response in State: {current_state.get('ai_response')}")
                break

        except Exception as e:
            print(f"\n[ERROR] Graph execution failed: {e}")
            break
    # --- Final Output ---
    print("\n" + "=" * 50)
    print("--- ✅ WORKFLOW COMPLETE! ---")
    print("=" * 50)
    
    final_ranked_list = current_state.get("ranked_programs")
    
    if final_ranked_list:
        print(f"\n🎯 Found {len(final_ranked_list)} Matching Programs!\n")
        
        for i, program in enumerate(final_ranked_list[:5]):
            print(f"{i+1}. {program.get('program_name', 'Unknown')} ({program.get('university_name')})")
            print(f"   📊 Match Score: {program.get('relevance_score', 0):.1f} / 10.0")
            
            # Show why (if Hard Filter logic added reasons, print them)
            # Otherwise, show the summary that matched
            print(f"   📝 Content: {program.get('course_content_summary')[:150]}...")
            print("-" * 30)
    else:
        print("❌ No eligible programs found. (Check Hard Filters or Data)")