import os
import json
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from models import AgentState, UserProfile

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
        print(f"  🔍 Searching application requirements for {program_name} at {uni_name}...")
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
        print(f"  ❌ Error querying Perplexity API: {e}")
        return {}


def agent_4_checklist_node(state: AgentState) -> AgentState:
    """
    Agent 4: Document Checklist Generator
    
    This agent:
    1. Takes the ranked programs from Agent 3
    2. Asks the user to select their top 3 programs
    3. Generates a detailed document checklist for each selected program
    """
    
    print("\n" + "=" * 60)
    print("🎯 AGENT 4: DOCUMENT CHECKLIST GENERATOR")
    print("=" * 60)
    
    ranked_programs = state.get("ranked_programs", [])
    user_profile: UserProfile = state.get("user_profile")
    
    if not ranked_programs:
        print("❌ No ranked programs found. Agent 4 cannot proceed.")
        return state
    
    if not user_profile or not user_profile.citizenship:
        print("❌ User citizenship not found. Using 'Non-EU' as default.")
        citizenship = "Non-EU"
    else:
        citizenship = user_profile.citizenship.country_of_citizenship or "Non-EU"
    
    # Ask user to select top 3 programs (programs already displayed in main.py)
    print("\n" + "=" * 60)
    print("Please select your TOP 3 programs by entering their numbers (e.g., 1 3 5)")
    print("=" * 60)
    
    selected_indices = []
    while len(selected_indices) != 3:
        try:
            user_input = input("\n👤 Enter 3 program numbers separated by spaces: ").strip()
            selected_indices = [int(x) - 1 for x in user_input.split()]
            
            if len(selected_indices) != 3:
                print(f"❌ Please select exactly 3 programs. You selected {len(selected_indices)}.")
                selected_indices = []
                continue
            
            # Validate indices
            if any(idx < 0 or idx >= len(ranked_programs) for idx in selected_indices):
                print(f"❌ Invalid program number(s). Please choose between 1 and {len(ranked_programs)}.")
                selected_indices = []
                continue
                
        except ValueError:
            print("❌ Invalid input. Please enter numbers only (e.g., 1 3 5)")
            selected_indices = []
    
    # Generate checklists for selected programs
    print("\n" + "=" * 60)
    print("🔍 GENERATING DOCUMENT CHECKLISTS")
    print("=" * 60)
    
    selected_programs_with_checklists = []
    
    for idx in selected_indices:
        program = ranked_programs[idx]
        program_name = program.get("program_name", "Unknown Program")
        uni_name = program.get("university_name", "Unknown University")
        
        print(f"\n📌 Processing: {program_name} at {uni_name}")
        print("-" * 60)
        
        # Query Perplexity for checklist
        checklist_data = query_perplexity_search_and_extract(
            program_name=program_name,
            uni_name=uni_name,
            citizenship=citizenship
        )
        
        if checklist_data:
            # Merge checklist data with program info
            program_with_checklist = {
                **program,  # Keep all original program data
                "checklist_data": checklist_data
            }
            selected_programs_with_checklists.append(program_with_checklist)
            
            # Display checklist
            print(f"\n✅ Checklist generated successfully!")
            print(f"   🔗 Official URL: {checklist_data.get('official_url', 'N/A')}")
            print(f"   📅 Deadline (Non-EU): {checklist_data.get('deadline_non_eu', 'N/A')}")
            print(f"   💰 Tuition Fee: €{checklist_data.get('tuition_fee_eur', 0)} per semester")
            print(f"   📝 Application Mode: {checklist_data.get('application_mode', 'N/A')}")
            
            country_req = checklist_data.get('country_specific_requirement', 'None')
            if country_req and country_req != 'None':
                print(f"   🌍 Country-Specific Requirement: {country_req}")
            
            print(f"\n   📋 Required Documents:")
            for doc in checklist_data.get('document_checklist', []):
                print(f"      • {doc}")
            
            notes = checklist_data.get('notes', '')
            if notes:
                print(f"\n   💡 Notes: {notes}")
        else:
            print(f"   ⚠️  Could not retrieve checklist data.")
            selected_programs_with_checklists.append(program)
    
    # Save results to state
    state["selected_programs_with_checklists"] = selected_programs_with_checklists
    
    # Final summary of selected programs
    print("\n" + "=" * 60)
    print("✅ YOUR SELECTED PROGRAMS")
    print("=" * 60)
    
    for i, program in enumerate(selected_programs_with_checklists, 1):
        print(f"\n{i}. {program.get('program_name')}")
        print(f"   🏛️  {program.get('university_name')}")
        print(f"   📊 Match Score: {program.get('relevance_score', 'N/A')}")
        
        checklist_data = program.get('checklist_data')
        if checklist_data:
            print(f"   📅 Deadline (Non-EU): {checklist_data.get('deadline_non_eu', 'N/A')}")
            print(f"   💰 Tuition: €{checklist_data.get('tuition_fee_eur', 0)}/semester")
            print(f"   📝 Application Mode: {checklist_data.get('application_mode', 'N/A')}")
            
            country_req = checklist_data.get('country_specific_requirement', 'None')
            if country_req and country_req != 'None':
                print(f"   🌍 Special Requirement: {country_req}")
            
            print(f"   📋 Documents Required: {len(checklist_data.get('document_checklist', []))} items")
            print(f"   🔗 More info: {checklist_data.get('official_url', 'N/A')}")
        else:
            print(f"   ⚠️  Checklist data unavailable")
        print("-" * 60)
    
    print("\n" + "=" * 60)
    print("💡 TIP: Review the detailed checklists above to prepare your applications!")
    print("=" * 60)
    
    return state