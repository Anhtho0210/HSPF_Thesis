# models.py

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# --- PART 1: THE STUDENT 
class StudentCourse(BaseModel):
    """Represents a single course/module from the transcript."""
    course_name: str = Field(description="Name of the subject (e.g. 'Calculus I').")
    original_credits: float = Field(description="Credits as listed on the transcript.", default=0.0)
    grade: Optional[str] = Field(default=None)

    # New Field: Only populated if Agent asks or user provides
    content_description: Optional[str] = Field(
        description="Short summary of topics covered, provided by user on demand.", 
        default=None
    )
    
    # Calculated Field
    converted_ects: float = Field(
        description="The calculated value: original_credits * conversion_factor", 
        default=0.0
    )

class Citizenship(BaseModel):
    country_of_citizenship: Optional[str] = Field(default=None)

class BachelorGPA(BaseModel):
    score: Optional[float] = Field(default=None)
    max_scale: Optional[float] = Field(default=None)
    min_passing_grade: Optional[float] = Field(default=None)
    score_german: Optional[float] = Field(default=None)

class AcademicBackground(BaseModel):
    bachelor_field_of_study: Optional[str] = Field(default=None)
    
    # Inputs for the Formula
    total_credits_earned: Optional[float] = Field(description="Original total credits (e.g. 130).", default=None)
    
    program_duration_semesters: Optional[int] = Field(default=None)
    ects_conversion_factor: float = Field(default=1.0)
    
    # Must match 'total_converted_ects' used in Agent1.py
    total_converted_ects: float = Field(default=0.0)
    
    # The Course List
    transcript_courses: List[StudentCourse] = Field(default_factory=list)
    
    bachelor_gpa: Optional[BachelorGPA] = None 

    fields_of_interest: Optional[List[str]] = Field(
        description="List of specific technical interests (e.g. 'AI', 'Supply Chain').", 
        default_factory=list
    )

class LanguageProficiency(BaseModel):
    language: str
    exam_type: str
    overall_score: Optional[float] = None
    level: Optional[str] = None

class Preferences(BaseModel):
    preferred_cities: Optional[List[str]] = Field(default_factory=list)
    preferred_state: Optional[str] = Field(description="Preferred German state (e.g., 'Bavaria', 'Baden-Württemberg').", default=None)
    max_tuition_fee_eur: Optional[int] = Field(default=0)
    preferred_start_semester: Optional[str] = Field(default=None)
    preferred_language_of_instruction: Optional[str] = Field(default='English')

class ProfessionalAndTests(BaseModel):
    relevant_work_experience_months: Optional[int] = Field(default=None)
    standardized_tests: Optional[List[dict]] = Field(default=None)
     
class DesiredProgram(BaseModel):
    program_name: List[str] = Field(description="List of target Master's program names (e.g. ['Data Science', 'MBA']).", default_factory=list)
    fields_of_interest: List[str] = Field(description="Specific interests/modules (module, course name).", default_factory=list)

class UserProfile(BaseModel): 
    full_name: Optional[str] = None
    citizenship: Optional[Citizenship] = None
    academic_background: Optional[AcademicBackground] = None
    desired_program: Optional[DesiredProgram] = None
    language_proficiency: Optional[List[LanguageProficiency]] = Field(default=[])
    professional_and_tests: Optional[ProfessionalAndTests] = None
    preferences: Preferences = Field(default_factory=Preferences)

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

class LanguageTest(BaseModel):
    """A specific accepted test and score."""
    test_name: str = Field(description="e.g. 'IELTS', 'TOEFL iBT', 'Cambridge FCE'.")
    min_score: Optional[str] = Field(
        description="The score required. e.g. '6.5', '90', 'B'. If no score applies (e.g. native speaker), leave null.", 
        default=None
    )

class DetailedLanguageRequirement(BaseModel):
    """Detailed breakdown for a specific language (English or German)."""
    min_cefr_level: Literal["A1", "A2", "B1", "B2", "C1", "C2", "None", "Unknown"] = Field(
        description="Standardized level for quick filtering.", default="Unknown"
    )
    accepted_tests: List[LanguageTest] = Field(
        description="List of specific tests mentioned in the text.", 
        default_factory=list
    )
    notes: Optional[str] = Field(
        description="Waivers or conditions (e.g. 'Native speakers exempt', 'Medium of instruction accepted').", 
        default=None
    )

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

    # --- TESTS (Added this back!) ---
    required_standardized_tests: List[StandardizedTest] = Field(default_factory=list)
    # Work Experience
    min_work_experience_months: int = Field(description="Mandatory work exp in months.", default=0)
    requires_internship: bool = Field(default=False)
    
    # Language
    english_requirements: DetailedLanguageRequirement = Field(default_factory=DetailedLanguageRequirement)
    german_requirements: DetailedLanguageRequirement = Field(default_factory=DetailedLanguageRequirement)
    
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
    pdf_path: Optional[str]
    latest_response: Optional[str]
    ai_response: Optional[str]  
    user_profile: Optional[UserProfile]
    program_catalog: List[dict]
    eligible_programs: List[dict]
    ranked_programs: List[dict]
    selected_programs_with_checklists: List[dict]  # Agent 4 output