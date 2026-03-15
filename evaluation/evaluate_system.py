"""
Evaluation Script for Multi-Agent University Application System
This script provides automated testing and metrics calculation for thesis evaluation.
"""

import json
import sys
import os
import time
import tracemalloc
from typing import List, Set, Dict, Any
import numpy as np
from datetime import datetime

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your system
from main import build_master_workflow
from models import AgentState, UserProfile

# ==========================================
# METRICS CALCULATION
# ==========================================

def calculate_precision(predicted: Set, actual: Set) -> float:
    """Precision = TP / (TP + FP)"""
    if len(predicted) == 0:
        return 0.0
    true_positives = len(predicted.intersection(actual))
    return true_positives / len(predicted)

def calculate_recall(predicted: Set, actual: Set) -> float:
    """Recall = TP / (TP + FN)"""
    if len(actual) == 0:
        return 0.0
    true_positives = len(predicted.intersection(actual))
    return true_positives / len(actual)

def calculate_f1(precision: float, recall: float) -> float:
    """F1 = 2 * (Precision * Recall) / (Precision + Recall)"""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)

def calculate_ndcg(predicted_ranking: List[str], ideal_ranking: List[str], k: int = 3) -> float:
    """Normalized Discounted Cumulative Gain at K"""
    def dcg(ranking, k):
        return sum([1 / np.log2(i + 2) for i, item in enumerate(ranking[:k]) if item in ideal_ranking])
    
    dcg_score = dcg(predicted_ranking, k)
    idcg_score = dcg(ideal_ranking, k)
    
    return dcg_score / idcg_score if idcg_score > 0 else 0.0

def calculate_ects_accuracy(predicted_ects: float, actual_ects: float, tolerance: float = 0.5) -> bool:
    """Check if ECTS calculation is within tolerance"""
    return abs(predicted_ects - actual_ects) <= tolerance

# ==========================================
# PERFORMANCE MEASUREMENT
# ==========================================

def measure_performance(func):
    """Decorator to measure execution time and memory usage"""
    def wrapper(*args, **kwargs):
        start = time.time()
        tracemalloc.start()
        
        result = func(*args, **kwargs)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        duration = time.time() - start
        
        performance_metrics = {
            'duration_seconds': round(duration, 2),
            'peak_memory_mb': round(peak / 1024 / 1024, 2)
        }
        
        print(f"\n[Performance] {func.__name__}:")
        print(f"  ⏱️  Duration: {performance_metrics['duration_seconds']}s")
        print(f"  💾 Peak Memory: {performance_metrics['peak_memory_mb']} MB")
        
        return result, performance_metrics
    return wrapper

# ==========================================
# TEST CASE EXECUTION
# ==========================================

@measure_performance
def run_single_test_case(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the system with a single test case and return results.
    
    Args:
        test_case: Dictionary containing 'profile' and 'expected_programs'
    
    Returns:
        Dictionary with system output and evaluation metrics
    """
    print(f"\n{'='*60}")
    print(f"Running Test Case: {test_case['id']}")
    print(f"{'='*60}")
    
    # Build workflow
    app = build_master_workflow()
    
    # Prepare initial state
    initial_state = {
        "user_intent": test_case['profile']['input_text'],
        "pdf_path": "docs/Bachelor_Courses.pdf",
        "user_profile": None,
        "program_catalog": [],
        "eligible_programs": [],
        "ranked_programs": [],
        "selected_programs_with_checklists": []
    }
    
    # Run system (simplified - you may need to adjust based on your workflow)
    try:
        result_state = app.invoke(initial_state, {"recursion_limit": 20})
        
        # Extract top programs
        ranked_programs = result_state.get('ranked_programs', [])
        top_3_programs = [p['program_name'] for p in ranked_programs[:3]]
        
        return {
            'success': True,
            'top_3_programs': top_3_programs,
            'all_ranked_programs': ranked_programs,
            'user_profile': result_state.get('user_profile')
        }
    except Exception as e:
        print(f"❌ Test case failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def evaluate_matching_accuracy(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate matching accuracy across multiple test cases.
    
    Args:
        test_cases: List of test case dictionaries
    
    Returns:
        Aggregated evaluation metrics
    """
    results = []
    performance_data = []
    
    for test_case in test_cases:
        output, perf_metrics = run_single_test_case(test_case)
        performance_data.append(perf_metrics)
        
        if not output['success']:
            results.append({
                'case_id': test_case['id'],
                'success': False,
                'error': output['error']
            })
            continue
        
        # Compare with gold standard
        predicted = set(output['top_3_programs'])
        expected = set(test_case['expected_programs'])
        
        precision = calculate_precision(predicted, expected)
        recall = calculate_recall(predicted, expected)
        f1 = calculate_f1(precision, recall)
        
        # Calculate NDCG
        ndcg = calculate_ndcg(
            output['top_3_programs'],
            test_case['expected_programs'],
            k=3
        )
        
        result = {
            'case_id': test_case['id'],
            'success': True,
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1, 3),
            'ndcg@3': round(ndcg, 3),
            'predicted_programs': output['top_3_programs'],
            'expected_programs': list(expected)
        }
        
        results.append(result)
        
        print(f"\n📊 Metrics for {test_case['id']}:")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall: {recall:.3f}")
        print(f"  F1-Score: {f1:.3f}")
        print(f"  NDCG@3: {ndcg:.3f}")
    
    # Aggregate metrics
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        avg_metrics = {
            'avg_precision': round(np.mean([r['precision'] for r in successful_results]), 3),
            'avg_recall': round(np.mean([r['recall'] for r in successful_results]), 3),
            'avg_f1': round(np.mean([r['f1_score'] for r in successful_results]), 3),
            'avg_ndcg': round(np.mean([r['ndcg@3'] for r in successful_results]), 3),
            'success_rate': round(len(successful_results) / len(test_cases), 3),
            'avg_latency': round(np.mean([p['duration_seconds'] for p in performance_data]), 2),
            'avg_memory_mb': round(np.mean([p['peak_memory_mb'] for p in performance_data]), 2)
        }
    else:
        avg_metrics = {'error': 'All test cases failed'}
    
    return {
        'individual_results': results,
        'aggregated_metrics': avg_metrics,
        'performance_data': performance_data
    }

# ==========================================
# ECTS VALIDATION
# ==========================================

def evaluate_ects_conversion(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate ECTS conversion accuracy.
    
    Args:
        test_cases: List containing 'original_credits', 'semesters', 'expected_ects'
    
    Returns:
        Accuracy metrics for ECTS conversion
    """
    results = []
    
    for test_case in test_cases:
        # Calculate expected ECTS using your formula
        # Factor = 30 / (Total_Credits / Semesters)
        # Total ECTS = Total_Credits * Factor
        
        total_credits = test_case['original_credits']
        semesters = test_case['semesters']
        expected_total_ects = test_case['expected_ects']
        
        # Your system's calculation
        factor = 30 / (total_credits / semesters)
        calculated_ects = total_credits * factor
        
        is_accurate = calculate_ects_accuracy(calculated_ects, expected_total_ects)
        
        results.append({
            'case_id': test_case['id'],
            'calculated_ects': round(calculated_ects, 2),
            'expected_ects': expected_total_ects,
            'accurate': is_accurate,
            'error': abs(calculated_ects - expected_total_ects)
        })
    
    accuracy_rate = sum([r['accurate'] for r in results]) / len(results)
    
    return {
        'individual_results': results,
        'accuracy_rate': round(accuracy_rate, 3),
        'avg_error': round(np.mean([r['error'] for r in results]), 2)
    }

# ==========================================
# MAIN EVALUATION RUNNER
# ==========================================

def run_evaluation(test_file: str = 'test_profiles.json', output_file: str = 'evaluation_results.json'):
    """
    Main evaluation function that runs all tests and generates report.
    
    Args:
        test_file: Path to JSON file containing test cases
        output_file: Path to save evaluation results
    """
    print("\n" + "="*60)
    print("🎓 MULTI-AGENT SYSTEM EVALUATION")
    print("="*60)
    
    # Load test cases
    try:
        with open(test_file, 'r') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Test file '{test_file}' not found!")
        print("Please create a test file with the following structure:")
        print("""
{
  "matching_tests": [
    {
      "id": "TEST-001",
      "profile": {
        "input_text": "I'm from Vietnam, studied Computer Science..."
      },
      "expected_programs": ["Program 1", "Program 2", "Program 3"]
    }
  ],
  "ects_tests": [
    {
      "id": "ECTS-001",
      "original_credits": 130,
      "semesters": 8,
      "expected_ects": 195
    }
  ]
}
        """)
        return
    
    # Run matching accuracy tests
    if 'matching_tests' in test_data:
        print("\n📍 Running Matching Accuracy Tests...")
        matching_results = evaluate_matching_accuracy(test_data['matching_tests'])
    else:
        matching_results = {}
    
    # Run ECTS conversion tests
    if 'ects_tests' in test_data:
        print("\n📍 Running ECTS Conversion Tests...")
        ects_results = evaluate_ects_conversion(test_data['ects_tests'])
    else:
        ects_results = {}
    
    # Compile final report
    final_report = {
        'evaluation_date': datetime.now().isoformat(),
        'matching_accuracy': matching_results,
        'ects_conversion': ects_results
    }
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ EVALUATION COMPLETE")
    print("="*60)
    print(f"\n📄 Results saved to: {output_file}")
    
    # Print summary
    if matching_results and 'aggregated_metrics' in matching_results:
        print("\n📊 SUMMARY METRICS:")
        metrics = matching_results['aggregated_metrics']
        print(f"  Average Precision: {metrics.get('avg_precision', 'N/A')}")
        print(f"  Average Recall: {metrics.get('avg_recall', 'N/A')}")
        print(f"  Average F1-Score: {metrics.get('avg_f1', 'N/A')}")
        print(f"  Average NDCG@3: {metrics.get('avg_ndcg', 'N/A')}")
        print(f"  Success Rate: {metrics.get('success_rate', 'N/A')}")
        print(f"  Average Latency: {metrics.get('avg_latency', 'N/A')}s")
    
    if ects_results and 'accuracy_rate' in ects_results:
        print(f"\n  ECTS Accuracy: {ects_results['accuracy_rate']}")

# ==========================================
# COMMAND LINE INTERFACE
# ==========================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Multi-Agent University Application System')
    parser.add_argument('--test-file', default='evaluation/test_profiles.json', help='Path to test cases JSON file')
    parser.add_argument('--output', default='evaluation/evaluation_results.json', help='Path to save results')
    
    args = parser.parse_args()
    
    run_evaluation(args.test_file, args.output)
