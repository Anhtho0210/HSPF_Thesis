# Agent 1 Testing Guide

## 📋 What This Test Script Does

The `test_agent1.py` script comprehensively tests Agent 1 with **4 test suites**:

### ✅ **Test Suite 1: ECTS Conversion Accuracy**
Tests all 5 profiles to verify ECTS conversion is correct:
- Profile 1 (Vietnamese): 130 credits → 195 ECTS
- Profile 2 (Indian): 180 credits → 180 ECTS  
- Profile 3 (Chinese): 140 credits → 210 ECTS
- Profile 4 (Spanish): 240 ECTS → 240 ECTS
- Profile 5 (US): 120 credits → 180 ECTS

**Success Criteria:** All conversions within ±0.5 ECTS

---

### ✅ **Test Suite 2: GPA Conversion to German Scale**
Tests GPA conversion from different grading systems:
- Vietnamese 3.5/4.0 → German 2.0
- Indian 75/100 → German 2.5
- Chinese 3.8/4.0 → German 1.5
- Spanish 6.5/10 → German 2.8
- US 3.6/4.0 → German 1.8

**Success Criteria:** All conversions within ±0.3 on German scale

---

### ✅ **Test Suite 3: Field Extraction from Natural Language**
Tests extraction of all required fields from input text:
- ✓ Full name
- ✓ Citizenship
- ✓ Bachelor field of study
- ✓ Total credits & semesters
- ✓ GPA (score, max scale)
- ✓ Language proficiency (test type, score)
- ✓ Preferences (tuition, semester, location)
- ✓ Interests

**Success Criteria:** ≥80% of fields extracted correctly

---

### ✅ **Test Suite 4: PDF Transcript Parsing**
Tests PDF parsing capability:
- ✓ Extract all courses from PDF
- ✓ Extract credits for each course
- ✓ Handle multi-page PDFs

**Success Criteria:** 
- Extract ≥30 courses (Profile 1)
- ≥90% of courses have credits

---

## 🚀 How to Run

### **Prerequisites:**
```bash
# Make sure you have Agent1.py in the same directory
# Make sure test_profiles.json exists
# Make sure all 5 PDF transcript files exist
```

### **Run the test:**
```bash
cd "/Users/ther/Documents/HS Pforzheim/Agent"
python3 test_agent1.py
```

---

## 📊 Expected Output

```
================================================================================
AGENT 1 COMPREHENSIVE TEST SUITE
================================================================================

================================================================================
TEST: ECTS Conversion Accuracy
================================================================================

Testing PROFILE-001-VN-CS...
✓ PASS - ECTS Conversion (130 credits → 195.0 ECTS)

Testing PROFILE-002-IN-BUS...
✓ PASS - ECTS Conversion (180 credits → 180.0 ECTS)

...

ECTS Conversion Summary: 5/5 tests passed

================================================================================
TEST: GPA Conversion to German Scale
================================================================================

Testing PROFILE-001-VN-CS...
✓ PASS - GPA Conversion to German Scale

...

GPA Conversion Summary: 5/5 tests passed

================================================================================
TEST: Field Extraction from Natural Language
================================================================================

Testing Profile 1 (Vietnamese CS)...
✓ PASS - Extract Full Name
✓ PASS - Extract Citizenship
✓ PASS - Extract Bachelor Field
...

Field Extraction Summary: 11/11 tests passed

================================================================================
TEST: PDF Transcript Parsing
================================================================================

Testing PROFILE-001-VN-CS...
✓ PASS - PDF Parsing - Extract Courses
✓ PASS - PDF Parsing - Extract Credits

...

PDF Parsing Summary: 2/2 tests passed

================================================================================
FINAL SUMMARY
================================================================================
✓ PASS - ECTS Conversion
✓ PASS - GPA Conversion
✓ PASS - Field Extraction
✓ PASS - PDF Parsing

Overall: 4/4 test suites passed

🎉 ALL TESTS PASSED! Agent 1 is ready for evaluation.
```

---

## ❌ If Tests Fail

### **Common Issues:**

**1. Import Error:**
```
ModuleNotFoundError: No module named 'Agent1'
```
**Fix:** Make sure `Agent1.py` is in the same directory

**2. File Not Found:**
```
FileNotFoundError: test_profiles.json
```
**Fix:** Make sure `test_profiles.json` exists in the same directory

**3. PDF Not Found:**
```
FileNotFoundError: PROFILE_001_VN_CS_Transcript.pdf
```
**Fix:** Run `python3 generate_test_transcripts.py` first

**4. ECTS Conversion Failed:**
```
✗ FAIL - ECTS Conversion (130 credits → 195.0 ECTS)
  Expected: 195.0 ECTS (±0.5)
  Actual:   190.0 ECTS
```
**Fix:** Check Agent 1's ECTS conversion formula

**5. GPA Conversion Failed:**
```
✗ FAIL - GPA Conversion to German Scale
  Expected: 2.0 (±0.3)
  Actual:   2.5
```
**Fix:** Check Agent 1's GPA conversion formula (Modified Bavarian Formula)

---

## 📈 For Your Thesis

### **Chapter 5.2.1: Agent 1 Evaluation Results**

Use the test results to create tables:

**Table 5.1: ECTS Conversion Accuracy**
| Profile | Original Credits | Semesters | Expected ECTS | Actual ECTS | Error | Pass |
|---------|-----------------|-----------|---------------|-------------|-------|------|
| VN-CS   | 130             | 8         | 195.0         | 195.0       | 0.0   | ✓    |
| IN-BUS  | 180             | 6         | 180.0         | 180.0       | 0.0   | ✓    |
| ...     | ...             | ...       | ...           | ...         | ...   | ...  |

**Table 5.2: GPA Conversion Accuracy**
| Profile | Original GPA | Scale | Expected German | Actual German | Error | Pass |
|---------|-------------|-------|-----------------|---------------|-------|------|
| VN-CS   | 3.5/4.0     | 4.0   | 2.0             | 2.0           | 0.0   | ✓    |
| ...     | ...         | ...   | ...             | ...           | ...   | ...  |

---

## 🔧 Customization

### **Adjust Tolerances:**
```python
# In test_ects_conversion()
"tolerance": 0.5  # Change to 1.0 for looser tolerance

# In test_gpa_conversion()
"tolerance": 0.3  # Change to 0.5 for looser tolerance
```

### **Add More Tests:**
```python
def test_custom_feature():
    """Test your custom feature"""
    # Add your test logic here
    pass

# Add to main()
results['Custom Feature'] = test_custom_feature()
```

---

## ✅ Next Steps After Agent 1 Tests Pass

1. ✅ Document results in thesis
2. ✅ Create test script for Agent 3 (filtering)
3. ✅ Create test script for Agent 5 (timeline)
4. ✅ Run end-to-end tests

Good luck! 🚀
