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
    pdf_filename = "ToR.pdf"
    app = build_master_workflow()
 
    # --- Define Initial State ---
    initial_raw_input = (
        "Hi, I'm Anny from Vietnam. I have a Bachelor in Electronic Commerce. "
        "I want to study master of Digital Business "
        "My interests are Business Informatics, Innovation, Transformation, and Data Analytics."
    )
    
    current_state = {
        "user_intent": initial_raw_input, # <--- Updated to match Anny's intent
        "pdf_path": pdf_filename, 
        "user_profile": None,
        "program_catalog": [], 
        "eligible_programs": [], 
        "ranked_programs": [] 
    }
    
    print("\n--- 🚀 Starting Anny's Matching Workflow (4-Layer Funnel) ---")
    
    while True:
        try:
            # Run the graph
            print(f"\n[System] Invoking Graph...")
            next_state = app.invoke(current_state, {"recursion_limit": 20})
            
            # Update current state
            current_state.update(next_state)

            # --- CHECK 1: SUCCESS (Found Programs) ---
            # If Agent 3 returned programs, we are done!
            if current_state.get("eligible_programs"):
                print("\n" + "=" * 60)
                print("✅ MATCHING COMPLETE: Top Candidates for Anny")
                print("=" * 60)
                
                final_ranked_list = current_state.get("ranked_programs", [])
                
                if final_ranked_list:
                    print(f"🎯 Found {len(final_ranked_list)} Top Matches (Filtered from DB)\n")
                    print("\n Final Score = 20% Degree Compalibility + 40% student intent + 40% meet ECTs requirements")
                    
                    for i, program in enumerate(final_ranked_list[:20]): # Show top 20
                        print(f"{i+1}. {program.get('program_name')} ({program.get('university_name')})")
                        print(f"   📊 Final Score: {program.get('relevance_score')}")
                        
                        ects = program.get('ects_score', 0.0)  # Retrieves the saved 0.0-1.0 score
                        print(f"   🎓 ECTS Audit:  {ects * 100:.0f}% Coverage")
                        # Display the reasoning from the 4 Layers
                        print(f"   💡 Logic Trace:")
                        print(f"      {program.get('llm_reasoning', 'N/A')}")
                        print("-" * 50)
                else:
                    print("❌ Agent 3 found matches, but ranking failed.")
                
                break 

            # --- CHECK 2: PAUSE FOR CHAT (Missing Info) ---
            ai_q = current_state.get("ai_response")
            if ai_q:
                print("\n" + "-" * 50)
                print(f"🤖 AI Assistant: {ai_q}")
                print("-" * 50)
                user_response = input("👤 You: ")
                current_state["user_intent"] += f" \nUser: {user_response}"
                current_state["ai_response"] = None 
                continue 

            # --- CHECK 3: FAILURE (Layer 1 or 2 killed everything) ---
            print("\n No eligible programs found.")
            print("   Possible reasons:")
            print("   1. Layer 1: Your Degree (E-Commerce) did not match any Program Domains.")
            print("   2. Layer 2: Your GPA (2.11) or Fees did not pass the hard filters.")
            break

        except Exception as e:
            print(f"\n[ERROR] Graph execution failed: {e}")
            break
            
    print("\n✅ WORKFLOW COMPLETE")