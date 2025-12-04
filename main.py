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
    # Note: We intentionally leave some fields vague to test Agent 1's questions
    initial_raw_input = (
        "Hi, I'm Anny from Vietnam. Here is my transcript. "
        "I want to study Business Management"
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
                
                # Print full user profile for debugging
                print("\n" + "=" * 50)
                print("📋 FULL USER PROFILE (After Agent1)")
                print("=" * 50)
                profile = current_state.get("user_profile")
                if profile:
                    print(f"\n👤 Name: {profile.full_name}")
                    print(f"🌍 Citizenship: {profile.citizenship.country_of_citizenship if profile.citizenship else 'N/A'}")
                    
                    if profile.academic_background:
                        acad = profile.academic_background
                        print(f"\n🎓 Academic Background:")
                        print(f"   - Field of Study: {acad.bachelor_field_of_study}")
                        print(f"   - Duration: {acad.program_duration_semesters} semesters")
                        print(f"   - Total Credits: {acad.total_credits_earned}")
                        print(f"   - ECTS Conversion Factor: {acad.ects_conversion_factor}")
                        print(f"   - Total Converted ECTS: {acad.total_converted_ects}")
                        
                        if acad.bachelor_gpa:
                            gpa = acad.bachelor_gpa
                            print(f"   - GPA: {gpa.score}/{gpa.max_scale} (min: {gpa.min_passing_grade})")
                            print(f"   - German GPA: {gpa.score_german}")
                        
                        print(f"   - Fields of Interest: {acad.fields_of_interest}")
                        
                        if acad.transcript_courses:
                            print(f"\n   📄 Transcript Courses ({len(acad.transcript_courses)} courses):")
                            for i, course in enumerate(acad.transcript_courses[:5]):  # Show first 5
                                print(f"      {i+1}. {course.course_name} - {course.original_credits} credits (ECTS: {course.converted_ects})")
                            if len(acad.transcript_courses) > 5:
                                print(f"      ... and {len(acad.transcript_courses) - 5} more courses")
                        else:
                            print(f"\n   📄 Transcript Courses: ❌ None extracted from PDF")
                    
                    if profile.language_proficiency:
                        lang = profile.language_proficiency
                        print(f"\n🗣️ Language: {lang.exam_type} - Overall: {lang.overall_score}")
                    
                    if profile.preferences:
                        pref = profile.preferences
                        print(f"\n⚙️ Preferences:")
                        print(f"   - Max Tuition: {pref.max_tuition_fee_eur} EUR/semester")
                        print(f"   - Preferred Cities: {pref.preferred_cities if pref.preferred_cities else 'No preference'}")
                        print(f"   - Start Semester: {pref.preferred_start_semester}")
                else:
                    print("❌ No profile found!")
                print("=" * 50 + "\n")
                
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
        print(f"\n🎯 Found {len(final_ranked_list)} Matching Programs!\n Those program passes the Hard Filter, it gets a score based on 60% Qualifications (ECTS) and 40% Desire (Interests)")
        
        for i, program in enumerate(final_ranked_list):
            print(f"{i+1}. {program.get('program_name')} ({program.get('university_name')})")
            print(f"   📊 Final Score: {program.get('relevance_score', 0):.1f} / 10.0")
            
            # --- PRINT THE REASONING ---
            print(f"   💡 Analysis: {program.get('llm_reasoning', 'N/A')}")
            # ---------------------------        
            print("-" * 50)
    else:
        print("❌ No eligible programs found. (Check Hard Filters or Data)")