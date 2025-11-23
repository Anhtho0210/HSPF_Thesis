import os
from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import json # Used for clean printing
from langgraph.graph import StateGraph, END
from typing import Any
import time
from dotenv import load_dotenv
from models import AgentState, UserProfile
#handling PDF
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS 
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader  
import math

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

load_dotenv()
# --- LLM SETUP 
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    print("[Warning] GEMINI_API_KEY not found in .env file or environment variables")

LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.1 
)

#handling PDF
def agent_1_ingest_syllabus(pdf_path):
    # 1. Split PDF into chunks (e.g., 1 page per chunk)
    loader = PyPDFLoader(pdf_path)
    pages = loader.load_and_split()
    
    # 2. Create Vector Index (Temporary, just for this session)
    vectorstore = FAISS.from_documents(pages, OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()
    
    return retriever

def agent_3_check_syllabus(retriever, requirement_name):
    # Instead of asking the user, ask the PDF!
    
    # Query: "Find courses about [Requirement Name]"
    docs = retriever.get_relevant_documents(f"Course description regarding {requirement_name}")
    
    # Feed these specific snippets to LLM to judge
    context_text = "\n".join([d.page_content for d in docs])
    
    prompt = f"""
    Based on the syllabus excerpts below, does the student have courses that cover '{requirement_name}'?
    Sum up the credits.
    
    Excerpts:
    {context_text}
    """

def load_pdf_text(file_path: str) -> str:
    """Reads text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text[:15000] # Limit to 15k chars to save tokens
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

#handling ECTs
def apply_ects_conversion(profile: UserProfile) -> UserProfile:
    """
    Calculates ECTS Conversion Factor based on:
    Factor = 30 / (Total_Credits / Semesters)
    Then applies this factor to:
    1. The Total Degree Credits
    2. Every individual course in the transcript
    """
    acad = profile.academic_background
    
    # 1. Validate Inputs
    # We check for 'total_credits_earned' because that is what your JSON output shows
    if not acad or not acad.total_credits_earned or not acad.program_duration_semesters:
        print("  [Logic] Cannot calculate ECTS Factor: Missing Total Credits or Duration.")
        return profile

    conversion_factor = 1.0

    # 2. Calculate Factor
    try:
        credits_per_semester = acad.total_credits_earned / acad.program_duration_semesters
        
        if credits_per_semester > 0:
            conversion_factor = 30.0 / credits_per_semester
            
            # Sanity Check: If factor is essentially 1.0, keep it 1.0
            if 0.9 <= conversion_factor <= 1.1:
                conversion_factor = 1.0
            
            acad.ects_conversion_factor = round(conversion_factor, 2)
            print(f"  [Logic] 🧮 Calculated Factor: {acad.ects_conversion_factor}")
            
    except Exception as e:
        print(f"  [Logic] ❌ Error calculating factor: {e}")
        return profile # Stop if we can't get a factor

    # 3. Apply to Total Degree (Safe Block)
    try:
        if acad.total_credits_earned:
            acad.total_converted_ects = round(acad.total_credits_earned * conversion_factor, 1)
            print(f"  [Logic] 🎓 Total Degree Converted: {acad.total_converted_ects} ECTS")
    except Exception as e:
        print(f"  [Logic] Could not convert total degree credits: {e}")

    # 4. Apply to Individual Courses (Safe Block)
    # This loop runs even if step 3 failed
    try:
        if acad.transcript_courses:
            count = 0
            for course in acad.transcript_courses:
                if course.original_credits:
                    # The Math: Original * Factor
                    val = float(course.original_credits) * conversion_factor
                    course.converted_ects = round(val, 1)
                    count += 1
            print(f"  [Logic] ✅ Converted {count} transcript courses.")
    except Exception as e:
        print(f"  [Logic] ❌ Error converting individual courses: {e}")

    return profile
# --- 4. HELPER FUNCTION: CHECK MISSING FIELDS ---

def get_missing_fields(profile: Optional[UserProfile]) -> List[str]:
    """
    Analyzes the UserProfile for critical missing data points for matching.
    Returns fields in priority order.
    """

    # 1. Safety Check: Is the profile object itself missing?
    if profile is None:
        return ["Initial full profile text (name, GPA, major, citizenship, interests)"]
    
    missing = []

    # 2. Basic Info Checks
    if not profile.full_name: 
        missing.append("full name")    
    if not profile.citizenship or not profile.citizenship.country_of_citizenship: 
        missing.append("country of citizenship")

    # 3. Academic Background Checks (CRITICAL FIX HERE)
    # We must check if the parent object exists before checking its children.
    if not profile.academic_background:
        # If the whole object is missing, request it entirely
        missing.append("academic background (bachelor field, GPA, credits, duration)")
    else:
        # Safe to access properties now
        acad = profile.academic_background

        if not acad.bachelor_field_of_study: 
            missing.append("bachelor field of study")
         
        # GPA Checks
        gpa = acad.bachelor_gpa
        if not gpa or not gpa.score or not gpa.max_scale or not gpa.min_passing_grade:
            # If any piece is missing, ask for the COMPLETE set
            missing.append("full bachelor GPA details (your score, maximum scale, and minimum passing grade)")
             
            
        # ECTS Calculation Requirements
        if not acad.total_credits_earned: 
            missing.append("total credit points earned")
        
        if not acad.program_duration_semesters:
            missing.append("duration of bachelor program semesters")

        # Interests (Needed for Agent 3 Semantic Search)
        if not acad.fields_of_interest: 
            missing.append("2-3 technical fields of interest")

    # 4. Language Checks
    if not profile.language_proficiency or len(profile.language_proficiency) == 0:
        missing.append("language proficiency (e.g., IELTS, TOEFL)")
    else:
        # Check if at least one language proof has a valid score
        has_valid_score = any(
            lang.overall_score is not None or lang.level is not None 
            for lang in profile.language_proficiency
        )
        if not has_valid_score:
            missing.append("language proof score or level")
        
    return missing

# CHECK other fields for desirability but not criticality
def get_desirable_missing_fields(profile: Optional[UserProfile], user_intent: str = "") -> List[str]:
    """Analyzes the UserProfile for helpful, but non-critical, data points."""
    desirable_missing = []
    
    # Safety Check 1: If profile is None, we can't check fields
    if profile is None:
        return []

    user_intent_lower = user_intent.lower()
    
    # Safety Check 2: Ensure preferences object exists
    # This fixes your "AttributeError: 'UserProfile' object has no attribute 'preferences'"
    if not hasattr(profile, "preferences") or profile.preferences is None:
        # If missing, we suggest asking about them
        desirable_missing.append("preferences (tuition fee, cities, language)")
        return desirable_missing

    # Check for "no" responses for cities
    cities_declined = any(phrase in user_intent_lower for phrase in [
        "no prefer", "no preference", "not important", "i don't care", "doesn't matter",
        "no cities", "no city preference", "any city", "no specific city"
    ])
    
    # Check Tuition
    tuition_mentioned = any(phrase in user_intent_lower for phrase in [
        "tuition", "fee", "cost", "price", "free", "no tuition", "tuition-free"
    ])
    if not tuition_mentioned and (not profile.preferences.max_tuition_fee_eur or profile.preferences.max_tuition_fee_eur == 0): 
        desirable_missing.append("maximum tuition fee (EUR per semester)")
    
    # Check Language Preference
    if not profile.preferences.preferred_language_of_instruction: 
        desirable_missing.append("preferred language of instruction")
    
    # Check Cities (if not declined)
    if not cities_declined:
        if not profile.preferences.preferred_cities: 
            desirable_missing.append("preferred cities")
    
    # Check Professional Info
    if not hasattr(profile, "professional_and_tests") or not profile.professional_and_tests:
        work_mentioned = any(phrase in user_intent_lower for phrase in ["work", "experience", "job", "internship"])
        if not work_mentioned:
            desirable_missing.append("professional information (work experience)")

    if not profile.preferences.preferred_start_semester:
        desirable_missing.append("preferred start semester")    
            
    return desirable_missing

# --- 5. LANGGRAPH NODES ---

# Node 1: Parsing & Intake (Tool 1)
def parse_profile_node(state: AgentState) -> Dict[str, Any]:
    """Attempts to parse the accumulated user_intent into a structured UserProfile."""
    print("\n[Node: Parsing/Tool 1] Attempting structured extraction...")

    # 1. CHECK: Have we already extracted the transcript?
    existing_profile = state.get("user_profile")
    has_transcript_data = existing_profile and existing_profile.academic_background and existing_profile.academic_background.transcript_courses
    
    pdf_text = ""
    
    # 2. LOAD: Only load PDF if we HAVEN'T extracted it yet
    if state.get("pdf_path") and not has_transcript_data:
        print("  📄 New PDF detected. Loading and Parsing...")
        pdf_text = load_pdf_text(state["pdf_path"])
    else:
        print("  ⏩ Transcript already processed. Skipping PDF re-read.")
        # We leave pdf_text empty so the LLM focuses only on the new chat text
    
    # 3. Combine Input
    # If pdf_text is empty, the LLM only sees the chat history (Fast & Cheap!)
    combined_input = f"""
    CHAT HISTORY: {state["user_intent"]}
    NEW PDF CONTENT: {pdf_text}
    """

    parser = JsonOutputParser(pydantic_object=UserProfile)
    format_instructions = parser.get_format_instructions()
    
    # --- MODIFIED SYSTEM PROMPT ---
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", 
             f"""You are a data extraction agent. 
             STRICTLY extract ALL details from the user's FULL accumulated text and adhere to the JSON schema.

             **For PDF extrac**
             ### PRIORITY 1: TRANSCRIPT DATA (CRITICAL) ###
             Scan the provided document text for a list of subjects/courses.
             - Extract them into 'academic_background.transcript_courses'.
             - **course_name**: The subject name (e.g. "Macroeconomics").
             - **original_credits**: The credit value exactly as written (e.g. 3, 4.0, 5).
             
             ### PRIORITY 2: DEGREE META-DATA ###
             - Look for 'total_credits_earned' (Sum of credits).
             - Look for 'program_duration_semesters' (e.g. 4 years = 8).
             
             ### PRIORITY 3: OTHER PROFILE INFO (OPTIONAL) ###
             - Try to find Name, Citizenship, GPA, and Degree Name.
             - **If you cannot find these, just leave them null.** Do NOT invent data.
             
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
             - For 'academic_background.transcript_courses': If the input contains a list of subjects/courses (e.g., from a PDF):
               - Extract them into 'academic_background.transcript_courses'.
               - **course_name**: The full subject title.
               - **original_credits**: The RAW credit value listed (do NOT convert to ECTS yourself).
             
             - For 'academic_background.meta_data':
               - Look for **'total_credits_earned'** (e.g., "Total Units: 140", "Credits: 128").
               - Look for **'program_duration_semesters'** (e.g., "4 years" = 8, "3.5 years" = 7).
             
             - For 'language_proficiency': Use 'exam_type' instead of 'exam'. For IELTS/TOEFL, use 'overall_score'. For CEFR (German), use 'level'.
             - The 'preferences' sections are optional.
             
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
        # 1. Extract
        structured_output_dict = parsing_chain.invoke({
            "input": combined_input,  # <--- Pass combined text
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
        
        # --- FIX: Only run ECTS logic if academic background exists ---
        if validated_profile.academic_background:
            print("  [Logic] Running ECTS Conversion...")
            validated_profile = apply_ects_conversion(validated_profile)
        else:
            print("  [Logic] Skipping ECTS: Academic background missing.")
        
        print(f"[Node: Parsing/Tool 1] ✅ Profile parsed. Missing fields: {len(get_missing_fields(validated_profile))}")
        print(validated_profile.model_dump_json(indent=2))
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
    if missing_data:
        prompt_text = f"The user is missing CRITICAL info: {', '.join(missing_data)}. Ask ONE question to get this."
    else:
        # 2. If Mandatory is done, check Desirable
        user_intent = state.get("user_intent", "")
        missing_desirable = get_desirable_missing_fields(profile, user_intent)
        
        if not missing_desirable:
            return {"ai_response": None} # Nothing left to ask!
    
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

