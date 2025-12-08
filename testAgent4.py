import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

def query_perplexity_search_and_extract(program_name: str, uni_name: str, citizenship: str = "Non-EU") -> Dict[str, Any]:
    """
    Finds official data for ANY international student.
    DYNAMICALLY adjusts checks based on 'citizenship'.
    """
    if not PERPLEXITY_API_KEY:
        print("❌ Error: PERPLEXITY_API_KEY not found.")
        return {}

    # --- DYNAMIC PROMPT ---
    system_prompt = (
        "You are an expert University Admissions Researcher. "
        "Your goal is to find the OFFICIAL University website for a specific Master's degree "
        f"and extract precise application data for a student from '{citizenship}' (Non-EU status). "
        "Output ONLY valid JSON."
    )

    user_prompt = f"""
    TARGET: Master's in "{program_name}" at "{uni_name}".
    APPLICANT ORIGIN: {citizenship}

    INSTRUCTIONS:
    1. SEARCH: Find the OFFICIAL degree page on the university's own domain (e.g. ending in .de). Ignore DAAD.
    2. LOCATE: Look for 'Application', 'International Students', or 'Requirements' sections.
    3. EXTRACT:
       - **Deadline**: Specific date for Non-EU/International applicants for the upcoming Winter Semester. 
         (If exact 2025 date is missing, provide the standard annual rule, e.g. 'Always July 15').
       - **Tuition**: Check for tuition fees (especially the ~1500 EUR/semester for Baden-Württemberg universities).
       - **Portal**: Is it 'Uni-Assist', 'VPD', or 'Direct'?
       - **Documents**: List mandatory docs (CV, Transcript, etc.).
       - **Country-Specific**: Check if there are special requirements for {citizenship} (e.g., APS Certificate, specific language waivers, notarization rules).
    
    Return JSON structure:
    {{
      "official_url": "The URL you found",
      "deadline_non_eu": "YYYY-MM-DD or 'July 15 (Annual)'",
      "tuition_fee_eur": "1500 or 0",
      "application_mode": "Uni-Assist / VPD / Direct",
      "country_specific_requirement": "String (e.g. 'APS required' or 'None')",
      "document_checklist": ["Item 1", "Item 2"],
      "notes": "Any other critical info"
    }}
    """

    payload = {
        "model": "sonar-pro", 
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
        print(f"  ...  Hunting data for {program_name} ({citizenship} Student)...")
        response = requests.post(PERPLEXITY_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        result_text = response.json()['choices'][0]['message']['content']
        
        # Clean Markdown
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
            
        return json.loads(result_text.strip())

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {}

# --- TEST RUNNER ---
if __name__ == "__main__":
    
    prog_name = "Management and Economics"
    uni_name = "University of Tübingen"
    
    # TEST CASE 1: VIETNAM (Should trigger APS)
    print("--- TEST CASE 1: USA ---")
    data_vn = query_perplexity_search_and_extract(prog_name, uni_name, citizenship="USA")
    print(json.dumps(data_vn, indent=2))
    
    print("\n" + "="*50 + "\n")

    # TEST CASE 2: INDIA (Should trigger APS)
    # print("--- TEST CASE 2: INDIA ---")
    # data_in = query_perplexity_search_and_extract(prog_name, uni_name, citizenship="India")
    # print(json.dumps(data_in, indent=2))
    
    # TEST CASE 3: USA (Should NOT trigger APS, might trigger Language Waiver)
    # print("--- TEST CASE 3: USA ---")
    # data_us = query_perplexity_search_and_extract(prog_name, uni_name, citizenship="USA")
    # print(json.dumps(data_us, indent=2))