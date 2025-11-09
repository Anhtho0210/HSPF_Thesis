"""
Streamlit Chat Application for University Application Matching System

This application integrates:
1. Profile intake system (Agent1.py) - Interactive chat to collect user profile
2. TF-IDF similarity (Agent2_Test_TFIDF.py) - Text-based similarity calculation
3. LLM similarity (Agent2_Test_LLM.py) - Semantic and eligibility matching
"""

import streamlit as st
import os
from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import json

# Load environment variables
load_dotenv()

# ============================================================================
# PYDANTIC SCHEMAS (from Agent1.py)
# ============================================================================

class AcademicData(BaseModel):
    bachelor_degree_name: str = Field(description="Full name of the previous degree (e.g., 'B.Sc. in Computer Science').", default=None)
    bachelor_gpa_score: Optional[float] = Field(description="The numeric GPA score on its original scale.", default=None)
    bachelor_gpa_scale: Optional[float] = Field(description="The maximum possible scale (e.g., 4.0 or 5.0).", default=None)
    country_of_citizenship: Optional[str] = Field(description="The student's citizenship (e.g., 'India', 'Germany', or 'Non-EU').", default=None)

class LanguageProficiency(BaseModel):
    language: str
    exam: Literal["TOEFL_iBT", "IELTS", "TestDaF", "Other"]
    score: float

class UserProfile(BaseModel):
    """The structured data model for the student applicant profile."""
    full_name: Optional[str] = Field(default=None)
    academic_data: AcademicData
    field_of_interest: List[str] = Field(description="2-3 specific technical fields the student targets (e.g., 'Agentic AI', 'Data Science').", default=None)
    language_proofs: List[LanguageProficiency] = Field(default=[])
    preferred_language_of_instruction: Optional[str] = Field(description="e.g., 'English' or 'German/English'.", default='English')
    max_tuition_fee_eur: Optional[int] = Field(default=0, description="Maximum EUR fee per semester (0 for tuition-free).")
    preferred_city: Optional[str] = Field(default=None, description="The preferred German city for the university (e.g., 'Berlin', 'Munich').")

# ============================================================================
# LANGGRAPH STATE (from Agent1.py)
# ============================================================================

class AgentState(TypedDict):
    user_intent: str      # ACCUMULATED raw text from the user (Full Profile)
    latest_response: str  # The user's newest, single reply
    ai_response: Optional[str] 
    user_profile: Optional[UserProfile]

# ============================================================================
# LLM SETUP
# ============================================================================

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ GEMINI_API_KEY not found in .env file or environment variables")

LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1
)

# ============================================================================
# HELPER FUNCTIONS (from Agent1.py)
# ============================================================================

def get_missing_fields(profile: Optional[UserProfile]) -> List[str]:
    """Analyzes the UserProfile for critical missing data points for matching."""
    missing = []
    
    if profile is None:
        return ["Initial full profile text (name, GPA, major, citizenship, interests)"]

    if not profile.full_name: missing.append("full name")
    if not profile.academic_data.bachelor_degree_name: missing.append("bachelor degree name")
    if not profile.academic_data.bachelor_gpa_score: missing.append("bachelor GPA score")
    if not profile.academic_data.country_of_citizenship: missing.append("country of citizenship")
    if not profile.field_of_interest: missing.append("2-3 technical fields of interest")
    if not profile.language_proofs or (profile.language_proofs and len(profile.language_proofs) > 0 and profile.language_proofs[0].score is None):
        missing.append("language proof score (e.g., IELTS, TOEFL)")
        
    return missing

def get_desirable_missing_fields(profile: Optional[UserProfile]) -> List[str]:
    """Analyzes the UserProfile for helpful, but non-critical, data points."""
    desirable_missing = []
    
    if profile is None:
        return []

    if not profile.max_tuition_fee_eur or profile.max_tuition_fee_eur == 0:
        desirable_missing.append("maximum tuition fee (EUR per semester)")
    
    if not profile.preferred_language_of_instruction:
        desirable_missing.append("preferred language of instruction")
        
    if not profile.preferred_city:
        desirable_missing.append("preferred city")

    if not profile.field_of_interest:
        desirable_missing.append("field_of_interest")
            
    return desirable_missing

# ============================================================================
# LANGGRAPH NODES (from Agent1.py)
# ============================================================================

def parse_profile_node(state: AgentState) -> Dict[str, Any]:
    """Attempts to parse the accumulated user_intent into a structured UserProfile."""
    
    parser = JsonOutputParser(pydantic_object=UserProfile)
    format_instructions = parser.get_format_instructions()
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             f"""You are a meticulous data extraction agent. 
             STRICTLY extract ALL details from the user's FULL accumulated text and adhere to the JSON schema.
             
             Crucial Context: The user's latest response might be a short answer. You must map that short answer to the most likely missing field.
             - If the user provides a city name (e.g., 'Munich'), populate the 'preferred_city' field.
             - If the user provides a number in EUR, it is likely 'max_tuition_fee_eur'.
             
             If the user explicitly states they have no preference or the data is not applicable (e.g., 'No', 'I don't care'), you MUST set that field to 'null' or its default value (like 0 for max_tuition_fee_eur).
             Do NOT invent data. Only output the JSON.
             
             Output Format Instructions: \n{{format_instructions}}"""
            ),
            ("user", "User's current accumulated profile text: \n---\n{input}\n---")
        ]
    )
    
    parsing_chain: Runnable = prompt | LLM | parser
    
    try:
        structured_output_dict = parsing_chain.invoke({
            "input": state["user_intent"],
            "format_instructions": format_instructions
        })
        
        validated_profile = UserProfile(**structured_output_dict)
        return {"user_profile": validated_profile}
        
    except Exception as e:
        st.error(f"Failed to parse profile: {e}")
        return {"user_profile": None}

def conversational_chat_node(state: AgentState) -> Dict[str, Any]:
    """Generates a follow-up question based on missing profile fields."""
    
    profile = state.get("user_profile")
    current_intent = state["user_intent"]
    missing_data = get_missing_fields(profile)
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are a friendly university application assistant. Your task is to generate ONE concise, friendly question to gather the most important missing data. Do NOT repeat the data the user has already provided."
            ),
            ("user", f"Current ACCUMULATED Profile Text: '{current_intent}'. The critical missing data is: {', '.join(missing_data)}. Ask a question to gather this information.")
        ]
    )
    
    messages = prompt.invoke({}).to_messages()
    response = LLM.invoke(messages).content
    
    return {"ai_response": response}

def wrap_up_chat_node(state: AgentState) -> Dict[str, Any]:
    """Generates a wrap-up question for non-mandatory, desirable fields."""
    
    profile = state.get("user_profile")
    missing_desirable = get_desirable_missing_fields(profile)
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are a friendly university application assistant. All mandatory profile fields are complete. Your task is to ask ONE friendly, encouraging question to gather any remaining preferences that help with matching, such as preferred city, max tuition fee, or instructional language."
            ),
            ("user", f"I see you've completed your core profile! To help me find the best matches, could you let me know about any preferences for your maximum tuition fee (in EUR per semester, use '0' for tuition-free), preferred city, or instructional language (e.g., English)?")
        ]
    )
    messages = prompt.invoke({}).to_messages()
    response = LLM.invoke(messages).content
    
    return {"ai_response": response}

def check_for_completion(state: AgentState) -> Literal["chat", "wrap_up", "matching"]:
    """Conditional edge logic: determines if we need more info or can proceed to matching."""
    
    profile = state.get("user_profile")
    missing_mandatory_data = get_missing_fields(profile)
    missing_desirable_data = get_desirable_missing_fields(profile)
    
    if missing_mandatory_data:
        return "chat"
    elif missing_desirable_data:
        return "wrap_up"
    else:
        return "matching"

def build_intake_workflow() -> Any:
    workflow = StateGraph(AgentState)
    workflow.add_node("parsing", parse_profile_node)
    workflow.add_node("chat", conversational_chat_node)
    workflow.add_node("wrap_up", wrap_up_chat_node)

    workflow.set_entry_point("parsing")

    workflow.add_conditional_edges(
        "parsing",
        check_for_completion,
        {
            "chat": "chat",
            "wrap_up": "wrap_up",
            "matching": END
        }
    )

    workflow.add_edge("chat", END)
    workflow.add_edge("wrap_up", END)

    return workflow.compile()

# ============================================================================
# SIMILARITY FUNCTIONS
# ============================================================================

def calculate_tfidf_cosine_similarity(doc1: str, doc2: str) -> float:
    """Calculate TF-IDF cosine similarity (from Agent2_Test_TFIDF.py)"""
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=1
    )
    
    tfidf_matrix = vectorizer.fit_transform([doc1, doc2])
    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return similarity_score

def calculate_llm_similarity_score(candidate_profile: str, program_requirements: str) -> float:
    """Calculate LLM-based similarity score (from Agent2_Test_LLM.py)"""
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             """You are an expert in semantic and eligibility matching for university admissions.

Your task is to evaluate how well a candidate's profile (Document 1) matches a university program's requirements (Document 2).

Consider both semantic similarity and eligibility constraints.

Weight the following factors strongly:

Hard requirements (if not satisfy, please return 0 because candidate will never get the admission): GPA minimum (German scale: 1.0 best, 5.0 failed), language requirements, tuition/fee expectations, citizenship eligibility.

Soft alignment: program name/field, study location, language of instruction, and motivation alignment.

Output only a single final score between 0 and 1, no need to explain anything:

0 = candidate unlikely to be admitted (fails hard requirements).

1 = candidate is a very strong match (meets or exceeds all requirements).

Please remember it, dont say anything"""
            ),
            ("user",
             """Document 1 (Candidate Profile):
{candidate_profile}

Document 2 (Program Requirements):
{program_requirements}

Output only the similarity score as a number between 0 and 1 (e.g., 0.75 or 0.5). Do not include any explanation or text, only the number."""
            )
        ]
    )
    
    chain = prompt | LLM
    
    try:
        response = chain.invoke({
            "candidate_profile": candidate_profile,
            "program_requirements": program_requirements
        })
        
        response_text = response.content.strip()
        score_match = re.search(r'\b(0\.\d+|1\.0|1|0)\b', response_text)
        
        if score_match:
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))
            return score
        else:
            numbers = re.findall(r'\d+\.?\d*', response_text)
            if numbers:
                score = float(numbers[0])
                score = max(0.0, min(1.0, score))
                return score
            else:
                return 0.0
                
    except Exception as e:
        st.error(f"Failed to calculate LLM similarity: {e}")
        return 0.0

# ============================================================================
# STREAMLIT APP
# ============================================================================

def format_profile_to_text(profile: UserProfile) -> str:
    """Convert UserProfile to text format for similarity calculation"""
    parts = []
    
    if profile.full_name:
        parts.append(f"I am {profile.full_name}.")
    
    if profile.academic_data.bachelor_degree_name:
        parts.append(f"I have a {profile.academic_data.bachelor_degree_name}.")
    
    if profile.academic_data.bachelor_gpa_score:
        parts.append(f"My GPA is {profile.academic_data.bachelor_gpa_score} (German scale).")
    
    if profile.academic_data.country_of_citizenship:
        parts.append(f"I am {profile.academic_data.country_of_citizenship} citizenship.")
    
    if profile.field_of_interest:
        parts.append(f"I want to study {', '.join(profile.field_of_interest)}.")
    
    if profile.preferred_city:
        parts.append(f"I prefer to study in {profile.preferred_city}.")
    
    if profile.preferred_language_of_instruction:
        parts.append(f"I prefer {profile.preferred_language_of_instruction} program.")
    
    if profile.max_tuition_fee_eur:
        if profile.max_tuition_fee_eur == 0:
            parts.append("I want free tuition fee.")
        else:
            parts.append(f"My maximum tuition fee is {profile.max_tuition_fee_eur} EUR per semester.")
    
    if profile.language_proofs:
        for lang_proof in profile.language_proofs:
            parts.append(f"I have {lang_proof.exam} score of {lang_proof.score}.")
    
    return " ".join(parts)

def main():
    st.set_page_config(
        page_title="University Application Matching System",
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 University Application Matching System")
    st.markdown("---")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "user_intent" not in st.session_state:
        st.session_state.user_intent = ""
    
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = None
    
    if "profile_complete" not in st.session_state:
        st.session_state.profile_complete = False
    
    if "workflow" not in st.session_state:
        st.session_state.workflow = build_intake_workflow()
    
    # Sidebar for program requirements
    with st.sidebar:
        st.header("📋 Program Requirements")
        st.markdown("Enter the university program requirements to match against your profile.")
        
        program_requirements = st.text_area(
            "Program Requirements:",
            height=200,
            placeholder="""Example: This program is AI and DS in TU Berlin, semester fee 150 euro, 500 euro tuition fee for EU and non EU student, English program can be taught in full but some optional courses are Deutsch. GPA at least 2.5 (German scale)""",
            key="program_requirements"
        )
        
        if st.button("🔄 Reset Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.user_intent = ""
            st.session_state.user_profile = None
            st.session_state.profile_complete = False
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Profile Collection Chat")
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Tell me about yourself..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Update user intent
            st.session_state.user_intent += " " + prompt if st.session_state.user_intent else prompt
            
            # Run the workflow
            current_state: AgentState = {
                "user_intent": st.session_state.user_intent,
                "latest_response": prompt,
                "ai_response": None,
                "user_profile": st.session_state.user_profile,
            }
            
            try:
                with st.spinner("Processing..."):
                    next_state = st.session_state.workflow.invoke(current_state)
                    st.session_state.user_profile = next_state.get("user_profile")
                    
                    # Check if profile is complete
                    if st.session_state.user_profile:
                        missing = get_missing_fields(st.session_state.user_profile)
                        if not missing:
                            st.session_state.profile_complete = True
                    
                    # Get AI response
                    ai_response = next_state.get("ai_response")
                    
                    if ai_response:
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        with st.chat_message("assistant"):
                            st.markdown(ai_response)
                    
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.subheader("📊 Profile Status")
        
        if st.session_state.user_profile:
            profile = st.session_state.user_profile
            
            # Display profile information
            st.json(profile.model_dump())
            
            missing = get_missing_fields(profile)
            if missing:
                st.warning(f"⚠️ Missing: {', '.join(missing)}")
            else:
                st.success("✅ Profile Complete!")
                st.session_state.profile_complete = True
        else:
            st.info("Start chatting to build your profile!")
        
        # Similarity calculation section
        if st.session_state.profile_complete and program_requirements:
            st.markdown("---")
            st.subheader("🔍 Similarity Analysis")
            
            if st.button("Calculate Similarity", use_container_width=True):
                with st.spinner("Calculating similarity scores..."):
                    # Convert profile to text
                    candidate_text = format_profile_to_text(st.session_state.user_profile)
                    
                    # Calculate TF-IDF similarity
                    tfidf_score = calculate_tfidf_cosine_similarity(candidate_text, program_requirements)
                    
                    # Calculate LLM similarity
                    llm_score = calculate_llm_similarity_score(candidate_text, program_requirements)
                    
                    # Display results
                    st.markdown("### Results")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.metric("TF-IDF Score", f"{tfidf_score:.3f}")
                        if tfidf_score >= 0.7:
                            st.success("High similarity")
                        elif tfidf_score >= 0.4:
                            st.info("Moderate similarity")
                        elif tfidf_score >= 0.2:
                            st.warning("Low similarity")
                        else:
                            st.error("Very low similarity")
                    
                    with col_b:
                        st.metric("LLM Score", f"{llm_score:.3f}")
                        if llm_score >= 0.8:
                            st.success("Very strong match")
                        elif llm_score >= 0.6:
                            st.success("Good match")
                        elif llm_score >= 0.4:
                            st.warning("Moderate match")
                        elif llm_score > 0.0:
                            st.warning("Weak match")
                        else:
                            st.error("No match")
                    
                    # Progress bars
                    st.progress(tfidf_score, text="TF-IDF Similarity")
                    st.progress(llm_score, text="LLM Similarity")
                    
                    # Combined score
                    combined_score = (tfidf_score + llm_score) / 2
                    st.metric("Combined Score", f"{combined_score:.3f}")
                    st.progress(combined_score, text="Overall Match")

if __name__ == "__main__":
    main()

