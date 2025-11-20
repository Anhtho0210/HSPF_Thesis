# models.py

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# --- PART 1: THE STUDENT 

class Citizenship(BaseModel):
    country_of_citizenship: Optional[str] = Field(default=None)

class BachelorGPA(BaseModel):
    score: Optional[float] = Field(default=None)
    max_scale: Optional[float] = Field(default=None)
    min_passing_grade: Optional[float] = Field(default=None)
    score_german: Optional[float] = Field(default=None)

class AcademicBackground(BaseModel):
    bachelor_field_of_study: Optional[str] = Field(default=None)
    bachelor_gpa: Optional[BachelorGPA] = Field(default=None)
    total_credit_points: Optional[int] = Field(default=None)
    fields_of_interest: Optional[List[str]] = Field(default=None)

class LanguageProficiency(BaseModel):
    language: str
    exam_type: str
    overall_score: Optional[float] = None
    level: Optional[str] = None

class UserProfile(BaseModel):
    full_name: Optional[str] = None
    citizenship: Optional[Citizenship] = None
    academic_background: Optional[AcademicBackground] = None
    language_proficiency: Optional[List[LanguageProficiency]] = Field(default=[])

# --- PART 2: THE PROGRAM DATABASE 

class ECTSModule(BaseModel):
    """The specific subject inside a domain (The 'Child')."""
    subject_area: str = Field(description="Specific subject, e.g., 'Mathematics', 'Water Management'.")
    min_ects: float = Field(description="Credits for this specific subject.", default=0.0)
    condition_comment: Optional[str] = Field(default=None)

class ECTSDomain(BaseModel):
    """The high-level category (The 'Parent')."""
    domain_name: str = Field(description="Broad category, e.g., 'Mathematical-physical basics'.")
    min_ects_total: float = Field(description="Total credits required for this entire domain.", default=0.0)
    condition_comment: Optional[str] = Field(
        description="Rules like 'Select 2 of 4 areas' or 'Total required'.", 
        default=None
    )
    modules: List[ECTSModule] = Field(
        description="List of specific subjects belonging to this domain.", 
        default_factory=list
    )

class ApplicationWindow(BaseModel):
    """Defines the start and end date for a specific group."""
    start_date: Optional[str] = Field(description="When applications open (e.g., '2025-01-15' or 'Jan 15').", default=None)
    end_date: Optional[str] = Field(description="When applications close (deadline) (e.g., '2025-05-31').", default=None)

class SemesterDeadlines(BaseModel):
    """Deadlines for a specific semester (Winter or Summer)."""
    eu_applicants: Optional[ApplicationWindow] = Field(description="Dates for EU citizens.", default=None)
    non_eu_applicants: Optional[ApplicationWindow] = Field(description="Dates for Non-EU/International citizens.", default=None)

class ProgramDeadlines(BaseModel):
    """Container for both semesters."""
    winter_semester: Optional[SemesterDeadlines] = Field(default=None)
    summer_semester: Optional[SemesterDeadlines] = Field(default=None)

class StandardizedTest(BaseModel):
    test_name: Literal["GRE", "GMAT"] = Field(description="Type of test.")
    target_group: Literal["All", "Non-EU"] = Field(
        description="Who must take this? 'All' means everyone. 'Non-EU' means only applicants from outside EU/EEA.",
        default="All"
    )
    min_score: Optional[float] = Field(description="Minimum score if specified (e.g. 155).", default=None)

class ProgramHardFilters(BaseModel):
    """Structured data for the University Program."""
    program_id: str = Field(default="Unknown")
    university_name: str = Field(default="Unknown")
    program_name: str = Field(default="Unknown")
    degree_type: str = Field(default="Master")
    
    # Application Mode
    application_mode: Literal["Uni-Assist", "VPD", "Direct", "Unknown"] = Field(
        description="Platform: 'VPD', 'Uni-Assist', or 'Direct'.", default="Unknown"
    )
    
    # Location
    city: str = Field(default="Unknown")
    state: str = Field(description="German state.", default="Unknown")
    
    # Financial
    tuition_fee_per_semester_eur: float = Field(default=0.0)
    semester_contribution_eur: float = Field(default=0.0)
    
    # Academic Requirements
    min_gpa_german_scale: Optional[float] = Field(description="Minimum German GPA (e.g. 2.5).", default=None)
    
    required_degree_domains: List[str] = Field(description="Acceptable bachelor fields.", default_factory=list)

    # --- NESTED ECTS LIST ---
    specific_ects_requirements: List[ECTSDomain] = Field(default_factory=list)
    # Work Experience
    min_work_experience_months: int = Field(description="Mandatory work exp in months.", default=0)
    requires_internship: bool = Field(default=False)
    
    # Language
    english_level_requirement: Literal["A1", "A2", "B1", "B2", "C1", "C2", "None", "Unknown"] = Field(default="Unknown")
    german_level_requirement: Literal["A1", "A2", "B1", "B2", "C1", "C2", "None", "Unknown"] = Field(default="None")
    
    # Granular Deadlines ---
    deadlines: ProgramDeadlines = Field(description="Structured application periods.", default_factory=ProgramDeadlines)

    # Metadata
    course_content_summary: str = Field(
        description="A dense, keyword-rich summary of all technical topics, subjects, and skills taught.", 
        default=""
    )
# --- PART 3: SHARED STATE ---
class AgentState(TypedDict):
    user_intent: str
    user_profile: Optional[UserProfile]
    program_catalog: List[dict]
    eligible_programs: List[dict]
    ranked_programs: List[dict]