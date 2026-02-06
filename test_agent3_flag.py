"""
Test to verify Agent3 returns the _agent3_ran flag correctly
This bypasses the LangGraph to test just the Agent3 function
"""

from Agent3 import agent_3_filter_node

# Create a minimal test state
test_state = {
    "user_profile": {
        "name": "Test User",
        "citizenship": {"country": "Germany", "is_eu_citizen": True},
        "english_proficiency": "C1",
        "gpa_info": {"score": 3.5, "scale_max": 4.0, "scale_min": 2.0},
        "student_major": "Computer Science",
        "current_education_level": "Bachelor",
        "work_experience_years": 0,
        "interests": ["AI", "Machine Learning"],
        "desired_city": None,
        "desired_state": None,
        "max_tuition_per_semester_eur": 10000,
        "semester_preference": None,
        "desired_program": ["Computer Science", "Computational Linguistics"]
    },
    "bachelor_pdf_path": None,
    "all_interests": ["AI", "Machine Learning"],
    "program_database": None  #Will load from file
}

print("=" * 60)
print("TEST: Verifying Agent3 Returns _agent3_ran Flag")
print("=" * 60)

# Call Agent3 directly
result = agent_3_filter_node(test_state)

print("\n" + "=" * 60)
print("RESULT FROM AGENT3:")
print("=" * 60)
print(f"Keys in result: {list(result.keys())}")
print(f"_agent3_ran in result: {'_agent3_ran' in result}")
print(f"_agent3_ran value: {result.get('_agent3_ran')}")
print(f"Type: {type(result.get('_agent3_ran'))}")

if result.get('_agent3_ran') is True:
    print("\n✅ SUCCESS: Agent3 correctly sets _agent3_ran = True")
else:
    print(f"\n❌ FAILURE: Agent3 returns _agent3_ran = {result.get('_agent3_ran')}")

print("\n" + "=" * 60)
print("Number of programs returned:", len(result.get('ranked_programs', [])))
print("=" * 60)
