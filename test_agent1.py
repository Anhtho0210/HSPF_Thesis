"""
Test Agent 1: Profile Extraction & ECTS Conversion

Tests:
1. Natural language input extraction
2. GPA conversion to German scale
3. ECTS conversion from various credit systems
4. PDF transcript parsing
5. Field completeness
"""

import json
import sys
from pathlib import Path

# Import your Agent 1 functions
from Agent1 import parse_profile_node, apply_ects_conversion
from models import AgentState

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test_header(test_name):
    """Print a formatted test header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST: {test_name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def print_result(test_name, passed, expected=None, actual=None, details=None):
    """Print test result with details"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {test_name}")
    
    if not passed:
        if expected is not None and actual is not None:
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
        if details:
            print(f"  Details:  {details}")

def print_extracted_profile(profile, profile_id):
    """Print the complete extracted profile as JSON for verification"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}EXTRACTED PROFILE JSON: {profile_id}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    if not profile:
        print(f"{RED}No profile extracted{RESET}")
        return
    
    # Convert profile to dict for JSON serialization
    profile_dict = {}
    
    # Basic fields
    profile_dict["full_name"] = profile.full_name
    
    # Citizenship
    if profile.citizenship:
        profile_dict["citizenship"] = {
            "country_of_citizenship": profile.citizenship.country_of_citizenship
        }
    
    # Academic Background
    if profile.academic_background:
        acad = profile.academic_background
        profile_dict["academic_background"] = {
            "bachelor_field_of_study": acad.bachelor_field_of_study,
            "total_credits_earned": acad.total_credits_earned,
            "program_duration_semesters": acad.program_duration_semesters,
            "total_converted_ects": acad.total_converted_ects,
            "ects_conversion_factor": acad.ects_conversion_factor,
            "fields_of_interest": acad.fields_of_interest,
        }
        
        # GPA
        if acad.bachelor_gpa:
            profile_dict["academic_background"]["bachelor_gpa"] = {
                "score": acad.bachelor_gpa.score,
                "max_scale": acad.bachelor_gpa.max_scale,
                "min_passing_grade": acad.bachelor_gpa.min_passing_grade,
                "score_german": acad.bachelor_gpa.score_german
            }
        
        # Transcript courses (just count)
        if acad.transcript_courses:
            profile_dict["academic_background"]["transcript_courses_count"] = len(acad.transcript_courses)
            profile_dict["academic_background"]["sample_courses"] = [
                {"name": c.course_name, "credits": c.original_credits, "ects": c.converted_ects}
                for c in acad.transcript_courses[:5]  # Show first 5 courses
            ]
    
    # Language Proficiency
    if profile.language_proficiency:
        profile_dict["language_proficiency"] = [
            {
                "language": lang.language,
                "exam_type": lang.exam_type,
                "overall_score": lang.overall_score,
                "level": lang.level
            }
            for lang in profile.language_proficiency
        ]
    
    # Professional and Tests
    if profile.professional_and_tests:
        profile_dict["professional_and_tests"] = {
            "relevant_work_experience_months": profile.professional_and_tests.relevant_work_experience_months
        }
    
    # Preferences
    if profile.preferences:
        profile_dict["preferences"] = {
            "max_tuition_fee_eur": profile.preferences.max_tuition_fee_eur,
            "preferred_cities": profile.preferences.preferred_cities,
            "preferred_start_semester": profile.preferences.preferred_start_semester,
            "preferred_language_of_instruction": profile.preferences.preferred_language_of_instruction
        }
    
    # Print as formatted JSON
    print(json.dumps(profile_dict, indent=2, ensure_ascii=False))
    print(f"{BLUE}{'='*80}{RESET}\n")

def test_ects_conversion():
    """Test ECTS conversion accuracy for all 5 profiles"""
    print_test_header("ECTS Conversion Accuracy")
    
    # Load test profiles
    with open('test_profiles.json', 'r') as f:
        data = json.load(f)
    
    # Build test cases from all 5 profiles using gold_standard
    test_cases = []
    for i, profile in enumerate(data['test_profiles']):
        gold = profile['gold_standard']['expected_profile']
        test_cases.append({
            "profile_id": profile['id'],
            "input_text": profile['input_text'],
            "pdf_file": profile['pdf_file'],
            "expected_ects": gold['expected_ects'],
            "expected_factor": gold['expected_ects_factor'],
            "original_credits": gold['total_credits'],
            "semesters": gold['semesters'],
            "tolerance": 0.5,
            "factor_tolerance": 0.05
        })
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for test_case in test_cases:
        print(f"\n{YELLOW}Testing {test_case['profile_id']}...{RESET}")
        
        try:
            # Create AgentState
            state: AgentState = {
                "user_intent": test_case['input_text'],
                "pdf_path": test_case['pdf_file'],
                "user_profile": None,
                "ai_response": None
            }
            
            # Run Agent 1 parse node
            result = parse_profile_node(state)
            
            # Print extracted profile JSON
            if result.get('user_profile'):
                print_extracted_profile(result['user_profile'], test_case['profile_id'])
            
            # Extract ECTS from result
            if not result.get('user_profile'):
                print_result(
                    f"ECTS Conversion",
                    False,
                    details="No user_profile returned"
                )
                continue
                
            user_profile = result['user_profile']
            if not user_profile.academic_background:
                print_result(
                    f"ECTS Conversion",
                    False,
                    details="No academic_background in profile"
                )
                continue
                
            actual_ects = user_profile.academic_background.total_converted_ects
            actual_factor = user_profile.academic_background.ects_conversion_factor
            expected_ects = test_case['expected_ects']
            expected_factor = test_case['expected_factor']
            tolerance = test_case['tolerance']
            factor_tolerance = test_case['factor_tolerance']
            
            # Check ECTS
            ects_passed = actual_ects and abs(actual_ects - expected_ects) <= tolerance
            
            print_result(
                f"ECTS Conversion ({test_case['original_credits']} credits → {expected_ects} ECTS)",
                ects_passed,
                expected=f"{expected_ects} ECTS (±{tolerance})",
                actual=f"{actual_ects} ECTS" if actual_ects else "None"
            )
            
            # Check conversion factor
            factor_passed = actual_factor and abs(actual_factor - expected_factor) <= factor_tolerance
            
            print_result(
                f"Conversion Factor",
                factor_passed,
                expected=f"{expected_factor} (±{factor_tolerance})",
                actual=f"{actual_factor}" if actual_factor else "None"
            )
            
            if ects_passed and factor_passed:
                passed_tests += 1
                
        except Exception as e:
            print_result(
                f"ECTS Conversion",
                False,
                details=f"Error: {str(e)}"
            )
    
    print(f"\n{BLUE}ECTS Conversion Summary: {passed_tests}/{total_tests} tests passed{RESET}")
    return passed_tests == total_tests

def test_gpa_conversion():
    """Test GPA conversion to German scale"""
    print_test_header("GPA Conversion to German Scale")
    
    # Load test profiles
    with open('test_profiles.json', 'r') as f:
        data = json.load(f)
    
    # Build test cases from all 5 profiles using gold_standard
    test_cases = []
    for i, profile in enumerate(data['test_profiles']):
        gold = profile['gold_standard']['expected_profile']
        test_cases.append({
            "profile_id": profile['id'],
            "input_text": profile['input_text'],
            "pdf_file": profile['pdf_file'],
            "expected_gpa_german": gold['gpa_german'],
            "tolerance": 0.3
        })
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for test_case in test_cases:
        print(f"\n{YELLOW}Testing {test_case['profile_id']}...{RESET}")
        
        try:
            # Create AgentState
            state: AgentState = {
                "user_intent": test_case['input_text'],
                "pdf_path": test_case['pdf_file'],
                "user_profile": None,
                "ai_response": None
            }
            
            # Run Agent 1
            result = parse_profile_node(state)
            
            # Print extracted profile JSON
            if result.get('user_profile'):
                print_extracted_profile(result['user_profile'], test_case['profile_id'])
            
            # Extract German GPA
            if not result.get('user_profile') or not result['user_profile'].academic_background:
                print_result(
                    f"GPA Conversion",
                    False,
                    details="No profile or academic_background"
                )
                continue
            
            gpa = result['user_profile'].academic_background.bachelor_gpa
            actual_gpa = gpa.score_german if gpa else None
            expected_gpa = test_case['expected_gpa_german']
            tolerance = test_case['tolerance']
            
            # Check if within tolerance
            passed = actual_gpa and abs(actual_gpa - expected_gpa) <= tolerance
            
            print_result(
                f"GPA Conversion to German Scale",
                passed,
                expected=f"{expected_gpa} (±{tolerance})",
                actual=f"{actual_gpa}" if actual_gpa else "None"
            )
            
            if passed:
                passed_tests += 1
                
        except Exception as e:
            print_result(
                f"GPA Conversion",
                False,
                details=f"Error: {str(e)}"
            )
    
    print(f"\n{BLUE}GPA Conversion Summary: {passed_tests}/{total_tests} tests passed{RESET}")
    return passed_tests == total_tests

def test_field_extraction():
    """Test extraction of all required fields from natural language"""
    print_test_header("Field Extraction from Natural Language")
    
    # Load test profiles
    with open('test_profiles.json', 'r') as f:
        data = json.load(f)
    
    # Test Profile 1 (Vietnamese CS student)
    profile = data['test_profiles'][0]
    
    print(f"\n{YELLOW}Testing Profile 1 (Vietnamese CS)...{RESET}")
    
    try:
        # Create AgentState
        state: AgentState = {
            "user_intent": profile['input_text'],
            "pdf_path": profile['pdf_file'],
            "user_profile": None,
            "ai_response": None
        }
        
        result = parse_profile_node(state)
        
        # Print extracted profile JSON
        if result.get('user_profile'):
            print_extracted_profile(result['user_profile'], profile['id'])
        
        if not result.get('user_profile'):
            print_result("Field Extraction", False, details="No user_profile returned")
            return False
        
        user_profile = result['user_profile']
        
        # Define required fields and expected values
        tests = [
            ("Full Name", user_profile.full_name, "Linh Nguyen"),
            ("Citizenship", user_profile.citizenship.country_of_citizenship if user_profile.citizenship else None, "Vietnam"),
            ("Bachelor Field", user_profile.academic_background.bachelor_field_of_study if user_profile.academic_background else None, "Computer Science"),
            ("Total Credits", user_profile.academic_background.total_credits_earned if user_profile.academic_background else None, 130),
            ("Semesters", user_profile.academic_background.program_duration_semesters if user_profile.academic_background else None, 8),
        ]
        
        # Add GPA tests if available
        if user_profile.academic_background and user_profile.academic_background.bachelor_gpa:
            gpa = user_profile.academic_background.bachelor_gpa
            tests.extend([
                ("GPA Score", gpa.score, 3.5),
                ("GPA Max Scale", gpa.max_scale, 4.0),
            ])
        
        # Add language test if available
        if user_profile.language_proficiency and len(user_profile.language_proficiency) > 0:
            tests.extend([
                ("English Test", user_profile.language_proficiency[0].exam_type, "IELTS"),
                ("English Score", user_profile.language_proficiency[0].overall_score, 7.0),
            ])
        
        # Add preferences if available
        if user_profile.preferences:
            tests.extend([
                ("Max Tuition", user_profile.preferences.max_tuition_fee_eur, 3000),
                ("Preferred Semester", user_profile.preferences.preferred_start_semester, "Winter"),
            ])
        
        passed_tests = 0
        for field_name, actual, expected in tests:
            passed = actual == expected
            print_result(
                f"Extract {field_name}",
                passed,
                expected=expected,
                actual=actual
            )
            if passed:
                passed_tests += 1
        
        # Check interests extraction
        if user_profile.academic_background:
            interests = user_profile.academic_background.fields_of_interest or []
            has_ai = any("AI" in str(interest) or "Artificial Intelligence" in str(interest) for interest in interests)
            has_ml = any("ML" in str(interest) or "Machine Learning" in str(interest) for interest in interests)
            
            print_result(
                "Extract Interests (AI/ML)",
                has_ai or has_ml,
                expected="Contains AI or ML",
                actual=f"{len(interests)} interests found"
            )
        
        print(f"\n{BLUE}Field Extraction Summary: {passed_tests}/{len(tests)} tests passed{RESET}")
        return passed_tests >= len(tests) * 0.8  # 80% pass rate
        
    except Exception as e:
        print_result("Field Extraction", False, details=f"Error: {str(e)}")
        return False

def test_pdf_parsing():
    """Test PDF transcript parsing"""
    print_test_header("PDF Transcript Parsing")
    
    # Load test profiles
    with open('test_profiles.json', 'r') as f:
        data = json.load(f)
    
    test_cases = [
        {
            "profile_id": "PROFILE-001-VN-CS",
            "pdf_file": data['test_profiles'][0]['pdf_file'],
            "input_text": data['test_profiles'][0]['input_text'],
            "expected_min_courses": 30,  # Should extract at least 30 courses
        },
        {
            "profile_id": "PROFILE-002-IN-BUS",
            "pdf_file": data['test_profiles'][1]['pdf_file'],
            "input_text": data['test_profiles'][1]['input_text'],
            "expected_min_courses": 25,
        },
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for test_case in test_cases:
        print(f"\n{YELLOW}Testing {test_case['profile_id']}...{RESET}")
        
        try:
            # Create AgentState
            state: AgentState = {
                "user_intent": test_case['input_text'],
                "pdf_path": test_case['pdf_file'],
                "user_profile": None,
                "ai_response": None
            }
            
            result = parse_profile_node(state)
            
            # Print extracted profile JSON
            if result.get('user_profile'):
                print_extracted_profile(result['user_profile'], test_case['profile_id'])
            
            if not result.get('user_profile') or not result['user_profile'].academic_background:
                print_result(
                    f"PDF Parsing",
                    False,
                    details="No profile or academic_background"
                )
                continue
            
            courses = result['user_profile'].academic_background.transcript_courses or []
            num_courses = len(courses)
            expected_min = test_case['expected_min_courses']
            
            passed = num_courses >= expected_min
            
            print_result(
                f"PDF Parsing - Extract Courses",
                passed,
                expected=f"≥{expected_min} courses",
                actual=f"{num_courses} courses"
            )
            
            # Check if courses have credits
            courses_with_credits = sum(1 for c in courses if c.original_credits and c.original_credits > 0)
            credits_passed = courses_with_credits >= expected_min * 0.9
            
            print_result(
                f"PDF Parsing - Extract Credits",
                credits_passed,
                expected=f"≥{int(expected_min * 0.9)} courses with credits",
                actual=f"{courses_with_credits} courses with credits"
            )
            
            if passed and credits_passed:
                passed_tests += 1
                
        except Exception as e:
            print_result(
                f"PDF Parsing",
                False,
                details=f"Error: {str(e)}"
            )
    
    print(f"\n{BLUE}PDF Parsing Summary: {passed_tests}/{total_tests} tests passed{RESET}")
    return passed_tests == total_tests

def main():
    """Run all Agent 1 tests"""
    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}AGENT 1 COMPREHENSIVE TEST SUITE{RESET}")
    print(f"{GREEN}{'='*80}{RESET}")
    
    results = {}
    
    # Run all tests
    results['ECTS Conversion'] = test_ects_conversion()
    results['GPA Conversion'] = test_gpa_conversion()
    results['Field Extraction'] = test_field_extraction()
    results['PDF Parsing'] = test_pdf_parsing()
    
    # Print summary
    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}FINAL SUMMARY{RESET}")
    print(f"{GREEN}{'='*80}{RESET}")
    
    for test_name, passed in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{status} - {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n{BLUE}Overall: {total_passed}/{total_tests} test suites passed{RESET}")
    
    if total_passed == total_tests:
        print(f"\n{GREEN}🎉 ALL TESTS PASSED! Agent 1 is ready for evaluation.{RESET}")
        return 0
    else:
        print(f"\n{RED}⚠️  Some tests failed. Please review and fix issues.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
