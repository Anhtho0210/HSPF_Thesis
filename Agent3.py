import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# For Semantic Matching
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_google_genai import ChatGoogleGenerativeAI

from models import AgentState, UserProfile

load_dotenv()

# --- HELPER: CEFR RANKING ---
def get_cefr_rank(level: str) -> int:
    """Converts CEFR levels to integers for comparison."""
    if not level or level == "Unknown" or level == "None": return 0
    # Clean string (e.g. "B2 (IELTS 6.0)" -> "B2")
    norm_level = level.split(' ')[0].split('/')[0].strip().upper()
    
    ranks = {
        "A1": 1, "A2": 2, 
        "B1": 3, "B2": 4, 
        "C1": 5, "C2": 6
    }
    return ranks.get(norm_level, 0)

# --- 1. HARD FILTER LOGIC (The Core Engine) ---
def check_hard_constraints(student: UserProfile, program: dict) -> dict:
    """
    Strictly rejects programs based on 'Must-Have' criteria.
    Rule: If Program Data is MISSING/NULL, we ACCEPT (Benefit of Doubt).
    """
    
    # --- 1. GPA Check ---
    # Logic: German Scale -> Lower is better. (1.0 best, 4.0 worst)
    if student.academic_background and student.academic_background.bachelor_gpa:
        student_gpa = student.academic_background.bachelor_gpa.score_german
        prog_min_gpa = program.get('min_gpa_german_scale')
        
        if student_gpa and prog_min_gpa:
            if student_gpa > prog_min_gpa:
                return {'eligible': False, 'reason': f"GPA {student_gpa} > Limit {prog_min_gpa}"}

    # --- 2. Total ECTS Check (Degree Volume) ---
    # Standard Master's requires 180 ECTS Bachelor. Some require 210.
    if student.academic_background and student.academic_background.total_converted_ects:
        student_ects = student.academic_background.total_converted_ects
        # If program doesn't specify, assume standard 180
        prog_min_ects = program.get('min_degree_ects', 180) 
        
        if student_ects < prog_min_ects:
             return {'eligible': False, 'reason': f"Total ECTS {student_ects} < Required {prog_min_ects}"}

    # --- 3. Language Proficiency Check ---
    if student.language_proficiency:
        # A. English
        student_eng = "Unknown"
        for lang in student.language_proficiency:
            if "english" in lang.language.lower():
                student_eng = lang.level if lang.level else "Unknown"
                # Add logic to map scores to levels here if needed
                break
        
        prog_eng = program.get('english_level_requirement', 'Unknown')
        
        # Only check if both sides are known
        if student_eng != "Unknown" and prog_eng != "Unknown" and prog_eng != "None":
            if get_cefr_rank(student_eng) < get_cefr_rank(prog_eng):
                return {'eligible': False, 'reason': f"English {student_eng} < Req {prog_eng}"}

    # --- 4. Tuition Fee Check ---
    if student.preferences and student.preferences.max_tuition_fee_eur is not None:
        max_fee = student.preferences.max_tuition_fee_eur
        prog_fee = program.get('tuition_fee_per_semester_eur', 0.0)
        
        if prog_fee > max_fee:
            return {'eligible': False, 'reason': f"Fee {prog_fee}€ > Budget {max_fee}€"}

    # --- 5. Location Check (City & State) ---
    if student.preferences and student.preferences.preferred_cities:
        user_locs = [c.lower() for c in student.preferences.preferred_cities]
        if user_locs: # Only check if user actually listed cities
            prog_city = program.get('city', '').lower()
            prog_state = program.get('state', '').lower()
            
            # Fail safe: If program has NO location data, we accept it
            if prog_city or prog_state:
                match = False
                for loc in user_locs:
                    if loc in prog_city or loc in prog_state:
                        match = True
                        break
                if not match:
                    return {'eligible': False, 'reason': f"Location mismatch ({prog_city})"}

    # --- 6. Semester Check (Winter/Summer) ---
    if student.preferences and student.preferences.preferred_start_semester:
        user_sem = student.preferences.preferred_start_semester.lower() # "winter" or "summer"
        deadlines = program.get('deadlines', {})
        
        # If deadlines object exists, check specific semester availability
        if deadlines:
            has_winter = deadlines.get('winter_semester') is not None
            has_summer = deadlines.get('summer_semester') is not None
            
            if user_sem == "winter" and not has_winter:
                 return {'eligible': False, 'reason': "No Winter Intake"}
            if user_sem == "summer" and not has_summer:
                 return {'eligible': False, 'reason': "No Summer Intake"}

    # --- 7. Teaching Language Preference ---
    if student.preferences and student.preferences.preferred_language_of_instruction:
        user_lang_pref = student.preferences.preferred_language_of_instruction.lower()
        
        # Infer teaching language from requirements
        prog_eng_req = program.get('english_level_requirement', 'None')
        prog_ger_req = program.get('german_level_requirement', 'None')
        
        # If user wants English, but Program requires NO English (implies German only)
        if "english" in user_lang_pref:
            if prog_eng_req == "None" and prog_ger_req != "None":
                 return {'eligible': False, 'reason': "Program not taught in English"}
                 
        # If user wants German, but Program requires NO German (implies English only)
        if "german" in user_lang_pref:
             if prog_ger_req == "None" and prog_eng_req != "None":
                  return {'eligible': False, 'reason': "Program not taught in German"}

    return {'eligible': True, 'reason': "Pass"}

# --- 2. SEMANTIC MATCHING LOGIC (Soft Scoring) ---
def calculate_semantic_match(student: UserProfile, program: dict) -> float:
    """
    Calculates similarity between Student Interest/Transcript and Program Description.
    """
    # 1. Student Text
    # Combine Interests + Course Names
    transcript_text = " ".join([c.course_name for c in student.academic_background.transcript_courses])
    interest_text = " ".join(student.academic_background.fields_of_interest or [])
    student_doc = f"{transcript_text} {interest_text}"

    # 2. Program Text
    # Combine Content Summary + ECTS Subject Areas
    prog_summary = program.get('course_content_summary', '')
    prog_subjects = ""
    if program.get('specific_ects_requirements'):
        for domain in program['specific_ects_requirements']:
            # Add domain name (e.g. "Mathematics")
            prog_subjects += f" {domain.get('domain_name', '')}"
            # Add modules (e.g. "Analysis", "Algebra")
            for mod in domain.get('modules', []):
                prog_subjects += f" {mod.get('subject_area', '')}"
    
    program_doc = f"{prog_summary} {prog_subjects}"

    # 3. Match
    if not student_doc.strip() or not program_doc.strip():
        return 0.0
        
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([student_doc, program_doc])
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(float(score) * 10.0, 1) # 0 to 10 scale
    except:
        return 0.0

# --- NODE: FILTER ---
def agent_3_filter_node(state: AgentState) -> Dict[str, Any]:
    print("\n" + "="*50)
    print("[Node: Agent 3] Filtering & Ranking...")
    
    user_profile = state["user_profile"]
    if not user_profile:
        return {"eligible_programs": [], "ranked_programs": []}

    # Load DB
    try:
        with open("structured_program_db.json", 'r', encoding='utf-8') as f:
            catalog = json.load(f)
    except FileNotFoundError:
        print("❌ DB Not Found")
        return {"eligible_programs": []}

    eligible = []
    
    for prog in catalog:
        # 1. Hard Filter
        check = check_hard_constraints(user_profile, prog)
        if check['eligible']:
            # 2. Soft Match (Only if eligible)
            score = calculate_semantic_match(user_profile, prog)
            prog['relevance_score'] = score
            eligible.append(prog)
        # else:
        #     print(f"Skipped {prog['program_id']}: {check['reason']}")

    # 3. Rank
    ranked = sorted(eligible, key=lambda x: x['relevance_score'], reverse=True)
    
    print(f"✅ Eligible Programs: {len(ranked)}")
    if ranked:
        print(f"🔝 Top Match: {ranked[0]['program_name']} (Score: {ranked[0]['relevance_score']})")
        
    return {"eligible_programs": ranked, "ranked_programs": ranked[:10]}