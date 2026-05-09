# Query Optimizer - Quick Reference

## Basic Usage

```python
from app.services.query_optimizer import QueryOptimizer

# Initialize
optimizer = QueryOptimizer()

# Optimize a query
result = optimizer.optimize("Why was my RTI request denied?")

# Access results
print(result['optimized_query'])
print(result['ministry_suggestion']['primary_ministry'])
print(result['section_recommendations']['primary_sections'])
```

## Response Structure

```python
{
    "status": "optimized",  # or "needs_clarification"
    "original_query": "...",
    "optimized_query": "...",
    
    "ministry_suggestion": {
        "primary_ministry": "Ministry of Finance",
        "confidence": 0.8,
        "reasoning": "Based on 4/5 similar cases",
        "alternative_ministries": [...]
    },
    
    "section_recommendations": {
        "primary_sections": [
            {"section": "Section 8(1)(j)", "reason": "..."}
        ],
        "optional_sections": [...],
        "exemption_notes": []
    },
    
    "relevant_precedents": [
        {
            "order_number": "CIC/...",
            "ministry": "...",
            "section_cited": "...",
            "order_date": "...",
            "text_preview": "...",
            "relevance_score": 0.8
        }
    ],
    
    "issues_detected": [
        {
            "type": "question_format",
            "severity": "medium",
            "description": "...",
            "suggestion": "..."
        }
    ],
    
    "improvements_made": [
        "Converted question to document request",
        "Added document-oriented language"
    ],
    
    "scores": {
        "original_clarity": 0.55,
        "optimized_clarity": 0.90,
        "legal_specificity": 0.70,
        "retrieval_quality_prediction": 0.21,
        "overall_confidence": 0.60
    },
    
    "metadata": {
        "query_length": 35,
        "has_dates": false,
        "has_documents": false,
        "extracted_sections": ["8(1)(a)"],
        "extracted_ministries": [],
        "date_range": {"start_year": 2023, "end_year": 2024},
        "document_types": ["records", "files"]
    }
}
```

## Common Patterns

### Check Ministry Confidence
```python
result = optimizer.optimize(query)
ministry = result['ministry_suggestion']

if ministry['confidence'] >= 0.7:
    print(f"High confidence: {ministry['primary_ministry']}")
else:
    print(f"Low confidence. Alternatives: {ministry['alternative_ministries']}")
```

### Get Top Sections
```python
sections = result['section_recommendations']['primary_sections']
for sec in sections:
    print(f"{sec['section']}: {sec['reason']}")
```

### Check for Issues
```python
issues = result['issues_detected']
high_priority = [i for i in issues if i['severity'] == 'high']

if high_priority:
    print("Critical issues found:")
    for issue in high_priority:
        print(f"- {issue['description']}")
        print(f"  Suggestion: {issue['suggestion']}")
```

### Access Precedents
```python
precedents = result['relevant_precedents']
print(f"Found {len(precedents)} relevant cases")

for prec in precedents[:3]:  # Top 3
    print(f"\nOrder: {prec['order_number']}")
    print(f"Ministry: {prec['ministry']}")
    print(f"Relevance: {prec['relevance_score']:.2f}")
    print(f"Preview: {prec['text_preview'][:100]}...")
```

## Testing

### Run Tests
```bash
# Full UI simulation test
python3 test_ui_simulation.py

# Simple verification test
python3 test_optimizer_simple.py
```

### Test Custom Query
```python
from app.services.query_optimizer import QueryOptimizer

optimizer = QueryOptimizer()
result = optimizer.optimize("Your custom query here")

# Check key metrics
print(f"Status: {result['status']}")
print(f"Ministry: {result['ministry_suggestion']['primary_ministry']}")
print(f"Confidence: {result['ministry_suggestion']['confidence']:.1%}")
print(f"Precedents: {len(result['relevant_precedents'])}")
print(f"Overall Score: {result['scores']['overall_confidence']:.2f}")
```

## Performance Tips

1. **Lazy Loading**: Dependencies load on first use (~2-3s cold start)
2. **Warm Queries**: Subsequent queries are fast (~200-500ms)
3. **Memory**: Requires ~500MB for embedding model + BM25 index
4. **Caching**: Consider caching results for identical queries

## Troubleshooting

### No Precedents Found
```python
if not result['relevant_precedents']:
    print("No precedents found. Query may be too generic or off-topic.")
    print(f"Clarification: {result.get('clarification_request')}")
```

### Low Confidence Scores
```python
if result['scores']['overall_confidence'] < 0.5:
    print("Low confidence. Consider:")
    print("- Adding more specific details")
    print("- Mentioning relevant sections or ministries")
    print("- Including time periods or document types")
```

### Import Errors
```python
# Ensure correct path
import sys
sys.path.insert(0, '/path/to/IDP')

from app.services.query_optimizer import QueryOptimizer
```

## Integration Example

### Streamlit UI
```python
import streamlit as st
from app.services.query_optimizer import QueryOptimizer

# Initialize once
if 'optimizer' not in st.session_state:
    st.session_state.optimizer = QueryOptimizer()

# Get user input
query = st.text_area("Enter your RTI query:")

if st.button("Optimize"):
    with st.spinner("Analyzing query..."):
        result = st.session_state.optimizer.optimize(query)
    
    # Display results
    st.success(f"Optimized Query: {result['optimized_query']}")
    
    ministry = result['ministry_suggestion']
    st.info(f"Suggested Ministry: {ministry['primary_ministry']} "
            f"({ministry['confidence']:.0%} confidence)")
    
    sections = result['section_recommendations']['primary_sections']
    st.write("Recommended Sections:")
    for sec in sections:
        st.write(f"- {sec['section']}: {sec['reason']}")
```

## Configuration

### Adjust Hybrid Search Weights
```python
# In query_optimizer.py, modify _retrieve_precedents():
hybrid_results = vector_loader.hybrid_search(
    query=query,
    bm25_results=bm25_results,
    top_k=top_k,
    bm25_weight=0.4,      # Keyword matching weight
    semantic_weight=0.6   # Semantic similarity weight
)
```

### Change Number of Precedents
```python
# In optimize() method:
precedents = self._retrieve_precedents(user_query, top_k=10)  # Default: 5
```

## API Reference

### Main Method
- `optimize(user_query: str) -> Dict`: Main entry point

### Helper Methods
- `_retrieve_precedents(query, top_k)`: Get relevant precedents
- `_suggest_ministry(precedents, extracted_ministries)`: Suggest ministry
- `_recommend_sections(precedents, extracted_sections)`: Recommend sections
- `_optimize_query_phrasing(query)`: Improve query phrasing
- `_calculate_scores(original, optimized, precedents)`: Calculate quality scores
- `_detect_basic_issues(query)`: Detect query issues
- `_extract_date_range(query)`: Extract date range
- `_extract_document_types(query)`: Extract document types

## Next Steps

1. Test with real user queries
2. Monitor ministry suggestion accuracy
3. Collect user feedback on recommendations
4. Fine-tune hybrid search weights
5. Add more sophisticated query rewriting
