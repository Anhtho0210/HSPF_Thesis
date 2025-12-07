import json
import os
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sklearn.metrics.pairwise import cosine_similarity
from models import AgentState, UserProfile
from pydantic import BaseModel, Field
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    print("❌ Error: GEMINI_API_KEY not found.")

# --- INITIALIZE MODELS ---
# Embedding Model for Semantic Search (Layer 3 & 4)
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# LLM for Intelligent Degree Checking (Layer 1)
llm_flash = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.0 # Strict logic, no creativity
)

# --- HELPERS (Embeddings) ---
def safe_embed_query(text: str) -> List[float]:
    """Single text embedding with retry."""
    for attempt in range(3):
        try:
            return embeddings_model.embed_query(text)
        except Exception as e:
            time.sleep(0.5)
    return []

def safe_batch_embed(texts: List[str], batch_size: int = 50) -> List[List[float]]:
    """Batch embedding for efficiency."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            all_embeddings.extend(embeddings_model.embed_documents(batch))
        except Exception as e:
            all_embeddings.extend([[0.0]*768 for _ in batch])
    return all_embeddings

# ==========================================
# LAYER 2: LLM-BASED DEGREE COMPATIBILITY
# ==========================================

class DegreeMatchScore(BaseModel):
    score: float = Field(description="A score between 0.0 (No match) and 1.0 (Perfect match).")
    reasoning: str = Field(description="Short explanation of the decision.")

def batch_check_degrees_with_llm(student_major: str, all_program_domains: List[List[str]]) -> Dict[str, float]:
    """
    Checks if the student's major satisfies the specific DEGREE DOMAINS required.
    Strictly ignores Program Name to prevent 'Title Bias'.
    """
    if not student_major: return {}

    # 1. Deduplicate: Many programs share identical requirements (e.g. ['CS', 'Math'])
    # We only want to ask the LLM about unique combinations.
    unique_sets = {}
    for domains in all_program_domains:
        if not domains: continue
        # Sort tuple to ensure ['CS', 'Math'] is same as ['Math', 'CS']
        key = tuple(sorted(domains)) 
        unique_sets[key] = domains

    print(f"  Layer 1: Evaluating '{student_major}' against {len(unique_sets)} unique domain requirements...")

    scores_cache = {}
    
    # 2. Strict Prompt: Compare Major vs. Required List
    parser = JsonOutputParser(pydantic_object=DegreeMatchScore)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a strict University Registrar. 
        Your ONLY job is to check if a student's Bachelor's Degree qualifies as a valid background for a set of REQUIRED DISCIPLINES.
        
        INPUTS:
        1. Student's Major (The degree they have)
        2. Required Domains (The degrees the university accepts)

        SCORING RULES:
        - 1.0 (Perfect): The Major is explicitly in the Required list (e.g. "CS" vs "CS").
        - 0.8-0.9 (Strong): The Major is a sub-field or very close synonym (e.g. "E-Commerce" vs "Business Informatics" or "Economics").
        - 0.5-0.7 (Partial): The Major has some overlap but lacks core theory (e.g. "E-Commerce" vs "Computer Science").
        - 0.0-0.2 (Reject): The Major is completely unrelated (e.g. "E-Commerce" vs "Agricuture" or "Physics").

        Ignore the Program Name. Focus ONLY on the academic content of the degrees.
        
        Respond in JSON: {{ "score": float, "reasoning": "string" }}
        """),
        ("user", """Student's Major: "{student_major}"
        Required Degree Domains: {target_domains}
        
        Is this major a valid background?""")
    ])

    chain = prompt | llm_flash | parser

    # 3. Batch Process
    for key, domains in unique_sets.items():
        try:
            # We pass the LIST of acceptable domains, not the Program Name
            result = chain.invoke({
                "student_major": student_major, 
                "target_domains": ", ".join(domains)
            })
            scores_cache[key] = result['score']        
            # Debug print to verify it's working
            print(f"    [Check] {student_major} vs {domains} -> Score: {result['score']}")
            
        except Exception as e:
            print(f"     Degree Check Error: {e}")
            scores_cache[key] = 0.5 

    return scores_cache
# ==========================================
# LAYER 1: HARD CONSTRAINTS (Rules)
# ==========================================
def check_hard_constraints(student: UserProfile, program: dict) -> dict:
    """
    Strict boolean checks for mandatory requirements.
    Returns {'eligible': False, 'reason': ...} if any check fails.
    """
    reasons = []

    # --- 1. GPA CHECK (German Scale) ---
    # In Germany: 1.0 is Best, 4.0 is Pass. 
    # Logic: Student GPA (2.11) <= Limit (2.5) -> Pass.
    if student.academic_background and student.academic_background.bachelor_gpa:
        student_gpa = student.academic_background.bachelor_gpa.score_german
        prog_min_gpa = program.get('min_gpa_german_scale')
        
        # Only check if both values exist
        if student_gpa and prog_min_gpa:
            # Allow a tiny buffer (0.1) for rounding differences
            if student_gpa > (prog_min_gpa + 0.05):
                reasons.append(f"GPA {student_gpa} > Limit {prog_min_gpa}")

    # --- 2. TUITION FEE CHECK ---
    if student.preferences and student.preferences.max_tuition_fee_eur is not None:
        max_fee = student.preferences.max_tuition_fee_eur
        prog_fee = program.get('tuition_fee_per_semester_eur', 0.0)
        
        # Allow buffer of 100 EUR (e.g. for semester contributions vs tuition)
        if max_fee > 0 and prog_fee > (max_fee + 100):
            reasons.append(f"Tuition {prog_fee}€ > Budget {max_fee}€")

    # --- 3. LOCATION CHECK (City & State) ---
    if student.preferences:
        # City Check
        pref_cities = [c.lower() for c in student.preferences.preferred_cities or []]
        prog_city = program.get('city', '').lower()
        
        if pref_cities and prog_city and prog_city not in pref_cities:
            reasons.append(f"City '{program.get('city')}' not in preferences")

        # State Check
        pref_state = (student.preferences.preferred_state or "").lower()
        prog_state = program.get('state', '').lower()
        
        if pref_state and prog_state and pref_state not in prog_state:
            reasons.append(f"State '{program.get('state')}' does not match '{student.preferences.preferred_state}'")

    # --- 4. WORK EXPERIENCE CHECK ---
    # Some programs (e.g. MBA) require strict work experience months
    req_months = program.get('min_work_experience_months', 0)
    
    if req_months > 0:
        student_exp = 0
        if student.professional_and_tests:
            student_exp = student.professional_and_tests.relevant_work_experience_months or 0
            
        if student_exp < req_months:
            reasons.append(f"Work Exp {student_exp}m < Required {req_months}m")

    # --- 5. START SEMESTER AVAILABILITY ---
    # If student explicitly wants 'Winter' start, reject programs that only offer 'Summer'
    if student.preferences and student.preferences.preferred_start_semester:
        wanted_start = student.preferences.preferred_start_semester.lower() # e.g., "winter"
        deadlines = program.get('deadlines', {})
        
        has_winter = deadlines.get('winter_semester') is not None
        has_summer = deadlines.get('summer_semester') is not None
        
        if "winter" in wanted_start and not has_winter:
            reasons.append("No Winter Start")
        elif "summer" in wanted_start and not has_summer:
            reasons.append("No Summer Start")

    # --- 6. TOTAL ECTS CHECK (Sanity Check) ---
    # Most Master's require a 180 ECTS Bachelor's minimum.
    if student.academic_background and student.academic_background.total_converted_ects:
        student_ects = student.academic_background.total_converted_ects
        # Default strict floor to 180 if not specified in DB
        min_required = program.get('min_degree_ects', 180)
        
        if student_ects < min_required:
            reasons.append(f"Bachelor ECTS {student_ects} < Minimum {min_required}")

    # --- FINAL VERDICT ---
    if reasons:
        return {'eligible': False, 'reason': "; ".join(reasons)}
    
    return {'eligible': True, 'reason': "Pass"}

# ==========================================
# LAYER 3: SEMANTIC RANKING (Embeddings)
# ==========================================
def calculate_semantic_match(user_vector: List[float], program_vector: List[float]) -> float:
    if not user_vector or not program_vector: return 0.5
    return cosine_similarity([user_vector], [program_vector])[0][0]

# ==========================================
# LAYER 4: DEEP ECTS CHECK (Reality Check)
# ==========================================
def check_ects_match_with_embeddings(student_course_vectors: list, student_courses: list, program: dict) -> dict:
    requirements = program.get('specific_ects_requirements', [])
    if not requirements:
        return {'eligible': True, 'score': 1.0, 'details': "No ECTS constraints"}

    # 1. Create a Ledger of Available Credits
    # We clone the credits so we can "spend" them without modifying the original object
    available_credits = [c.converted_ects for c in student_courses]
    
    # 2. Pre-Calculate All Similarities Matrix
    # Shape: (Num_Requirements, Num_Student_Courses)
    req_vectors = []
    req_infos = [] # Store metadata to map back later
    
    for domain in requirements:
        req_name = domain.get('domain_name', '')
        req_credits = domain.get('min_ects_total', 0)
        
        # Improvement: Enhance the embedding text if sub-modules exist
        # This helps 'Business Admin' match 'Marketing' courses better
        sub_modules = ", ".join([m.get('subject_area','') for m in domain.get('modules', [])])
        embed_text = f"{req_name} {sub_modules}".strip()
        
        if req_credits > 0:
            vec = safe_embed_query(embed_text)
            if vec:
                req_vectors.append(vec)
                req_infos.append({
                    'name': req_name, 
                    'target': req_credits, 
                    'filled': 0.0, 
                    'status': '❌'
                })

    if not req_vectors:
        return {'eligible': True, 'score': 0.5, 'details': "Cannot embed requirements"}

    # Calculate Matrix: Rows=Reqs, Cols=Courses
    similarity_matrix = cosine_similarity(req_vectors, student_course_vectors)

    # 3. Create a List of Potential Matches and Sort by Confidence
    # We want to fulfill the STRONGEST matches first (Greedy Approach)
    potential_matches = []
    
    rows, cols = similarity_matrix.shape
    for r in range(rows):
        for c in range(cols):
            score = similarity_matrix[r][c]
            if score > 0.60: # Keep your threshold
                potential_matches.append({
                    'req_idx': r,
                    'course_idx': c,
                    'score': score
                })
    
    # Sort descending: Best match gets first dibs on credits
    potential_matches.sort(key=lambda x: x['score'], reverse=True)

    # 4. Consume Credits
    for match in potential_matches:
        r_idx = match['req_idx']
        c_idx = match['course_idx']
        
        # How much does this requirement still need?
        needed = req_infos[r_idx]['target'] - req_infos[r_idx]['filled']
        if needed <= 0: continue # Requirement already full
        
        # How much does this course have left?
        have = available_credits[c_idx]
        if have <= 0: continue # Course already used up
        
        # Take the minimum of what's needed vs what's available
        take = min(needed, have)
        
        # Update Ledger
        req_infos[r_idx]['filled'] += take
        available_credits[c_idx] -= take

    # 5. Final Grading
    met_count = 0
    details = []
    
    for info in req_infos:
        # Soft pass: If we found at least 60% of the required credits
        if info['filled'] >= (info['target'] * 0.6):
            info['status'] = '✔'
            met_count += 1
        
        details.append(f"{info['status']} {info['name']}: {int(info['filled'])}/{int(info['target'])}")

    final_score = met_count / len(req_infos) if req_infos else 1.0
    
    return {
        'eligible': True, 
        'score': final_score, 
        'details': ", ".join(details)
    }

# ==========================================
# MAIN NODE: AGENT 3 (FILTER & RANK)
# ==========================================
def agent_3_filter_node(state: AgentState) -> Dict[str, Any]:
    print("\n" + "="*60)
    print("🚀 [Node: Agent 3] STARTING 4-LAYER FUNNEL")
    print("="*60)
    
    user_profile = state.get("user_profile")
    if not user_profile: return {"eligible_programs": []}
    
    # --- DEBUG: Print User Profile as JSON ---
    print("\n📋 DEBUG: User Profile (JSON)")
    print("=" * 60)
    print(user_profile.model_dump_json(indent=2))
    print("=" * 60 + "\n")

    try:
        with open("structured_program_db.json", 'r', encoding='utf-8') as f:
            catalog = json.load(f)
    except FileNotFoundError:
        return {"eligible_programs": []}

    total_start = len(catalog)
    print(f"📥 INPUT: Loaded {total_start} programs from database.")

    # --- PREPARE USER DATA ---
    student_major = "General"
    if user_profile.academic_background:
        student_major = user_profile.academic_background.bachelor_field_of_study or "General"
        
    # User Persona Vector (Layer 3)
    user_intent = state.get("user_intent", "")
    interests = []
    if user_profile.academic_background:
         interests = user_profile.academic_background.fields_of_interest
    
    user_persona_text = (
        f"Student with Bachelor in {student_major}. "
        f"Goal: {user_intent}. "
        f"Interests: {', '.join(interests)}."
    )
    user_vector = safe_embed_query(user_persona_text)

    # Transcript Vectors (Layer 4)
    student_courses = []
    student_course_vectors = []
    if user_profile.academic_background and user_profile.academic_background.transcript_courses:
        student_courses = user_profile.academic_background.transcript_courses
        course_names = [c.course_name for c in student_courses]
        if course_names:
            student_course_vectors = safe_batch_embed(course_names, batch_size=50)

    # =========================================================
    # ⚡ LAYER 1: HARD CONSTRAINTS (The Cost Saver)
    # =========================================================
    print(f"\n--- Layer 1: Running Hard Filters (GPA, Fee, etc.) ---")
    
    survivors_layer_1 = []
    for prog in catalog:
        hard_check = check_hard_constraints(user_profile, prog)
        if hard_check['eligible']:
            survivors_layer_1.append(prog)
    
    count_l1 = len(survivors_layer_1)
    dropped_l1 = total_start - count_l1
    print(f"✅ L1 Survivors: {count_l1} (Dropped {dropped_l1})")
    
    if not survivors_layer_1:
        print("❌ Funnel ended at Layer 1.")
        return {"eligible_programs": []}

    # =========================================================
    # 🧠 LAYER 2: LLM DEGREE CHECK (The Intelligent Gatekeeper)
    # =========================================================
    print(f"\n--- Layer 2: Running LLM Degree Compatibility Check ---")
    
    # Optimization: Only check domains for survivors!
    surviving_reqs = [p.get('required_degree_domains', []) for p in survivors_layer_1]
    
    # Batch Call to Gemini
    domain_scores_map = batch_check_degrees_with_llm(student_major, surviving_reqs)
    
    survivors_layer_2 = []
    program_texts = []

    for prog in survivors_layer_1:
        req_domains = prog.get('required_degree_domains', [])
        
        # Lookup Score
        if not req_domains:
            d_score = 1.0
        else:
            key = tuple(sorted(req_domains))
            d_score = domain_scores_map.get(key, 0.0)
            
        # FILTER: Strict Cutoff (Reject < 0.3)
        if d_score >= 0.3:
            prog['_domain_score'] = d_score
            survivors_layer_2.append(prog)
            
            # Prep text for Layer 3
            p_name = prog.get('program_name', '')
            p_sum = prog.get('course_content_summary', '')
            program_texts.append(f"Master in {p_name}. {p_sum}")

    count_l2 = len(survivors_layer_2)
    dropped_l2 = count_l1 - count_l2
    print(f"✅ L2 Survivors: {count_l2} (Dropped {dropped_l2} unrelated degrees)")

    if not survivors_layer_2:
        print("❌ Funnel ended at Layer 2.")
        return {"eligible_programs": []}

    # =========================================================
    # 🔍 LAYER 3: SEMANTIC RANKING (The Matchmaker)
    # =========================================================
    print(f"\n--- Layer 3: Running Semantic Ranking ---")
    
    program_vectors = safe_batch_embed(program_texts, batch_size=50)
    
    ranked_candidates = []
    for i, prog in enumerate(survivors_layer_2):
        sem_score = 0.5
        if user_vector and i < len(program_vectors):
             sem_score = calculate_semantic_match(user_vector, program_vectors[i])
        
        prog['_semantic_score'] = sem_score
        
        # Weighted Score for Layer 3 (70% Semantic, 30% Degree Strength)
        prelim_score = (sem_score * 0.7) + (prog['_domain_score'] * 0.3)
        
        # Relevance Threshold
        if prelim_score > 0.4:
            ranked_candidates.append(prog)
            
    # Sort and take Top 20
    ranked_candidates.sort(key=lambda x: x['_semantic_score'], reverse=True)
    top_candidates = ranked_candidates[:20]

    count_l3 = len(top_candidates)
    dropped_l3 = len(ranked_candidates) - count_l3
    print(f"✅ L3 Top Candidates: {count_l3} selected for Deep Scan (from {len(ranked_candidates)} relevant matches)")

    # =========================================================
    # 🔬 LAYER 4: DEEP ECTS VERIFICATION (The Auditor)
    # =========================================================
    print(f"\n--- Layer 4: Running Deep ECTS Verification ---")
    
    final_results = []
    for prog in top_candidates:
        if student_course_vectors:
            ects_check = check_ects_match_with_embeddings(student_course_vectors, student_courses, prog)
        else:
            ects_check = {'eligible': True, 'score': 0.5, 'details': "Transcript missing"}

        # Final Scoring
        final_score = (prog['_semantic_score'] * 0.6) + (ects_check['score'] * 0.3) + (prog['_domain_score'] * 0.1)
        
        prog['relevance_score'] = round(final_score * 10, 1)
        prog['llm_reasoning'] = (
            f"Degree: {int(prog['_domain_score']*100)}% | "
            f"Semantic: {int(prog['_semantic_score']*100)}% | "
            f"ECTS: {ects_check['details']}"
        )
        final_results.append(prog)

    # Final Sort
    final_ranked = sorted(final_results, key=lambda x: x['relevance_score'], reverse=True)
    
    print(f"🏁 DONE: Returning {len(final_ranked)} programs.")
    print("="*60 + "\n")
    
    return {"eligible_programs": final_ranked, "ranked_programs": final_ranked[:10]}