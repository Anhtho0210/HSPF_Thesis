# Agent4.py
import os
import json
import requests
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from models import AgentState

load_dotenv()

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

def query_perplexity(program_name: str, uni_name: str) -> Dict[str, Any]:
    """
    Sends a specific research query to Perplexity API to get live data.
    """
    if not PERPLEXITY_API_KEY:
        print("❌ Error: PERPLEXITY_API_KEY not found.")
        return {}

    # 1. Construct a precise prompt for Vietnamese/Non-EU context
    system_prompt = (
        "You are a University Admissions Verifier. "
        "Your goal is to extract current, factual application data for a Master's program in Germany. "
        "The applicant is from VIETNAM (Non-EU). "
        "Output ONLY valid JSON. No markdown formatting."
    )

    user_prompt = f"""
    Research the following program:
    - Program: {program_name}
    - University: {uni_name}

    Find the following details for the UPCOMING intake (likely Winter Semester 2025/2026):
    1. 'deadline_date': The specific deadline date for Non-EU applicants (Format: YYYY-MM-DD or 'Unknown').
    2. 'tuition_fees': The tuition fee amount per semester in EUR for international students (specifically check if Baden-Württemberg fees of 1500 EUR apply).
    3. 'application_mode': Does it require 'Uni-Assist', 'VPD', or is it 'Direct' to the university?
    4. 'notes': Any crucial warning (e.g., 'Requires APS certificate', 'Requires GMAT').

    Return a JSON object with keys: deadline_date, tuition_fees, application_mode, notes.
    """

    payload = {
        "model": "sonar-pro", # Or 'sonar' for faster/cheaper, 'sonar-reasoning' for deep research
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0
    }

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(PERPLEXITY_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        # Parse content
        result_text = response.json()['choices'][0]['message']['content']
        
        # Clean up Markdown if Perplexity adds it (e.g. ```json ... ```)
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
            
        return json.loads(result_text.strip())

    except Exception as e:
        print(f"  [Agent 4] Perplexity Error for {program_name}: {e}")
        return {}

def agent_4_verifier_node(state: AgentState) -> Dict[str, Any]:
    print("\n" + "="*60)
    print("🕵️‍♂️ [Node: Agent 4] Verifying Top Programs with Perplexity")
    print("="*60)

    ranked_programs = state.get("ranked_programs", [])
    
    # Cost Control: Only verify the Top 3 programs
    top_candidates = ranked_programs[:3] 
    
    verified_programs = []

    for prog in top_candidates:
        p_name = prog.get("program_name")
        u_name = prog.get("university_name")
        
        print(f"  > Researching: {p_name} @ {u_name}...")
        
        # Call Perplexity
        live_data = query_perplexity(p_name, u_name)
        
        if live_data:
            print(f"    ✅ Found Data: {live_data}")
            # Update the program object with a new 'verified_data' field
            prog["verified_data"] = live_data
            
            # Optional: Overwrite old data if you trust Perplexity more
            # if live_data.get('deadline_date') != 'Unknown':
            #     prog['deadlines']['winter_semester']['non_eu_applicants']['end_date'] = live_data['deadline_date']
        else:
            print("    ⚠️ No data found or parse error.")
            prog["verified_data"] = {"status": "verification_failed"}

        verified_programs.append(prog)
        time.sleep(1) # Polite rate limiting

    # Merge verified programs back into the main list
    # (Keep the unverified ones at the bottom if you want, or just return top 3)
    final_list = verified_programs + ranked_programs[3:]

    return {"ranked_programs": final_list}