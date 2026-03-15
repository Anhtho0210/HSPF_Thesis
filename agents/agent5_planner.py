import datetime
import re
from typing import Dict, Any, List

# --- HELPER 1: Robust Date Parser ---
def parse_date(date_str: str) -> datetime.date:
    """
    Parses deadline strings like 'July 15', 'Nov 30', '2025-07-15', or '15.07.2025'.
    Intelligently assigns the year if missing (e.g. 'July 15' becomes '2025-07-15' or '2026-07-15').
    """
    if not date_str or date_str.lower() in ["not specified", "unknown", "n/a"]:
        return None

    current_year = datetime.date.today().year
    # Remove text like "(Annual)" or "(Estimated)"
    clean_str = re.sub(r'\s*\(.*?\)', '', date_str).strip()

    formats = [
        "%Y-%m-%d",      # 2025-07-15
        "%B %d",         # July 15
        "%b %d",         # Nov 30, Jan 15 (abbreviated months)
        "%B %d, %Y",     # July 15, 2025
        "%b %d, %Y",     # Nov 30, 2025 (abbreviated with year)
        "%d.%m.%Y",      # 15.07.2025
        "%d %B %Y",      # 15 July 2025
        "%d %b %Y"       # 15 Nov 2025 (abbreviated)
    ]

    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(clean_str, fmt).date()
            
            # If the format didn't have a year (e.g., "July 15" or "Nov 30"), deduce it
            if "%Y" not in fmt:
                today = datetime.date.today()
                # If the date has passed this year, assume next year
                if dt.month < today.month or (dt.month == today.month and dt.day < today.day):
                    dt = dt.replace(year=current_year + 1)
                else:
                    dt = dt.replace(year=current_year)
            return dt
        except ValueError:
            continue
    
    return None

# --- HELPER 2: Triage Logic (Conflict Resolution) ---
def create_event(date_obj, title, ideal_desc, priority="normal"):
    """
    Checks if a calculated date is in the past.
    If YES: Clamps to Today + Marks URGENT.
    If NO:  Returns normal scheduled event.
    """
    today = datetime.date.today()
    
    if date_obj < today:
        # CONFLICT: Ideal date is in the past
        return {
            "date": today,
            "event": f"🔥 URGENT: {title}",
            "description": f"You are behind schedule! (Ideally started on {date_obj}). {ideal_desc}",
            "type": "overdue"
        }
    else:
        # NORMAL STATUS
        return {
            "date": date_obj,
            "event": title,
            "description": ideal_desc,
            "type": priority
        }

# --- MAIN NODE ---
def agent_5_planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n" + "="*60)
    print("🗓️  AGENT 5: TIMELINE & STRATEGY PLANNER")
    print("="*60)
    
    # Get input from Agent 4
    selected_programs = state.get("selected_programs_with_checklists", [])
    if not selected_programs:
        return {"final_application_plans": []}

    # Get user citizenship to check for APS requirement
    user_profile = state.get("user_profile")
    user_citizenship = None
    if user_profile and hasattr(user_profile, 'citizenship'):
        if hasattr(user_profile.citizenship, 'country_of_citizenship'):
            user_citizenship = user_profile.citizenship.country_of_citizenship
    
    # Countries that require APS certificate
    APS_COUNTRIES = ["China", "Vietnam", "India", "Mongolia"]
    requires_aps = user_citizenship in APS_COUNTRIES if user_citizenship else False
    
    if requires_aps:
        print(f"   ℹ️  User citizenship: {user_citizenship} - APS certificate required for all programs")

    today = datetime.date.today()
    final_plans = []
    
    for prog in selected_programs:
        checklist_data = prog.get('checklist_data', {})
        prog_name = prog.get('program_name', 'Unknown')
        uni_name = prog.get('university_name', 'Unknown')
        
        deadline_str = checklist_data.get('deadline', 'Unknown')
        app_mode = checklist_data.get('application_mode', 'Direct')
        country_req = checklist_data.get('country_specific_requirement', '')

        print(f"\n   ⚙️  Planning for: {prog_name}")

        deadline_dt = parse_date(deadline_str)
        timeline_events = []

        if deadline_dt:
            # 1. FATAL CHECK: Is the deadline itself passed?
            if deadline_dt < today:
                print(f"      ❌ Deadline {deadline_dt} has passed. Marking as missed.")
                timeline_events.append({
                    "date": today,
                    "event": "❌ DEADLINE MISSED",
                    "description": f"The deadline was {deadline_dt}. Look for the next intake.",
                    "type": "fatal"
                })
            else:
                # 2. RULE: APS (Vietnam/China/India/Mongolia) -> 6 Months Before
                # Check both program requirements AND user citizenship
                needs_aps = (
                    "APS" in country_req or 
                    "APS" in checklist_data.get("document_checklist", []) or
                    requires_aps  # Based on user citizenship
                )
                
                if needs_aps:
                    ideal_start = deadline_dt - datetime.timedelta(days=180)
                    timeline_events.append(create_event(
                        ideal_start, 
                        "Check APS Schedule and Start as soon as possible", 
                        "Apply immediately. Processing takes ~6 months.", 
                        "critical"
                    ))

                # 3. RULE: Translations -> 2 Months Before
                ideal_trans = deadline_dt - datetime.timedelta(days=60)
                timeline_events.append(create_event(
                    ideal_trans, 
                    "Notarization & Translations", 
                    "Prepare documents for upload.", 
                    "task"
                ))

                # 4. RULE: Submission Buffer
                if "Uni-Assist" in app_mode or "VPD" in app_mode:
                    ideal_submit = deadline_dt - datetime.timedelta(days=30)
                    desc = "Uni-Assist processing buffer (4 weeks)."
                else:
                    ideal_submit = deadline_dt - datetime.timedelta(days=3)
                    desc = "Direct application safety buffer."

                timeline_events.append(create_event(
                    ideal_submit, 
                    f"Submit to {app_mode}", 
                    desc, 
                    "action"
                ))

                # 5. OFFICIAL DEADLINE
                timeline_events.append({
                    "date": deadline_dt,
                    "event": "🏁 OFFICIAL DEADLINE",
                    "description": f"Hard deadline for {uni_name}.",
                    "type": "deadline"
                })

            # Sort milestones by date
            timeline_events.sort(key=lambda x: x['date'])
            print(f"      ✅ Generated {len(timeline_events)} milestones.")

        else:
            # Fallback if deadline parsing failed
            timeline_events.append({
                "date": today,
                "event": "Manual Check Required",
                "description": f"Could not parse deadline string: '{deadline_str}'",
                "type": "warning"
            })

        # Create the plan object
        plan = {
            "program_name": prog_name,
            "university": uni_name,
            "official_url": checklist_data.get("official_url", ""),
            "timeline": timeline_events,
            "checklist": checklist_data.get("document_checklist", [])
        }
        final_plans.append(plan)
        
        # Print the milestones for this program
        print(f"\n   📅 Timeline for {prog_name}:")
        for event in timeline_events:
            date_str = event['date'].strftime("%Y-%m-%d") if hasattr(event['date'], 'strftime') else str(event['date'])
            
            # Add icons based on urgency
            icon = "⚪"
            if event['type'] == "overdue": icon = "🔥"
            elif event['type'] == "critical": icon = "🚨"
            elif event['type'] == "deadline": icon = "🏁"
            elif event['type'] == "fatal": icon = "❌"
            elif event['type'] == "action": icon = "📤"
            elif event['type'] == "task": icon = "📝"
            
            print(f"      {icon} [{date_str}] {event['event']}")
        print(f"      {'-' * 50}")

    return {"final_application_plans": final_plans}