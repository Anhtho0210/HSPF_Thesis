import os
from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import json # Used for clean printing
from langgraph.graph import StateGraph, END
from typing import Any
import time
from dotenv import load_dotenv
import math

# --- Import Your Models ---
from models import AgentState, UserProfile, Citizenship, AcademicBackground, BachelorGPA, Preferences, ProfessionalAndTests

# --- Handling PDF ---
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS 
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader  

# --- Gemini/LangChain Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable

load_dotenv()

# --- YOUR SPECIFIC API SETUP (RESTORED) ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    print("[Warning] GEMINI_API_KEY not found in .env file or environment variables")

LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.1 
)

# --- 2. HELPER: PDF LOADER ---
def load_pdf_text(file_path: str) -> str:
    """Reads text from a PDF file safely."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text[:15000] 
    except Exception as e:
        print(f"  [PDF] Error reading file: {e}")
        return ""

# --- 3. HELPER: MERGE PROFILES (CRITICAL FIX) ---
def merge_user_profiles(old_profile: Optional[UserProfile], new_profile: UserProfile) -> UserProfile:
    """
    Merges new extraction results into the existing profile.
    Keeps old data if the new extraction returns null/empty for that field.
    """
    if not old_profile:
        return new_profile

    # 1. Merge Basic Fields
    if new_profile.full_name: old_profile.full_name = new_profile.full_name
    
    if new_profile.citizenship and new_profile.citizenship.country_of_citizenship:
        if not old_profile.citizenship: old_profile.citizenship = Citizenship()
        old_profile.citizenship.country_of_citizenship = new_profile.citizenship.country_of_citizenship

    # 2. Merge Academic Background
    if new_profile.academic_background:
        if not old_profile.academic_background:
            old_profile.academic_background = AcademicBackground()
            
        new_acad = new_profile.academic_background
        old_acad = old_profile.academic_background
        
        if new_acad.bachelor_field_of_study: old_acad.bachelor_field_of_study = new_acad.bachelor_field_of_study
        if new_acad.total_credits_earned: old_acad.total_credits_earned = new_acad.total_credits_earned
        if new_acad.program_duration_semesters: old_acad.program_duration_semesters = new_acad.program_duration_semesters
            
        # GPA (Merge individual sub-fields)
        if new_acad.bachelor_gpa:
             if not old_acad.bachelor_gpa: old_acad.bachelor_gpa = BachelorGPA()
             if new_acad.bachelor_gpa.score: old_acad.bachelor_gpa.score = new_acad.bachelor_gpa.score
             if new_acad.bachelor_gpa.max_scale: old_acad.bachelor_gpa.max_scale = new_acad.bachelor_gpa.max_scale
             if new_acad.bachelor_gpa.min_passing_grade: old_acad.bachelor_gpa.min_passing_grade = new_acad.bachelor_gpa.min_passing_grade

        # Interests
        if new_acad.fields_of_interest:
            old_acad.fields_of_interest = new_acad.fields_of_interest

        # CRITICAL: Transcript Courses
        # If we found courses before, but the new chat didn't mention them, KEEP THE OLD ONES.
        if new_acad.transcript_courses:
             print(f"  [Merge] Updating transcript with {len(new_acad.transcript_courses)} new items.")
             old_acad.transcript_courses = new_acad.transcript_courses
        elif old_acad.transcript_courses:
             pass 

    # 3. Merge Language
    if new_profile.language_proficiency:
        old_profile.language_proficiency = new_profile.language_proficiency
    
    # 4. Merge Professional & Tests (Work Experience)
    if new_profile.professional_and_tests:
        if not old_profile.professional_and_tests:
            old_profile.professional_and_tests = ProfessionalAndTests()
        if new_profile.professional_and_tests.relevant_work_experience_months is not None:
            old_profile.professional_and_tests.relevant_work_experience_months = new_profile.professional_and_tests.relevant_work_experience_months
        
    # 5. Merge Preferences
    if new_profile.preferences:
        if not old_profile.preferences: old_profile.preferences = Preferences()
        if new_profile.preferences.preferred_cities: old_profile.preferences.preferred_cities = new_profile.preferences.preferred_cities
        if new_profile.preferences.max_tuition_fee_eur: old_profile.preferences.max_tuition_fee_eur = new_profile.preferences.max_tuition_fee_eur
        if new_profile.preferences.preferred_start_semester: old_profile.preferences.preferred_start_semester = new_profile.preferences.preferred_start_semester
        if new_profile.preferences.preferred_language_of_instruction: old_profile.preferences.preferred_language_of_instruction = new_profile.preferences.preferred_language_of_instruction

    return old_profile

# --- 4. HELPER: ECTS LOGIC ---
def apply_ects_conversion(profile: UserProfile) -> UserProfile:
    """
    ECTS Conversion Logic:
    
    European Bachelor's degrees are typically 180-240 ECTS over 6-8 semesters.
    
    For non-European systems:
    1. If credits are already close to ECTS range (170-250), assume they ARE ECTS (factor = 1.0)
    2. Otherwise, calculate factor based on standard Bachelor's degree:
       - 6 semesters → 180 ECTS target
       - 8 semesters → 240 ECTS target
    3. Factor = Target_ECTS / Total_Credits_Earned
    4. Apply factor to all courses
    """
    if not profile or not profile.academic_background: return profile
    acad = profile.academic_background
    
    print(f"\n[DEBUG ECTS] Starting ECTS conversion...")
    print(f"[DEBUG ECTS] total_credits_earned: {acad.total_credits_earned}")
    print(f"[DEBUG ECTS] program_duration_semesters: {acad.program_duration_semesters}")
    
    # We require explicit total credits and duration to calculate the factor
    if not acad.total_credits_earned or not acad.program_duration_semesters:
        print(f"[DEBUG ECTS] Missing required fields - skipping conversion")
        return profile

    try:
        total_credits = acad.total_credits_earned
        semesters = acad.program_duration_semesters
        
        # 1. Check if already in ECTS range (European system)
        if 170 <= total_credits <= 250:
            print(f"[DEBUG ECTS] Credits already in ECTS range - using factor 1.0")
            conversion_factor = 1.0
        else:
            # 2. Calculate target ECTS based on program duration
            # Standard: 30 ECTS per semester
            target_ects = semesters * 30.0
            
            # 3. Calculate conversion factor
            conversion_factor = target_ects / total_credits
            
            print(f"[DEBUG ECTS] Target ECTS: {target_ects}")
            print(f"[DEBUG ECTS] Conversion factor: {conversion_factor}")
        
        # Sanity Check: If factor is very close to 1.0, just use 1.0
        if 0.95 <= conversion_factor <= 1.05:
            conversion_factor = 1.0
            print(f"[DEBUG ECTS] Factor close to 1.0 - using 1.0")
        
        acad.ects_conversion_factor = round(conversion_factor, 2)
        
        # 4. Calculate Total Degree ECTS
        acad.total_converted_ects = round(total_credits * conversion_factor, 1)
        
        print(f"[DEBUG ECTS] Final total ECTS: {acad.total_converted_ects}")
        
        # 5. Apply to Individual Courses
        if acad.transcript_courses:
            for course in acad.transcript_courses:
                if course.original_credits:
                    val = float(course.original_credits) * conversion_factor
                    course.converted_ects = round(val, 1)

    except Exception as e:
        print(f"  [Logic] ECTS Error: {e}")

    return profile

# --- 5. CHECK MISSING FIELDS ---
def get_missing_fields(profile: Optional[UserProfile]) -> List[str]:
    """
    Analyzes profile and returns missing fields ONE AT A TIME in priority order.
    PRIORITY: Basic Info → Academics → Interests → Language → Work Experience → Transcript Data.
    """
    if profile is None:
        return ["Initial full profile text (name, GPA, major, citizenship, interests)"]
    
    # 1. Basic Info (Ask one at a time)
    if not profile.full_name: 
        return ["full name"]
    if not profile.citizenship or not profile.citizenship.country_of_citizenship: 
        return ["country of citizenship"]

    # 2. Academic Background
    if not profile.academic_background:
        return ["academic background (bachelor field of study, GPA)"]
    
    acad = profile.academic_background
    if not acad.bachelor_field_of_study: 
        return ["bachelor field of study"]
        
    # GPA (All sub-fields required)
    gpa = acad.bachelor_gpa
    if not gpa or not gpa.score or not gpa.max_scale or not gpa.min_passing_grade:
        print(f"[DEBUG] GPA missing - gpa object: {gpa}, score: {gpa.score if gpa else 'N/A'}, max: {gpa.max_scale if gpa else 'N/A'}, min: {gpa.min_passing_grade if gpa else 'N/A'}")
        return ["full bachelor GPA details (score, max scale, min passing grade)"]

    # 3. Interests (Separate question) 
    has_interests = False
    if acad.fields_of_interest: has_interests = True
    if hasattr(profile, 'desired_program') and profile.desired_program and profile.desired_program.fields_of_interest:
        has_interests = True
    
    if not has_interests:
        return ["3-5 technical fields of interest for your master's program"]

    # 4. Language (Separate question)
    if not profile.language_proficiency:
        return ["language proficiency (e.g. IELTS/TOEFL)"]

    # 5. Work Experience (Separate question)
    if not profile.professional_and_tests or profile.professional_and_tests.relevant_work_experience_months is None:
        return ["relevant work experience (in months, or 0 if none)"]

    # 6. Transcript & Meta-Data (Last priority)
    if not acad.transcript_courses:
        return ["official transcript (PDF upload)"]
    
    # These are mandatory for ECTS calculation
    if not acad.total_credits_earned: 
        return ["total credits earned (explicit number)"]
    if not acad.program_duration_semesters: 
        return ["program duration (in semesters)"]
        
    return []

def get_desirable_missing_fields(profile: Optional[UserProfile], user_intent: str = "") -> List[str]:
    if not profile or not profile.preferences: return ["preferences"]
    desirable = []
    pref = profile.preferences
    intent = user_intent.lower()

    if not pref.max_tuition_fee_eur and not any(x in intent for x in ["cost", "tuition", "budget", "fee"]):
        desirable.append("budget/tuition limit")
    
    cities_declined = any(x in intent for x in ["no prefer", "any city", "don't care"])
    if not pref.preferred_cities and not cities_declined:
        desirable.append("preferred cities")

    if not pref.preferred_start_semester:
        desirable.append("preferred start semester")

    return desirable

# --- 6. LANGGRAPH NODES ---

# Node 1: Parsing & Intake
def parse_profile_node(state: AgentState) -> Dict[str, Any]:
    print("\n[Node: Parsing/Tool 1] Attempting structured extraction...")
    
    existing_profile = state.get("user_profile")
    
    # 1. Handle PDF
    pdf_text = ""
    pdf_path = state.get("pdf_path")
    
    has_transcript = existing_profile and existing_profile.academic_background and existing_profile.academic_background.transcript_courses
    
    if pdf_path and os.path.exists(pdf_path) and not has_transcript:
        print(f"  📄 New PDF detected. Loading: {pdf_path}")
        pdf_text = load_pdf_text(pdf_path)
    
    combined_input = f"""
    CHAT HISTORY: {state["user_intent"]}
    NEW PDF CONTENT: {pdf_text}
    """

    parser = JsonOutputParser(pydantic_object=UserProfile)
    format_instructions = parser.get_format_instructions()
    
    # --- YOUR SYSTEM PROMPT ---
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a data extraction agent. 
             STRICTLY extract ALL details from the user's FULL accumulated text and adhere to the JSON schema.
             
             CRITICAL RULES - ABSOLUTELY NO ASSUMPTIONS:
             - Do NOT invent or assume data that is not explicitly mentioned by the user.
             - If a field is not mentioned in the user's text, ask user again to get the answer .

             MANDATORY RULES FOR ACADEMIC FIELDS:
             - For 'academic_background.bachelor_field_of_study': 
               - This is where you put the BACHELOR DEGREE FIELD the user studied (e.g., "Computer Science", "Engineering", "Business", "Mathematics").
               - Do NOT assume from terms like "degree", "CompSci", "CS degree", "tech degree", or "I have a degree", "degree in tech" or "studied programming".
             
             - For 'fields_of_interest': 
               - **CRITICAL**: This field is for the user's DESIRED MASTER'S PROGRAM interests, NOT their bachelor's courses.
               - ONLY populate this if the user EXPLICITLY states what they want to study in their MASTER'S program.
               - DO NOT extract course names from transcripts/PDFs and put them here.
               - DO NOT infer interests from bachelor's courses (e.g., if transcript shows "Database" course, do NOT add "Database" to interests).
               - Examples of valid input: "I want to study AI and Machine Learning", "interested in Data Science and Analytics".
               - If the user has NOT explicitly mentioned their master's program interests, set this to null or empty list [].

             - For 'academic_background.bachelor_gpa': Only extract if the user provides actual GPA numbers. Set score, max_scale, and min_passing_grade to null if not provided.
             - For academic_background.program_duration_semester, ask about the total semester in bachelor degree
             
             - For 'academic_background.transcript_courses': If the input contains a list of subjects/courses (e.g., from a PDF):
               - Extract them into 'academic_background.transcript_courses'.
               - **course_name**: The full subject title.
               - **original_credits**: The RAW credit value listed (do NOT convert to ECTS yourself).

             - For 'academic_background':
               - **DO NOT** extract 'total_credits_earned' or 'program_duration_semesters' from PDFs.
               - These fields should ONLY be populated when the user explicitly provides them in chat.

             - For 'professional_and_tests.relevant_work_experience_months':
                - If user says "no experience", "none", "fresh graduate", "student", or "0", set this to 0.
                - Do NOT set to null if they explicitly say "no" or "0".

             - For 'language_proficiency': Use 'exam_type' instead of 'exam'. For IELTS/TOEFL, use 'overall_score'.
             
             Crucial Context: The user's latest response might be a short answer. Map it to the CORRECT field:
             - If user says "Munich", populate 'preferences.preferred_cities'.
             - If user says "1000", it is likely 'preferences.max_tuition_fee_eur'.
             - If user says "No preference", set the specific list to [].
             - If user says "0" or "none", check if it implies 'professional_and_tests.relevant_work_experience_months' is 0.
             
             REMEMBER: When in doubt, return null. Do NOT invent data. Only output the JSON.
             
             {format_instructions}"""),
        ("user", "{input}")
    ])
    
    chain = prompt | LLM | parser
    
    try:
        # Extract
        result = chain.invoke({"input": combined_input, "format_instructions": format_instructions})
        new_profile_update = UserProfile(**result)
        
        # DEBUG: Print extracted GPA
        print("\n[DEBUG] Extracted GPA from LLM:")
        if new_profile_update.academic_background and new_profile_update.academic_background.bachelor_gpa:
            gpa = new_profile_update.academic_background.bachelor_gpa
            print(f"  Score: {gpa.score}, Max: {gpa.max_scale}, Min: {gpa.min_passing_grade}")
        else:
            print("  GPA is None or not extracted")
        
        # --- CRITICAL: MERGE WITH EXISTING STATE ---
        final_profile = merge_user_profiles(existing_profile, new_profile_update)
        
        # DEBUG: Print merged GPA
        print("\n[DEBUG] GPA after merge:")
        if final_profile.academic_background and final_profile.academic_background.bachelor_gpa:
            gpa = final_profile.academic_background.bachelor_gpa
            print(f"  Score: {gpa.score}, Max: {gpa.max_scale}, Min: {gpa.min_passing_grade}")
        else:
            print("  GPA is None after merge")
        
        # Post-Processing
        if final_profile.academic_background:
            # GPA Calc
            gpa = final_profile.academic_background.bachelor_gpa
            if gpa and gpa.score and gpa.max_scale and gpa.min_passing_grade:
                denom = gpa.max_scale - gpa.min_passing_grade
                if denom != 0:
                    german_val = 1 + 3 * (gpa.max_scale - gpa.score) / denom
                    gpa.score_german = round(max(1.0, min(4.0, german_val)), 2)
                    print(f"\n[DEBUG] GPA German conversion: {gpa.score_german}")
                else:
                    print("\n[DEBUG] GPA calculation skipped: denominator is 0")

            # ECTS Calc
            final_profile = apply_ects_conversion(final_profile)

        return {"user_profile": final_profile}

    except Exception as e:
        print(f"  ❌ Parsing Failed: {e}")
        # Fallback: Return existing profile if parsing fails
        return {"user_profile": state.get("user_profile")}

# NODE 2: MANDATORY CHAT (STRICT)
def conversational_chat_node(state: AgentState) -> Dict[str, Any]:
    profile = state.get("user_profile")
    missing = get_missing_fields(profile)
    
    if not missing: return {"ai_response": None}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strict University Registrar. Ask ONLY for the missing fields listed below. Be direct. Do not make small talk."),
        ("user", f"The user profile is missing these MANDATORY fields: {', '.join(missing)}. Ask the user for this specific information.")
    ])
    
    response = LLM.invoke(prompt.format_messages())
    print(f"[Node: Chat] AI Question: {response.content}")
    return {"ai_response": response.content}

# NODE 3: WRAP-UP CHAT
def wrap_up_chat_node(state: AgentState) -> Dict[str, Any]:
    profile = state.get("user_profile")
    intent = state.get("user_intent", "")
    missing = get_desirable_missing_fields(profile, intent)
    
    if not missing: return {"ai_response": None}
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Mandatory info is complete. Ask the user if they have preferences for the following optional items."),
        ("user", f"Optional items: {', '.join(missing)}. Ask if they have preferences. Combine into one question.")
    ])
    
    response = LLM.invoke(prompt.format_messages())
    print(f"[Node: Wrap-Up] AI Question: {response.content}")
    return {"ai_response": response.content}

# --- 7. EDGE LOGIC ---
def check_for_completion(state: AgentState) -> Literal["chat", "wrap_up", "matching"]:
    profile = state.get("user_profile")
    intent = state.get("user_intent", "")
    
    if get_missing_fields(profile): return "chat"
    if get_desirable_missing_fields(profile, intent): return "wrap_up"
    return "matching"