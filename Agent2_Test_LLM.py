"""
LLM-based Semantic Similarity and Eligibility Matching Calculator

This script calculates the similarity between a candidate's profile (Document 1) 
and a university program's requirements (Document 2) using an LLM.
It considers both semantic similarity and eligibility constraints.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# --- LLM SETUP (from Agent1.py) ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    # Error will be caught during LLM initialization if not set
    print("[Warning] GEMINI_API_KEY not found in .env file or environment variables")

LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1
)


def calculate_llm_similarity_score(candidate_profile: str, program_requirements: str) -> float:
    """
    Calculate the similarity score between a candidate profile and program requirements using LLM.
    
    The LLM evaluates:
    - Hard requirements: GPA minimum, language requirements, tuition/fee expectations, citizenship eligibility
    - Soft alignment: program name/field, study location, language of instruction, motivation alignment
    
    Args:
        candidate_profile: Document 1 - Candidate's profile text
        program_requirements: Document 2 - University program requirements text
    
    Returns:
        float: Similarity score between 0 and 1
              - 0 = candidate unlikely to be admitted (fails hard requirements)
              - 1 = candidate is a very strong match (meets or exceeds all requirements)
    """
    
    # Define the prompt template
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
    
    # Create the chain
    chain = prompt | LLM
    
    try:
        # Invoke the LLM
        response = chain.invoke({
            "candidate_profile": candidate_profile,
            "program_requirements": program_requirements
        })
        
        # Extract the score from the response
        # The LLM should return just a number, but we'll parse it to be safe
        response_text = response.content.strip()
        
        # Try to extract a float from the response
        # Look for patterns like "0.75", "0.5", "1.0", etc.
        score_match = re.search(r'\b(0\.\d+|1\.0|1|0)\b', response_text)
        
        if score_match:
            score = float(score_match.group(1))
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            return score
        else:
            # If we can't parse, try to extract any number
            numbers = re.findall(r'\d+\.?\d*', response_text)
            if numbers:
                score = float(numbers[0])
                score = max(0.0, min(1.0, score))
                return score
            else:
                print(f"[Warning] Could not parse score from LLM response: {response_text}")
                print("[Warning] Returning 0.0 as default")
                return 0.0
                
    except Exception as e:
        print(f"[Error] Failed to calculate similarity score: {e}")
        return 0.0


if __name__ == "__main__":
    # Example documents
    document_1 = """I want to study Data Science in Berlin City, English Program, Free tuition fee. I am vietnamese citizenship. My GPA 2.5 (German scale)"""
    
    document_2 = """This programm is AI and DS in TU Berlin, semester fee 150 euro, 500 euro tuition fee for EU and non EU student, English program can be taught in full but some optional courses are Deutsch. GPA at least 2.5 (German scale)"""
    
    print("="*80)
    print("LLM-based Semantic Similarity and Eligibility Matching")
    print("="*80)
    
    print("\n--- Document 1 (Candidate Profile) ---")
    print(document_1)
    
    print("\n--- Document 2 (Program Requirements) ---")
    print(document_2)
    
    print("\n[Calculating similarity score using LLM...]")
    
    # Calculate similarity
    similarity_score = calculate_llm_similarity_score(document_1, document_2)
    
    print("\n" + "="*80)
    print(f"LLM Similarity Score: {similarity_score:.4f}")
    print(f"Similarity Percentage: {similarity_score * 100:.2f}%")
    print("="*80)
    
    # Interpretation
    print("\n" + "="*80)
    print("Interpretation:")
    print("="*80)
    if similarity_score >= 0.8:
        print("Very strong match: Candidate meets or exceeds all requirements.")
    elif similarity_score >= 0.6:
        print("Good match: Candidate meets most requirements with minor gaps.")
    elif similarity_score >= 0.4:
        print("Moderate match: Candidate has some alignment but may have significant gaps.")
    elif similarity_score > 0.0:
        print("Weak match: Candidate has minimal alignment or fails some requirements.")
    else:
        print("No match: Candidate fails hard requirements and is unlikely to be admitted.")
    print("="*80)
