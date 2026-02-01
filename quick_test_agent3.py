"""
Quick Test for Agent3 with test_profiles.json and test_sample_programs.json
Run this BEFORE manual labeling to verify Agent3 works with test data
"""

import json
import sys
from pathlib import Path
from Agent3 import agent_3_filter_node
from Agent1 import parse_profile_node
from models import AgentState

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def quick_test_agent3():
    """Quick sanity test without ground truth"""
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}AGENT 3 QUICK TEST - Test Profiles + Sample Programs{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    # Load data
    print(f"\n{YELLOW}Loading test data...{RESET}")
    with open('test_profiles.json') as f:
        profiles_data = json.load(f)
        profiles = profiles_data['test_profiles']
    
    with open('test_sample_programs.json') as f:
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
            
            # Show top 10
            print(f"\n{BLUE}Top 10 Programs:{RESET}")
            for j, prog in enumerate(filtered_programs[:10], 1):
                tuition = prog.get('non_eu_tuition_fee_eur') or prog.get('tuition_fee_per_semester_eur', 0) or 0
                relevance = prog.get('relevance_score', 0)
                print(f"  {j:2d}. {prog['program_name'][:50]:50} | Score: {relevance:5.1f} | {tuition:>5.0f} EUR")
            
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
            
            match_rate = len(matches) / len(expected_top) if expected_top else 0
            
            if match_rate >= 0.5:
                print(f"\n{GREEN}✓ Found {len(matches)}/{len(expected_top)} expected programs in top 10 ({match_rate:.0%}){RESET}")
                status = "GOOD"
            elif match_rate > 0:
                print(f"\n{YELLOW}⚠ Found {len(matches)}/{len(expected_top)} expected programs in top 10 ({match_rate:.0%}){RESET}")
                status = "PARTIAL"
            else:
                print(f"\n{RED}✗ Found {len(matches)}/{len(expected_top)} expected programs in top 10 ({match_rate:.0%}){RESET}")
                status = "POOR"
            
            results_summary.append({
                'profile_id': profile['id'],
                'total_programs': len(programs),
                'passed_filters': len(filtered_programs),
                'filter_rate': len(filtered_programs) / len(programs),
                'expected_in_top_10': len(matches),
                'total_expected': len(expected_top),
                'match_rate': match_rate,
                'status': status
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
            print(f"{result['profile_id']:<20} "
                  f"{result['passed_filters']}/{result['total_programs']:<13} "
                  f"{result['filter_rate']:<14.1%} "
                  f"{result['expected_in_top_10']}/{result['total_expected']:<18} "
                  f"{result['status']:<10}")
        else:
            print(f"{result['profile_id']:<20} ERROR: {result.get('error', 'Unknown')}")
    
    # Calculate overall metrics
    successful = [r for r in results_summary if r['status'] != 'ERROR']
    if successful:
        avg_filter_rate = sum(r['filter_rate'] for r in successful) / len(successful)
        avg_match_rate = sum(r['match_rate'] for r in successful) / len(successful)
        
        print(f"\n{BLUE}Metrics:{RESET}")
        print(f"  Average filter rate: {avg_filter_rate:.1%} (programs that pass hard constraints)")
        print(f"  Average match rate: {avg_match_rate:.1%} (expected programs in top 10)")
        
        if avg_match_rate >= 0.5:
            print(f"\n{GREEN}✓ Agent3 is working reasonably well! Ready for detailed evaluation.{RESET}")
            print(f"\n{YELLOW}Next steps:{RESET}")
            print(f"  1. Open 'agent3_ground_truth_template.xlsx'")
            print(f"  2. Manually label expected outcomes (2-3 hours)")
            print(f"  3. Save as 'agent3_ground_truth.xlsx'")
            print(f"  4. Run 'test_agent3_with_ground_truth.py' for detailed metrics")
            return 0
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
