import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from typing import Dict, Any

# --- HELPER: Text Wrapping ---
def draw_wrapped_text(c, text, x, y, max_width, line_height=12):
    """Draw wrapped text and return new y position. Handles page breaks."""
    if not text: return y
    words = text.split()
    line = ""
    for word in words:
        if c.stringWidth(line + word, "Helvetica", 10) < max_width:
            line += word + " "
        else:
            # Check if we need a new page
            if y < 50:
                c.showPage()
                y = 750
            c.drawString(x, y, line)
            y -= line_height
            line = word + " "
    # Draw final line
    if y < 50:
        c.showPage()
        y = 750
    c.drawString(x, y, line)
    return y - line_height

# --- HELPER: Draw Matching Score Section ---
def draw_matching_section(c, y, program, user_profile, width):
    """Draw the 'Why This Matches You' section with scores and reasoning."""
    # Check if we have enough space for this section
    if y < 300:
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
    
    # Score calculation explanation
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, y, "How is the score calculated?")
    y -= 11
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    
    # Calculate weighted scores
    domain_weighted = int(domain_score * 10)
    semantic_weighted = int(semantic_score * 50)
    ects_weighted = int(ects_score * 40)
    
    c.drawString(65, y, f"Score = ({int(domain_score)} * 0.1) + ({int(semantic_score)} * 0.5) + ({int(ects_score)} * 0.4) = {relevance_score}/100")
    c.setFillColorRGB(0, 0, 0)
    y -= 13
    
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
    elif score >= 50:
        c.setFillColorRGB(0.8, 0.6, 0)    # Orange/Yellow
    else:
        c.setFillColorRGB(0.8, 0.2, 0.2)  # Red
    
    c.rect(x, y-bar_height, filled_width, bar_height, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    
    return y - 3

# --- HELPER: Draw Requirements Section ---
def draw_requirements_section(c, y, program, user_profile, width):
    """Draw detailed program requirements with student's actual values."""
    # Check if we have enough space for this section
    if y < 350:
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
    # Check if we have enough space for this section
    if y < 250:
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

# --- HELPER: Draw Application Strategy Section ---
def draw_application_strategy_section(c, y, program, user_profile, width):
    """Draw application strategy with mode details and country-specific requirements."""
    # Check if we have enough space for this section
    if y < 300:
        c.showPage()
        y = 750
    
    # Section header
    c.setFillColorRGB(0.2, 0.4, 0.8)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "🎯 APPLICATION STRATEGY")
    c.setFillColorRGB(0, 0, 0)
    y -= 18
    
    c.setFont("Helvetica", 9)
    
    # Application Mode
    app_mode = program.get('application_mode', 'Unknown')
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, f"Application Mode: {app_mode}")
    y -= 13
    
    c.setFont("Helvetica", 9)
    
    # Explain application mode
    if app_mode == "Uni-Assist" or app_mode == "VPD":
        c.drawString(65, y, "• Centralized application platform for international students")
        y -= 11
        c.drawString(65, y, "• Handles document verification and preliminary assessment")
        y -= 11
        c.drawString(65, y, "• Processing time: 4-6 weeks")
        y -= 11
        c.drawString(65, y, "• Fee: €75 (first application) + €30 (each additional)")
        y -= 13
        
        if app_mode == "VPD":
            c.setFont("Helvetica-Bold", 10)
            c.drawString(65, y, "VPD (Vorprüfungsdokumentation) Required:")
            y -= 11
            c.setFont("Helvetica", 9)
            c.drawString(75, y, "• Pre-assessment certificate from Uni-Assist")
            y -= 11
            c.drawString(75, y, "• Verifies your degree is equivalent to German standards")
            y -= 11
            c.drawString(75, y, "• Required BEFORE applying to this university")
            y -= 13
    elif app_mode == "Direct":
        c.drawString(65, y, "• Apply directly to the university (no Uni-Assist)")
        y -= 11
        c.drawString(65, y, "• Check university website for specific application portal")
        y -= 11
        c.drawString(65, y, "• Processing time varies by university (typically 4-8 weeks)")
        y -= 13
    
    # Country-specific requirements
    student_country = None
    if user_profile and user_profile.citizenship:
        student_country = user_profile.citizenship.country_of_citizenship
    
    if student_country:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(55, y, f"Country-Specific Requirements ({student_country}):")
        y -= 13
        c.setFont("Helvetica", 9)
        
        # APS requirement for specific countries
        aps_countries = ["China", "Vietnam", "India"]
        if student_country in aps_countries:
            c.setFillColorRGB(0.8, 0.2, 0.2)
            c.drawString(65, y, "⚠️ APS Certificate REQUIRED")
            c.setFillColorRGB(0, 0, 0)
            y -= 11
            c.drawString(75, y, "• Akademische Prüfstelle (Academic Evaluation Center)")
            y -= 11
            c.drawString(75, y, "• Verifies authenticity of your academic documents")
            y -= 11
            c.drawString(75, y, "• Processing time: 6 months recommended (START EARLY!)")
            y -= 11
            c.drawString(75, y, "• Cost: ~€180")
            y -= 11
            
            # Country-specific APS links
            if student_country == "Vietnam":
                c.setFont("Helvetica", 8)
                c.drawString(75, y, "Book at: www.aps.org.vn")
                c.setFont("Helvetica", 9)
            elif student_country == "China":
                c.setFont("Helvetica", 8)
                c.drawString(75, y, "Book at: www.aps.org.cn")
                c.setFont("Helvetica", 9)
            elif student_country == "India":
                c.setFont("Helvetica", 8)
                c.drawString(75, y, "Book at: www.aps-india.de")
                c.setFont("Helvetica", 9)
            y -= 13
        else:
            c.drawString(65, y, "• No special country-specific requirements")
            y -= 11
            c.drawString(65, y, "• Standard document authentication may be required")
            y -= 13
    
    # Recommended timeline
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, "Recommended Application Timeline:")
    y -= 13
    c.setFont("Helvetica", 9)
    
    if student_country in ["China", "Vietnam", "India"]:
        c.drawString(65, y, "1. Start APS process NOW (6 months lead time recommended)")
        y -= 11
        c.drawString(65, y, "2. Prepare documents while waiting for APS")
        y -= 11
        c.drawString(65, y, "3. Submit to Uni-Assist/University once APS received")
        y -= 11
    else:
        c.drawString(65, y, "1. Prepare all required documents")
        y -= 11
        c.drawString(65, y, "2. Submit application 2-3 months before deadline")
        y -= 11
    
    c.drawString(65, y, f"{3 if student_country in ['China', 'Vietnam', 'India'] else 2}. Wait for admission decision (4-8 weeks)")
    y -= 11
    c.drawString(65, y, f"{4 if student_country in ['China', 'Vietnam', 'India'] else 3}. Apply for visa after receiving admission letter")
    y -= 11
    
    y -= 10
    return y

# --- HELPER: Draw Comparison Table ---
def draw_comparison_table(c, plans, user_profile, width, height):
    """Draw side-by-side comparison table of all programs."""
    c.showPage()
    y = height - 50
    
    # Page header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "📊 Program Comparison")
    y -= 30
    
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Side-by-side comparison to help you make an informed decision:")
    y -= 25
    
    # Table setup
    col_width = (width - 100) / (len(plans) + 1)
    x_start = 50
    
    # Helper function to draw table row
    def draw_row(label, values, y_pos, bold_label=True):
        if bold_label:
            c.setFont("Helvetica-Bold", 9)
        else:
            c.setFont("Helvetica", 9)
        c.drawString(x_start, y_pos, label)
        
        c.setFont("Helvetica", 9)
        for i, val in enumerate(values):
            x_pos = x_start + col_width + (i * col_width)
            # Truncate if too long
            val_str = str(val)
            if len(val_str) > 20:
                val_str = val_str[:17] + "..."
            c.drawString(x_pos, y_pos, val_str)
        
        return y_pos - 12
    
    # Header row with program names
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_start, y, "Criteria")
    for i, plan in enumerate(plans):
        x_pos = x_start + col_width + (i * col_width)
        prog_name = plan.get('program_name', 'Unknown')[:15]
        c.drawString(x_pos, y, f"Program {i+1}")
    y -= 15
    
    # Draw separator line
    c.setLineWidth(1)
    c.line(x_start, y, width - 50, y)
    y -= 15
    
    # Data rows
    y = draw_row("Match Score", 
                 [f"{plan.get('relevance_score', 0)}/100 {'⭐' * min(5, int(plan.get('relevance_score', 0)/20))}" for plan in plans], y)
    
    y = draw_row("University", 
                 [plan.get('university', 'Unknown')[:20] for plan in plans], y)
    
    # Tuition (show applicable fee)
    from Agent3 import EU_COUNTRIES
    student_country = user_profile.citizenship.country_of_citizenship if user_profile and user_profile.citizenship else None
    is_eu = student_country in EU_COUNTRIES if student_country else False
    
    tuition_values = []
    for plan in plans:
        if is_eu:
            fee = plan.get('tuition_fee_per_semester_eur', 0)
        else:
            fee = plan.get('non_eu_tuition_fee_eur') or plan.get('tuition_fee_per_semester_eur', 0)
        tuition_values.append(f"€{fee}/sem")
    
    y = draw_row("Tuition (You)", tuition_values, y)
    
    y = draw_row("App Mode", 
                 [plan.get('application_mode', 'Unknown') for plan in plans], y)
    
    # Deadline - extract from timeline events
    deadline_values = []
    for plan in plans:
        timeline = plan.get('timeline', [])
        deadline = "N/A"
        
        # Find the application deadline in timeline
        for event in timeline:
            event_text = event.get('event', '').lower()
            event_type = event.get('type', '')
            
            # Look for deadline events
            if event_type == 'deadline' or 'deadline' in event_text or 'application' in event_text:
                date = event.get('date')
                if date:
                    if hasattr(date, 'strftime'):
                        deadline = date.strftime('%b %d, %Y')
                    else:
                        deadline = str(date)
                    break  # Use first deadline found
        
        deadline_values.append(deadline)
    
    y = draw_row("Deadline", deadline_values, y)
    
    y = draw_row("Min GPA", 
                 [str(plan.get('min_gpa_german_scale', 'None')) for plan in plans], y)
    
    # Language requirement
    lang_values = []
    for plan in plans:
        eng_req = plan.get('english_requirements', {})
        level = eng_req.get('min_cefr_level', 'Unknown')
        lang_values.append(f"Eng: {level}")
    
    y = draw_row("Language", lang_values, y)
    
    # APS requirement - need to get student country first
    student_country = user_profile.citizenship.country_of_citizenship if user_profile and user_profile.citizenship else None
    aps_required = "Yes" if student_country in ["China", "Vietnam", "India"] else "No"
    y = draw_row("APS Required", [aps_required] * len(plans), y)
    
    y -= 10
    
    # Recommendation
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_start, y, "Recommendation Priority:")
    y -= 15
    
    c.setFont("Helvetica", 9)
    medals = ["🥇", "🥈", "🥉"]
    for i, plan in enumerate(plans[:3]):
        medal = medals[i] if i < len(medals) else "•"
        prog_name = plan.get('program_name', 'Unknown')
        score = plan.get('relevance_score', 0)
        c.drawString(x_start + 10, y, f"{medal} Program {i+1}: {prog_name[:30]} (Score: {score})")
        y -= 12
    
    return y

# --- HELPER: Draw Executive Summary ---
def draw_executive_summary(c, y, plans, user_profile, width):
    """Draw executive summary box on first page."""
    if y < 150:
        c.showPage()
        y = 750
    
    # Box setup
    box_height = 100
    c.setLineWidth(1)
    c.setFillColorRGB(0.95, 0.95, 1.0)  # Light blue
    c.rect(45, y - box_height - 5, width-90, box_height, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    
    # Title
    c.setFont("Helvetica-Bold", 12)
    c.drawString(55, y-15, "📋 EXECUTIVE SUMMARY")
    
    c.setFont("Helvetica", 9)
    y -= 30
    
    # Total programs
    c.drawString(55, y, f"• Total Programs Selected: {len(plans)}")
    y -= 12
    
    # Application window (find earliest and latest deadlines)
    # This is simplified - you'd need to parse actual deadlines
    c.drawString(55, y, "• Application Window: Check individual program timelines")
    y -= 12
    
    # Show user's budget instead of average cost
    user_budget = "N/A"
    if user_profile and user_profile.preferences and user_profile.preferences.max_tuition_fee_eur:
        user_budget = f"€{user_profile.preferences.max_tuition_fee_eur}"
    
    c.drawString(55, y, f"• Your Budget per Semester: {user_budget}")
    y -= 12
    
    # Key action items
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, y, "• Key Action Items:")
    y -= 11
    c.setFont("Helvetica", 8)
    
    # Get student country for APS check
    student_country = user_profile.citizenship.country_of_citizenship if user_profile and user_profile.citizenship else None
    
    if student_country in ["China", "Vietnam", "India"]:
        c.drawString(65, y, "1. Start APS certificate process immediately (6 months recommended)")
        y -= 10
        c.drawString(65, y, "2. Prepare language test (TOEFL/IELTS)")
        y -= 10
        c.drawString(65, y, "3. Gather and translate all documents")
    else:
        c.drawString(65, y, "1. Prepare language test (TOEFL/IELTS)")
        y -= 10
        c.drawString(65, y, "2. Gather and translate all documents")
        y -= 10
        c.drawString(65, y, "3. Submit applications 2-3 months before deadline")
    
    y -= (box_height - 85)
    return y

# --- HELPER: Draw Disclaimer & Information Section ---
def draw_disclaimer_section(c, plans, user_profile, width, height):
    """Draw disclaimer and important information at the end of PDF."""
    c.showPage()
    y = height - 50
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "⚠️ Important Information & Disclaimer")
    y -= 30
    
    # Disclaimer box
    c.setLineWidth(2)
    c.setStrokeColorRGB(0.8, 0.2, 0.2)  # Red border
    c.setFillColorRGB(1.0, 0.95, 0.95)  # Light red background
    c.rect(45, y - 65, width - 90, 65, fill=1, stroke=1)
    c.setStrokeColorRGB(0, 0, 0)  # Reset to black
    c.setFillColorRGB(0, 0, 0)
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.8, 0, 0)
    c.drawString(55, y - 15, "⚠️ VERIFICATION REQUIRED")
    c.setFillColorRGB(0, 0, 0)
    y -= 28
    
    c.setFont("Helvetica", 9)
    c.drawString(55, y, "This is an AI-generated recommendation. While we strive for accuracy, information may")
    y -= 11
    c.drawString(55, y, "change. ALWAYS verify deadlines, requirements, and fees on official university websites.")
    y -= 11
    c.drawString(55, y, "Do not rely 100% on this report - use it as a starting point for your research.")
    y -= 30
    
    # Check if student needs APS
    student_country = user_profile.citizenship.country_of_citizenship if user_profile and user_profile.citizenship else None
    show_aps = student_country in ["China", "Vietnam", "India", "Mongolia"]
    show_hec = student_country == "Pakistan"
    
    # Check if any program requires Uni-Assist
    show_uniassist = any(plan.get('application_mode') in ['Uni-Assist', 'VPD'] for plan in plans)
    
    # APS Information (only if student is from APS country)
    if show_aps:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "📋 What is APS Certificate?")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(55, y, "APS (Akademische Prüfstelle) is an Academic Evaluation Center that verifies the authenticity")
        y -= 11
        c.drawString(55, y, "of academic documents from certain countries (China, Vietnam, India, Mongolia).")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Required for:")
        y -= 11
        c.setFont("Helvetica", 9)
        c.drawString(65, y, "• Students from China, Vietnam, India applying to German universities")
        y -= 11
        c.drawString(65, y, "• Verifies your degree is genuine and grades are authentic")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Processing Time:")
        c.setFont("Helvetica", 9)
        c.drawString(150, y, "6 months recommended (START EARLY!)")
        y -= 11
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Cost:")
        c.setFont("Helvetica", 9)
        c.drawString(150, y, "~€180")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "How to apply:")
        y -= 11
        c.setFont("Helvetica", 8)
        c.drawString(65, y, "China: www.aps.org.cn  |  Vietnam: www.aps.org.vn  |  India: www.aps-india.de")
        y -= 25
    
    # HEC Information (only if student is from Pakistan)
    if show_hec:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "📋 What is HEC Attestation?")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(55, y, "HEC (Higher Education Commission) attestation is required for Pakistani students applying")
        y -= 11
        c.drawString(55, y, "to German universities. It verifies that your degree is recognized by Pakistan's HEC.")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Required for:")
        y -= 11
        c.setFont("Helvetica", 9)
        c.drawString(65, y, "• Students from Pakistan")
        y -= 11
        c.drawString(65, y, "• Degree attestation from HEC Pakistan")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "More info:")
        c.setFont("Helvetica", 8)
        c.drawString(150, y, "www.hec.gov.pk")
        y -= 25
    
    # Uni-Assist Information (only if at least one program requires it)
    if show_uniassist:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "📋 What is Uni-Assist?")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(55, y, "Uni-Assist is a centralized application platform for international students applying to")
        y -= 11
        c.drawString(55, y, "German universities. Many universities require applications through Uni-Assist.")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Website:")
        c.setFont("Helvetica", 8)
        c.drawString(150, y, "www.uni-assist.de")
        y -= 11
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Fee:")
        c.setFont("Helvetica", 9)
        c.drawString(150, y, "€75 (first application) + €30 (each additional)")
        y -= 25
    
    # Baden-Württemberg Tuition Fee Information (if student is non-EU and programs are in BW)
    student_country = user_profile.citizenship.country_of_citizenship if user_profile and user_profile.citizenship else None
    from Agent3 import EU_COUNTRIES
    is_non_eu = student_country not in EU_COUNTRIES if student_country else False
    
    # Check if any program is in Baden-Württemberg
    has_bw_program = any('Baden-Württemberg' in str(plan.get('state', '')) for plan in plans)
    
    if is_non_eu and has_bw_program:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "💰 Baden-Württemberg Tuition Fees")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(55, y, "Baden-Württemberg (BW) is one of the few German states that charges tuition fees for")
        y -= 11
        c.drawString(55, y, "non-EU/EEA international students at public universities.")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Fee Amount:")
        c.setFont("Helvetica", 9)
        c.drawString(150, y, "€1,500 per semester (for non-EU/EEA students)")
        y -= 11
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Who pays:")
        y -= 11
        c.setFont("Helvetica", 9)
        c.drawString(65, y, "• Non-EU/EEA international students")
        y -= 11
        c.drawString(65, y, "• EU/EEA students: €0 (tuition-free)")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Exemptions:")
        y -= 11
        c.setFont("Helvetica", 9)
        c.drawString(65, y, "• Scholarship holders (e.g., DAAD)")
        y -= 11
        c.drawString(65, y, "• Students from certain partner countries")
        y -= 11
        c.drawString(65, y, "• Refugees with recognized status")
        y -= 13
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(55, y, "Note:")
        c.setFont("Helvetica", 8)
        c.drawString(150, y, "Other German states (e.g., Bavaria, Berlin) are tuition-free for all students")
        y -= 25
    
    # Final reminder
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0, 0.4, 0.8)
    c.drawString(50, y, "💡 Always Check Official Sources")
    c.setFillColorRGB(0, 0, 0)
    y -= 15
    c.setFont("Helvetica", 9)
    c.drawString(55, y, "Visit each university's official website to verify:")
    y -= 11
    c.drawString(65, y, "✓ Application deadlines (they may change!)")
    y -= 11
    c.drawString(65, y, "✓ Admission requirements (GPA, language tests, etc.)")
    y -= 11
    c.drawString(65, y, "✓ Tuition fees and living costs")
    y -= 11
    c.drawString(65, y, "✓ Application process and required documents")
    y -= 20
    
    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 30, "Generated by AI-Powered University Matching System | Always verify with official sources")
    c.setFillColorRGB(0, 0, 0)
    
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
    # --- EXTRACT DATA FIRST (to calculate box height) ---
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
    
    # Format for display - separate target and interests
    target_programs_display = ", ".join(desired_programs) if desired_programs else "Not specified"
    # Show ALL interests (no truncation)
    target_interests_display = ", ".join(fields_of_interest) if fields_of_interest else "Not specified"
    
    # Truncate target programs if too long, but NOT interests
    if len(target_programs_display) > 70:
        target_programs_display = target_programs_display[:67] + "..."
    
    # --- CALCULATE HOW MANY LINES INTERESTS WILL TAKE ---
    interests_x = 200
    max_interests_width = width - interests_x - 55
    
    # Count wrapped lines for interests
    num_interest_lines = 1  # At least 1 line
    if len(target_interests_display) > 0:
        words = target_interests_display.split()
        line = ""
        line_count = 0
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, "Helvetica", 9) < max_interests_width:
                line = test_line
            else:
                if line:
                    line_count += 1
                line = word + " "
        if line:
            line_count += 1
        num_interest_lines = max(1, line_count)
    
    # Calculate dynamic box height based on interests
    # Base: 145, add 10 pixels per extra interest line beyond 1
    extra_lines = max(0, num_interest_lines - 1)
    box_height = 145 + (extra_lines * 10)
    
    # Draw the box
    c.setLineWidth(1)
    c.setFillColorRGB(0.95, 0.95, 0.95) # Light grey
    c.rect(45, y - box_height - 5, width-90, box_height, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0) # Black text
    
    # Title
    c.setFont("Helvetica-Bold", 12)
    c.drawString(55, y-15, "👤 APPLICANT PROFILE")
    
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
    
    if u_ects != "N/A":
        c.drawString(300, y-55, f"Credits: {u_credits} (ECTS: {u_ects})")
    else:
        c.drawString(300, y-55, f"Total Credits: {u_credits}")

    # --- ROW 3: TARGET MASTER PROGRAM ---
    c.setLineWidth(0.5)
    c.line(55, y-65, width-55, y-65) # Thin separator line
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y-80, "Target Master Program:")
    c.setFont("Helvetica", 9)
    c.drawString(200, y-80, target_programs_display)
    
    # --- ROW 4: INTERESTS (with wrapping for long lists) ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y-95, "Interests:")
    c.setFont("Helvetica", 9)
    
    # Use text wrapping for interests to handle long lists
    interests_x = 200
    interests_y = y-95
    max_interests_width = width - interests_x - 55  # Available width for interests
    
    # Wrap interests text
    if len(target_interests_display) > 0:
        words = target_interests_display.split()
        line = ""
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, "Helvetica", 9) < max_interests_width:
                line = test_line
            else:
                if line:  # Draw the current line
                    c.drawString(interests_x, interests_y, line.strip())
                    interests_y -= 10
                line = word + " "
        # Draw remaining text
        if line:
            c.drawString(interests_x, interests_y, line.strip())
    
    # --- ROW 5: ATTACHED TRANSCRIPT FILE ---
    # Position dynamically based on number of interest lines
    y_file = y - 95 - (num_interest_lines * 10) - 15  # Start after interests + spacing
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y_file, "Transcript File:")
    c.setFont("Helvetica", 9)
    
    # Get the PDF filename from user profile or state
    pdf_filename = "Bachelor_Courses.pdf"  # Default, should be extracted from actual file
    if user_profile and hasattr(user_profile, 'transcript_file'):
        pdf_filename = getattr(user_profile, 'transcript_file', 'Bachelor_Courses.pdf')
    
    c.drawString(200, y_file, f"📄 {pdf_filename}")

    y -= (box_height + 40) # Move cursor past the box
    
    # ==============================
    # 2.5 EXECUTIVE SUMMARY
    # ==============================
    y = draw_executive_summary(c, y, plans, user_profile, width)
    y -= 20  # Add extra space after executive summary

    # ==============================
    # 3. PROGRAM STRATEGIES
    # ==============================
    for plan in plans:
        # Check if we need a new page before starting a program
        if y < 250: 
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
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(50, y, f"Mode: {plan['application_mode']}")
        y -= 12
        c.drawString(50, y, f"URL: {plan['official_url'][:60]}...")
        y -= 15
        
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
        
        # NEW: Application Strategy
        y = draw_application_strategy_section(c, y, plan, user_profile, width)
        
        # Check if we need a new page before timeline
        if y < 200:
            c.showPage()
            y = height - 50
        
        # Timeline
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "⏳ Action Timeline")
        y -= 15
        c.setFont("Helvetica", 10)
        
        for event in plan['timeline']:
            # Check if we need a new page during timeline
            if y < 60:
                c.showPage()
                y = height - 50
            
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

        # Check if we need a new page before checklist
        if y < 150: 
            c.showPage()
            y = height - 50

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "📝 Required Documents")
        y -= 15
        c.setFont("Helvetica", 10)
        
        for item in plan['checklist']:
            # Check if we need a new page during checklist
            if y < 60:
                c.showPage()
                y = height - 50
            c.drawString(60, y, f"[ ] {item}")
            y -= 12
            
        y -= 30 
        c.setLineWidth(0.5)
        c.line(50, y, width-50, y)
        y -= 30

    # ==============================
    # 4. COMPARISON TABLE (Final Page)
    # ==============================
    draw_comparison_table(c, plans, user_profile, width, height)
    
    # ==============================
    # 5. DISCLAIMER & INFORMATION (Last Page)
    # ==============================
    draw_disclaimer_section(c, plans, user_profile, width, height)

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