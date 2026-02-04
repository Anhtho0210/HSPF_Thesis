# Ground Truth Filtering Summary

## ✅ Filtering Complete

The Excel file `agent3_ground_truth_FILLED.xlsx` has been filtered to remove irrelevant programs.

## Filtering Criteria

### Sheet 2 (Degree Compatibility)
**Rule**: Keep only programs that pass **ALL** hard constraints
- GPA Pass = YES
- Tuition Pass = YES
- Location Pass = YES
- Semester Pass = YES
- English Pass = YES (if applicable)
- Work Experience Pass = YES (if applicable)

### Sheet 3 (Overall Ranking)
**Rule**: Keep only programs that:
1. Pass ALL hard constraints **AND**
2. Have relevance score ≥ 2.5 out of 5.0 (which equals 0.5 on normalized 0-1 scale)

## Results

| Sheet | Before | After | Removed | Criteria |
|-------|--------|-------|---------|----------|
| **Sheet 1** (Hard Constraints) | 105 | 105 | 0 | Not filtered (reference data) |
| **Sheet 2** (Degree Compatibility) | 100 | 38 | 62 | Pass ALL hard constraints |
| **Sheet 3** (Overall Ranking) | 100 | 2 | 98 | Pass hard constraints + score ≥ 2.5 |

## Key Findings

### Programs Passing ALL Hard Constraints
- **38 out of 100** program-profile combinations pass all hard constraints
- This represents **38%** pass rate across all profiles
- These 38 programs are the only ones that should be evaluated for degree compatibility and semantic matching

### Relevance Scores
- Only **2 programs** had relevance scores filled in (both scored 5/5)
- **98 programs** had empty relevance scores and were removed from Sheet 3
- The 2 remaining programs:
  - PROFILE-002-IN-BUS | Digital Business Management (MSc) | Score: 5
  - PROFILE-005-PK-MKT | International Business and Intercultural Management (MSc) | Score: 5

## What This Means

### For Sheet 2 (Degree Compatibility)
✅ **Ready to use** - Contains only the 38 programs that passed hard constraints  
✅ **Efficient** - No need to manually check which programs to evaluate  
✅ **Accurate** - Degree compatibility only matters for programs students can actually apply to

### For Sheet 3 (Overall Ranking)
⚠️ **Needs completion** - Only 2 programs have relevance scores filled in  
📝 **Action needed**: Fill in relevance scores for the remaining 36 programs that passed hard constraints  
💡 **Tip**: Focus on scoring only the 38 programs in Sheet 2 (those that passed hard constraints)

## How to Complete Sheet 3

Since only programs that pass hard constraints matter, you should:

1. **Use Sheet 2 as reference** - It has the 38 programs worth evaluating
2. **Score each program** - Rate relevance from 1-5 based on:
   - How well the program matches student interests
   - How relevant the course content is to desired career path
   - Whether it's in the student's desired program list
3. **Fill Expected Top N** - Mark which programs should appear in top 10 results
4. **Re-run filter** - After filling scores, run `python filter_ground_truth.py` again

## Verification

After filtering:
- ✅ Sheet 1: 105 rows (unchanged - reference data)
- ✅ Sheet 2: 38 rows (only programs passing hard constraints)
- ✅ Sheet 3: 2 rows (only programs with scores ≥ 2.5 AND passing hard constraints)

## Next Steps

1. ✅ Filtering complete
2. ⏳ Fill relevance scores for 36 remaining programs in Sheet 3
3. ⏳ Re-run `python filter_ground_truth.py` after scoring
4. ⏳ Run `python add_layer_percentages.py` to update Layer Summary
5. ⏳ Compare with actual Agent3 results using `python quick_test_agent3.py`

## Script Usage

To re-run the filtering (e.g., after adding more scores):
```bash
python filter_ground_truth.py
```

The script will:
- Analyze which programs pass ALL hard constraints
- Filter Sheet 2 to keep only those programs
- Filter Sheet 3 to keep only programs with score ≥ 2.5 AND passing hard constraints
- Overwrite the original file with filtered data
