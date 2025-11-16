# agent3.py

import json
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# --- Import from new models.py ---
from models import AgentState, StructuredRequirements, UserProfile

# --- LLM SETUP (can be shared or re-initialized) ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment.")
LLM = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)


# --- AGENT 3 TOOLS ---
def get_requirement_extractor_chain() -> Runnable:
    parser = JsonOutputParser(pydantic_object=StructuredRequirements)
    
    # Remove the f-string and add {format_instructions} as a variable
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Extract key admission requirements.\n{format_instructions}"),
            ("user", "Program Text:\n{program_text}")
        ]
    )

    return prompt | LLM | parser

def get_field_reasoning_chain() -> Runnable:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Answer with only 'YES' or 'NO'."),
            ("user", "Is a Bachelor's degree in '{user_field}' considered a relevant background for a Master's program that requires: '{required_fields_list}'?")
        ]
    )
    return prompt | LLM | (lambda x: "YES" in x.content.upper())


# --- AGENT 3 NODES ---

def agent_3_filter_node(state: AgentState) -> Dict[str, Any]:
    """Filters the full program catalog down to only eligible programs."""
    print("\n" + "="*50)
    print("--- [Node: Agent 3 Filter] ---")
    print("Starting eligibility check...")
    
    user_profile = state["user_profile"]
    if not user_profile:
        print("  [DEBUG] ❌ ERROR: User profile is None. Stopping filter.")
        return {"eligible_programs": [], "program_catalog": []}

    try:
        with open("TESTING_MASTER_LIST_100.json", 'r') as f:
            program_catalog = json.load(f)
        print(f"  [DEBUG] Loaded {len(program_catalog)} programs from JSON.")
    except Exception as e:
        print(f"  [DEBUG] ❌ ERROR: Failed to load TESTING_MASTER_LIST_100.json: {e}")
        return {"eligible_programs": [], "program_catalog": []}

    # --- 1. Print User Profile for Debugging ---
    user_gpa = user_profile.academic_background.bachelor_gpa.score_german
    user_field = user_profile.academic_background.bachelor_field_of_study
    user_ielts = next((lang.overall_score for lang in user_profile.language_proficiency if lang.exam_type == 'IELTS'), None)
    
    print("\n  --- [DEBUG] User Profile ---")
    print(f"  User GPA (German): {user_gpa}")
    print(f"  User Field:        {user_field}")
    print(f"  User IELTS:        {user_ielts}")
    print("  --------------------------\n")

    # Get LLM tools
    extractor_chain = get_requirement_extractor_chain()
    reasoning_chain = get_field_reasoning_chain()

    # Get the format instructions ONCE before the loop
    parser = JsonOutputParser(pydantic_object=StructuredRequirements)
    format_instructions = parser.get_format_instructions()

    eligible_programs = []

    # --- 2. Iterate and Filter (The Loop) ---
    # Limiting to 10 for a test run. Remove "[:10]" for the full 100.
    for program in program_catalog[:10]:
        print(f"--- Checking Program: {program['program_id']} - {program['name']} ---")
        combined_text = f"Admission: {program['admission_req']} \nLanguage: {program['language_req']}"
        
        try:
            # Pass BOTH variables to the invoke call
            reqs_dict = extractor_chain.invoke({
                "program_text": combined_text,
                "format_instructions": format_instructions  # <-- Add this line
            })
            # --- 3. Debug the LLM Extractor ---
            reqs = StructuredRequirements(**reqs_dict)
            print(f"  [DEBUG] Extracted Reqs: {reqs.model_dump_json(indent=2)}")

            is_eligible = True # Assume eligible until a check fails
            
            # --- 4. Debug the Filter Logic ---
            # GPA Check
            if reqs.min_gpa_german:
                if user_gpa > reqs.min_gpa_german:
                    print(f"  [DEBUG] ❌ REJECT (GPA): User {user_gpa} is worse than required {reqs.min_gpa_german}")
                    is_eligible = False
                else:
                    print(f"  [DEBUG] ✅ PASS (GPA): User {user_gpa} <= Req {reqs.min_gpa_german}")
            
            # IELTS Check
            if reqs.min_ielts_score and is_eligible:
                if user_ielts is None or user_ielts < reqs.min_ielts_score:
                    print(f"  [DEBUG] ❌ REJECT (IELTS): User {user_ielts} is less than required {reqs.min_ielts_score}")
                    is_eligible = False
                else:
                    print(f"  [DEBUG] ✅ PASS (IELTS): User {user_ielts} >= Req {reqs.min_ielts_score}")

            # Field of Study Check (LLM Reasoning)
            if reqs.required_field_of_study and is_eligible:
                print(f"  [DEBUG] Reasoning: Is '{user_field}' related to '{reqs.required_field_of_study}'?")
                is_related = reasoning_chain.invoke({
                    "user_field": user_field,
                    "required_fields_list": ", ".join(reqs.required_field_of_study)
                })
                
                if not is_related:
                    print(f"  [DEBUG] ❌ REJECT (Field): LLM said '{user_field}' is NOT related.")
                    is_eligible = False
                else:
                    print(f"  [DEBUG] ✅ PASS (Field): LLM said 'YES'.")
            
            # GRE Check
            if reqs.requires_gre and is_eligible:
                user_has_gre = user_profile.professional_and_tests and user_profile.professional_and_tests.standardized_tests
                if not user_has_gre:
                    print(f"  [DEBUG] ❌ REJECT (GRE): Program requires GRE, user has none.")
                    is_eligible = False
                else:
                    print(f"  [DEBUG] ✅ PASS (GRE): User has GRE (assumed).")


            # --- 5. Final Decision for this program ---
            if is_eligible:
                print("\n  [RESULT] 🎉🎉🎉 THIS PROGRAM IS ELIGIBLE 🎉🎉🎉\n")
                eligible_programs.append(program)
            else:
                print("\n  [RESULT] 🛑 This program is NOT eligible.\n")

        except Exception as e:
            print(f"  [DEBUG] ❌ ERROR: Failed to process program {program['program_id']}. Error: {e}")

    print("="*50)
    print(f"[Node: Agent 3 Filter] Complete. Found {len(eligible_programs)} eligible programs.")
    print("="*50 + "\n")
    
    return {
        "program_catalog": program_catalog,
        "eligible_programs": eligible_programs
    }


def agent_3_rank_node(state: AgentState) -> Dict[str, Any]:
    print("\n[Node: Agent 3 Rank] Ranking eligible programs...")
    eligible_programs = state["eligible_programs"]
    user_interests = state["user_profile"].academic_background.fields_of_interest
    
    if not eligible_programs:
        return {"ranked_programs": []}

    # --- This is the RANK stage ---
    descriptions = [p["description"] for p in eligible_programs]
    user_query = " ".join(user_interests)
    
    vectorizer = TfidfVectorizer(stop_words='english')
    program_vectors = vectorizer.fit_transform(descriptions)
    query_vector = vectorizer.transform([user_query])
    keyword_scores = cosine_similarity(query_vector, program_vectors)[0]
    
    ranked_list = []
    for i, program in enumerate(eligible_programs):
        # Here you would add your LLM-based score for a weighted average
        program['relevance_score'] = keyword_scores[i]
        ranked_list.append(program)

    ranked_list = sorted(ranked_list, key=lambda p: p['relevance_score'], reverse=True)
    
    print(f"[Node: Agent 3 Rank] Ranking complete.")
    return {"ranked_programs": ranked_list}