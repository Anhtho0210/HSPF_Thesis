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

def query_perplexity_search_and_extract(
    program_name: str, 
    uni_name: str, 
    citizenship: str = "Non-EU",
    deadline_info: str = "Not specified",
    tuition_fee: float = 0.0,
    application_mode: str = "Unknown",
    preferred_semester: str = "Winter"
) -> Dict[str, Any]:
    """
    Queries Perplexity to extract country-specific requirements and required documents.
    Uses existing program data (deadline, tuition, application mode) from the database.
    """
    if not PERPLEXITY_API_KEY:
        print("❌ Error: PERPLEXITY_API_KEY not found.")
        return {}

    # --- DYNAMIC PROMPT ---
    system_prompt = (
        "You are an expert University Admissions Researcher. "
        "Your goal is to find the OFFICIAL University website for a specific Master's degree "
        f"and extract precise application data for a student from '{citizenship}'. "
        "Output ONLY valid JSON."
    )

    user_prompt = f"""
    TARGET: Master's in "{program_name}" at "{uni_name}".
    APPLICANT ORIGIN: {citizenship}
    PREFERRED START SEMESTER: {preferred_semester}
    
    KNOWN INFORMATION (from database):
    - Application Deadline: {deadline_info}
    - Tuition Fee: €{tuition_fee} per semester
    - Application Mode: {application_mode}

    INSTRUCTIONS:
    1. SEARCH: Find the OFFICIAL "Admission Regulations" (Zulassungsordnung) or "Application Requirements" page.
    2. FOCUS ON: Extract ONLY the following information:
       
       A. **Country-Specific Requirements for {citizenship}**:
          * CRITICAL RULE: If {citizenship} is **China**, **Vietnam**, or **India**, you MUST check for "APS" (Akademische Prüfstelle) certificate requirement.
          * PAKISTAN RULE: If {citizenship} is **Pakistan**, check if "HEC Attestation" or "Embassy Verification" is mentioned (but do NOT ask for APS).
          * Check for additional requirements such as GMAT, GRE, or other standardized tests specifically for {citizenship} or non-EU countries.
          * FALLBACK: If the website is silent but the student is from China/Vietnam/India, output: "APS Certificate (Standard Federal Requirement)".
          * If no country-specific requirements exist, output: "None".
       
       B. **Document Checklist**: A COMPLETE list of PDF documents required for the APPLICATION phase.
          * FILTER: Extract ONLY documents for **APPLICATION** (Admission). EXCLUDE **ENROLLMENT** documents (e.g., Health Insurance, Semester Fee confirmation).
          * CHECK SPECIFICALLY: Does the university require a Completed Online Application Form (do online/fill out/printout)? If yes, YOU MUST INCLUDE IT.
          * INCLUDE administrative basics: "Passport Copy", "CV", "Motivation Letter" if mentioned.
          * STANDARDIZE NAMES: Use "Bachelor Certificate" instead of "Proof of first degree". Use "Transcript of Records" instead of "Overview of grades".
          * HANDLING OPTIONAL ITEMS: If a document (e.g. GMAT, GRE, Portfolio) is listed as "Selection Criteria", "Recommended", or "Bonus Points" (not strictly mandatory), **append "(Optional)" to the name**.
          * Example: "GMAT Result (Optional)" instead of "GMAT Result".
          * Keep it clean: Max 10 words per item.
       
       C. **Notes**: Extract ONLY rules related to **Document Formats/Logistics**.
          * KEEP: "Official notarized translations required", "Send hard copies by post", "Upload limit 5MB".
          * REMOVE: Admission requirements (e.g. "Needs 2.5 GPA", "Needs 18 ECTS in Math").
          * REMOVE: General program info or deadlines (already provided above).
          * MAX LENGTH: 2 sentences.
    
    Return JSON structure:
    {{
      "official_url": "The official program URL you found",
      "country_specific_requirement": "String (e.g. 'APS certificate required; GRE (Quantitative 164+) required' or 'None')",
      "document_checklist": ["Document 1", "Document 2", "GMAT (Optional)", ...],
      "notes": "Document format/logistics rules only"
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
        print(f"  🔍 Searching country-specific requirements for {program_name} at {uni_name}...")
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
    Uses existing program data (deadline, tuition, application mode) from the database.
    """
    
    print("\n" + "=" * 60)
    print("🎯 AGENT 4: DOCUMENT CHECKLIST GENERATOR")
    print("=" * 60)
    
    ranked_programs = state.get("ranked_programs", [])
    user_profile: UserProfile = state.get("user_profile")
    
    if not ranked_programs:
        print("❌ No ranked programs found. Agent 4 cannot proceed.")
        return state
    
    # Get user citizenship
    if not user_profile or not user_profile.citizenship:
        print("❌ User citizenship not found. Using 'Vietnam' as default.")
        citizenship = "Vietnam"
    else:
        citizenship = user_profile.citizenship.country_of_citizenship or "Vietnam"
    
    # Get user's preferred semester
    preferred_semester = "Winter"
    if user_profile and user_profile.preferences and user_profile.preferences.preferred_start_semester:
        preferred_semester = user_profile.preferences.preferred_start_semester
    
    print(f"\n📋 User Info: Citizenship = {citizenship}, Preferred Semester = {preferred_semester}")
    
    # Determine how many programs to select (up to 3, or all if fewer)
    max_selections = min(3, len(ranked_programs))
    
    # Ask user to select programs
    print("\n" + "=" * 60)
    if max_selections == 1:
        print(f"Only 1 program available. It will be automatically selected.")
        selected_indices = [0]
    else:
        print(f"Please select up to {max_selections} programs by entering their numbers (e.g., 1 2 3)")
        print(f"You can select between 1 and {max_selections} programs.")
        print("=" * 60)
        
        selected_indices = []
        while len(selected_indices) == 0:
            try:
                user_input = input(f"\n👤 Enter 1-{max_selections} program numbers separated by spaces: ").strip()
                selected_indices = [int(x) - 1 for x in user_input.split()]
                
                if len(selected_indices) == 0:
                    print(f"❌ Please select at least 1 program.")
                    continue
                
                if len(selected_indices) > max_selections:
                    print(f"❌ Please select at most {max_selections} programs. You selected {len(selected_indices)}.")
                    selected_indices = []
                    continue
                
                # Validate indices
                if any(idx < 0 or idx >= len(ranked_programs) for idx in selected_indices):
                    print(f"❌ Invalid program number(s). Please choose between 1 and {len(ranked_programs)}.")
                    selected_indices = []
                    continue
                    
            except ValueError:
                print(f"❌ Invalid input. Please enter numbers only (e.g., 1 2 3)")
                selected_indices = []
    
    print(f"\n✅ Selected {len(selected_indices)} program(s)")
    
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
        
        # Extract deadline, tuition, and application mode from program data
        tuition_fee = program.get("tuition_fee_per_semester_eur", 0.0)
        application_mode = program.get("application_mode", "Unknown")
        
        # Determine deadline based on preferred semester and citizenship
        deadline_info = "Not specified"
        deadlines = program.get("deadlines", {})
        
        # Determine which semester to use
        semester_key = "winter_semester" if "winter" in preferred_semester.lower() else "summer_semester"
        semester_deadlines = deadlines.get(semester_key)
        
        if semester_deadlines:
            # Determine EU vs Non-EU
            is_eu = citizenship in ["Germany", "France", "Italy", "Spain", "Netherlands", "Belgium", "Austria", "Sweden", "Denmark", "Finland", "Poland", "Czech Republic", "Hungary", "Romania", "Bulgaria", "Greece", "Portugal", "Ireland", "Croatia", "Slovenia", "Slovakia", "Lithuania", "Latvia", "Estonia", "Cyprus", "Malta", "Luxembourg"]
            
            applicant_type = "eu_applicants" if is_eu else "non_eu_applicants"
            deadline_window = semester_deadlines.get(applicant_type)
            
            if deadline_window and deadline_window.get("end_date"):
                deadline_info = deadline_window.get("end_date")
        
        print(f"  📅 Deadline ({preferred_semester}): {deadline_info}")
        print(f"  💰 Tuition Fee: €{tuition_fee}/semester")
        print(f"  📝 Application Mode: {application_mode}")
        
        # Query Perplexity for country-specific requirements and documents
        checklist_data = query_perplexity_search_and_extract(
            program_name=program_name,
            uni_name=uni_name,
            citizenship=citizenship,
            deadline_info=deadline_info,
            tuition_fee=tuition_fee,
            application_mode=application_mode,
            preferred_semester=preferred_semester
        )
        
        if checklist_data:
            # Merge checklist data with program info (including deadline, tuition, application mode)
            program_with_checklist = {
                **program,  # Keep all original program data
                "checklist_data": {
                    **checklist_data,
                    # Add the program data we already have
                    "deadline": deadline_info,
                    "tuition_fee_eur": tuition_fee,
                    "application_mode": application_mode,
                    "preferred_semester": preferred_semester
                }
            }
            selected_programs_with_checklists.append(program_with_checklist)
            
            # Display checklist
            print(f"\n✅ Checklist generated successfully!")
            print(f"   🔗 Official URL: {checklist_data.get('official_url', 'N/A')}")
            print(f"   📅 Deadline ({preferred_semester}): {deadline_info}")
            print(f"   💰 Tuition Fee: €{tuition_fee} per semester")
            print(f"   📝 Application Mode: {application_mode}")
            
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
            # Still add program with basic info even if Perplexity fails
            program_with_checklist = {
                **program,
                "checklist_data": {
                    "deadline": deadline_info,
                    "tuition_fee_eur": tuition_fee,
                    "application_mode": application_mode,
                    "preferred_semester": preferred_semester
                }
            }
            selected_programs_with_checklists.append(program_with_checklist)
    
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
            semester_label = checklist_data.get('preferred_semester', 'Winter')
            print(f"   📅 Deadline ({semester_label}): {checklist_data.get('deadline', 'N/A')}")
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