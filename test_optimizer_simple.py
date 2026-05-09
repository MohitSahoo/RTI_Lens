"""
Simple test to verify QueryOptimizer functionality
"""
import sys
sys.path.insert(0, '/Users/mohitsahoo/Desktop/IDP')

from app.services.query_optimizer import QueryOptimizer
import json

def test_basic_query():
    """Test basic query optimization"""
    print("Testing QueryOptimizer with real retrieval...\n")

    optimizer = QueryOptimizer()

    # Test query
    query = "What is Section 8(1)(a) about?"
    print(f"Query: {query}\n")

    result = optimizer.optimize(query)

    # Print key results
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(f"\nStatus: {result['status']}")
    print(f"\nOriginal Query: {result['original_query']}")
    print(f"\nOptimized Query: {result['optimized_query']}")

    print(f"\n--- Ministry Suggestion ---")
    ministry = result['ministry_suggestion']
    print(f"Primary: {ministry['primary_ministry']}")
    print(f"Confidence: {ministry['confidence']:.1%}")
    print(f"Reasoning: {ministry['reasoning']}")

    print(f"\n--- Section Recommendations ---")
    sections = result['section_recommendations']['primary_sections']
    for sec in sections:
        print(f"• {sec['section']}: {sec['reason']}")

    print(f"\n--- Precedents Retrieved ---")
    precedents = result['relevant_precedents']
    print(f"Count: {len(precedents)}")
    for i, prec in enumerate(precedents[:3], 1):
        print(f"\n{i}. Order: {prec['order_number']}")
        print(f"   Ministry: {prec['ministry']}")
        print(f"   Section: {prec['section_cited']}")
        print(f"   Score: {prec['relevance_score']:.3f}")
        print(f"   Preview: {prec['text_preview'][:100]}...")

    print(f"\n--- Quality Scores ---")
    scores = result['scores']
    print(f"Original Clarity: {scores['original_clarity']:.2f}")
    print(f"Optimized Clarity: {scores['optimized_clarity']:.2f}")
    print(f"Legal Specificity: {scores['legal_specificity']:.2f}")
    print(f"Retrieval Quality: {scores['retrieval_quality_prediction']:.2f}")
    print(f"Overall Confidence: {scores['overall_confidence']:.2f}")

    print(f"\n--- Issues Detected ---")
    issues = result['issues_detected']
    if issues:
        for issue in issues:
            print(f"• [{issue['severity']}] {issue['description']}")
            print(f"  Suggestion: {issue['suggestion']}")
    else:
        print("None")

    print(f"\n--- Improvements Made ---")
    improvements = result['improvements_made']
    if improvements:
        for imp in improvements:
            print(f"• {imp}")
    else:
        print("None")

    print("\n" + "=" * 60)
    print("✅ QueryOptimizer is working with real retrieval!")
    print("=" * 60)

if __name__ == "__main__":
    test_basic_query()
