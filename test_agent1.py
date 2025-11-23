# test_agent1.py
import os
from dotenv import load_dotenv
from models import AgentState

# Import ONLY Agent 1 functions
from Agent1 import parse_profile_node, get_missing_fields

# Load environment variables (API Keys)
load_dotenv()

def run_test():
    print("🧪 STARTING AGENT 1 ISOLATION TEST...")

    # 1. Define a Mock State (What Agent 1 expects)
    # We simulate a user who just uploaded a transcript and said "Hi".
    test_state: AgentState = {
        "user_intent": "Hi, I am Anny. I want to apply for Data Science masters. I have 3 years of work experience.",
        "pdf_path": "Anny_Transcript.pdf", # <--- Make sure you have a dummy PDF with this name, or set to None
        "user_profile": None,
        "program_catalog": [],
        "eligible_programs": [],
        "ranked_programs": []
    }

    # 2. Run the Extraction Node
    # This will trigger PDF reading + LLM extraction + ECTS conversion
    result = parse_profile_node(test_state)
    
    # 3. Check the Output
    profile = result.get("user_profile")
    
    if profile:
        print("\n✅ AGENT 1 SUCCESS!")
        print("-------------------------------------------------")
        print(f"Name: {profile.full_name}")
        
        if profile.academic_background:
            print(f"Bachelor: {profile.academic_background.bachelor_field_of_study}")
            # Check if bachelor_gpa exists before asking for score_german
            if profile.academic_background.bachelor_gpa:
                print(f"German GPA: {profile.academic_background.bachelor_gpa.score_german}")
            else:
                print("German GPA: Not found in text")
            print(f"Calculated ECTS Factor: {profile.academic_background.ects_conversion_factor}")
            
            print("\n--- Extracted Courses (First 3) ---")
            for course in profile.academic_background.transcript_courses[:3]:
                print(f"- {course.course_name}: {course.original_credits} Credits -> {course.converted_ects} ECTS")
        
        print("-------------------------------------------------")
        
        # 4. Check Missing Data Logic
        missing = get_missing_fields(profile)
        if missing:
            print(f"⚠️ Missing Data Detected: {missing}")
            # Optional: Test the chat node
            # from Agent1 import conversational_chat_node
            # chat_response = conversational_chat_node(test_state | result)
            # print(f"Agent would ask: {chat_response['ai_response']}")
        else:
            print("🎉 Profile is COMPLETE for matching!")

    else:
        print("❌ Agent 1 failed to generate a profile.")

if __name__ == "__main__":
    # Create a dummy PDF if it doesn't exist to avoid errors
    if not os.path.exists("Anny_Transcript.pdf"):
        print("⚠️ 'Anny_Transcript.pdf' not found. creating a dummy file...")
        from reportlab.pdfgen import canvas
        c = canvas.Canvas("Anny_Transcript.pdf")
        c.drawString(100, 750, "TRANSCRIPT OF RECORDS")
        c.drawString(100, 730, "Student: Anny Tran")
        c.drawString(100, 710, "Program: Electronic Commerce (4 Years)")
        c.drawString(100, 690, "Total Credits Earned: 130")
        c.drawString(100, 670, "Cumulative GPA: 8.0 / 10.0 (Min Pass: 5.0)")
        c.drawString(100, 650, "1. Advanced Mathematics - 4.0 Credits - Grade 8.0")
        c.drawString(100, 630, "2. Introduction to CS - 3.0 Credits - Grade 9.0")
        c.drawString(100, 610, "3. Database Systems - 3.0 Credits - Grade 8.5")
        c.save()
        
    run_test()