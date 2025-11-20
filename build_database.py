# build_database.py

import json
import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import the updated Schema
from models import ProgramHardFilters

load_dotenv()

LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.0,
    api_key=os.environ.get("GEMINI_API_KEY")
)

def get_extraction_chain():
    parser = JsonOutputParser(pydantic_object=ProgramHardFilters)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert German University Data Extractor.
        
        YOUR TASK: Convert raw university data into a structured database format.
        
        RULES:
        1. RULES FOR ECTS (CRITICAL: CAPTURE ALL DOMAINS) ###
        Scan the text for **EVERY** major/group credit category. Do not stop after the first one.
        
        - Explicit Groups
        Input: "Mathematical-physical basics (38 CP): Math (16), Stats (3)"
        Output:
        {{
            "domain_name": "Mathematical-physical basics",
            "min_ects_total": 38,
            "condition_comment": null,
            "modules": [
                {{ "subject_area": "Mathematics", "min_ects": 16 }},
                {{ "subject_area": "Statistics", "min_ects": 3 }}
            ]
        }}

       - Selection / Options
        Input: "Civil Engineering (80 CP), whereof at least 20 CP each must be demonstrated from two of the areas listed below:
        - Constructive engineering
        - Water management
        - Construction operations and geotechnics
        - Transportation"
        Output:
        {{
            "domain_name": "Civil Engineering",
            "min_ects_total": 80,
            "condition_comment": "at least 20 CP each from 2 of: Constructive, Water, Geotechnics, Transport",
            "modules": [
                {{ "subject_area": "Constructive engineering", "min_ects": 20 }},
                {{ "subject_area": "Water management", "min_ects": 20 }},
                {{ "subject_area": "Construction operations and geotechnics", "min_ects": 20 }},
                {{ "subject_area": "Transportation", "min_ects": 20 }}
            ]
        }}
           
        2. **English Level**: STANDARDIZE to CEFR (B2, C1).
           - IELTS 6.0 or 6.5 -> "B2"
           - IELTS 7.0+ -> "C1"
           - TOEFL 80-94 -> "B2"
           - TOEFL 95+ -> "C1"
           - If text says "fluent" or "good" without scores -> Output "B2"
           - If text says "excellent" or "proficient" -> Output "C1"
           
        3. **Application Mode**:
           - "VPD" or "Vorprüfungsdokumentation" -> "VPD"
           - "Uni-Assist" -> "Uni-Assist"
           - "Direct" / "Online Portal" -> "Direct"
           - "Unknown" if ambiguous
           
        4. **Fees**: 
           - "Tuition Fee" is usually 0 for public unis. 
           - "Semester Contribution" is usually 100-400 EUR. Separate them.

        5. **GPA**: Look for "German grading system". If it says "2.5 or better", output 2.5. If not found, return null.
        6. **Location**: Infere the 'State' (Bundesland) based on the City
        
        7.CRITICAL INSTRUCTION FOR DEADLINES ###
        You must populate the 'deadlines' object. Do not leave it null.
        Scan the 'Deadlines Text' for Winter and Summer dates.
        
        **Rule 1: Defaults**
        - If text says "July 15" with no start date, set 'end_date': "July 15" and 'start_date': null.
        - If text says "Apply from May 1 to July 15", set 'start_date': "May 1", 'end_date': "July 15".
        - If no Winter and Summer is specified, apply the date between September to March to Summer, otherwise to Winter.
        
        **Rule 2: Citizen Groups**
        - "Non-EU", "International", "Third Country" -> map to 'non_eu_applicants'
        - "EU", "German", "Bildungsinländer" -> map to 'eu_applicants'
        - If no group is specified, apply the dates to BOTH Citizen Groups.

        8.RULES FOR STANDARDIZED TESTS:
        - **Identify**: Look for "GRE" or "GMAT".
        - **Condition**: Check if it says "for non-EU applicants" or "applicants from non-member states".
           - If yes -> set 'target_group': "Non-EU"
           - If no condition mentioned -> set 'target_group': "All"
        - **Score**: Extract minimum score if available (IF it minimum score is specific for each section, just leave it empty)
        
        Example Output:
        "required_standardized_tests": [
            {{ "test_name": "GRE", "target_group": "Non-EU", "min_score": 155 }}
        ]

        9.RULES FOR EXPERIENCE:
        - "1 year work experience" -> min_work_experience_months: 12
        - "Internship required" -> requires_internship: true
        
        **EXAMPLE OF DESIRED OUTPUT STRUCTURE:**
        {{
            "deadlines": {{
                "winter_semester": {{
                    "non_eu_applicants": {{ "start_date": "Feb 1", "end_date": "May 31" }},
                    "eu_applicants": {{ "start_date": "May 1", "end_date": "July 15" }}
                }},
                "summer_semester": null
            }},
            ... other fields
        }}
        

        {format_instructions}
        """),
        ("user", """
        Raw Program Data:
        Name: {name}
        Institution: {institution}
        Submit To: {submit_to}
        Admission Text: {admission_req}
        Language Text: {language_req}
        Deadlines Text: {application_deadline}  
        Fees Text: {tuition_fee} | {semester_fee}
        Description: {description}
        City: {city}
        """)
    ])
    
    return prompt | LLM | parser

def process_catalog(input_file="TESTING_MASTER_LIST_10.json", output_file="structured_program_db.json"):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        print(f"Loaded {len(raw_data)} raw programs.")
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found. Run the crawler first.")
        return

    chain = get_extraction_chain()
    # We create a dummy object just to get the instructions format
    format_instructions = JsonOutputParser(pydantic_object=ProgramHardFilters).get_format_instructions()
    
    structured_programs = []

    print("Starting LLM Processing... (Press Ctrl+C to stop safely)")

    for i, program in enumerate(raw_data):
        try:
            print(f"[{i+1}/{len(raw_data)}] Extracting: {program.get('name', 'Unknown')}...")
            
            # 1. Call LLM
            result_dict = chain.invoke({
                "name": program.get("name", ""),
                "institution": program.get("institution", ""),
                "submit_to": program.get("submit_to", ""),
                "admission_req": program.get("admission_req", ""),
                "language_req": program.get("language_req", ""),
                "application_deadline": program.get("application_deadline", ""), # Passing the raw text
                "description": program.get("description", ""),
                "tuition_fee": program.get("tuition_fee", ""),
                "semester_fee": program.get("semester_fee", ""),
                "city": program.get("city", ""),
                "format_instructions": format_instructions
            })
            
            # 2. Validate
            validated_program = ProgramHardFilters(**result_dict)
            
            # 3. Add Metadata
            validated_program.program_id = program.get("program_id", f"prog_{i}")
            
            # 4. Dump
            final_record = validated_program.model_dump()
            final_record['url'] = program.get("url")

            structured_programs.append(final_record)
            
            # Rate Limit Sleep
            time.sleep(4) 

        except Exception as e:
            print(f"  ⚠️ Error on item {i}: {e}")
            continue

    # Save
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structured_programs, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Success! Database saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    process_catalog()