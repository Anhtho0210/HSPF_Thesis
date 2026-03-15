"""
Quick Test for Agent3 with test_profiles.json and test_sample_programs.json
Run this BEFORE manual labeling to verify Agent3 works with test data
"""

import json
import sys
import os
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent3_matcher import agent_3_filter_node, EU_COUNTRIES
from agents.agent1_intake import parse_profile_node
from models import AgentState

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def calculate_layer_pass_rates(user_profile, programs):
    """Calculate pass rates for each filtering layer"""
    total = len(programs)
    
    stats = {
        'total_programs': total,
        'gpa_pass': 0,
        'tuition_pass': 0,
        'language_pass': 0,
        'location_pass': 0,
        'semester_pass': 0,
        'work_exp_pass': 0,
        'all_hard_pass': 0
    }
    
    # Extract user profile attributes
    # Determine if student is from EU/EEA country
    student_country = None
    if user_profile.citizenship and user_profile.citizenship.country_of_citizenship:
        student_country = user_profile.citizenship.country_of_citizenship
    
    is_eu = student_country in EU_COUNTRIES if student_country else False
    
    # Get GPA (German scale)
    gpa_german = 4.0  # Default worst passing grade
    if user_profile.academic_background and user_profile.academic_background.bachelor_gpa:
        gpa_german = user_profile.academic_background.bachelor_gpa.score_german or 4.0
    
    # Get preferences
    max_tuition = 0
    preferred_cities = []
    preferred_semester = 'No preference'
    if user_profile.preferences:
        max_tuition = user_profile.preferences.max_tuition_fee_eur or 0
        preferred_cities = [c.lower() for c in (user_profile.preferences.preferred_cities or [])]
        preferred_semester = user_profile.preferences.preferred_start_semester or 'No preference'
    
    # Get work experience
    work_exp_months = 0
    if user_profile.professional_and_tests:
        work_exp_months = user_profile.professional_and_tests.relevant_work_experience_months or 0
    
    for program in programs:
        # L1.1: GPA Filter (with 0.05 buffer)
        program_min_gpa = program.get('min_gpa_german_scale')
        if program_min_gpa is None:
            stats['gpa_pass'] += 1
            gpa_ok = True
        else:
            # Check: student_gpa <= required (lower is better)
            # Allow buffer: if student has 2.55 and limit is 2.5, we check 2.55 <= 2.5 + 0.05
            if gpa_german <= (program_min_gpa + 0.05):
                stats['gpa_pass'] += 1
                gpa_ok = True
            else:
                gpa_ok = False
        
        # L1.2: Tuition Filter (with 100 EUR buffer)
        if is_eu:
            applicable_tuition = program.get('tuition_fee_per_semester_eur', 0) or 0
        else:
            applicable_tuition = program.get('non_eu_tuition_fee_eur', 0) or 0
        
        if applicable_tuition <= (max_tuition + 100):
            stats['tuition_pass'] += 1
            tuition_ok = True
        else:
            tuition_ok = False
        
        # L1.3: Language Filter (simplified - assume all pass for now)
        stats['language_pass'] += 1
        language_ok = True
        
        # L1.4: Location Filter
        prog_city = str(program.get('city', '')).lower()
        if not preferred_cities or (prog_city and prog_city in preferred_cities):
            stats['location_pass'] += 1
            location_ok = True
        else:
            location_ok = False
        
        # L1.5: Semester Filter
        deadlines = program.get('deadlines', {})
        semester_ok = False
        
        wanted_start = preferred_semester.lower()
        has_winter = deadlines.get('winter_semester') is not None
        has_summer = deadlines.get('summer_semester') is not None
        
        if "winter" in wanted_start:
            if has_winter:
                semester_ok = True
        elif "summer" in wanted_start:
            if has_summer:
                semester_ok = True
        else:
            # No specific preference (e.g. "No preference", or just "Any")
            semester_ok = True
        
        if semester_ok:
            stats['semester_pass'] += 1
        
        # L1.6: Work Experience Filter
        min_work_exp = program.get('min_work_experience_months', 0) or 0
        if work_exp_months >= min_work_exp:
            stats['work_exp_pass'] += 1
            work_exp_ok = True
        else:
            work_exp_ok = False
        
        # All hard constraints combined
        if gpa_ok and tuition_ok and language_ok and location_ok and semester_ok and work_exp_ok:
            stats['all_hard_pass'] += 1
    
    # Calculate percentages
    stats['gpa_pct'] = stats['gpa_pass'] / total * 100 if total > 0 else 0
    stats['tuition_pct'] = stats['tuition_pass'] / total * 100 if total > 0 else 0
    stats['language_pct'] = stats['language_pass'] / total * 100 if total > 0 else 0
    stats['location_pct'] = stats['location_pass'] / total * 100 if total > 0 else 0
    stats['semester_pct'] = stats['semester_pass'] / total * 100 if total > 0 else 0
    stats['work_exp_pct'] = stats['work_exp_pass'] / total * 100 if total > 0 else 0
    stats['all_hard_pct'] = stats['all_hard_pass'] / total * 100 if total > 0 else 0
    
    return stats



def quick_test_agent3():
    """Quick sanity test without ground truth"""
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}AGENT 3 QUICK TEST - Test Profiles + Sample Programs{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    # Load data
    print(f"\n{YELLOW}Loading test data...{RESET}")
    with open('evaluation/test_profiles.json') as f:
        profiles_data = json.load(f)
        profiles = profiles_data['test_profiles']
    
    with open('evaluation/test_sample_programs.json') as f:
        programs_data = json.load(f)
        programs = programs_data['programs']
    
    print(f"  ✓ Loaded {len(profiles)} test profiles")
    print(f"  ✓ Loaded {len(programs)} sample programs")
    
    # Test each profile
    results_summary = []
    
    for i, profile in enumerate(profiles, 1):
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{BLUE}Testing Profile {i}/5: {profile['id']}{RESET}")
        print(f"{BLUE}{'='*80}{RESET}")
        print(f"Description: {profile['description']}")
        
        gold = profile['gold_standard']['expected_profile']
        print(f"\nStudent Info:")
        print(f"  • Bachelor: {gold.get('bachelor_field')}")
        print(f"  • GPA (German): {gold.get('gpa_german')}")
        print(f"  • Max Tuition: {gold.get('max_tuition')} EUR")
        print(f"  • Interests: {', '.join(gold.get('interests', [])[:3])}")
        print(f"  • Desired Programs: {', '.join(gold.get('desired_programs', []))}")
        
        try:
            # Parse profile
            print(f"\n{YELLOW}Step 1: Parsing profile with Agent 1...{RESET}")
            state = {
                "user_intent": profile['input_text'],
                "pdf_path": profile['pdf_file'],
                "user_profile": None,
                "program_database": programs
            }
            
            result = parse_profile_node(state)
            state['user_profile'] = result['user_profile']
            print(f"  {GREEN}✓ Profile parsed successfully{RESET}")
            
            # Run Agent 3
            print(f"\n{YELLOW}Step 2: Running Agent 3 filtering...{RESET}")
            filtered = agent_3_filter_node(state)
            
            filtered_programs = filtered.get('eligible_programs', [])
            print(f"  {GREEN}✓ Filtering complete{RESET}")
            print(f"  Programs passed filters: {len(filtered_programs)}/{len(programs)}")
            
            
            # Show top 10 with Layer 4 details
            print(f"\n{BLUE}Top 10 Programs (with Layer 4 ECTS Details):{RESET}")
            for j, prog in enumerate(filtered_programs[:10], 1):
                tuition = prog.get('non_eu_tuition_fee_eur') or prog.get('tuition_fee_per_semester_eur', 0) or 0
                relevance = prog.get('relevance_score', 0)
                
                # Get Layer 4 ECTS details
                ects_score = prog.get('_ects_match_score', 'N/A')
                ects_details = prog.get('_ects_details', 'No ECTS constraints')
                
                print(f"  {j:2d}. {prog['program_name'][:45]:45} | Score: {relevance:5.1f} | {tuition:>5.0f} EUR")
                
                # Show ECTS domain requirements if they exist
                if ects_score != 'N/A' and ects_score != 1.0:
                    print(f"      └─ ECTS Match: {ects_score:.2f} | {ects_details}")
                elif prog.get('specific_ects_requirements'):
                    print(f"      └─ ECTS: {ects_details}")
            
            # Check against expected top programs
            expected_top = profile['gold_standard']['expected_top_programs']
            print(f"\n{YELLOW}Expected Top Programs (from gold standard):{RESET}")
            for exp in expected_top:
                print(f"  • {exp}")
            
            # Check if any expected programs are in top 10
            top_10_names = [p['program_name'] for p in filtered_programs[:10]]
            matches = []
            for exp in expected_top:
                for name in top_10_names:
                    if exp.lower() in name.lower() or name.lower() in exp.lower():
                        matches.append(exp)
                        break
            
            # Calculate match rate based on expected programs found
            if expected_top:
                match_rate = len(matches) / len(expected_top)
            else:
                match_rate = None  # No expected programs to match
            
            if match_rate is None:
                print(f"\n{YELLOW}⚠ No expected programs defined for this profile{RESET}")
                status = "N/A"
            elif match_rate >= 0.5:
                print(f"\n{GREEN}✓ Found {len(matches)}/{len(expected_top)} expected programs in top 10 ({match_rate:.0%}){RESET}")
                status = "GOOD"
            elif match_rate > 0:
                print(f"\n{YELLOW}⚠ Found {len(matches)}/{len(expected_top)} expected programs in top 10 ({match_rate:.0%}){RESET}")
                status = "PARTIAL"
            else:
                print(f"\n{RED}✗ Found {len(matches)}/{len(expected_top)} expected programs in top 10 ({match_rate:.0%}){RESET}")
                status = "POOR"
            
            # Calculate layer-by-layer pass rates
            layer_stats = calculate_layer_pass_rates(state['user_profile'], programs)
            
            results_summary.append({
                'profile_id': profile['id'],
                'total_programs': len(programs),
                'passed_filters': len(filtered_programs),
                'filter_rate': len(filtered_programs) / len(programs),
                'expected_in_top_10': len(matches),
                'total_expected': len(expected_top),
                'match_rate': match_rate,
                'status': status,
                'layer_stats': layer_stats
            })
            
        except Exception as e:
            print(f"\n{RED}✗ Error testing profile: {str(e)}{RESET}")
            import traceback
            traceback.print_exc()
            results_summary.append({
                'profile_id': profile['id'],
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Print overall summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}OVERALL SUMMARY{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    print(f"\n{'Profile':<20} {'Passed/Total':<15} {'Filter Rate':<15} {'Expected in Top 10':<20} {'Status':<10}")
    print("-" * 80)
    
    for result in results_summary:
        if result['status'] != 'ERROR':
            # Format match rate display
            if result['match_rate'] is None:
                match_display = "N/A"
            else:
                match_display = f"{result['match_rate']:.0%}"
            
            print(f"{result['profile_id']:<20} "
                  f"{result['passed_filters']}/{result['total_programs']:<13} "
                  f"{result['filter_rate']:<14.1%} "
                  f"{result['expected_in_top_10']}/{result['total_expected']} ({match_display})"[:20] + " " * max(0, 20 - len(f"{result['expected_in_top_10']}/{result['total_expected']} ({match_display})")) + ""
                  f"{result['status']:<10}")
        else:
            print(f"{result['profile_id']:<20} ERROR: {result.get('error', 'Unknown')}")
    
    # Calculate overall metrics
    successful = [r for r in results_summary if r['status'] != 'ERROR']
    if successful:
        avg_filter_rate = sum(r['filter_rate'] for r in successful) / len(successful)
        
        # Calculate average match rate only for profiles with expected programs
        with_expected = [r for r in successful if r['match_rate'] is not None]
        if with_expected:
            avg_match_rate = sum(r['match_rate'] for r in with_expected) / len(with_expected)
        else:
            avg_match_rate = None
        
        print(f"\n{BLUE}Metrics:{RESET}")
        print(f"  Average filter rate: {avg_filter_rate:.1%} (programs that pass hard constraints)")
        if avg_match_rate is not None:
            print(f"  Average match rate: {avg_match_rate:.1%} (expected programs found in top 10)")
        else:
            print(f"  Average match rate: N/A (no profiles with expected programs)")
        
        # Print layer-by-layer statistics
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{BLUE}LAYER-BY-LAYER PASS RATES (Detailed Breakdown){RESET}")
        print(f"{BLUE}{'='*80}{RESET}")
        
        for result in successful:
            if 'layer_stats' in result:
                stats = result['layer_stats']
                total = stats['total_programs']
                layer1_pass = stats['all_hard_pass']
                
                print(f"\n{YELLOW}{result['profile_id']}:{RESET}")
                print(f"  Total Programs: {total}")
                
                # Layer 1: Individual Hard Constraints
                print(f"\n  {BLUE}Layer 1 - Hard Constraints (Individual):{RESET}")
                print(f"    • GPA:            {stats['gpa_pass']:2d}/{total} ({stats['gpa_pct']:5.1f}%)")
                print(f"    • Tuition:        {stats['tuition_pass']:2d}/{total} ({stats['tuition_pct']:5.1f}%)")
                print(f"    • Language:       {stats['language_pass']:2d}/{total} ({stats['language_pct']:5.1f}%)")
                print(f"    • Location:       {stats['location_pass']:2d}/{total} ({stats['location_pct']:5.1f}%)")
                print(f"    • Semester:       {stats['semester_pass']:2d}/{total} ({stats['semester_pct']:5.1f}%)")
                print(f"    • Work Exp:       {stats['work_exp_pass']:2d}/{total} ({stats['work_exp_pct']:5.1f}%)")
                print(f"    {GREEN}→ ALL Combined:   {layer1_pass:2d}/{total} ({stats['all_hard_pct']:5.1f}%){RESET}")
                
                # Calculate Layer 2 and Layer 3 from filtered results
                # Layer 2 would be after degree compatibility (we'll estimate from final results)
                # For now, we'll show the progression
                final_pass = result['passed_filters']
                
                # Estimate Layer 2 (assuming degree compatibility filters some programs)
                # This is a simplified view - actual Layer 2/3 breakdown would need more instrumentation
                if layer1_pass > 0:
                    layer2_pct = (final_pass / layer1_pass) * 100
                    print(f"\n  {BLUE}Layer 2 - Degree Compatibility:{RESET}")
                    print(f"    Programs passing: {final_pass}/{layer1_pass} ({layer2_pct:5.1f}% of Layer 1)")
                    print(f"    Overall:          {final_pass}/{total} ({result['filter_rate']*100:5.1f}% of total)")
                else:
                    print(f"\n  {BLUE}Layer 2 - Degree Compatibility:{RESET}")
                    print(f"    No programs passed Layer 1")
                
                print(f"\n  {GREEN}Final Result: {final_pass}/{total} programs ({result['filter_rate']*100:5.1f}%){RESET}")
        
        print(f"\n{YELLOW}Note: Layer 2 shows programs that pass degree compatibility after passing Layer 1{RESET}")
        print(f"{YELLOW}      Compare with ground truth in agent3_ground_truth_FILLED.xlsx{RESET}")
        
        
        if avg_match_rate is not None and avg_match_rate >= 0.5:
            print(f"\n{GREEN}✓ Agent3 is working reasonably well! Ready for detailed evaluation.{RESET}")
            print(f"\n{YELLOW}Next steps:{RESET}")
            print(f"  1. Open 'agent3_ground_truth_template.xlsx'")
            print(f"  2. Manually label expected outcomes (2-3 hours)")
            print(f"  3. Save as 'agent3_ground_truth.xlsx'")
            print(f"  4. Run 'test_agent3_with_ground_truth.py' for detailed metrics")
            return 0
        elif avg_match_rate is None:
            print(f"\n{YELLOW}⚠ No expected programs defined. Cannot evaluate match rate.{RESET}")
            print(f"\n{YELLOW}Recommendations:{RESET}")
            print(f"  1. Define expected_top_programs in test_profiles.json")
            print(f"  2. Re-run this test")
            return 1
        else:
            print(f"\n{YELLOW}⚠ Agent3 needs tuning. Match rate is low.{RESET}")
            print(f"\n{YELLOW}Recommendations:{RESET}")
            print(f"  1. Check if hard constraints are too strict")
            print(f"  2. Review degree compatibility matching")
            print(f"  3. Verify semantic matching weights")
            return 1
    else:
        print(f"\n{RED}✗ All tests failed. Check Agent3 implementation.{RESET}")
        return 2

if __name__ == "__main__":
    sys.exit(quick_test_agent3())
