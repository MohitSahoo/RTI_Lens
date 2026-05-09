"""
UI Simulation Test
Simulates what happens when user submits query in Streamlit UI
"""
import sys
sys.path.insert(0, '/Users/mohitsahoo/Desktop/IDP')

from app.services.query_optimizer import QueryOptimizer
import json

def test_query(query_text, test_name):
    """Simulate UI query submission"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    print(f"Input: {query_text[:80]}...")

    optimizer = QueryOptimizer()
    result = optimizer.optimize(query_text)

    # Check 1: Ministry Classification
    ministry = result['ministry_suggestion']
    print(f"\n✓ Ministry: {ministry['primary_ministry']}")
    print(f"  Confidence: {ministry['confidence']:.0%}")

    if ministry['confidence'] >= 0.7:
        print(f"  ✅ HIGH confidence (target: >70%)")
    else:
        print(f"  ⚠️  Low confidence: {ministry['confidence']:.0%}")

    # Check 2: Section Recommendations
    sections = result['section_recommendations']['primary_sections']
    print(f"\n✓ Sections: {len(sections)} recommended")
    for sec in sections:
        print(f"  • {sec['section']}: {sec['reason'][:60]}...")

    # Check for context-aware guidance
    section_text = str(sections)
    if "third party" in query_text.lower() and "Third-party" in section_text:
        print(f"  ✅ Context-aware guidance detected")

    # Check 3: Optimized Query Length
    optimized = result['optimized_query']
    char_count = len(optimized)
    word_count = len(optimized.split())
    para_count = len([p for p in optimized.split('\n\n') if p.strip()])

    print(f"\n✓ Optimized Query:")
    print(f"  Length: {char_count} chars, {word_count} words")
    print(f"  Paragraphs: {para_count}")

    if char_count <= 600:
        print(f"  ✅ CONCISE (target: <600 chars)")
    else:
        print(f"  ⚠️  Too long: {char_count} chars")

    if para_count <= 3:
        print(f"  ✅ BRIEF (target: ≤3 paragraphs)")
    else:
        print(f"  ⚠️  Too many paragraphs: {para_count}")

    # Check 4: Precedent Quality
    precedents = result['relevant_precedents']
    print(f"\n✓ Precedents: {len(precedents)} retrieved")

    has_artifacts = False
    for i, prec in enumerate(precedents[:2], 1):
        preview = prec['text_preview']
        if '##' in preview or '# ' in preview:
            has_artifacts = True
            print(f"  ⚠️  Precedent {i} has markdown artifacts")
        else:
            print(f"  • Precedent {i}: {len(preview)} chars, clean ✓")

    if not has_artifacts:
        print(f"  ✅ NO markdown artifacts")

    # Check 5: Metadata Extraction
    metadata = result['metadata']
    print(f"\n✓ Metadata:")
    if metadata.get('date_range'):
        dr = metadata['date_range']
        print(f"  Date Range: {dr['start_year']}-{dr['end_year']}")
    else:
        print(f"  Date Range: None (will be added in optimized query)")

    print(f"  Document Types: {len(metadata.get('document_types', []))}")

    # Overall Status
    print(f"\n{'='*70}")
    checks_passed = 0
    checks_total = 5

    if ministry['confidence'] >= 0.7:
        checks_passed += 1
    if char_count <= 600:
        checks_passed += 1
    if para_count <= 3:
        checks_passed += 1
    if not has_artifacts:
        checks_passed += 1
    if len(sections) > 0:
        checks_passed += 1

    print(f"Status: {checks_passed}/{checks_total} checks passed")

    if checks_passed == checks_total:
        print("✅ ALL CHECKS PASSED")
    elif checks_passed >= 4:
        print("⚠️  MOSTLY PASSING")
    else:
        print("❌ NEEDS ATTENTION")

    return result


if __name__ == "__main__":
    print("\n" + "="*70)
    print("RTI QUERY ASSISTANT - UI SIMULATION TEST")
    print("="*70)

    # Test Case 1: Tax Assessment (Third-Party Denial)
    test_query(
        "I want details of tax assessments for my business. PIO denied saying it's confidential third party information. But I am requesting my own tax records.",
        "Tax Assessment (Third-Party Denial)"
    )

    # Test Case 2: Electricity Cut
    test_query(
        "Why was electricity cut in my area?",
        "Electricity Cut"
    )

    # Test Case 3: Road Repair
    test_query(
        "Road repair work not completed in my area",
        "Road Repair"
    )

    print("\n" + "="*70)
    print("UI SIMULATION COMPLETE")
    print("="*70)
    print("\nNext: Test manually in Streamlit UI at http://localhost:8501")
    print("Use queries from UI_TEST_QUERIES.txt")
