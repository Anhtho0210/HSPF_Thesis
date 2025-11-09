"""
TF-IDF and Cosine Similarity Calculator for Document Comparison

This script calculates the similarity between two documents using:
1. TF-IDF (Term Frequency-Inverse Document Frequency) vectorization
2. Cosine similarity metric
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def calculate_tfidf_cosine_similarity(doc1: str, doc2: str) -> float:
    """
    Calculate the cosine similarity between two documents using TF-IDF.
    
    Args:
        doc1: First document text
        doc2: Second document text
    
    Returns:
        float: Cosine similarity score between 0 and 1 (1 = identical, 0 = no similarity)
    """
    # Create TF-IDF vectorizer
    # Parameters:
    # - lowercase: Convert all text to lowercase
    # - stop_words: Remove common stop words (optional, can be 'english' or None)
    # - ngram_range: Use unigrams (1,1) or include bigrams (1,2) for better matching
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',  # Remove common English stop words
        ngram_range=(1, 2),    # Use both unigrams and bigrams
        min_df=1               # Minimum document frequency (1 = include all terms)
    )
    
    # Fit and transform the documents
    # This creates TF-IDF vectors for both documents
    tfidf_matrix = vectorizer.fit_transform([doc1, doc2])
    
    # Calculate cosine similarity between the two documents
    # cosine_similarity returns a matrix, we need the [0,1] or [1,0] element
    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    
    return similarity_score


def display_tfidf_features(doc1: str, doc2: str):
    """
    Display the TF-IDF features and their weights for both documents.
    This helps understand which terms contribute to the similarity.
    """
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=1
    )
    
    tfidf_matrix = vectorizer.fit_transform([doc1, doc2])
    feature_names = vectorizer.get_feature_names_out()
    
    print("\n" + "="*80)
    print("TF-IDF Feature Analysis")
    print("="*80)
    
    # Get top features for each document
    for doc_idx, doc_text in enumerate([doc1, doc2], 1):
        print(f"\n--- Document {doc_idx} Top Features ---")
        # Get the TF-IDF vector for this document
        tfidf_vector = tfidf_matrix[doc_idx - 1].toarray()[0]
        
        # Get indices sorted by TF-IDF score (descending)
        top_indices = np.argsort(tfidf_vector)[::-1][:15]  # Top 15 features
        
        for idx in top_indices:
            if tfidf_vector[idx] > 0:
                print(f"  {feature_names[idx]:30s} : {tfidf_vector[idx]:.4f}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Example documents
    document_1 = """I want to study Data Science in Berlin City, English Program, Free tuition fee. I am vietnamese citizenship. My GPA 2.5 (German scale)"""
    
    document_2 = """This programm is AI and DS in TU Berlin, semester fee 150 euro, 500 euro tuition fee for EU and non EU student, English program can be taught in full but some optional courses are Deutsch. GPA at least 2.5 (German scale)"""
    
    print("="*80)
    print("TF-IDF and Cosine Similarity Calculator")
    print("="*80)
    
    print("\n--- Document 1 ---")
    print(document_1)
    
    print("\n--- Document 2 ---")
    print(document_2)
    
    # Calculate similarity
    similarity_score = calculate_tfidf_cosine_similarity(document_1, document_2)
    
    print("\n" + "="*80)
    print(f"Cosine Similarity Score: {similarity_score:.4f}")
    print(f"Similarity Percentage: {similarity_score * 100:.2f}%")
    print("="*80)
    
    # Display detailed TF-IDF analysis
    display_tfidf_features(document_1, document_2)
    
    # Interpretation
    print("\n" + "="*80)
    print("Interpretation:")
    print("="*80)
    if similarity_score >= 0.7:
        print("High similarity: Documents are very similar in content and topics.")
    elif similarity_score >= 0.4:
        print("Moderate similarity: Documents share some common themes and keywords.")
    elif similarity_score >= 0.2:
        print("Low similarity: Documents have minimal overlap in content.")
    else:
        print("Very low similarity: Documents are quite different.")
    print("="*80)

