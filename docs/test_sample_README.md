# Test Sample Programs - README

## Overview
This document describes the test sample of 20 programs created from `structured_program_db_all_bw.json` for testing the 5 profiles in `test_profiles.json`.

## Sample Composition

The sample includes **20 diverse programs** selected to test various aspects of the recommendation system:

### 1. Profile-Relevant Programs (10 programs)
Programs that match the interests and desired fields of the 5 test profiles:

**For Profile 1 (Vietnamese CS/AI student):**
- Computer and Information Science (University of Konstanz)
- Industrial Artificial Intelligence (Albstadt-Sigmaringen University)
- Applied Artificial Intelligence (MAAI) (Heilbronn University)
- Bioinformatics (University of Tübingen)

**For Profile 2 & 5 (Indian Business & Pakistani Marketing):**
- Master of Science in Economics (University of Mannheim)
- Economics and Finance (University of Tübingen)
- Corporate Management & Economics (Zeppelin University)
- Digital Business Management (Pforzheim University)

**For Profile 3 (Spanish Economics):**
- Economics and Finance (University of Tübingen)
- Master of Science in Economics (University of Mannheim)

**For Profile 4 (German Business Informatics):**
- Digital Business Management (Pforzheim University)
- International Business and Intercultural Management (Reutlingen University)

### 2. Moderately Relevant Programs (6 programs)
Programs in related fields that might partially match:
- Intelligent Mechatronic Systems (Heilbronn University)
- Master of Engineering in Electrical Engineering (Aalen University)
- Master of Science in Chemistry (Ulm University)
- Master of Science in Chemical Engineering (Ulm University)
- Life Science Innovation (University of Hohenheim)
- Master of Science in Biotechnology (University of Hohenheim)

### 3. Unrelated Programs (4 programs)
Programs completely outside the profiles' interests to test filtering:
- International Master of Landscape Architecture (Nürtingen-Geislingen University)
- Advisory and Innovation Services in Agri-Food Systems (University of Hohenheim)
- Food Science and Technology (University of Hohenheim)
- Dance Movement Therapy (SRH University)

## Diversity Characteristics

### By Tuition Fee (Non-EU):
- **Free (0 EUR):** 4 programs
- **Low Fee (≤1500 EUR):** 14 programs
- **High Fee (>3000 EUR):** 2 programs
  - Dance Movement Therapy: 5,450 EUR
  - Applied Computer Science: 6,950 EUR

### By Application Mode:
- **Direct Application:** 17 programs
- **VPD (uni-assist):** 3 programs
  - International Master of Landscape Architecture
  - Applied Artificial Intelligence (MAAI)
  - International Business and Intercultural Management

### By Field:
- **Computer Science/AI:** 17 programs
- **Business/Economics:** 11 programs
- **Engineering:** 9 programs
- **Science:** 14 programs
- **Agriculture:** 4 programs

### By City:
Programs are distributed across multiple cities in Baden-Württemberg:
- Stuttgart, Tübingen, Mannheim, Konstanz, Ulm, Heilbronn, Aalen, Albstadt, Friedrichshafen, Nürtingen, Heidelberg, Pforzheim, Reutlingen

## Testing Scenarios

This sample enables testing of:

1. **Hard Filters:**
   - GPA requirements (some programs require 2.5, 3.0)
   - Tuition fee limits (profiles have budgets from 2,000 to 10,000 EUR)
   - Language requirements (English B2/C1, some require German)
   - ECTS requirements (specific domain requirements)

2. **Soft Matching:**
   - Field relevance (CS vs Business vs Agriculture)
   - Interest alignment (AI, Marketing, Economics, etc.)
   - City preferences (Stuttgart, Mannheim, etc.)

3. **Application Mode:**
   - Direct vs VPD application processes
   - Different deadlines for EU vs non-EU applicants

4. **Edge Cases:**
   - Programs with no tuition fee vs high tuition
   - Programs requiring work experience vs no requirement
   - Programs requiring internships
   - Programs with specific ECTS requirements in certain domains

## Files Generated

1. **test_sample_programs.json** - The main sample file containing 20 programs
2. **create_test_sample.py** - The script used to generate the sample
3. **test_sample_README.md** - This documentation file

## Usage

Use `test_sample_programs.json` as input to your recommendation system instead of the full `structured_program_db_all_bw.json` for faster testing and validation of:
- Profile extraction accuracy
- Hard filter logic
- Soft matching algorithms
- Ranking and scoring mechanisms
- Timeline generation
- Report generation

## Expected Behavior by Profile

### Profile 1 (Vietnamese CS/AI):
- **Should match:** CS/AI programs with tuition ≤3,000 EUR, English requirements met
- **Should filter out:** High-fee programs, Agriculture programs, programs requiring German

### Profile 2 (Indian Business):
- **Should match:** Business/Economics programs with tuition ≤5,000 EUR
- **Should filter out:** CS-only programs, Agriculture programs

### Profile 3 (Spanish Economics - EU):
- **Should match:** Economics programs, benefits from EU tuition rates
- **Should filter out:** Programs requiring high GPA (has 3.1 German GPA)

### Profile 4 (German Business Informatics - EU):
- **Should match:** Business Informatics, Digital Business programs
- **Should filter out:** Pure agriculture, high-fee programs

### Profile 5 (Pakistani Marketing):
- **Should match:** Marketing, Business programs with tuition ≤4,000 EUR
- **Should filter out:** Technical CS programs, Agriculture programs
