#!/usr/bin/env python3
"""
Standalone test script to verify tuition fee filtering logic

This script contains a copy of the check_hard_constraints logic
to test without importing the full Agent3 module.
"""

import sys
from typing import Optional
from models import UserProfile, Citizenship, Preferences

# EU/EEA countries list (same as in Agent3.py)
EU_COUNTRIES = [
    "Germany", "France", "Italy", "Spain", "Netherlands", "Belgium", "Austria", 
    "Sweden", "Denmark", "Finland", "Poland", "Czech Republic", "Hungary", 
    "Romania", "Bulgaria", "Greece", "Portugal", "Ireland", "Croatia", 
    "Slovenia", "Slovakia", "Lithuania", "Latvia", "Estonia", "Cyprus", 
    "Malta", "Luxembourg"
]

def check_tuition_fee_constraint(student: UserProfile, program: dict) -> dict:
    """
    Simplified version of tuition fee check from Agent3.check_hard_constraints
    Returns {'eligible': bool, 'reason': str}
    """
    reasons = []
    
    # --- TUITION FEE CHECK ---
    if student.preferences and student.preferences.max_tuition_fee_eur is not None:
        max_fee = student.preferences.max_tuition_fee_eur
        
        # Determine if student is from EU/EEA country
        student_country = None
        if student.citizenship and student.citizenship.country_of_citizenship:
            student_country = student.citizenship.country_of_citizenship
        
        is_eu_student = student_country in EU_COUNTRIES if student_country else False
        
        # Use appropriate tuition fee based on student's origin
        # Non-EU students should be evaluated against non_eu_tuition_fee_eur if available
        if not is_eu_student and program.get('non_eu_tuition_fee_eur') is not None:
            # Non-EU student: use non_eu_tuition_fee_eur if available
            prog_fee = program.get('non_eu_tuition_fee_eur', 0.0)
            fee_type = "non-EU"
        else:
            # EU student or no specific non-EU fee: use general tuition fee
            prog_fee = program.get('tuition_fee_per_semester_eur', 0.0)
            fee_type = "EU/general"
        
        # Allow buffer of 100 EUR (e.g. for semester contributions vs tuition)
        if max_fee > 0 and prog_fee > (max_fee + 100):
            reasons.append(f"Tuition {prog_fee}€ ({fee_type}) > Budget {max_fee}€")
    
    # --- FINAL VERDICT ---
    if reasons:
        return {'eligible': False, 'reason': "; ".join(reasons)}
    
    return {'eligible': True, 'reason': "Pass"}

def create_test_student(citizenship: str, max_tuition: int) -> UserProfile:
    """Create a test student profile with specified citizenship and max tuition."""
    return UserProfile(
        citizenship=Citizenship(country_of_citizenship=citizenship),
        preferences=Preferences(max_tuition_fee_eur=max_tuition)
    )

def create_test_program(name: str, general_fee: float, non_eu_fee: float = None) -> dict:
    """Create a test program with specified tuition fees."""
    return {
        'program_name': name,
        'tuition_fee_per_semester_eur': general_fee,
        'non_eu_tuition_fee_eur': non_eu_fee
    }

def run_tests():
    """Run all test cases and report results."""
    print("=" * 70)
    print("TESTING TUITION FEE FILTERING LOGIC")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # Test Case 1: Non-EU student with budget 1000 EUR
    print("\n[Test 1] Non-EU student (Vietnam) with max budget 1000 EUR")
    print("-" * 70)
    student = create_test_student("Vietnam", 1000)
    
    # Should REJECT: non_eu_tuition_fee_eur = 1500 > 1000
    program = create_test_program("Physics", 0.0, 1500.0)
    result = check_tuition_fee_constraint(student, program)
    if not result['eligible'] and "1500" in result['reason'] and "non-EU" in result['reason']:
        print(f"✅ PASS: Rejected program with non-EU fee 1500 EUR")
        print(f"   Reason: {result['reason']}")
        passed += 1
    else:
        print(f"❌ FAIL: Should reject program with non-EU fee 1500 EUR")
        print(f"   Result: {result}")
        failed += 1
    
    # Should ACCEPT: non_eu_tuition_fee_eur = 500 < 1000
    program = create_test_program("Economics", 0.0, 500.0)
    result = check_tuition_fee_constraint(student, program)
    if result['eligible']:
        print(f"✅ PASS: Accepted program with non-EU fee 500 EUR")
        passed += 1
    else:
        print(f"❌ FAIL: Should accept program with non-EU fee 500 EUR")
        print(f"   Reason: {result['reason']}")
        failed += 1
    
    # Test Case 2: EU student with budget 1000 EUR
    print("\n[Test 2] EU student (Germany) with max budget 1000 EUR")
    print("-" * 70)
    student = create_test_student("Germany", 1000)
    
    # Should REJECT: tuition_fee_per_semester_eur = 5040 > 1000
    # Even though non_eu_tuition_fee_eur exists, EU students use general fee
    program = create_test_program("Computer Science", 5040.0, 6950.0)
    result = check_tuition_fee_constraint(student, program)
    if not result['eligible'] and "5040" in result['reason'] and "EU/general" in result['reason']:
        print(f"✅ PASS: Rejected program with general fee 5040 EUR")
        print(f"   Reason: {result['reason']}")
        passed += 1
    else:
        print(f"❌ FAIL: Should reject program with general fee 5040 EUR")
        print(f"   Result: {result}")
        failed += 1
    
    # Should ACCEPT: tuition_fee_per_semester_eur = 0 < 1000
    program = create_test_program("Data Science", 0.0, 1500.0)
    result = check_tuition_fee_constraint(student, program)
    if result['eligible']:
        print(f"✅ PASS: Accepted program with general fee 0 EUR (ignores non-EU fee)")
        passed += 1
    else:
        print(f"❌ FAIL: Should accept program with general fee 0 EUR")
        print(f"   Reason: {result['reason']}")
        failed += 1
    
    # Test Case 3: Non-EU student with higher budget
    print("\n[Test 3] Non-EU student (India) with max budget 2000 EUR")
    print("-" * 70)
    student = create_test_student("India", 2000)
    
    # Should ACCEPT: non_eu_tuition_fee_eur = 1500 < 2000
    program = create_test_program("Engineering", 0.0, 1500.0)
    result = check_tuition_fee_constraint(student, program)
    if result['eligible']:
        print(f"✅ PASS: Accepted program with non-EU fee 1500 EUR")
        passed += 1
    else:
        print(f"❌ FAIL: Should accept program with non-EU fee 1500 EUR")
        print(f"   Reason: {result['reason']}")
        failed += 1
    
    # Test Case 4: Non-EU student with null non_eu_tuition_fee_eur
    print("\n[Test 4] Non-EU student with program having null non-EU fee")
    print("-" * 70)
    student = create_test_student("China", 1000)
    
    # Should use general fee as fallback: tuition_fee_per_semester_eur = 0 < 1000
    program = create_test_program("Mathematics", 0.0, None)
    result = check_tuition_fee_constraint(student, program)
    if result['eligible']:
        print(f"✅ PASS: Accepted program (falls back to general fee 0 EUR)")
        passed += 1
    else:
        print(f"❌ FAIL: Should accept program with null non-EU fee and general fee 0 EUR")
        print(f"   Reason: {result['reason']}")
        failed += 1
    
    # Test Case 5: Student with missing citizenship
    print("\n[Test 5] Student with missing citizenship (defaults to non-EU)")
    print("-" * 70)
    student = UserProfile(
        citizenship=None,
        preferences=Preferences(max_tuition_fee_eur=1000)
    )
    
    # Should default to non-EU logic and use general fee (since citizenship is None)
    program = create_test_program("Biology", 0.0, 1500.0)
    result = check_tuition_fee_constraint(student, program)
    # When citizenship is None, is_eu_student = False, so it tries non_eu_tuition_fee_eur
    if not result['eligible'] and "1500" in result['reason']:
        print(f"✅ PASS: Correctly uses non-EU fee when citizenship is missing")
        print(f"   Reason: {result['reason']}")
        passed += 1
    else:
        print(f"❌ FAIL: Should reject using non-EU fee when citizenship is missing")
        print(f"   Result: {result}")
        failed += 1
    
    # Test Case 6: Buffer tolerance (100 EUR)
    print("\n[Test 6] Testing 100 EUR buffer tolerance")
    print("-" * 70)
    student = create_test_student("Vietnam", 1000)
    
    # Should ACCEPT: non_eu_tuition_fee_eur = 1050 is within buffer (1000 + 100)
    program = create_test_program("Chemistry", 0.0, 1050.0)
    result = check_tuition_fee_constraint(student, program)
    if result['eligible']:
        print(f"✅ PASS: Accepted program with fee 1050 EUR (within 100 EUR buffer)")
        passed += 1
    else:
        print(f"❌ FAIL: Should accept program within 100 EUR buffer")
        print(f"   Reason: {result['reason']}")
        failed += 1
    
    # Should REJECT: non_eu_tuition_fee_eur = 1150 exceeds buffer (1000 + 100)
    program = create_test_program("Physics", 0.0, 1150.0)
    result = check_tuition_fee_constraint(student, program)
    if not result['eligible']:
        print(f"✅ PASS: Rejected program with fee 1150 EUR (exceeds buffer)")
        print(f"   Reason: {result['reason']}")
        passed += 1
    else:
        print(f"❌ FAIL: Should reject program exceeding 100 EUR buffer")
        print(f"   Result: {result}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed!")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
