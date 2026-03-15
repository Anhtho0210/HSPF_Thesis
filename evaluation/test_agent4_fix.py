#!/usr/bin/env python3
"""
Quick test for Agent4 document extraction fix.
Tests that the updated prompt correctly extracts all required documents
for University of Stuttgart programs.
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Agent4 import query_perplexity_search_and_extract

def test_uni_stuttgart_computational_linguistics():
    """Test document extraction for Computational Linguistics at Uni Stuttgart"""
    print("=" * 80)
    print("TESTING: Agent4 Document Extraction Fix")
    print("Program: Computational Linguistics M.Sc. at University of Stuttgart")
    print("=" * 80)
    
    # Test with Vietnam citizenship (requires APS)
    result = query_perplexity_search_and_extract(
        program_name="Computational Linguistics M.Sc.",
        uni_name="University of Stuttgart",
        citizenship="Vietnam",
        deadline_info="15 July 2026",
        tuition_fee=1500.0,
        application_mode="Online via C@MPUS",
        preferred_semester="Winter"
    )
    
    print("\n" + "=" * 80)
    print("EXTRACTION RESULTS:")
    print("=" * 80)
    
    if result:
        print(f"\n✅ Official URL: {result.get('official_url', 'N/A')}")
        print(f"\n🌍 Country-Specific Requirement: {result.get('country_specific_requirement', 'None')}")
        
        print("\n📋 Document Checklist:")
        checklist = result.get('document_checklist', [])
        for i, doc in enumerate(checklist, 1):
            print(f"   {i}. {doc}")
        
        notes = result.get('notes', '')
        if notes:
            print(f"\n💡 Notes: {notes}")
        
        # Verify critical documents are present
        print("\n" + "=" * 80)
        print("VALIDATION CHECKS:")
        print("=" * 80)
        
        required_docs = {
            "Transcript of Records": False,
            "Bachelor": False,  # Bachelor's Degree Certificate or Bachelor Certificate
            "Module Descriptions": False,
            "Online Application": False,
            "Passport": False,
            "English": False,  # English language proof
        }
        
        for doc in checklist:
            doc_lower = doc.lower()
            if "transcript" in doc_lower:
                required_docs["Transcript of Records"] = True
            if "bachelor" in doc_lower and ("certificate" in doc_lower or "degree" in doc_lower):
                required_docs["Bachelor"] = True
            if "module" in doc_lower and "description" in doc_lower:
                required_docs["Module Descriptions"] = True
            if "online" in doc_lower and ("application" in doc_lower or "form" in doc_lower):
                required_docs["Online Application"] = True
            if "passport" in doc_lower:
                required_docs["Passport"] = True
            if "english" in doc_lower or "language" in doc_lower:
                required_docs["English"] = True
        
        all_present = True
        for doc_name, is_present in required_docs.items():
            status = "✅" if is_present else "❌"
            print(f"{status} {doc_name}: {'FOUND' if is_present else 'MISSING'}")
            if not is_present:
                all_present = False
        
        # Check APS requirement for Vietnam
        aps_mentioned = "aps" in result.get('country_specific_requirement', '').lower()
        print(f"\n{'✅' if aps_mentioned else '❌'} APS Requirement: {'FOUND' if aps_mentioned else 'MISSING'}")
        
        print("\n" + "=" * 80)
        if all_present and aps_mentioned:
            print("✅ TEST PASSED: All required documents extracted!")
        else:
            print("❌ TEST FAILED: Missing required documents!")
        print("=" * 80)
        
    else:
        print("❌ ERROR: No results returned from Perplexity API")

if __name__ == "__main__":
    load_dotenv()
    test_uni_stuttgart_computational_linguistics()
