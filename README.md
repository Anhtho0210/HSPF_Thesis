# 🎓 MasterMatch — AI-Powered Master's Program Advisor for Germany

> **Thesis Project** · Hochschule Pforzheim · Anh-Tho Tran  
> A multi-agent AI system that helps international students find, evaluate, and apply to German Master's programs — from profile intake to a personalised PDF application strategy.

---

## 📌 Overview

**MasterMatch** is an end-to-end AI pipeline built with [LangGraph](https://github.com/langchain-ai/langgraph) and Google's Gemini LLM family. It automates the most time-consuming parts of the German university application process for international students:

1. **Profile Intake** — conversational extraction of the student's academic background, language scores, preferences, and transcript.
2. **Smart Matching** — a 4-layer funnel that filters 500 + Master's programs from Baden-Württemberg down to the best-fit candidates.
3. **Document Checklist** — real-time web search (via Perplexity) for country-specific, program-specific required documents.
4. **Application Timeline** — generates a milestone calendar with urgency flags, calibrated to the student's citizenship (APS, Uni-Assist, HEC Attestation, etc.).
5. **PDF Report** — a personalised, ready-to-use strategy document the student can act on immediately.

---

## 🏗️ Architecture — The Agent Pipeline

```
📄 PDF Transcript                          💬 User Input (natural language)
        │                                              │
        └──────────────────────────┬──────────────────┘
                                   ▼
                         ┌─────────────────┐
                         │   AGENT 1       │  Profile Intake & NLU
                         │  (Agent1.py)    │  • LLM-based extraction (Gemini Flash)
                         │                 │  • Stateful chat loop (LangGraph)
                         │                 │  • GPA → German scale converter
                         │                 │  • Non-European ECTS normaliser
                         └────────┬────────┘
                                  │ Completed UserProfile
                                  ▼
                         ┌─────────────────┐
                         │   AGENT 3       │  4-Layer Program Matching Funnel
                         │  (Agent3.py)    │
                         │                 │  L1 Hard Constraints (GPA, budget, location…)
                         │                 │  L2 LLM Degree Compatibility (Gemini Pro)
                         │                 │  L3 Semantic Ranking (Gemini Embeddings + TF-IDF)
                         │                 │  L4 Deep ECTS Verification (transcript audit)
                         └────────┬────────┘
                                  │ Top-10 ranked programs
                                  ▼
                         ┌─────────────────┐
                         │   AGENT 4       │  Document Checklist Generator
                         │  (Agent4.py)    │  • Perplexity sonar-pro web search
                         │                 │  • Country-specific requirements
                         │                 │  • APS / HEC / Uni-Assist detection
                         └────────┬────────┘
                                  │ Programs + checklists
                                  ▼
                         ┌─────────────────┐
                         │   AGENT 5       │  Application Timeline Planner
                         │  (Agent5.py)    │  • Milestone generation engine
                         │                 │  • Urgency / overdue detection
                         │                 │  • APS 6-month lead-time rule
                         └────────┬────────┘
                                  │ Personalised timelines
                                  ▼
                         ┌─────────────────┐
                         │   AGENT 6       │  PDF Report Generator
                         │  (Agent6.py)    │  • ReportLab-based multi-page PDF
                         │                 │  • Score breakdown + visual bars
                         │                 │  • Program comparison table
                         │                 │  • Disclaimer & verification section
                         └────────┬────────┘
                                  │
                                  ▼
                    📄 My_Application_Strategy.pdf
```

---

## 📂 Repository Structure

```
Agent/
│
├── main.py                      # 🚀 Main entry point — LangGraph workflow orchestrator
│
│── Data Collection
│   ├── Crawling_Data.py         # Selenium scraper → DAAD programme portal
│   ├── build_database.py        # LLM-based structured program DB builder
│   └── structured_program_db_all_bw.json  # 500+ BW programs (primary DB)
│
├── Core Agents
│   ├── models.py                # Pydantic data models (UserProfile, AgentState, …)
│   ├── Agent1.py                # Profile intake & conversational NLU
│   ├── Agent3.py                # 4-layer program matching funnel
│   ├── Agent4.py                # Document checklist (Perplexity web search)
│   ├── Agent5.py                # Application timeline planner
│   └── Agent6.py                # PDF report generator
│
├── Evaluation & Testing
│   ├── test_agent1.py           # Unit tests — profile extraction (5 profiles)
│   ├── test_agent3.py           # Evaluation — matching accuracy & metrics
│   ├── test_agent4_fix.py       # Integration tests — Agent 4
│   ├── evaluate_system.py       # End-to-end system evaluation
│   ├── quick_test_agent3.py     # Fast sanity check for Agent 3
│   ├── agent3_testing_report.md # Detailed Agent 3 evaluation report
│   ├── agent3_ground_truth_FILLED.xlsx  # Ground-truth labels (5 profiles × N programs)
│   └── test_profiles.json       # 5 synthetic international student profiles
│
├── Test Transcripts (Synthetic)
│   ├── PROFILE_001_VN_CS_Transcript.pdf   # Vietnam — Computer Science
│   ├── PROFILE_002_IN_BUS_Transcript.pdf  # India — Business
│   ├── PROFILE_003_ES_ECON_Transcript.pdf # Spain — Economics
│   ├── PROFILE_004_DE_BINF_Transcript.pdf # Germany — Bioinformatics
│   └── PROFILE_005_PK_MKT_Transcript.pdf  # Pakistan — Marketing
│
├── Sample PDF Outputs
│   ├── My_Application_Strategy_01.pdf  … _05.pdf
│
└── Utilities
    ├── generate_test_transcripts.py
    ├── generate_ground_truth_template.py
    ├── auto_fill_ground_truth.py
    ├── filter_ground_truth.py
    └── create_test_sample.py
```

---

## 🚦 Prerequisites

| Requirement | Version |
|---|---|
| Python | ≥ 3.11 |
| Chrome + ChromeDriver | (auto-managed by `webdriver-manager`) |

### Python Dependencies

```bash
pip install langgraph langchain langchain-google-genai langchain-community
pip install langchain-openai openai google-generativeai
pip install pypdf reportlab faiss-cpu
pip install selenium webdriver-manager
pip install scikit-learn numpy pydantic python-dotenv
pip install openpyxl requests
```

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

> **Get your keys:**  
> • Gemini API → [Google AI Studio](https://aistudio.google.com/)  
> • Perplexity API → [Perplexity Labs](https://www.perplexity.ai/settings/api)

---

## ▶️ Running the System

### Full Pipeline (Recommended)

```bash
python main.py
```

The workflow will:
1. Parse the student profile from the hard-coded initial input (or prompt for missing fields interactively).
2. Run the 4-layer funnel against `structured_program_db_all_bw.json`.
3. Display the top-10 ranked programs, then pause for your selection (up to 3 programs).
4. Fetch document checklists, build timelines, and generate the PDF report.

> 💡 **To change the student profile**, edit the `initial_raw_input` string and `pdf_filename` variable inside the `if __name__ == "__main__":` block in `main.py`.

### Running Individual Agents (for Development / Testing)

```bash
# Test Agent 1 — profile extraction on all 5 synthetic profiles
python test_agent1.py

# Test Agent 3 — matching accuracy & F1 scores
python test_agent3.py

# Quick sanity check for Agent 3
python quick_test_agent3.py
```

### Crawling New Program Data

```bash
# Scrapes DAAD portal for English-taught Master's programs in Baden-Württemberg
python Crawling_Data.py
```

---

## 🧠 Key Technical Details

### Agent 3 — 4-Layer Matching Funnel

| Layer | Method | Purpose |
|---|---|---|
| **L1** | Rule-based hard filters | GPA, tuition budget, location, work experience, semester availability |
| **L2** | Gemini 2.5 Pro LLM | Degree domain compatibility ("Is Marketing similar to Business?") |
| **L3** | Gemini Embeddings + TF-IDF (hybrid) | Semantic similarity between student interests and program content |
| **L4** | Embedding-based ECTS audit | Verifies transcript covers program's subject prerequisites |

**Final Score Formula:**
```
Score = (Semantic Score × 0.50) + (ECTS Match × 0.40) + (Degree Compatibility × 0.10)
```

### ECTS Credit Normalisation

For non-European transcripts, credit hours are converted to ECTS:
```
Conversion Factor = (Semesters × 30 ECTS) ÷ Total Credits Earned
Converted ECTS = Original Credits × Factor
```
Credits already in the 170–250 range are assumed to be native ECTS and left unchanged.

### Country-Specific Admission Rules

| Country | Special Requirement |
|---|---|
| China, Vietnam, India, Mongolia | **APS Certificate** (6-month processing, ~€180) |
| Pakistan | **HEC Attestation** |
| All non-EU via certain universities | **Uni-Assist / VPD** processing (4–6 weeks, €75+) |

---

## 🧪 Evaluation

The system was evaluated against a manually labelled ground-truth Excel file (`agent3_ground_truth_FILLED.xlsx`) covering **5 international student profiles** across 500+ programs:

| Profile | Background | Citizenship |
|---|---|---|
| Profile 1 | Computer Science | Vietnam |
| Profile 2 | Business Administration | India |
| Profile 3 | Economics | Spain (EU) |
| Profile 4 | Bioinformatics | Germany (EU) |
| Profile 5 | Marketing | Pakistan |

Key metrics reported: **Precision, Recall, F1-Score** per layer and end-to-end.  
Full report: [`agent3_testing_report.md`](agent3_testing_report.md)

---

## 📄 Sample Output

After a complete run, a PDF is generated (e.g. `My_Application_Strategy_05.pdf`) containing:

- ✅ Student profile summary
- 🎯 Match score breakdown per program (Degree / Semantic / ECTS)
- 📋 Program requirements vs. student's actual values
- 💰 Cost breakdown (EU vs. non-EU tuition, semester contribution)
- 🗓️ Application milestone calendar with urgency indicators
- 📑 Full document checklist (country-specific + program-specific)
- ⚠️ Disclaimer and important verification notes

---

## 🔮 Limitations & Future Work

- The program database is scoped to **Baden-Württemberg only** (by design, for research focus).
- Agent 4 (Perplexity search) occasionally returns incomplete checklists for programs with poorly structured web pages.
- The system currently runs as a **CLI tool**; a web UI would improve usability.
- Deadline parsing may fail for non-standard date formats—a fallback manual-check event is inserted.

---

## 📜 Licence

This project is a thesis prototype developed at **Hochschule Pforzheim** and is intended for academic use only.  
© 2025 Anh-Tho Tran. All rights reserved.
