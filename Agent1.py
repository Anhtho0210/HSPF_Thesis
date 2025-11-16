import os
from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import json # Used for clean printing
from langgraph.graph import StateGraph, END
from typing import Any
import time
from dotenv import load_dotenv

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

class Citizenship(BaseModel):
    country_of_citizenship: Optional[str] = Field(description="The student's citizenship (e.g., 'Vietnam', 'India', 'Germany', or 'Non-EU').", default=None)

class BachelorGPA(BaseModel):
    score: Optional[float] = Field(description="The numeric GPA score on its original scale.", default=None)
    max_scale: Optional[float] = Field(description="The maximum possible scale (e.g., 4.0 or 5.0).", default=None)
    min_passing_grade: Optional[float] = Field(description="The minimum passing grade on the scale (e.g., 1.0).", default=None)
    score_german: Optional[float] = Field(description="The GPA score converted to German grading system (1.0-4.0).", default=None)

class AcademicBackground(BaseModel):
    bachelor_field_of_study: Optional[str] = Field(description="Field of study for the bachelor's degree (e.g., 'Computer Science').", default=None)
    bachelor_duration_years: Optional[int] = Field(description="Duration of the bachelor's degree in years (e.g., 4).", default=None)
    bachelor_gpa: Optional[BachelorGPA] = Field(default=None)
    total_credit_points: Optional[int] = Field(description="Total credit points earned in the bachelor's degree (e.g., 180).", default=None)
    fields_of_interest: Optional[List[str]] = Field(description="4-5 specific technical fields the student targets (e.g., 'AI', 'Machine Learning', 'Data Science').", default=None)

class LanguageProficiency(BaseModel):
    language: str = Field(description="The language name (e.g., 'English', 'German').")
    exam_type: Literal["TOEFL_iBT", "IELTS", "TestDaF", "CEFR", "Other"] = Field(description="Type of language exam.")
    overall_score: Optional[float] = Field(description="Overall score for IELTS/TOEFL (e.g., 6.0).", default=None)
    level: Optional[str] = Field(description="CEFR level for German (e.g., 'A2', 'B1', 'B2').", default=None)

class StandardizedTest(BaseModel):
    exam_type: str = Field(description="Type of standardized test (e.g., 'GRE', 'GMAT').")
    total_score: Optional[float] = Field(description="Total score for the standardized test (e.g., 320).", default=None)

class ProfessionalAndTests(BaseModel):
    relevant_work_experience_months: Optional[int] = Field(description="Relevant work experience in months (e.g., 6).", default=None)
    standardized_tests: Optional[List[StandardizedTest]] = Field(default=None)

class Preferences(BaseModel):
    preferred_cities: Optional[List[str]] = Field(description="List of preferred cities (e.g., ['Munich', 'Berlin', 'Aachen']).", default=None)
    max_tuition_fee_eur: Optional[int] = Field(default=0, description="Maximum EUR fee per semester (0 for tuition-free).")
    preferred_start_semester: Optional[str] = Field(description="Preferred start semester (e.g., 'Winter', 'Summer', 'Either').", default=None)
    preferred_language_of_instruction: Optional[str] = Field(description="e.g., 'English' or 'German/English'.", default='English')

class UserProfile(BaseModel):
    """The structured data model for the student applicant profile."""
    full_name: Optional[str] = Field(default=None)
    citizenship: Optional[Citizenship] = Field(default=None)
    academic_background: Optional[AcademicBackground] = Field(default=None)
    language_proficiency: Optional[List[LanguageProficiency]] = Field(default=[])
    professional_and_tests: Optional[ProfessionalAndTests] = Field(default=None)
    preferences: Optional[Preferences] = Field(default=None)

# --- 2. LANGGRAPH SHARED STATE (Memory) ---
class AgentState(TypedDict):
    user_intent: str      # ACCUMULATED raw text from the user (Full Profile)
    latest_response: str  # The user's newest, single reply
    ai_response: Optional[str] 
    user_profile: Optional[UserProfile]
    # ...
    # Status flags could be added here later

# --- 3. LLM SETUP ---
# Load environment variables from .env file
load_dotenv()
# --- LLM SETUP (from Agent1.py) ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    # Error will be caught during LLM initialization if not set
    print("[Warning] GEMINI_API_KEY not found in .env file or environment variables")

LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.1 
)

# --- 4. HELPER FUNCTION: CHECK MISSING FIELDS ---

def get_missing_fields(profile: Optional[UserProfile]) -> List[str]:
    """Analyzes the UserProfile for critical missing data points for matching.
    Returns fields in priority order: academic fields first, then others."""
    missing = []
    
    # If initial parsing failed completely or hasn't run
    if profile is None:
        return ["Initial full profile text (name, GPA, major, citizenship, interests)"]

    # PRIORITY 1: Academic fields (ask these first)
    academic_missing = []
    if not profile.academic_background:
        academic_missing.append("academic background (bachelor field of study, GPA, credit points)")
    if not profile.full_name: 
        missing.append("full name")
    
    if not profile.citizenship or not profile.citizenship.country_of_citizenship: 
        missing.append("country of citizenship")

    else:
        if not profile.academic_background.bachelor_field_of_study: 
            academic_missing.append("bachelor field of study")
        if not profile.academic_background.bachelor_duration_years:
            academic_missing.append("bachelor duration years")
        if not profile.academic_background.bachelor_gpa or not profile.academic_background.bachelor_gpa.score: 
            academic_missing.append("bachelor GPA score")
        if not profile.academic_background.bachelor_gpa or not profile.academic_background.bachelor_gpa.max_scale: 
            academic_missing.append("bachelor GPA max scale")
        if not profile.academic_background.bachelor_gpa or not profile.academic_background.bachelor_gpa.min_passing_grade: 
            academic_missing.append("bachelor GPA min passing grade")
        if not profile.academic_background.total_credit_points: 
            academic_missing.append("total credit points")
        if not profile.academic_background.fields_of_interest or (isinstance(profile.academic_background.fields_of_interest, list) and len(profile.academic_background.fields_of_interest) == 0): 
            academic_missing.append("2-3 technical fields of interest")
    
    # Add academic fields first (priority order)
    missing.extend(academic_missing)
    
    # PRIORITY 2: Language proof check is critical for filtering
    if not profile.language_proficiency or len(profile.language_proficiency) == 0:
        missing.append("language proficiency (e.g., IELTS, TOEFL)")
    else:
        # Check if at least one language proof has a valid score
        has_valid_score = any(
            lang.overall_score is not None or lang.level is not None 
            for lang in profile.language_proficiency
        )
        if not has_valid_score:
            missing.append("language proof score or level (e.g., IELTS score, CEFR level)")
        
    return missing

# CHECK other fields for desirability but not criticality
def get_desirable_missing_fields(profile: Optional[UserProfile], user_intent: str = "") -> List[str]:
    """Analyzes the UserProfile for helpful, but non-critical, data points."""
    desirable_missing = []
    
    # Only check if profile is not None and has been partially successful
    if profile is None:
        return []

    user_intent_lower = user_intent.lower()
    
    # Check for "no" responses for cities - don't ask again if user explicitly declined
    cities_declined = any(phrase in user_intent_lower for phrase in [
        "no prefer", "no preference", "not important", "i don't care", "doesn't matter",
        "no cities", "no city preference", "any city", "no specific city"
    ])
    
    # Check for non-critical, yet highly useful fields in preferences
    if not profile.preferences:
        # If preferences don't exist, we might want to ask about them (but skip cities if declined)
        if not cities_declined:
            desirable_missing.append("preferences (tuition fee, preferred cities, language of instruction)")
        else:
            desirable_missing.append("preferences (tuition fee, language of instruction)")
    else:
        # Only consider tuition fee missing if user hasn't explicitly mentioned it
        tuition_mentioned = any(phrase in user_intent_lower for phrase in [
            "tuition", "fee", "cost", "price", "free", "no tuition", "tuition-free"
        ])
        if not tuition_mentioned and (not profile.preferences.max_tuition_fee_eur or profile.preferences.max_tuition_fee_eur == 0): 
            desirable_missing.append("maximum tuition fee (EUR per semester)")
        
        if not profile.preferences.preferred_language_of_instruction: 
            desirable_missing.append("preferred language of instruction")
        
        # Only ask about cities if they haven't been explicitly declined
        # Empty list [] means user was asked and said no, None means not asked yet
        if not cities_declined:
            if profile.preferences.preferred_cities is None: 
                desirable_missing.append("preferred cities")
            elif isinstance(profile.preferences.preferred_cities, list) and len(profile.preferences.preferred_cities) == 0:
                # Empty list - this is actually fine, user said no preference, don't ask again
                pass
    
    # Check for professional_and_tests (optional but desirable)
    if not profile.professional_and_tests:
        # Check if user mentioned anything about work experience or standardized tests
        work_mentioned = any(phrase in user_intent_lower for phrase in [
            "work", "experience", "job", "employment", "internship", "intern"
        ])
        test_mentioned = any(phrase in user_intent_lower for phrase in [
            "gre", "gmat", "standardized test", "test score"
        ])
        if not work_mentioned and not test_mentioned:
            desirable_missing.append("professional information (work experience, standardized tests like GRE/GMAT)")
    else:
        # If professional_and_tests exists, check if it has meaningful data
        if not profile.professional_and_tests.relevant_work_experience_months and (
            not profile.professional_and_tests.standardized_tests or 
            len(profile.professional_and_tests.standardized_tests) == 0
        ):
            # Professional_and_tests exists but is empty - might want to ask
            pass
            
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
             
             CRITICAL RULES - ABSOLUTELY NO ASSUMPTIONS:
             - Do NOT invent or assume data that is not explicitly mentioned by the user.
             - Do NOT infer or guess fields like 'bachelor_field_of_study' or 'fields_of_interest' from vague statements.
             - If a field is not mentioned in the user's text, ask user again to get the answer.

             MANDATORY RULES FOR ACADEMIC FIELDS:
             - For 'academic_background.bachelor_field_of_study': 
               - This is where you put the BACHELOR DEGREE FIELD the user studied (e.g., "Computer Science", "Engineering", "Business", "Mathematics").
               - Do NOT assume from terms like "degree", "CompSci", "CS degree", "tech degree", or "I have a degree", "degree in tech" or "studied programming", you should ask for confirm.
             
             - For 'academic_background.fields_of_interest': 
               - This is for RESEARCH/TECHNICAL INTERESTS/DESIRED MASTER PROGRAMS for Master's studies (e.g., "AI", "Machine Learning", "Data Science").
               - ONLY extract specific technical/research fields that are EXPLICITLY mentioned (e.g., "AI", "Machine Learning", "Cybersecurity").
               - If the user only says "interested in tech" or "technology" without specific field names, ask again for confirm.
               - You should ask for 4-5 specific field of interests.

             - For 'academic_background.bachelor_gpa': Only extract if the user provides actual GPA numbers. Set score, max_scale, and min_passing_grade to null if not provided.
             
             - For 'language_proficiency': Use 'exam_type' instead of 'exam'. For IELTS/TOEFL, use 'overall_score'. For CEFR (German), use 'level'.
             - The 'professional_and_tests' and 'preferences' sections are optional.
             
             Crucial Context: The user's latest response might be a short answer to a specific question. You must map that short answer to the CORRECT field based on what was asked.
             - If asked about bachelor's degree field and user answers with a discipline name (e.g., "Computer Science"), put it in 'bachelor_field_of_study'.
             - If asked about interests and user answers with technical fields (e.g., "AI", "Machine Learning"), put them in 'fields_of_interest'.
             - If the user provides a city name (e.g., 'Munich'), populate 'preferences.preferred_cities' as a list.
             - If the user provides a number in EUR, it is likely 'preferences.max_tuition_fee_eur'.
             - IMPORTANT: If the user explicitly states they have no preference for cities, set 'preferences.preferred_cities' to an empty list [].
             
             REMEMBER: When in doubt, you should confirm with the user. Do NOT invent data. Only output the JSON.
             
             
             Output Format Instructions: \n{{format_instructions}}"""
            ),
            ("user", "User's current accumulated profile text: \n---\n{input}\n---")
        ]
    )
    
    parsing_chain: Runnable = prompt | LLM | parser
    
    try:
        # Pass variables using the required keys: 'input' and 'format_instructions'
                # Pass variables using the required keys: 'input' and 'format_instructions'
        structured_output_dict = parsing_chain.invoke({
            "input": state["user_intent"], 
            "format_instructions": format_instructions
        })
        
        # Handle "no" responses for preferred_cities - set to empty list if user declined
        user_intent_lower = state["user_intent"].lower()
        cities_declined = any(phrase in user_intent_lower for phrase in [
            "no prefer", "no preference", "not important", "i don't care", "doesn't matter",
            "no cities", "no city preference", "any city", "no specific city"
        ])
        if cities_declined:
            # Create preferences object if it doesn't exist
            if "preferences" not in structured_output_dict or structured_output_dict["preferences"] is None:
                structured_output_dict["preferences"] = {}
            # Set preferred_cities to empty list to indicate user declined
            structured_output_dict["preferences"]["preferred_cities"] = []
        
        # Calculate German GPA score if all required GPA fields are present
        if ("academic_background" in structured_output_dict and 
            structured_output_dict["academic_background"] and 
            "bachelor_gpa" in structured_output_dict["academic_background"] and
            structured_output_dict["academic_background"]["bachelor_gpa"]):
            
            gpa = structured_output_dict["academic_background"]["bachelor_gpa"]
            score = gpa.get("score")
            max_scale = gpa.get("max_scale")
            min_passing_grade = gpa.get("min_passing_grade")
            
            # Calculate German grade using formula: N_de = 1 + 3 × (N_max - N_d) / (N_max - N_min)
            if (score is not None and max_scale is not None and min_passing_grade is not None):
                try:
                    denominator = max_scale - min_passing_grade
                    if denominator != 0:  # Avoid division by zero
                        score_german = 1 + 3 * (max_scale - score) / denominator
                        # Round to 2 decimal places
                        score_german = round(score_german, 2)
                        structured_output_dict["academic_background"]["bachelor_gpa"]["score_german"] = score_german
                        print(f"[Post-processing] Calculated German GPA: {score_german} (from score={score}, max={max_scale}, min={min_passing_grade})")
                    else:
                        print(f"[Post-processing] Warning: Cannot calculate German GPA - division by zero (max_scale={max_scale}, min_passing_grade={min_passing_grade})")
                except Exception as e:
                    print(f"[Post-processing] Error calculating German GPA: {e}")
        
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
    user_intent = state.get("user_intent", "")
    missing_desirable = get_desirable_missing_fields(profile, user_intent)
    
    if not missing_desirable:
        # No more desirable fields to ask about
        return {"ai_response": None}
    
    # Combine all missing fields into one comprehensive question
    missing_fields_text = ", ".join(missing_desirable[:-1]) + (f" and {missing_desirable[-1]}" if len(missing_desirable) > 1 else missing_desirable[0])
        
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", 
             "You are a friendly university application assistant. All mandatory profile fields are complete. Your task is to ask ONE friendly, comprehensive question that combines ALL remaining preferences in a natural way. Ask about all missing fields at once. If the user says 'no' or 'skip' to any specific preference, that's fine - just note it and move on. Only stop asking if the user explicitly says they're done or have no more preferences."
            ),
            ("user", f"Current profile context: '{user_intent[:200]}...'. The remaining optional preferences to ask about are: {missing_fields_text}. Generate ONE natural, friendly question that asks about all of these at once. Make it conversational and easy to answer.")
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
    user_intent = state.get("user_intent", "")
    missing_mandatory_data = get_missing_fields(profile)
    missing_desirable_data = get_desirable_missing_fields(profile, user_intent) # Pass user_intent
    
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
    initial_raw_input = "I want to apply to Master's in Germany"
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
        
        # 1. Check for Completion (will break if everything is filled OR user said no)
        profile = current_state.get("user_profile")
        user_intent = current_state.get("user_intent", "")
        
        # Check if user said "no" to stop asking questions (more specific check)
        latest_response_lower = current_state.get("latest_response", "").lower()
        # Only consider it a "no" if they're declining ALL remaining questions, not just one field
        user_said_no = any(phrase in latest_response_lower for phrase in [
            "no more", "that's all", "nothing else", "i'm done", "no preferences", 
            "no other", "skip the rest", "no thanks", "that's it"
        ])
        
        # Break if mandatory fields complete AND (desirable fields complete OR user declined all)
        if profile and not get_missing_fields(profile):
            missing_desirable = get_desirable_missing_fields(profile, user_intent)
            if not missing_desirable or user_said_no:
                break
        
        # 2. Run the graph from the current state (Parsing -> Check -> Chat/Wrap-up)
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