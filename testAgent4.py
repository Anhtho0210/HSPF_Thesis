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
       - **Document Checklist**: List ONLY the actual DOCUMENTS/FILES that applicants must submit or upload.
         These are the physical items to prepare (e.g., "Passport copy", "CV/Resume", "Bachelor's degree certificate", 
         "Official transcripts", "English language certificate", "Motivation letter", "Passport photo", etc.).
         DO NOT include eligibility criteria or program requirements (like "grade 2.5 or better" or "degree in Computer Science").
         DO NOT include country-specific documents here (like APS certificate).
       - **Country-Specific**: Check if there are ADDITIONAL special requirements for {citizenship} specifically 
         (e.g., APS Certificate for Vietnam/India/China, specific language waivers, notarization rules).
         List these separately from the standard documents.
    
    CRITICAL DISTINCTIONS:
    - "document_checklist" = Physical DOCUMENTS to submit that apply to ALL international applicants 
      (passport, transcripts, certificates, CV, motivation letter, etc.)
    - "country_specific_requirement" = ADDITIONAL requirements ONLY for {citizenship} (e.g., APS certificate)
    - DO NOT mix program admission requirements (eligibility criteria like GPA thresholds) with the document checklist
    
    Return JSON structure:
    {{
      "official_url": "The URL you found",
      "deadline_non_eu": "YYYY-MM-DD or 'July 15 (Annual)'",
      "tuition_fee_eur": "1500 or 0",
      "application_mode": "Uni-Assist / VPD / Direct",
      "country_specific_requirement": "String (e.g. 'APS certificate required' or 'None')",
      "document_checklist": ["Document 1", "Document 2", "Document 3"],
      "notes": "Any other critical info including program admission requirements/eligibility criteria"
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
    
    prog_name = "Master of E-Government"
    uni_name = "Koblenz University"
    
    # TEST CASE 1: VIETNAM (Should trigger APS)
    # print("--- TEST CASE 1: Vietnam ---")
    # data_vn = query_perplexity_search_and_extract(prog_name, uni_name, citizenship="Vietnam")
    # print(json.dumps(data_vn, indent=2))
    
    # print("\n" + "="*50 + "\n")

    # TEST CASE 2: INDIA (Should trigger APS)
    print("--- TEST CASE 2: INDIA ---")
    data_in = query_perplexity_search_and_extract(prog_name, uni_name, citizenship="India")
    print(json.dumps(data_in, indent=2))
    
