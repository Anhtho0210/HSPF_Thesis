import json
import os
import time
from typing import Dict, Any, List
from collections import Counter
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
from models import AgentState, UserProfile

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    print("❌ Error: GEMINI_API_KEY not found.")

embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# --- HELPERS (Fast Mode) ---
def safe_embed_query(text: str) -> List[float]:
    """Single text embedding. Retries only on actual errors."""
    for attempt in range(3):
        try:
            return embeddings_model.embed_query(text)
        except Exception as e:
            print(f"  ⚠️ Embed Retry {attempt+1}: {e}")
            time.sleep(0.5) # Small safety pause only on ERROR
    return []

def safe_batch_embed(texts: List[str], batch_size: int = 50) -> List[List[float]]:
    """
    Batch embedding for Paid API.
    Increased batch_size to 50 for speed. Removed artificial sleep.
    """
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            all_embeddings.extend(embeddings_model.embed_documents(batch))
        except Exception as e:
            print(f"  ❌ Batch Error: {e}")
            # Fallback: Fill with zeros to keep index alignment
            all_embeddings.extend([[0.0]*768 for _ in batch])
            
    return all_embeddings

# --- LOGIC FUNCTIONS ---
def check_hard_constraints(student: UserProfile, program: dict) -> dict:
    """Strictly rejects programs based on 'Must-Have' criteria."""
    
    # 1. GPA Check
    if student.academic_background and student.academic_background.bachelor_gpa:
        student_gpa = student.academic_background.bachelor_gpa.score_german
        prog_min_gpa = program.get('min_gpa_german_scale')
        if student_gpa and prog_min_gpa:
            if student_gpa > prog_min_gpa:
                return {'eligible': False, 'reason': f"GPA {student_gpa} > Limit {prog_min_gpa}"}

    # 2. Total ECTS Check
    if student.academic_background and student.academic_background.total_converted_ects:
        student_ects = student.academic_background.total_converted_ects
        prog_min_ects = program.get('min_degree_ects', 180) 
        if student_ects > 0 and student_ects < prog_min_ects:
             return {'eligible': False, 'reason': f"Total ECTS {student_ects} < Required {prog_min_ects}"}

    # 3. Language Check
    if student.language_proficiency:
        student_eng = "Unknown"
        # FIX: Loop through the list to find the English exam
        for lang in student.language_proficiency:
            if lang.language and "english" in lang.language.lower():
                 # Check if level exists, otherwise infer from score if needed
                 student_eng = lang.level if lang.level else "Unknown"
                 break
        
        prog_eng = program.get('english_level_requirement', 'Unknown')
        
        # Helper inner function for ranking
        def get_cefr_rank(level: str) -> int:
            if not level or level in ["Unknown", "None"]: return 0
            norm_level = level.split(' ')[0].split('/')[0].strip().upper()
            ranks = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
            return ranks.get(norm_level, 0)

        if student_eng != "Unknown" and prog_eng not in ["Unknown", "None"]:
            if get_cefr_rank(student_eng) < get_cefr_rank(prog_eng):
                return {'eligible': False, 'reason': f"English {student_eng} < Req {prog_eng}"}

    # 4. Tuition Fee Check
    if student.preferences and student.preferences.max_tuition_fee_eur is not None:
        max_fee = student.preferences.max_tuition_fee_eur
        prog_fee = program.get('tuition_fee_per_semester_eur', 0.0)
        if prog_fee > (max_fee + 100):
            return {'eligible': False, 'reason': f"Fee {prog_fee} > {max_fee}"}

    return {'eligible': True, 'reason': "Pass"}

def calculate_interest_match(user_vector: List[float], program_vector: List[float]) -> float:
    """Calculates cosine similarity between user interest and program."""
    if not user_vector or not program_vector: 
        return 0.5
    try:
        sim = cosine_similarity([user_vector], [program_vector])[0][0]
        return min(sim * 1.2, 1.0) # Boost score slightly
    except:
        return 0.5

def check_ects_match_with_embeddings(student_course_vectors: List[Any], student_courses: List[Any], program: dict) -> dict:
    """
    The Expensive Check: Runs on survivors.
    """
    requirements = program.get('specific_ects_requirements', [])
    if not requirements:
        # Return 0.5 (Neutral) instead of 1.0 (Perfect)
        return {'eligible': True, 'score': 0.5, 'details': "No ECTS Data listed"}

    total_domains = 0
    met_domains = 0
    details = []

    for domain in requirements:
        req_name = domain.get('domain_name', '')
        req_credits = domain.get('min_ects_total', 0)
        
        if req_credits <= 0: continue
        total_domains += 1
        
        # Single API Call per requirement
        req_vector = safe_embed_query(req_name) 
        time.sleep(0.2) # Sleep 200ms to smooth out the burst
        if not req_vector: continue

        similarities = cosine_similarity([req_vector], student_course_vectors)[0]
        
        found_credits = 0.0
        # Threshold 0.55 finds matches like "Marketing" <-> "Business"
        for i, score in enumerate(similarities):
            if score > 0.55:
                found_credits += student_courses[i].converted_ects

        if found_credits >= (req_credits * 0.6): 
            met_domains += 1
        else:
            details.append(f"{req_name}: {int(found_credits)}/{int(req_credits)}")
                
    if details:
        if met_domains < (total_domains / 2):
             return {'eligible': False, 'score': 0.0, 'details': f"Missing: {', '.join(details)}"}
        else:
             return {'eligible': True, 'score': 0.5, 'details': f"Partial: {', '.join(details)}"}
            
    return {'eligible': True, 'score': 1.0, 'details': "All Met"}


# ==========================================
# MAIN NODE (FAST MODE)
# ==========================================
def agent_3_filter_node(state: AgentState) -> Dict[str, Any]:
    print("\n" + "="*50)
    print("[Node: Agent 3] High-Speed Processing...")
    
    user_profile = state.get("user_profile")
    if not user_profile: return {"eligible_programs": []}

    try:
        with open("structured_program_db.json", 'r', encoding='utf-8') as f:
            catalog = json.load(f)
    except FileNotFoundError:
        return {"eligible_programs": []}

    # --- 0. PREPARE USER DATA ---
    print("  🧠 Embedding User Profile...")
    interests = []
    if user_profile.academic_background:
         interests = user_profile.academic_background.fields_of_interest
    user_text = " ".join(interests) if interests else "General"
    user_interest_vector = safe_embed_query(user_text)

    student_courses = []
    student_course_vectors = []
    if user_profile.academic_background and user_profile.academic_background.transcript_courses:
        student_courses = user_profile.academic_background.transcript_courses
        course_names = [c.course_name for c in student_courses]
        if course_names:
             # Batch embed transcript
            student_course_vectors = safe_batch_embed(course_names, batch_size=50)

    # --- STAGE 1: HARD FILTER & INTEREST MATCH (The Wide Funnel) ---
    print(f"  🔍 Stage 1: Filtering {len(catalog)} programs...")
    
    survivors = []
    program_texts = []
    
    # A. Hard Filter Loop
    for prog in catalog:
        check = check_hard_constraints(user_profile, prog)
        if check['eligible']:
            survivors.append(prog)
            # Prepare text for batch embedding
            p_name = prog.get('program_name', '')
            p_sum = prog.get('course_content_summary', '')
            program_texts.append(f"{p_name} {p_name} {p_sum}")

    print(f"     -> {len(survivors)} passed Hard Filters.")
    
    # B. Batch Embed Interest (Fast Batching)
    if survivors:
        # Increased batch size to 50 for Paid API
        program_vectors = safe_batch_embed(program_texts, batch_size=50)
    else:
        return {"eligible_programs": []}

    # C. Calculate Interest Scores & Filter
    interest_filtered_programs = []
    
    for i, prog in enumerate(survivors):
        interest_score = 0.5
        if user_interest_vector and i < len(program_vectors):
             interest_score = calculate_interest_match(user_interest_vector, program_vectors[i])
        
        prog['temp_interest_score'] = interest_score
        
        # THRESHOLD: Keep decent matches
        if interest_score >= 0.4:
            interest_filtered_programs.append(prog)
        time.sleep(0.1)

    print(f"     -> {len(interest_filtered_programs)} passed Interest Check.")

    # --- STAGE 2: ECTS DEEP CHECK (The Narrow Funnel) ---
    print("  🔬 Stage 2: Running Deep ECTS Check...")
    
    final_results = []
    
    for i, prog in enumerate(interest_filtered_programs):
        
        # --- FIX: HANDLE MISSING TRANSCRIPT ---
        if student_course_vectors:
            # We have data, calculate REAL score
            ects_check = check_ects_match_with_embeddings(student_course_vectors, student_courses, prog)
        else:
            # No data: Pass them, but give a LOWER score (0.5) so they rank below verified matches
            ects_check = {'eligible': True, 'score': 0.5, 'details': "⚠️ Transcript missing - Unverified"}
        # --------------------------------------
        
        if not ects_check['eligible']:
            continue

        # Final Score Calculation
        # ECTS (60%) + Interest (40%)
        final_score = (ects_check['score'] * 0.6) + (prog['temp_interest_score'] * 0.4)
        prog['relevance_score'] = round(final_score * 10, 1) # Scale to 10
        prog['llm_reasoning'] = f"Interest: {int(prog['temp_interest_score']*100)}% | ECTS: {ects_check['details']}"
        
        # Filter out very low scores
        if final_score > 0.2:  # Adjusted to ensure unverified users (min ~0.3-0.5) still appear
            final_results.append(prog)

    # --- SORT & RETURN ---
    ranked = sorted(final_results, key=lambda x: x['relevance_score'], reverse=True)
    print(f"✅ Final Eligible: {len(ranked)}")
    
    return {"eligible_programs": ranked, "ranked_programs": ranked[:10]}