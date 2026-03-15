# MasterMatch — AI-Powered Master's Program Advisor for Germany

> **Thesis Project** · Hochschule Pforzheim · Anh-Tho Tran
>
> A multi-agent AI system that guides international students from a raw profile description to a personalised, print-ready application strategy for German Master's programs — all in one automated pipeline.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Prerequisites & Installation](#prerequisites--installation)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Key Technical Details](#key-technical-details)
- [Evaluation](#evaluation)
- [Limitations & Future Work](#limitations--future-work)

---

## Overview

MasterMatch is an end-to-end pipeline built with [LangGraph](https://github.com/langchain-ai/langgraph) and Google's Gemini model family. It automates the most time-consuming steps of applying to German universities for international students:

| Step | What it does |
|---|---|
| **Profile Intake** | Conversational extraction of academic background, GPA, language scores, interests, and transcript via natural language + PDF |
| **Smart Matching** | A 4-layer funnel that filters 500+ Master's programs in Baden-Württemberg down to the best-fit candidates |
| **Document Checklist** | Real-time web search (Perplexity) for program- and country-specific required documents |
| **Application Timeline** | Milestone calendar with urgency indicators, calibrated to citizenship rules (APS, Uni-Assist, HEC, etc.) |
| **PDF Report** | A personalised, ready-to-use strategy document the student can act on immediately |

---

## System Architecture

```
User Input (natural language + PDF transcript)
            │
            ▼
┌───────────────────────┐
│      AGENT 1          │  agents/agent1_intake.py
│   Profile Intake      │  • Gemini Flash — structured extraction
│                       │  • LangGraph stateful chat loop
│                       │  • GPA → German scale converter
│                       │  • Non-European ECTS normaliser
└──────────┬────────────┘
           │  Completed UserProfile object
           ▼
┌───────────────────────┐
│      AGENT 3          │  agents/agent3_matcher.py
│  4-Layer Matching     │
│                       │  L1  Hard Constraints  (GPA, budget, location…)
│                       │  L2  Degree Compatibility  (Gemini 2.5 Pro LLM)
│                       │  L3  Semantic Ranking  (Gemini Embeddings + TF-IDF)
│                       │  L4  ECTS Audit  (transcript vs. program requirements)
└──────────┬────────────┘
           │  Top-10 ranked programs
           ▼
┌───────────────────────┐
│      AGENT 4          │  agents/agent4_checklist.py
│  Document Checklist   │  • Perplexity sonar-pro web search
│                       │  • Country-specific rules (APS / HEC / Uni-Assist)
└──────────┬────────────┘
           │  Programs + checklists
           ▼
┌───────────────────────┐
│      AGENT 5          │  agents/agent5_planner.py
│  Timeline Planner     │  • Milestone generation engine
│                       │  • Urgency / overdue detection
│                       │  • APS 6-month lead-time rule
└──────────┬────────────┘
           │  Personalised timelines
           ▼
┌───────────────────────┐
│      AGENT 6          │  agents/agent6_report.py
│  PDF Report Generator │  • ReportLab multi-page PDF
│                       │  • Score breakdown with visual bars
│                       │  • Program comparison table
│                       │  • Disclaimer & verification notes
└──────────┬────────────┘
           │
           ▼
  outputs/My_Application_Strategy.pdf
```

---

## Project Structure

```
HSPF_Thesis/
│
├── main.py                      # 🚀 Entry point — LangGraph workflow orchestrator
├── models.py                    # Pydantic data models (UserProfile, AgentState, …)
├── requirements.txt             # Python dependencies
├── .env.example                 # API key template (copy to .env)
│
├── agents/                      # Core agent modules
│   ├── __init__.py
│   ├── agent1_intake.py         # Profile intake & NLU
│   ├── agent3_matcher.py        # 4-layer program matching funnel
│   ├── agent4_checklist.py      # Document checklist (Perplexity search)
│   ├── agent5_planner.py        # Application timeline planner
│   └── agent6_report.py         # PDF report generator
│
├── data/                        # Program databases (JSON)
│   ├── structured_program_db_all_bw.json   # Primary DB — 500+ BW programs
│   ├── structured_program_db_BW.json
│   ├── structured_program_db.json
│   └── MASTER_LIST_ALL_BW.json             # Raw scraped data
│
├── data_pipeline/               # Data collection & DB building
│   ├── __init__.py
│   ├── crawling_data.py         # Selenium scraper → DAAD portal
│   └── build_database.py        # LLM-based structured DB builder
│
├── evaluation/                  # Testing, evaluation & ground truth
│   ├── __init__.py
│   ├── test_agent1.py           # Unit tests — profile extraction (5 profiles)
│   ├── test_agent3.py           # Evaluation — matching accuracy & metrics
│   ├── quick_test_agent3.py     # Fast sanity check for Agent 3
│   ├── evaluate_system.py       # End-to-end system evaluation (P / R / F1)
│   ├── test_profiles.json       # 5 synthetic international student profiles
│   ├── test_sample_programs.json
│   └── agent3_ground_truth_FILLED.xlsx     # Hand-labelled ground truth
│
├── transcripts/                 # Synthetic student PDF transcripts
│   ├── PROFILE_001_VN_CS_Transcript.pdf    # Vietnam — Computer Science
│   ├── PROFILE_002_IN_BUS_Transcript.pdf   # India — Business
│   ├── PROFILE_003_ES_ECON_Transcript.pdf  # Spain — Economics
│   ├── PROFILE_004_DE_BINF_Transcript.pdf  # Germany — Bioinformatics
│   └── PROFILE_005_PK_MKT_Transcript.pdf   # Pakistan — Marketing
│
├── outputs/                     # Generated application strategy PDFs
│   └── My_Application_Strategy_0X.pdf
│
└── docs/                        # Documentation & reports
    ├── agent3_testing_report.md
    ├── Agent5_Timeline_Logic_Report.md
    └── FILTERING_SUMMARY.md
```

---

## Prerequisites & Installation

**Requirements:** Python ≥ 3.11, Chrome browser (for data pipeline only).

```bash
# 1. Clone the repository
git clone https://github.com/Anhtho0210/HSPF_Thesis.git
cd HSPF_Thesis

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

```bash
# Copy the template and fill in your API keys
cp .env.example .env
```

Open `.env` and set:

```env
GEMINI_API_KEY=your_google_gemini_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) |
| `PERPLEXITY_API_KEY` | [Perplexity Labs](https://www.perplexity.ai/settings/api) |

---

## Running the System

### Full Pipeline

```bash
python main.py
```

The workflow will:
1. Parse the student profile from the hard-coded initial input in `main.py` (edit to change student).
2. Run the 4-layer funnel against `data/structured_program_db_all_bw.json`.
3. Display the top-10 ranked programs, then **pause** for your selection (up to 3 programs).
4. Fetch document checklists, build timelines, and generate a PDF in the project root.

> 💡 To change the student profile, edit `initial_raw_input` and `pdf_filename` inside `main.py`.

### Individual Agent Tests

```bash
# Test Agent 1 — profile extraction on all 5 synthetic profiles
python evaluation/test_agent1.py

# Test Agent 3 — matching accuracy & F1 scores
python evaluation/test_agent3.py

# End-to-end system evaluation
python evaluation/evaluate_system.py
```

### Rebuild the Program Database (optional)

```bash
# Step 1: Scrape DAAD for English-taught Master's programs in Baden-Württemberg
python data_pipeline/crawling_data.py

# Step 2: Build the structured JSON database using the LLM
python data_pipeline/build_database.py
```

---

## Key Technical Details

### Agent 3 — 4-Layer Matching Funnel

| Layer | Technique | Purpose |
|---|---|---|
| **L1 Hard Constraints** | Rule-based filters | GPA, tuition budget, location, work experience, semester availability |
| **L2 Degree Compatibility** | Gemini 2.5 Pro LLM | "Is Marketing a valid background for a Business Analytics master?" |
| **L3 Semantic Ranking** | Gemini Embeddings + TF-IDF (50/50 hybrid) | Concept + keyword similarity between student interests and program content |
| **L4 ECTS Audit** | Embedding-based credit matching | Verifies transcript covers the program's subject prerequisites |

**Final Score formula:**

```
Score = (Semantic Score × 0.50) + (ECTS Match × 0.40) + (Degree Compatibility × 0.10)
```

### ECTS Credit Normalisation

For non-European transcripts, credit hours are automatically converted:

```
Conversion Factor = (Semesters × 30 ECTS) ÷ Total Credits Earned
Converted ECTS    = Original Credits × Factor
```

Credits already in the 170–250 range are assumed to be native ECTS (factor = 1.0).

### Country-Specific Admission Rules

| Citizenship | Requirement | Lead Time |
|---|---|---|
| China, Vietnam, India, Mongolia | **APS Certificate** | ~6 months, ~€180 |
| Pakistan | **HEC Attestation** | Varies |
| Most non-EU via certain universities | **Uni-Assist / VPD** | 4–6 weeks, €75+ |

---

## Evaluation

The system was evaluated against a hand-labelled ground-truth dataset (`evaluation/agent3_ground_truth_FILLED.xlsx`) covering **5 international student profiles** across 500+ programs.

| Profile | Background | Citizenship |
|---|---|---|
| PROFILE-001 | Computer Science | Vietnam (Non-EU) |
| PROFILE-002 | Business Administration | India (Non-EU) |
| PROFILE-003 | Economics | Spain (EU) |
| PROFILE-004 | Bioinformatics | Germany (EU) |
| PROFILE-005 | Marketing | Pakistan (Non-EU) |

Key metrics reported: **Precision, Recall, F1-Score, NDCG@3** per layer and end-to-end.
Full report: [`docs/agent3_testing_report.md`](docs/agent3_testing_report.md)

---

## Limitations & Future Work

- The program database is scoped to **Baden-Württemberg** by design (thesis research focus).
- Agent 4 (Perplexity search) may return incomplete checklists for programs with poorly structured websites.
- The system runs as a **CLI tool**; a web interface would significantly improve usability.
- Deadline parsing may fail for non-standard date strings — a fallback manual-check event is inserted automatically.

---

## Licence

This project is a thesis prototype developed at **Hochschule Pforzheim** and is intended for academic use only.
© 2025 Anh-Tho Tran. All rights reserved.
