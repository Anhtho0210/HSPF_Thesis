import os
from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import json # Used for clean printing
from langgraph.graph import StateGraph, END
from typing import Any
import time

# WORKFLOW
# parsing →(check_for_completion) → "chat" (if mandatory missing)
# parsing →check_for_completion) →"wrap_up" (if mandatory complete, but desirable missing)
# parsing →(check_for_completion)→"matching" (if everything is complete)
# wrap_up_chat_node →END (to pause for user input)

# --- Gemini/LangChain Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable

# --- 1. PYDANTIC SCHEMAS ---

class AcademicData(BaseModel):
    bachelor_degree_name: str = Field(description="Full name of the previous degree (e.g., 'B.Sc. in Computer Science').",default=None)
    bachelor_gpa_score: Optional[float] = Field(description="The numeric GPA score on its original scale.", default=None)
    bachelor_gpa_scale: Optional[float] = Field(description="The maximum possible scale (e.g., 4.0 or 5.0).", default=None)
    country_of_citizenship: Optional[str] = Field(description="The student's citizenship (e.g., 'India', 'Germany', or 'Non-EU').", default=None)

class LanguageProficiency(BaseModel):
    language: str
    exam: Literal["TOEFL_iBT", "IELTS", "TestDaF", "Other"]
    score: float

class UserProfile(BaseModel):
    """The structured data model for the student applicant profile."""
    full_name: Optional[str] = Field(default=None)
    academic_data: AcademicData
    field_of_interest: List[str] = Field(description="2-3 specific technical fields the student targets (e.g., 'Agentic AI', 'Data Science').", default=None)
    language_proofs: List[LanguageProficiency] = Field(default=[])
    preferred_language_of_instruction: Optional[str] = Field(description="e.g., 'English' or 'German/English'.", default='English')
    max_tuition_fee_eur: Optional[int] = Field(default=0, description="Maximum EUR fee per semester (0 for tuition-free).")
    # --- NEW FIELD ---
    preferred_city: Optional[str] = Field(default=None, description="The preferred German city for the university (e.g., 'Berlin', 'Munich').")
    max_tuition_fee_eur: Optional[int] = Field(default=0, description="Maximum EUR fee per semester (0 for tuition-free).")

# --- 2. LANGGRAPH SHARED STATE (Memory) ---
class AgentState(TypedDict):
    user_intent: str      # ACCUMULATED raw text from the user (Full Profile)
    latest_response: str  # The user's newest, single reply
    ai_response: Optional[str] 
    user_profile: Optional[UserProfile]
    # ...
    # Status flags could be added here later

# --- 3. LLM SETUP ---
# export GEMINI_API_KEY='AIzaSyCbhuCLgaEoF3e5yIz9dxRRWbMxRq_gmVo'
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key 
else:
    # Error will be caught during LLM initialization if not set
    pass 

LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.1 
)

# --- 4. HELPER FUNCTION: CHECK MISSING FIELDS ---

def get_missing_fields(profile: Optional[UserProfile]) -> List[str]:
    """Analyzes the UserProfile for critical missing data points for matching."""
    missing = []
    
    # If initial parsing failed completely or hasn't run
    if profile is None:
        return ["Initial full profile text (name, GPA, major, citizenship, interests)"]

    # Check key mandatory fields required for Tool 3 (Matching)
    if not profile.full_name: missing.append("full name")
    if not profile.academic_data.bachelor_degree_name: missing.append("bachelor degree name")
    if not profile.academic_data.bachelor_gpa_score: missing.append("bachelor GPA score")
    if not profile.academic_data.country_of_citizenship: missing.append("country of citizenship")
    if not profile.field_of_interest: missing.append("2-3 technical fields of interest")
    # Language proof check is critical for filtering
    if not profile.language_proofs or profile.language_proofs[0].score is None: 
        missing.append("language proof score (e.g., IELTS, TOEFL)")
        
    return missing

# CHECK other fields for desirability but not criticality
def get_desirable_missing_fields(profile: Optional[UserProfile]) -> List[str]:
    """Analyzes the UserProfile for helpful, but non-critical, data points."""
    desirable_missing = []
    
    # Only check if profile is not None and has been partially successful
    if profile is None:
        return []

    # Check for non-critical, yet highly useful fields
    if not profile.max_tuition_fee_eur or profile.max_tuition_fee_eur == 0: 
        desirable_missing.append("maximum tuition fee (EUR per semester)")
    
    if not profile.preferred_language_of_instruction: 
        desirable_missing.append("preferred language of instruction")
        
    if not profile.preferred_city: 
            desirable_missing.append("preferred city")

    if not profile.field_of_interest:
        desirable_missing.append("field_of_interest")
            
    return desirable_missing
# --- 5. LANGGRAPH NODES ---

# Node 1: Parsing & Intake (Tool 1)
def parse_profile_node(state: AgentState) -> Dict[str, Any]:
    """Attempts to parse the accumulated user_intent into a structured UserProfile."""
    print("\n[Node: Parsing/Tool 1] Attempting structured extraction...")
    
    parser = JsonOutputParser(pydantic_object=UserProfile)
    format_instructions = parser.get_format_instructions()
    
    # --- MODIFIED SYSTEM PROMPT ---
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", 
             f"""You are a meticulous data extraction agent. 
             STRICTLY extract ALL details from the user's FULL accumulated text and adhere to the JSON schema.
             
             Crucial Context: The user's latest response might be a short answer. You must map that short answer to the most likely missing field.
             - If the user provides a city name (e.g., 'Munich'), populate the 'preferred_city' field.
             - If the user provides a number in EUR, it is likely 'max_tuition_fee_eur'.
             
             If the user explicitly states they have no preference or the data is not applicable (e.g., 'No', 'I don't care'), you MUST set that field to 'null' or its default value (like 0 for max_tuition_fee_eur).
             Do NOT invent data. Only output the JSON.
             
             Output Format Instructions: \n{{format_instructions}}"""
            ),
            ("user", "User's current accumulated profile text: \n---\n{input}\n---")
        ]
    )
    
    parsing_chain: Runnable = prompt | LLM | parser
    
    try:
        # Pass variables using the required keys: 'input' and 'format_instructions'
        structured_output_dict = parsing_chain.invoke({
            "input": state["user_intent"], 
            "format_instructions": format_instructions
        })
        
        validated_profile = UserProfile(**structured_output_dict)
        print(f"[Node: Parsing/Tool 1] ✅ Profile parsed. Missing fields: {len(get_missing_fields(validated_profile))}")
        
        # --- ADDED FOR TESTING/DEBUGGING ---
        print("\n--- Parsed Profile (Debug) ---")
        # Use .model_dump_json(indent=2) for clean, readable JSON output
        print(validated_profile.model_dump_json(indent=2))
        print("-----------------------------\n")
        # ------------------------------------

        return {"user_profile": validated_profile}
        
    except Exception as e:
        print(f"[Node: Parsing/Tool 1] ❌ Failed to parse: {e}")
        # Return state unchanged for user_profile, forcing re-run or chat
        return {"user_profile": None}


# Node 2: Conversational Chat (Asks follow-up questions)
def conversational_chat_node(state: AgentState) -> Dict[str, Any]:
    """Generates a follow-up question based on missing profile fields."""
    print("[Node: Chat] Generating follow-up question...")
    
    profile = state.get("user_profile")
    current_intent = state["user_intent"]
    missing_data = get_missing_fields(profile)
    
    # 1. Define the Prompt Template
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", 
             "You are a friendly university application assistant. Your task is to generate ONE concise, friendly question to gather the most important missing data. Do NOT repeat the data the user has already provided."
            ),
            ("user", f"Current ACCUMULATED Profile Text: '{current_intent}'. The critical missing data is: {', '.join(missing_data)}. Ask a question to gather this information.")
        ]
    )
    
    # 2. Format the prompt and invoke the LLM
    messages = prompt.invoke({}).to_messages()
    response = LLM.invoke(messages).content 

    print(f"[Node: Chat] AI Question: {response}")
    return {"ai_response": response}

# Node 3: Wrap-Up Chat (Asks for non-mandatory fields)
def wrap_up_chat_node(state: AgentState) -> Dict[str, Any]:
    """Generates a wrap-up question for non-mandatory, desirable fields."""
    print("[Node: Wrap-Up Chat] Generating final questions...")
    
    profile = state.get("user_profile")
    missing_desirable = get_desirable_missing_fields(profile)
    
    question_list = " or ".join(missing_desirable)

    # Note: We encourage the user to provide all non-mandatory fields, 
    # even if they were 'missing' because of a negative previous answer, 
    # to ensure the prompt is comprehensive.
        
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", 
             "You are a friendly university application assistant. All mandatory profile fields are complete. Your task is to ask ONE friendly, encouraging question to gather any remaining preferences that help with matching, such as preferred city, max tuition fee, or instructional language."
            ),
            ("user", f"I see you've completed your core profile! To help me find the best matches, could you let me know about any preferences for your maximum tuition fee (in EUR per semester, use '0' for tuition-free), preferred city, or instructional language (e.g., English)?")
        ]
    )
    messages = prompt.invoke({}).to_messages()
    response = LLM.invoke(messages).content 

    print(f"[Node: Wrap-Up Chat] AI Question: {response}")
    return {"ai_response": response}

# --- 6. CONDITIONAL EDGE (UPDATED) ---

def check_for_completion(state: AgentState) -> Literal["chat", "wrap_up", "matching"]:
    """Conditional edge logic: determines if we need more info or can proceed to matching."""
    
    profile = state.get("user_profile")
    missing_mandatory_data = get_missing_fields(profile)
    missing_desirable_data = get_desirable_missing_fields(profile) # NEW CHECK
    
    if missing_mandatory_data:
        # Mandatory data is still missing (e.g., GPA, citizenship)
        print(f"[Decision] 🗣️ Profile INCOMPLETE (Missing Mandatory: {', '.join(missing_mandatory_data[:2])}). Going to Chat.")
        return "chat"
    
    elif missing_desirable_data:
        # Mandatory data is complete, but we need useful optional data (e.g., tuition fee)
        print(f"[Decision] 🗣️ Profile COMPLETE (Mandatory), but missing desirable: {', '.join(missing_desirable_data[:2])}. Going to Wrap-Up.")
        return "wrap_up"

    else:
        # Everything is complete
        print("[Decision] ✅ Profile COMPLETELY FILLED. Moving to Tool 3 (Matching).")
        return "matching"

# --- 7. BUILD THE LANGGRAPH WORKFLOW (FIXED) ---

# --- 7. BUILD THE LANGGRAPH WORKFLOW (FIXED and EXTENDED) ---

def build_intake_workflow() -> Any:
    workflow = StateGraph(AgentState)
    workflow.add_node("parsing", parse_profile_node)
    workflow.add_node("chat", conversational_chat_node)
    workflow.add_node("wrap_up", wrap_up_chat_node) # NEW NODE

    workflow.set_entry_point("parsing")

    # The conditional edge now has three possible outputs
    workflow.add_conditional_edges(
        "parsing",
        check_for_completion,
        {
            "chat": "chat",       # Mandatory data missing -> go to chat node
            "wrap_up": "wrap_up", # Mandatory complete, desirable missing -> go to wrap-up node
            "matching": END       # Everything complete -> finish
        }
    )

    # After the mandatory chat question, we stop to wait for user input
    workflow.add_edge("chat", END) 
    
    # After the wrap-up question, we stop to wait for user input
    workflow.add_edge("wrap_up", END) # NEW EDGE

    return workflow.compile()

# --- 8. REVISED EXECUTION EXAMPLE FOR INTERACTIVE CHAT ---

if __name__ == "__main__":
    
    # 1. Define Initial State
    initial_raw_input = "I want to apply to Master's in Germany, interested in AI. I have a degree in CompSci."
    current_state: AgentState = {
        "user_intent": initial_raw_input,
        "latest_response": initial_raw_input,
        "ai_response": None,
        "user_profile": None,
    }
    
    # Compile the graph
    app = build_intake_workflow()

    print("\n--- 🚀 Starting Interactive Profile Intake ---")
    
    # --- Main Loop ---
    while True:
        
        # 1. Check for Completion (will break if everything is filled)
        profile = current_state.get("user_profile")
        if profile and not get_missing_fields(profile):
            break
        
        # 2. Run the graph from the current state (Parsing -> Check -> Chat)
        try:
            next_state = app.invoke(current_state)
            current_state.update(next_state)
        except Exception as e:
            print(f"\n[ERROR] Graph execution failed: {e}. Exiting loop.")
            break

        # 3. Check for AI Question (Pause point)
        ai_q = current_state.get("ai_response")

        if ai_q:
            # A. Display Question
            print("-" * 50)
            print(f"AI Assistant: {ai_q}")
            
            # B. Get User Input <--- YOU CAN NOW INPUT HERE
            user_response = input("You: ")
            print("-" * 50)
            
            # C. CRITICAL UPDATE: Update the state with the NEW input
            current_state["user_intent"] += " " + user_response
            current_state["latest_response"] = user_response
            current_state["ai_response"] = None # Reset AI response for the next iteration
            
        else:
            # Should only happen on startup or if parser fails repeatedly
            print("[System Notice] No new question generated. Retrying with current intent...")
            time.sleep(1) 

    # --- Final Output (Section 2) ---
    print("\n" + "=" * 50)
    print("--- ✅ PROFILE INTAKE COMPLETE! ---")
    print("=" * 50)
    
    # Retrieve the final, complete profile from the state
    final_profile = current_state.get("user_profile")
    
    if final_profile:
        print("\n--- Final Structured User Profile ---")
        print(final_profile.model_dump_json(indent=2))
        print("-------------------------------------")
    else:
        print("ERROR: Graph completed, but final profile object was not found in the state.")