import json
import random

# Load the test profiles
with open('test_profiles.json', 'r') as f:
    profiles_data = json.load(f)
    test_profiles = profiles_data['test_profiles']

# Load all programs
with open('structured_program_db_all_bw.json', 'r') as f:
    all_programs = json.load(f)

print(f"Total programs available: {len(all_programs)}")
print(f"Total test profiles: {len(test_profiles)}")

# Extract profile interests and desired programs for matching
profile_interests = {}
for profile in test_profiles:
    profile_id = profile['id']
    interests = profile['gold_standard']['expected_profile']['interests']
    desired = profile['gold_standard']['expected_profile']['desired_programs']
    bachelor_field = profile['gold_standard']['expected_profile']['bachelor_field']
    profile_interests[profile_id] = {
        'interests': [i.lower() for i in interests],
        'desired': [d.lower() for d in desired],
        'bachelor_field': bachelor_field.lower()
    }

print("\nProfile interests summary:")
for pid, data in profile_interests.items():
    print(f"{pid}: {data['desired']}")

# Categorize programs for diverse sampling
def categorize_program(program):
    """Categorize a program based on its characteristics"""
    program_name = program['program_name'].lower()
    content = program.get('course_content_summary', '').lower()
    
    categories = []
    
    # Field categories
    if any(keyword in program_name or keyword in content for keyword in ['computer', 'data science', 'artificial intelligence', 'machine learning', 'ai']):
        categories.append('CS_AI')
    if any(keyword in program_name or keyword in content for keyword in ['business', 'management', 'mba', 'marketing', 'economics']):
        categories.append('BUSINESS')
    if any(keyword in program_name or keyword in content for keyword in ['engineering', 'mechanical', 'civil', 'environmental']):
        categories.append('ENGINEERING')
    if any(keyword in program_name or keyword in content for keyword in ['physics', 'chemistry', 'biology', 'science']):
        categories.append('SCIENCE')
    if any(keyword in program_name or keyword in content for keyword in ['agriculture', 'food', 'animal']):
        categories.append('AGRICULTURE')
    
    # Tuition fee categories
    tuition = program.get('non_eu_tuition_fee_eur', 0)
    if tuition is None:
        tuition = 0
    if tuition == 0:
        categories.append('FREE')
    elif tuition <= 1500:
        categories.append('LOW_FEE')
    elif tuition <= 3000:
        categories.append('MID_FEE')
    else:
        categories.append('HIGH_FEE')
    
    # Application mode
    if program.get('application_mode') == 'VPD':
        categories.append('VPD')
    else:
        categories.append('DIRECT')
    
    return categories

# Categorize all programs
categorized_programs = {}
for program in all_programs:
    categories = categorize_program(program)
    for cat in categories:
        if cat not in categorized_programs:
            categorized_programs[cat] = []
        categorized_programs[cat].append(program)

print("\nProgram categories:")
for cat, progs in categorized_programs.items():
    print(f"{cat}: {len(progs)} programs")

# Select diverse sample of 20 programs
sample_programs = []
used_program_ids = set()

# Strategy: 
# 1. Select some highly relevant programs for each profile (8 programs)
# 2. Select some moderately relevant programs (4 programs)
# 3. Select some completely unrelated programs (4 programs)
# 4. Select programs with different tuition fees (2 programs)
# 5. Select programs with different application modes (2 programs)

# 1. Highly relevant programs (2 per profile type, but we have 5 profiles)
# Profile 1 (CS/AI): 2 programs
cs_ai_programs = [p for p in categorized_programs.get('CS_AI', []) if p['program_id'] not in used_program_ids]
if cs_ai_programs:
    selected = random.sample(cs_ai_programs, min(2, len(cs_ai_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])

# Profile 2 & 5 (Business/Marketing): 2 programs
business_programs = [p for p in categorized_programs.get('BUSINESS', []) if p['program_id'] not in used_program_ids]
if business_programs:
    selected = random.sample(business_programs, min(2, len(business_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])

# Profile 3 (Economics): 2 programs - overlap with business
econ_programs = [p for p in business_programs if p['program_id'] not in used_program_ids and 'econom' in p['program_name'].lower()]
if econ_programs:
    selected = random.sample(econ_programs, min(2, len(econ_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])
elif business_programs:
    # If no specific economics programs, take more business programs
    remaining_business = [p for p in business_programs if p['program_id'] not in used_program_ids]
    if remaining_business:
        selected = random.sample(remaining_business, min(2, len(remaining_business)))
        sample_programs.extend(selected)
        used_program_ids.update([p['program_id'] for p in selected])

# Profile 4 (Business Informatics): 2 programs - mix of CS and Business
informatics_programs = [p for p in all_programs if p['program_id'] not in used_program_ids and 
                       ('informatic' in p['program_name'].lower() or 'information system' in p['program_name'].lower())]
if informatics_programs:
    selected = random.sample(informatics_programs, min(2, len(informatics_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])
else:
    # Mix of CS and Business
    remaining_cs = [p for p in cs_ai_programs if p['program_id'] not in used_program_ids]
    if remaining_cs:
        selected = random.sample(remaining_cs, min(1, len(remaining_cs)))
        sample_programs.extend(selected)
        used_program_ids.update([p['program_id'] for p in selected])

# 2. Moderately relevant programs (4 programs) - related fields
engineering_programs = [p for p in categorized_programs.get('ENGINEERING', []) if p['program_id'] not in used_program_ids]
if engineering_programs:
    selected = random.sample(engineering_programs, min(2, len(engineering_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])

science_programs = [p for p in categorized_programs.get('SCIENCE', []) if p['program_id'] not in used_program_ids]
if science_programs:
    selected = random.sample(science_programs, min(2, len(science_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])

# 3. Completely unrelated programs (4 programs)
agriculture_programs = [p for p in categorized_programs.get('AGRICULTURE', []) if p['program_id'] not in used_program_ids]
if agriculture_programs:
    selected = random.sample(agriculture_programs, min(4, len(agriculture_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])

# 4. Different tuition fees (ensure variety)
# Add high fee programs if not enough
high_fee_programs = [p for p in categorized_programs.get('HIGH_FEE', []) if p['program_id'] not in used_program_ids]
if len(sample_programs) < 18 and high_fee_programs:
    selected = random.sample(high_fee_programs, min(2, len(high_fee_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])

# 5. Different application modes (ensure VPD programs)
vpd_programs = [p for p in categorized_programs.get('VPD', []) if p['program_id'] not in used_program_ids]
if len(sample_programs) < 20 and vpd_programs:
    needed = 20 - len(sample_programs)
    selected = random.sample(vpd_programs, min(needed, len(vpd_programs)))
    sample_programs.extend(selected)
    used_program_ids.update([p['program_id'] for p in selected])

# Fill remaining slots with random programs
if len(sample_programs) < 20:
    remaining_programs = [p for p in all_programs if p['program_id'] not in used_program_ids]
    needed = 20 - len(sample_programs)
    if remaining_programs:
        selected = random.sample(remaining_programs, min(needed, len(remaining_programs)))
        sample_programs.extend(selected)

# Ensure exactly 20 programs
sample_programs = sample_programs[:20]

print(f"\nSelected {len(sample_programs)} programs for testing")

# Save the sample
output_data = {
    "description": "Sample of 20 programs for testing 5 profiles. Includes variety of fields, tuition fees, and application modes.",
    "total_programs": len(sample_programs),
    "programs": sample_programs
}

with open('test_sample_programs.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print("\nSample saved to test_sample_programs.json")

# Print summary
print("\n=== SAMPLE SUMMARY ===")
print(f"Total programs: {len(sample_programs)}")

# Count by category
category_counts = {}
for program in sample_programs:
    categories = categorize_program(program)
    for cat in categories:
        category_counts[cat] = category_counts.get(cat, 0) + 1

print("\nCategory distribution:")
for cat, count in sorted(category_counts.items()):
    print(f"  {cat}: {count}")

print("\nPrograms by tuition fee:")
for program in sorted(sample_programs, key=lambda x: x.get('non_eu_tuition_fee_eur') or 0):
    tuition = program.get('non_eu_tuition_fee_eur') or 0
    print(f"  {program['program_name'][:50]:50} - {tuition:>7.2f} EUR - {program.get('application_mode', 'N/A')}")
