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
    1. SEARCH: Find the OFFICIAL "Admission Regulations" (Zulassungsordnung) or "Application Requirements" page.
    2. FILTER: 
       - Extract ONLY documents required for the **APPLICATION** (Admission) phase. 
       - EXCLUDE documents for **ENROLLMENT** (e.g., Health Insurance, Semester Fee confirmation).
    3. EXTRACT:
       - **Deadline**: Specific date for {citizenship} students base on EU, non-EU countries.
       - **Tuition Fee**: Total fees per semester in EUR (use 0 if none).
       - **Application Mode**: "Uni-Assist", "Direct", or "VPD".
       - **Country Specifics**: 
         * CHECK: Is {citizenship} listed as requiring specific documents?
         * CRITICAL RULE: If {citizenship} is **China**, **Vietnam**, or **India**, you MUST check for "APS" (Akademische Prüfstelle) 
         * **CRITICAL RULE:** check addtional requirement such as GMAT, GRE, ... for some specific countries or non-EU countries
         * **PAKISTAN RULE:** If {citizenship} is **Pakistan**, check if "HEC Attestation" or "Embassy Verification" is mentioned (but do NOT ask for APS).
         * **FALLBACK:** If the website is silent but the student is from China/Vietnam/India, do NOT say "None". Output: "APS Certificate (Standard Federal Requirement)".
       
    - **Document Checklist**: A COMPLETE list of PDF documents required for upload.
         * CRITICAL RULES for Checklist:
         * **INCLUDE administrative basics:** You MUST list "Passport Copy", "CV", and "Online Application Form" if they are mentioned.
         * **Standardize Names:** Use "Bachelor Certificate" instead of "Proof of first degree". Use "Transcript of Records" instead of "Overview of grades".
         * **Handling Selection Criteria:** If a document (e.g. GMAT, GRE, Portfolio) is listed as "Selection Criteria", "Recommended", or "Bonus Points" (not strictly mandatory for eligibility), **you MUST append "(Optional)" to the name.**
         * **Example:** Output "GMAT Result (Optional)" instead of just "GMAT Result".
         * **Keep it Clean:** Max 10 words per item.

    - **Notes**: Extract ONLY rules related to **Document Formats/Logistics**.
         * KEEP: "Official notarized translations required", "Send hard copies by post", "Upload limit 5MB".
         * REMOVE: Admission requirements (e.g. "Needs 2.5 GPA", "Needs 18 ECTS in Math"). 
         * REMOVE: General program info or deadlines (already listed above).
         * MAX LENGTH: 2 sentences.
    
    Return JSON structure:
    {{
      "official_url": "The URL you found",
      "deadline_eu": "YYYY-MM-DD or 'July 15 (Annual)'",
      "deadline_non_eu": "YYYY-MM-DD or 'July 15 (Annual)'",
      "tuition_fee_eur": number,
      "application_mode": "Uni-Assist / VPD / Direct",
      "country_specific_requirement": "String (e.g. 'APS certificate required' or 'None')",
      "document_checklist": ["Document 1", "Document 2", "GMAT (Optional), ..."],
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
    
    prog_name = "Master's in Finance, Accounting and Taxation"
    uni_name = "University of Mannheim"
    
    # TEST CASE 1: VIETNAM (Should trigger APS)
    print("--- TEST CASE 1: Vietnam ---")
    data_vn = query_perplexity_search_and_extract(prog_name, uni_name, citizenship="Vietnam")
    print(json.dumps(data_vn, indent=2))
    
    # print("\n" + "="*50 + "\n")

    # TEST CASE 2: INDIA (Should trigger APS)
    # print("--- TEST CASE 2: INDIA ---")
    # data_in = query_perplexity_search_and_extract(prog_name, uni_name, citizenship="China")
    # print(json.dumps(data_in, indent=2))
    
