from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

# --- 1. PYDANTIC SCHEMAS ---

class Citizenship(BaseModel):
    country_of_citizenship: Optional[str] = Field(description="The student's citizenship (e.g., 'Vietnam', 'India', 'Germany', or 'Non-EU').", default=None)

class BachelorGPA(BaseModel):
    score: Optional[float] = Field(description="The numeric GPA score on its original scale.", default=None)
    max_scale: Optional[float] = Field(description="The maximum possible scale (e.g., 4.0 or 5.0).", default=None)
    min_passing_grade: Optional[float] = Field(description="The minimum passing grade on the scale (e.g., 1.0).", default=None)
    score_german: Optional[float] = Field(description="The GPA score converted to German grading system (1.0-4.0).", default=None)

class AcademicBackground(BaseModel):
    bachelor_field_of_study: Optional[str] = Field(description="Field of study for the bachelor's degree (e.g., 'Computer Science').", default=None)
    bachelor_duration_years: Optional[int] = Field(description="Duration of the bachelor's degree in years (e.g., 4).", default=None)
    bachelor_gpa: Optional[BachelorGPA] = Field(default=None)
    total_credit_points: Optional[int] = Field(description="Total credit points earned in the bachelor's degree (e.g., 180).", default=None)
    fields_of_interest: Optional[List[str]] = Field(description="4-5 specific technical fields the student targets (e.g., 'AI', 'Machine Learning', 'Data Science').", default=None)

class LanguageProficiency(BaseModel):
    language: str = Field(description="The language name (e.g., 'English', 'German').")
    exam_type: Literal["TOEFL_iBT", "IELTS", "TestDaF", "CEFR", "Other"] = Field(description="Type of language exam.")
    overall_score: Optional[float] = Field(description="Overall score for IELTS/TOEFL (e.g., 6.0).", default=None)
    level: Optional[str] = Field(description="CEFR level for German (e.g., 'A2', 'B1', 'B2').", default=None)

class StandardizedTest(BaseModel):
    exam_type: str = Field(description="Type of standardized test (e.g., 'GRE', 'GMAT').")
    total_score: Optional[float] = Field(description="Total score for the standardized test (e.g., 320).", default=None)

class ProfessionalAndTests(BaseModel):
    relevant_work_experience_months: Optional[int] = Field(description="Relevant work experience in months (e.g., 6).", default=None)
    standardized_tests: Optional[List[StandardizedTest]] = Field(default=None)

class Preferences(BaseModel):
    preferred_cities: Optional[List[str]] = Field(description="List of preferred cities (e.g., ['Munich', 'Berlin', 'Aachen']).", default=None)
    max_tuition_fee_eur: Optional[int] = Field(default=0, description="Maximum EUR fee per semester (0 for tuition-free).")
    preferred_start_semester: Optional[str] = Field(description="Preferred start semester (e.g., 'Winter', 'Summer', 'Either').", default=None)
    preferred_language_of_instruction: Optional[str] = Field(description="e.g., 'English' or 'German/English'.", default='English')

class UserProfile(BaseModel):
    """The structured data model for the student applicant profile."""
    full_name: Optional[str] = Field(default=None)
    citizenship: Optional[Citizenship] = Field(default=None)
    academic_background: Optional[AcademicBackground] = Field(default=None)
    language_proficiency: Optional[List[LanguageProficiency]] = Field(default=[])
    professional_and_tests: Optional[ProfessionalAndTests] = Field(default=None)
    preferences: Optional[Preferences] = Field(default=None)

# Schema for Agent 3's extractor tool
class StructuredRequirements(BaseModel):
    min_gpa_german: Optional[float] = Field(description="The minimum required German grade (1.0-4.0).")
    required_field_of_study: Optional[List[str]] = Field(description="List of required bachelor fields.")
    required_ects: Optional[int] = Field(description="Minimum ECTS points required.")
    min_ielts_score: Optional[float] = Field(description="Minimum IELTS score.")
    min_toefl_ibt_score: Optional[int] = Field(description="Minimum TOEFL iBT score.")
    requires_gre: Optional[bool] = Field(description="True if GRE is mandatory.")

# --- LANGGRAPH SHARED STATE ---
class AgentState(TypedDict):
    user_intent: str
    latest_response: str
    ai_response: Optional[str]
    user_profile: Optional[UserProfile]
    
    # New keys for Agent 3
    program_catalog: List[Dict]
    eligible_programs: List[Dict]
    ranked_programs: List[Dict]
