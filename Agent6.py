import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from typing import Dict, Any

# --- HELPER: Text Wrapping ---
def draw_wrapped_text(c, text, x, y, max_width, line_height=12):
    if not text: return y
    words = text.split()
    line = ""
    for word in words:
        if c.stringWidth(line + word, "Helvetica", 10) < max_width:
            line += word + " "
        else:
            c.drawString(x, y, line)
            y -= line_height
            line = word + " "
    c.drawString(x, y, line)
    return y - line_height

# --- HELPER: Draw Matching Score Section ---
def draw_matching_section(c, y, program, user_profile, width):
    """Draw the 'Why This Matches You' section with scores and reasoning."""
    if y < 250:
        c.showPage()
        y = 750
    
    # Section header
    c.setFillColorRGB(0.2, 0.4, 0.8)  # Blue
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "🎯 WHY THIS PROGRAM MATCHES YOU")
    c.setFillColorRGB(0, 0, 0)
    y -= 20
    
    # Overall score
    relevance_score = program.get('relevance_score', 0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y, f"Overall Match Score: {relevance_score}/100")
    
    # Star rating
    stars = "⭐" * min(5, int(relevance_score / 20))
    c.drawString(220, y, stars)
    y -= 18
    
    # Score breakdown
    c.setFont("Helvetica", 10)
    c.drawString(55, y, "Breakdown:")
    y -= 15
    
    # Degree compatibility
    domain_score = program.get('_domain_score', 0) * 100
    c.drawString(65, y, f"📚 Degree Compatibility: {int(domain_score)}%")
    y = draw_score_bar(c, 250, y, domain_score, width-300)
    y -= 12
    
    # Interest alignment
    semantic_score = program.get('_semantic_score', 0) * 100
    c.drawString(65, y, f"🔍 Interest Alignment: {int(semantic_score)}%")
    y = draw_score_bar(c, 250, y, semantic_score, width-300)
    y -= 12
    
    # ECTS requirements
    ects_score = program.get('ects_score', 0) * 100
    ects_details = program.get('ects_details', 'N/A')
    c.drawString(65, y, f"📊 ECTS Requirements: {int(ects_score)}%")
    y = draw_score_bar(c, 250, y, ects_score, width-300)
    y -= 5
    
    # ECTS details
    if ects_details and ects_details != 'N/A':
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawString(75, y, f"Details: {ects_details}")
        c.setFillColorRGB(0, 0, 0)
        y -= 12
    else:
        y -= 8
    
    # Reasoning
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, "Why Agent3 Ranked This Program:")
    y -= 12
    
    c.setFont("Helvetica", 9)
    reasoning_points = [
        f"• Your {user_profile.academic_background.bachelor_field_of_study if user_profile and user_profile.academic_background else 'bachelor'} background matches the required degree domains",
        f"• Program content aligns with your interests and goals",
        f"• Your transcript shows {int(ects_score)}% coverage of required technical subjects"
    ]
    
    # Add GPA check if available
    if user_profile and user_profile.academic_background and user_profile.academic_background.bachelor_gpa:
        student_gpa = user_profile.academic_background.bachelor_gpa.score_german
        prog_min_gpa = program.get('min_gpa_german_scale')
        if student_gpa and prog_min_gpa:
            if student_gpa <= prog_min_gpa:
                reasoning_points.append(f"• Your GPA ({student_gpa}) meets the minimum requirement ({prog_min_gpa})")
    
    for point in reasoning_points:
        c.drawString(65, y, point)
        y -= 11
    
    y -= 10
    return y

# --- HELPER: Draw Score Bar ---
def draw_score_bar(c, x, y, score, max_width=200):
    """Draw a visual score bar."""
    bar_height = 8
    
    # Background (gray)
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(x, y-bar_height, max_width, bar_height, fill=1, stroke=0)
    
    # Filled portion (color based on score)
    filled_width = (score / 100) * max_width
    if score >= 80:
        c.setFillColorRGB(0.2, 0.7, 0.2)  # Green
    elif score >= 60:
        c.setFillColorRGB(0.8, 0.6, 0)    # Orange
    else:
        c.setFillColorRGB(0.8, 0.2, 0.2)  # Red
    
    c.rect(x, y-bar_height, filled_width, bar_height, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    
    return y - 3

# --- HELPER: Draw Requirements Section ---
def draw_requirements_section(c, y, program, user_profile, width):
    """Draw detailed program requirements with student's actual values."""
    if y < 300:
        c.showPage()
        y = 750
    
    # Section header
    c.setFillColorRGB(0.2, 0.4, 0.8)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "📋 PROGRAM REQUIREMENTS")
    c.setFillColorRGB(0, 0, 0)
    y -= 18
    
    # Academic Requirements
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, "Academic Requirements:")
    y -= 13
    
    c.setFont("Helvetica", 9)
    
    # GPA
    prog_min_gpa = program.get('min_gpa_german_scale')
    if prog_min_gpa:
        student_gpa = "N/A"
        status = ""
        if user_profile and user_profile.academic_background and user_profile.academic_background.bachelor_gpa:
            student_gpa = user_profile.academic_background.bachelor_gpa.score_german
            if student_gpa and student_gpa <= prog_min_gpa:
                status = " ✅"
            else:
                status = " ⚠️"
        
        c.drawString(65, y, f"• Minimum GPA: {prog_min_gpa} (German scale) → Your GPA: {student_gpa}{status}")
        y -= 11
    
    # Required degree
    req_degrees = program.get('required_degree_domains', [])
    if req_degrees:
        degrees_str = ", ".join(req_degrees[:3])
        if len(req_degrees) > 3:
            degrees_str += ", ..."
        c.drawString(65, y, f"• Required Degree: {degrees_str}")
        y -= 11
    
    # Minimum ECTS
    min_ects = program.get('min_degree_ects', 180)
    student_ects = "N/A"
    status = ""
    if user_profile and user_profile.academic_background:
        student_ects = user_profile.academic_background.total_converted_ects or "N/A"
        if student_ects != "N/A" and student_ects >= min_ects:
            status = " ✅"
        elif student_ects != "N/A":
            status = " ⚠️"
    
    c.drawString(65, y, f"• Minimum Total ECTS: {min_ects} → Your ECTS: {student_ects}{status}")
    y -= 13
    
    # Specific ECTS Requirements
    specific_ects = program.get('specific_ects_requirements', [])
    if specific_ects and len(specific_ects) > 0:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(55, y, "Specific ECTS Requirements:")
        y -= 13
        c.setFont("Helvetica", 9)
        
        for req in specific_ects[:3]:  # Show top 3
            domain_name = req.get('domain_name', 'Unknown')
            min_ects_total = req.get('min_ects_total', 0)
            c.drawString(65, y, f"• {domain_name}: {min_ects_total} ECTS minimum")
            y -= 11
        
        if len(specific_ects) > 3:
            c.drawString(65, y, f"  ... and {len(specific_ects) - 3} more requirements")
            y -= 11
        y -= 5
    
    # Language Requirements
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, "Language Requirements:")
    y -= 13
    c.setFont("Helvetica", 9)
    
    # English
    eng_req = program.get('english_requirements', {})
    eng_level = eng_req.get('min_cefr_level', 'Unknown')
    if eng_level and eng_level != 'None' and eng_level != 'Unknown':
        c.drawString(65, y, f"English: {eng_level} (CEFR) required")
        y -= 11
        
        accepted_tests = eng_req.get('accepted_tests', [])
        if accepted_tests:
            test_str = ", ".join([f"{t.get('test_name')} ({t.get('min_score', 'N/A')})" for t in accepted_tests[:2]])
            c.setFont("Helvetica", 8)
            c.drawString(75, y, f"Accepted: {test_str}")
            c.setFont("Helvetica", 9)
            y -= 11
    
    # German
    ger_req = program.get('german_requirements', {})
    ger_level = ger_req.get('min_cefr_level', 'None')
    if ger_level and ger_level != 'None':
        c.drawString(65, y, f"German: {ger_level} (CEFR) required")
        y -= 11
    else:
        c.drawString(65, y, "German: Not required")
        y -= 11
    
    y -= 5
    
    # Work Experience
    work_exp = program.get('min_work_experience_months', 0)
    if work_exp > 0:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(55, y, "Work Experience:")
        y -= 13
        c.setFont("Helvetica", 9)
        c.drawString(65, y, f"• Minimum: {work_exp} months required")
        y -= 11
    
    y -= 10
    return y

# --- HELPER: Draw Cost Breakdown Section ---
def draw_cost_section(c, y, program, user_profile, width):
    """Draw tuition fee breakdown with EU/non-EU distinction."""
    if y < 200:
        c.showPage()
        y = 750
    
    # Section header
    c.setFillColorRGB(0.2, 0.4, 0.8)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "💰 COST BREAKDOWN")
    c.setFillColorRGB(0, 0, 0)
    y -= 18
    
    c.setFont("Helvetica", 9)
    
    # Determine if student is EU or non-EU
    from Agent3 import EU_COUNTRIES
    student_country = None
    if user_profile and user_profile.citizenship:
        student_country = user_profile.citizenship.country_of_citizenship
    
    is_eu_student = student_country in EU_COUNTRIES if student_country else False
    
    # Tuition fees
    general_fee = program.get('tuition_fee_per_semester_eur', 0)
    non_eu_fee = program.get('non_eu_tuition_fee_eur')
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, "Tuition Fee (per semester):")
    y -= 13
    c.setFont("Helvetica", 9)
    
    # Show both fees
    c.drawString(65, y, f"• For EU/EEA Students: €{general_fee}")
    y -= 11
    
    if non_eu_fee is not None:
        applicable = " ← Applies to you" if not is_eu_student else ""
        c.drawString(65, y, f"• For Non-EU Students: €{non_eu_fee}{applicable}")
        y -= 11
    
    # Semester contribution
    semester_contrib = program.get('semester_contribution_eur', 0)
    c.drawString(65, y, f"• Semester Contribution: €{semester_contrib} (mandatory for all)")
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(75, y-10, "Includes: Student services, public transport, admin fees")
    c.setFillColorRGB(0, 0, 0)
    y -= 22
    
    # Calculate total for student
    if is_eu_student:
        student_fee = general_fee
    else:
        student_fee = non_eu_fee if non_eu_fee is not None else general_fee
    
    total_per_semester = student_fee + semester_contrib
    total_program = total_per_semester * 4  # Assuming 2-year program (4 semesters)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, f"Your Total Cost per Semester: €{total_per_semester}")
    y -= 12
    c.setFont("Helvetica", 9)
    c.drawString(55, y, f"Estimated Total for 2-Year Program: €{total_program}")
    y -= 15
    
    # Budget comparison
    if user_profile and user_profile.preferences and user_profile.preferences.max_tuition_fee_eur:
        max_budget = user_profile.preferences.max_tuition_fee_eur
        if max_budget > 0:
            if student_fee <= max_budget:
                c.setFillColorRGB(0.2, 0.6, 0.2)
                c.drawString(55, y, f"✅ Within your budget (€{max_budget}/semester)")
            else:
                c.setFillColorRGB(0.8, 0.2, 0.2)
                difference = student_fee - max_budget
                c.drawString(55, y, f"⚠️ Exceeds budget by €{difference}/semester")
                y -= 11
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica", 8)
                c.drawString(65, y, "Consider: DAAD scholarships, Deutschlandstipendium, part-time work")
            c.setFillColorRGB(0, 0, 0)
            y -= 11
    
    y -= 10
    c.setFont("Helvetica", 9)
    return y

# --- HELPER: PDF Generation ---
def generate_pdf_report(plans, user_profile, user_intent, filename="My_Application_Strategy.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50 
    
    # ==============================
    # 1. HEADER
    # ==============================
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "🎓 Application Strategy Dossier")
    y -= 25
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, y, "Generated by Agentic AI for German University Admissions")
    y -= 30

    # ==============================
    # 2. APPLICANT PROFILE BOX
    # ==============================
    # Increased height from 70 to 90 to fit the 3rd row
    box_height = 90
    c.setLineWidth(1)
    c.setFillColorRGB(0.95, 0.95, 0.95) # Light grey
    c.rect(45, y - box_height - 5, width-90, box_height, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0) # Black text
    
    # Title
    c.setFont("Helvetica-Bold", 12)
    c.drawString(55, y-15, "👤 APPLICANT PROFILE")
    
    # --- EXTRACT DATA ---
    u_cit = "Unknown"
    if user_profile and user_profile.citizenship:
        u_cit = getattr(user_profile.citizenship, 'country_of_citizenship', 'Unknown')

    u_gpa = "N/A"
    u_gpa_german = "N/A"
    if user_profile and user_profile.academic_background and user_profile.academic_background.bachelor_gpa:
        u_gpa = getattr(user_profile.academic_background.bachelor_gpa, 'score', 'N/A')
        u_gpa_german = getattr(user_profile.academic_background.bachelor_gpa, 'score_german', 'N/A')

    u_major = "Unknown"
    u_credits = "N/A"
    u_ects = "N/A"
    if user_profile and user_profile.academic_background:
        u_major = getattr(user_profile.academic_background, 'bachelor_field_of_study', 'Unknown')
        u_credits = getattr(user_profile.academic_background, 'total_credits_earned', 'N/A')
        u_ects = getattr(user_profile.academic_background, 'total_converted_ects', 'N/A')
    
    
    # Extract desired program and field of interests from user profile
    desired_programs = []
    fields_of_interest = []
    
    if user_profile and user_profile.desired_program:
        desired_programs = getattr(user_profile.desired_program, 'program_name', [])
        fields_of_interest = getattr(user_profile.desired_program, 'fields_of_interest', [])
    
    # Also check academic_background for fields_of_interest (backup)
    if not fields_of_interest and user_profile and user_profile.academic_background:
        fields_of_interest = getattr(user_profile.academic_background, 'fields_of_interest', [])
    
    # Format for display
    target_programs = ", ".join(desired_programs) if desired_programs else "Not specified"
    target_interests = ", ".join(fields_of_interest[:5]) if fields_of_interest else "Not specified"
    
    # Combine for display (truncate if too long)
    if target_programs != "Not specified" and target_interests != "Not specified":
        target_display = f"{target_programs} | Interests: {target_interests}"
    elif target_programs != "Not specified":
        target_display = target_programs
    elif target_interests != "Not specified":
        target_display = f"Interests: {target_interests}"
    else:
        target_display = "Not specified"
    
    if len(target_display) > 80:
        target_display = target_display[:77] + "..."

    # --- ROW 1: Origin & GPA ---
    c.setFont("Helvetica", 10)
    c.drawString(55, y-35, f"Origin: {u_cit}")
    if u_gpa_german != "N/A":
        c.drawString(300, y-35, f"GPA: {u_gpa} (German: {u_gpa_german})")
    else:
        c.drawString(300, y-35, f"Bachelor GPA: {u_gpa}")

    # --- ROW 2: Background & Credits/ECTS ---
    if len(u_major) > 35: u_major = u_major[:35] + "..."
    c.drawString(55, y-55, f"B.Sc Major: {u_major}")
    
    c.setFont("Helvetica-Bold", 10) # Bold for emphasis
    if u_ects != "N/A":
        c.drawString(300, y-55, f"Credits: {u_credits} → ECTS: {u_ects}")
    else:
        c.drawString(300, y-55, f"Total Credits: {u_credits}")
    c.setFont("Helvetica", 10)

    # --- ROW 3: TARGET / INTEREST (NEW) ---
    c.setLineWidth(0.5)
    c.line(55, y-65, width-55, y-65) # Thin separator line
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y-80, "🎯 Target / Interest:")
    c.setFont("Helvetica", 10)
    c.drawString(160, y-80, target_display)

    y -= (box_height + 40) # Move cursor past the box

    # ==============================
    # 3. PROGRAM STRATEGIES
    # ==============================
    for plan in plans:
        if y < 200: 
            c.showPage()
            y = height - 50
            
        # Header
        c.setFillColorRGB(0.9, 0.9, 0.9) 
        c.rect(45, y-5, width-90, 20, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0) 
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"{plan['program_name']}")
        y -= 20
        
        # Meta
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, f"University: {plan['university']}")
        c.drawString(300, y, f"Tuition: €{plan['tuition']}/sem")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(50, y, f"Mode: {plan['application_mode']}  |  URL: {plan['official_url'][:50]}...")
        y -= 25
        
        # NEW: Matching Score Section
        y = draw_matching_section(c, y, plan, user_profile, width)
        
        # NEW: Requirements Section
        y = draw_requirements_section(c, y, plan, user_profile, width)
        
        # NEW: Cost Breakdown Section
        y = draw_cost_section(c, y, plan, user_profile, width)
        
        # Content
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "📖 Program Content")
        y -= 15
        c.setFont("Helvetica", 9)
        desc = plan.get('course_content', 'No description available.')
        y = draw_wrapped_text(c, desc, 50, y, width-100)
        y -= 15
        
        # Timeline
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "⏳ Action Timeline")
        y -= 15
        c.setFont("Helvetica", 10)
        
        for event in plan['timeline']:
            date_display = event['date']
            if hasattr(event['date'], 'strftime'):
                date_display = event['date'].strftime('%Y-%m-%d')
            
            prefix = "•"
            if event['type'] == 'overdue': 
                c.setFillColorRGB(0.8, 0, 0) 
                prefix = "🔥 [LATE]"
            elif event['type'] == 'critical':
                c.setFillColorRGB(0.8, 0, 0) 
                prefix = "🚨"
            elif event['type'] == 'deadline':
                c.setFillColorRGB(0, 0, 0.8) 
                prefix = "🏁"
            else:
                c.setFillColorRGB(0, 0, 0)
                
            c.drawString(60, y, f"{prefix} {date_display}: {event['event']}")
            y -= 12
        
        c.setFillColorRGB(0, 0, 0) 
        y -= 15

        # Checklist
        if y < 100: 
            c.showPage()
            y = height - 50

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "📝 Required Documents")
        y -= 15
        c.setFont("Helvetica", 10)
        
        for item in plan['checklist']:
            c.drawString(60, y, f"[ ] {item}")
            y -= 12
            
        y -= 30 
        c.setLineWidth(0.5)
        c.line(50, y, width-50, y)
        y -= 30

    c.save()

# --- MAIN NODE ---
def agent_6_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n" + "="*60)
    print("📦 AGENT 6: COMPREHENSIVE PDF GENERATOR")
    print("="*60)
    
    # Get data from Agent5 (timeline) and Agent4 (full program details)
    timeline_plans = state.get("final_application_plans", [])
    selected_programs = state.get("selected_programs_with_checklists", [])
    user_profile = state.get("user_profile")
    user_intent = state.get("user_intent", "")
    
    if not timeline_plans:
        print("❌ No timeline plans to report.")
        return {}
    
    if not selected_programs:
        print("❌ No selected programs data found.")
        return {}
    
    # Merge Agent5's timeline with Agent4's full program data
    # Match by program_name and university
    merged_plans = []
    for timeline_plan in timeline_plans:
        prog_name = timeline_plan.get("program_name")
        uni_name = timeline_plan.get("university")
        
        # Find matching program from Agent4's output
        matching_program = None
        for prog in selected_programs:
            if prog.get("program_name") == prog_name and prog.get("university_name") == uni_name:
                matching_program = prog
                break
        
        if matching_program:
            # Merge timeline with full program data (including Agent3 scores)
            checklist_data = matching_program.get("checklist_data", {})
            merged_plan = {
                "program_name": prog_name,
                "university": uni_name,
                "official_url": timeline_plan.get("official_url", ""),
                "timeline": timeline_plan.get("timeline", []),
                "checklist": timeline_plan.get("checklist", []),
                # Add program data from Agent4
                "tuition": matching_program.get("tuition_fee_per_semester_eur", 0),
                "application_mode": checklist_data.get("application_mode", "Unknown"),
                "course_content": matching_program.get("course_content_summary", "No description available."),
                # Add Agent3 scoring data
                "relevance_score": matching_program.get("relevance_score", 0),
                "_domain_score": matching_program.get("_domain_score", 0),
                "_semantic_score": matching_program.get("_semantic_score", 0),
                "ects_score": matching_program.get("ects_score", 0),
                "ects_details": matching_program.get("ects_details", "N/A"),
                "llm_reasoning": matching_program.get("llm_reasoning", ""),
                # Add complete program details for requirements section
                "min_gpa_german_scale": matching_program.get("min_gpa_german_scale"),
                "required_degree_domains": matching_program.get("required_degree_domains", []),
                "min_degree_ects": matching_program.get("min_degree_ects", 180),
                "specific_ects_requirements": matching_program.get("specific_ects_requirements", []),
                "english_requirements": matching_program.get("english_requirements", {}),
                "german_requirements": matching_program.get("german_requirements", {}),
                "min_work_experience_months": matching_program.get("min_work_experience_months", 0),
                "tuition_fee_per_semester_eur": matching_program.get("tuition_fee_per_semester_eur", 0),
                "non_eu_tuition_fee_eur": matching_program.get("non_eu_tuition_fee_eur"),
                "semester_contribution_eur": matching_program.get("semester_contribution_eur", 0)
            }
            merged_plans.append(merged_plan)
        else:
            print(f"⚠️  Warning: Could not find full data for {prog_name}")
            # Use timeline plan as-is with defaults
            merged_plan = {
                **timeline_plan,
                "tuition": 0,
                "application_mode": "Unknown",
                "course_content": "No description available."
            }
            merged_plans.append(merged_plan)
    
    filename = "My_Application_Strategy.pdf"
    
    # Generate PDF with merged data
    generate_pdf_report(merged_plans, user_profile, user_intent, filename)
    
    print(f"   ✅ Report generated: '{filename}'")
    print(f"      - Included user profile (GPA, credits, citizenship)")
    print(f"      - Included desired program and field of interests")
    print(f"      - Included full program details (tuition, mode, content)")
    print(f"      - Included timeline and checklist")
    
    return {"reports_generated": True}