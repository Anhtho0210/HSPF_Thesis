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

# --- Import nodes from Agent 4 ---
from Agent4 import agent_4_checklist_node
from Agent5 import agent_5_planner_node
from Agent6 import agent_6_report_node

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
    
    # Add Agent 4 Node
    workflow.add_node("agent_4_checklist", agent_4_checklist_node)
    workflow.add_node("agent_5_planner", agent_5_planner_node)
    workflow.add_node("agent_6_report", agent_6_report_node)

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
    
    # Connect Agent 3 to END (to allow display of top 20 programs)
    workflow.add_edge("agent_3_filter", END)
    
    # Connect Agent 4 -> Agent 5 -> Agent 6 -> END
    workflow.add_edge("agent_4_checklist", "agent_5_planner")
    workflow.add_edge("agent_5_planner", "agent_6_report")
    workflow.add_edge("agent_6_report", END)

    return workflow.compile()


# --- 2. EXECUTION ---
if __name__ == "__main__":
    
    # 1. Prepare Data
    pdf_filename = "PROFILE_005_PK_MKT_Transcript.pdf"
    app = build_master_workflow()
 
    # --- Define Initial State ---
    initial_raw_input = (
            "Hello, I'm Ayesha Khan from Pakistan. I have a Bachelor's degree in Marketing from Lahore University of Management Sciences (LUMS). My CGPA is 3.2 out of 4.0 (minimum passing is 2.0). I studied for 8 semesters and earned 128 credits. I'm interested in Digital Marketing, Brand Management, Consumer Behavior, Social Media Marketing, and Marketing Analytics. I want to study a Master's in Marketing or Digital Marketing. I have IELTS 6.5 (overall) with Reading 7.0, Listening 6.5, Speaking 6.0, Writing 6.5. I don't speak German yet. My maximum tuition budget is 4000 EUR per semester. I prefer to study in Baden-Württemberg state. I don't have prefered semester. I have 24 months of work experience as a Marketing Executive at a digital agency."
    )
     
    current_state = {
        "user_intent": initial_raw_input, # <--- Updated to match Anny's intent
        "pdf_path": pdf_filename, 
        "user_profile": None,
        "program_catalog": [], 
        "eligible_programs": [], 
        "ranked_programs": [],
        "selected_programs_with_checklists": []  # Agent 4 output
    }
    
    print("\n--- 🚀 Starting Anny's Matching Workflow (4-Layer Funnel) ---")
    
    while True:
        try:
            # Run the graph
            print(f"\n[System] Invoking Graph...")
            next_state = app.invoke(current_state, {"recursion_limit": 20})
            
            # Update current state
            current_state.update(next_state)

            # --- CHECK 1: Agent 6 completed (PDF generated) ---
            if current_state.get("reports_generated"):
                # Agent 6 has completed - workflow is done
                print("\n" + "=" * 60)
                print("✅ WORKFLOW COMPLETE - PDF REPORT GENERATED")
                print("=" * 60)
                break

            # --- CHECK 2: Agent 3 completed (ranked programs available) ---
            if current_state.get("ranked_programs") and not current_state.get("_agent3_displayed"):
                print("\n" + "=" * 60)
                print("✅ AGENT 3 COMPLETE: Top Candidates")
                print("=" * 60)
                
                final_ranked_list = current_state.get("ranked_programs", [])
                
                if final_ranked_list:
                    print(f"🎯 Found {len(final_ranked_list)} Top Matches (Filtered from DB)\n")
                    print("Final Score = 50% Student Intent + 40% ECTS Requirements + 10% Degree Compatibility\n")
                    
                    for i, program in enumerate(final_ranked_list[:10]): # Show top 10
                        print(f"{i+1}. {program.get('program_name')} ({program.get('university_name')})")
                        print(f"   📊 Final Score: {program.get('relevance_score')}")
                        print(f"   🎓 ECTS Coverage: {program.get('ects_score', 0.0) * 100:.0f}%")
                        print(f"   🏛️  City: {program.get('city', 'N/A')}, State: {program.get('state', 'N/A')}")
                        print(f"   💰 Tuition: €{program.get('tuition_fee_per_semester_eur', 0)}/semester")
                        print(f"   💡 Reasoning: {program.get('llm_reasoning', 'N/A')}")
                        print("-" * 50)
                    
                    # Mark that we've displayed Agent 3 results
                    current_state["_agent3_displayed"] = True
                    
                    # Pause to let user review the programs
                    print("\n" + "=" * 60)
                    print("Review the programs above, then press ENTER to continue to Agent 4...")
                    print("=" * 60)
                    input()
                    
                    # Manually invoke Agent 4
                    print("\n" + "=" * 60)
                    print("Proceeding to Agent 4: Document Checklist Generator...")
                    print("=" * 60)
                    
                    # Import and call Agent 4 directly
                    from Agent4 import agent_4_checklist_node
                    from Agent5 import agent_5_planner_node
                    from Agent6 import agent_6_report_node
                    
                    agent4_result = agent_4_checklist_node(current_state)
                    current_state.update(agent4_result)
                    
                    # Now invoke Agent 5
                    print("\n" + "=" * 60)
                    print("Proceeding to Agent 5: Application Timeline Planner...")
                    print("=" * 60)
                    
                    agent5_result = agent_5_planner_node(current_state)
                    current_state.update(agent5_result)
                    
                    # Now invoke Agent 6
                    print("\n" + "=" * 60)
                    print("Proceeding to Agent 6: PDF Report Generator...")
                    print("=" * 60)
                    
                    agent6_result = agent_6_report_node(current_state)
                    current_state.update(agent6_result)
                    
                    # Display Agent 5 output and Agent 6 completion
                    if current_state.get("final_application_plans"):
                        print("\n" + "=" * 60)
                        print("🎉 TIMELINE GENERATED - Creating PDF Report...")
                        print("=" * 60)
                        
                        plans = current_state.get("final_application_plans")
                        
                        for plan in plans:
                            print(f"\n📘 PROGRAM: {plan['program_name']}")
                            print(f"   🏛️  {plan['university']}")
                            print("-" * 40)
                            
                            for event in plan['timeline']:
                                # Pretty print date
                                d_str = event['date'].strftime("%Y-%m-%d")
                                
                                # Add icons based on urgency
                                icon = "⚪"
                                if event['type'] == "overdue": icon = "🔥"
                                elif event['type'] == "critical": icon = "🚨"
                                elif event['type'] == "deadline": icon = "🏁"
                                elif event['type'] == "fatal": icon = "❌"
                                elif event['type'] == "action": icon = "📤"
                                elif event['type'] == "task": icon = "📝"
                                
                                print(f"   {icon} [{d_str}] {event['event']}")
                            
                            print("-" * 40)
                    
                    # Check if Agent 6 completed
                    if current_state.get("reports_generated"):
                        print("\n" + "=" * 60)
                        print("✅ PDF REPORT SUCCESSFULLY GENERATED!")
                        print("=" * 60)
                        print("📄 File: My_Application_Strategy.pdf")
                        print("📦 Contains: User profile, program details, timeline, and checklists")
                    
                    # Exit the workflow - Agent 6 is the final step
                    break
                else:
                    print("❌ Agent 3 found matches, but ranking failed.")
                    break

            # --- CHECK 3: PAUSE FOR CHAT (Missing Info) ---
            ai_q = current_state.get("ai_response")
            if ai_q:
                print("\n" + "-" * 50)
                print(f"🤖 AI Assistant: {ai_q}")
                print("-" * 50)
                user_response = input("👤 You: ")
                current_state["user_intent"] += f" \nUser: {user_response}"
                current_state["ai_response"] = None 
                continue

            # --- SAFETY CHECK: Prevent infinite loop if Agent3 returned empty results ---
            # If ranked_programs exists in state (even if empty), Agent3 has run
            if "ranked_programs" in current_state:
                # Agent3 has run and returned results
                if not current_state.get("ranked_programs"):
                    # Empty list - no programs found
                    print("\n" + "=" * 60)
                    print("❌ WORKFLOW COMPLETE - No matching programs found")
                    print("=" * 60)
                    print("Agent 3 checked all programs but found no matches.")
                    print("Try widening your criteria (tuition, location, interests).")
                    break
                elif current_state.get("_agent3_displayed"):
                    # Programs were displayed and processed
                    print("\n[System] Agent processing complete - exiting")
                    break


        except Exception as e:
            print(f"\n[ERROR] Graph execution failed: {e}")
            break
            
    print("\n✅ WORKFLOW COMPLETE")