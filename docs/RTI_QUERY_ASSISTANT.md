# RTI Query Assistant

AI-powered query optimization for RTI requests.

## Architecture

```
Streamlit UI (frontend)
    ↓
Query Optimizer Service (orchestrator)
    ↓
├── Weakness Detector
├── Metadata Extractor
├── Precedent Retriever (uses hybrid RAG)
└── Query Rewriter (LLM-based)
```

## Service Layer

### 1. Weakness Detector
**File:** `app/services/weakness_detector.py`

Detects issues in RTI queries:
- Vague wording (why, how, reason)
- Emotional language (unfair, corrupt)
- Missing date ranges
- Missing departments
- Not document-oriented
- Subjective questions
- Overly broad scope

**Severity levels:** high, medium, low

### 2. Metadata Extractor
**File:** `app/services/metadata_extractor.py`

Extracts structured information:
- Date ranges (YYYY-YYYY, between X and Y)
- Ministries (Ministry of X, abbreviations)
- Document types (records, files, reports)

### 3. Precedent Retriever
**File:** `app/services/precedent_retriever.py`

Retrieves relevant CIC cases using existing hybrid RAG pipeline:
- BM25 search
- Semantic vector search
- Hybrid scoring (BM25_WEIGHT + SEMANTIC_WEIGHT)
- Filters by minimum relevance score

### 4. Query Rewriter
**File:** `app/services/query_rewriter.py`

LLM-based query rewriting:
- Converts vague queries to document-oriented requests
- Adds specificity (dates, departments)
- Removes emotional language
- Uses precedents as examples
- Generates improvement summary

### 5. Query Optimizer (Main Orchestrator)
**File:** `app/services/query_optimizer.py`

Coordinates full pipeline:
1. Detect weaknesses
2. Extract metadata
3. Retrieve precedents
4. Rewrite query
5. Calculate confidence scores

**Returns:**
```python
{
    "original_query": str,
    "optimized_query": str,
    "issues_detected": List[Dict],
    "improvements_made": List[str],
    "relevant_precedents": List[Dict],
    "metadata": Dict,
    "scores": {
        "original_clarity": float,
        "optimized_clarity": float,
        "legal_specificity": float,
        "retrieval_quality_prediction": float
    }
}
```

## Streamlit UI

**Tab:** "✨ RTI Query Assistant"

**Features:**
- Text area for user query input
- Optimize button triggers full pipeline
- Issues detected (expandable cards with severity)
- Side-by-side comparison (original vs optimized)
- Improvements made (checklist)
- Quality scores (3 metrics with delta)
- Relevant precedents (expandable with metadata)
- Extracted metadata (JSON view)
- Help section with tips and examples

## Usage

### From Streamlit UI:
1. Navigate to "✨ RTI Query Assistant" tab
2. Enter query (min 10 characters)
3. Click "🔍 Optimize RTI Query"
4. Review issues, improvements, and optimized query
5. Check precedents for similar cases

### Programmatic:
```python
from app.services.query_optimizer import QueryOptimizer

optimizer = QueryOptimizer()
result = optimizer.optimize("Why was electricity cut?")

print(result["optimized_query"])
print(result["scores"])
```

## Example

**Input:**
```
Why was electricity cut in my area?
```

**Issues Detected:**
- Vague wording (high)
- Missing date range (medium)
- Missing department (medium)
- Not document-oriented (high)
- Subjective question (medium)

**Optimized Output:**
```
Provide records/documents regarding the electricity cut in my area, specifically:

1. Notices or orders issued for electricity cuts between January 1, 2023, and December 31, 2024
2. Maintenance schedules and planned outage notifications
3. Complaint logs and resolution reports
4. Communication with the electricity distribution company
5. Any correspondence regarding power supply disruptions
```

**Improvements:**
- ✓ Made document-oriented
- ✓ Added date range
- ✓ Added specificity and detail
- ✓ Converted question to document request
- ✓ Replaced vague terms with specific requests

**Scores:**
- Original clarity: 0.40 → Optimized clarity: 0.80 (+100%)
- Legal specificity: 1.00
- Retrieval quality prediction: 0.54

## Design Principles

1. **Separation of Concerns**
   - UI layer (Streamlit) only handles display
   - Service layer handles business logic
   - Retrieval layer (existing RAG) stays hidden

2. **Reusability**
   - Services can be used independently
   - Programmatic access available
   - No tight coupling to Streamlit

3. **Transparency**
   - Shows what was detected
   - Explains improvements made
   - Provides confidence scores

4. **Educational**
   - Teaches users how to write better RTIs
   - Shows precedent examples
   - Provides tips and guidelines

## Dependencies

- Groq API (for LLM-based rewriting)
- Existing hybrid RAG pipeline (BM25 + vector search)
- Backend config (GROQ_API_KEY, GROQ_MODEL)

## Configuration

Uses existing backend config:
- `GROQ_API_KEY`: API key for query rewriting
- `GROQ_MODEL`: Model for LLM operations
- `BM25_WEIGHT`: Weight for BM25 in hybrid search
- `SEMANTIC_WEIGHT`: Weight for semantic search

## Future Enhancements

1. **Query Templates**
   - Pre-built templates for common RTI types
   - Ministry-specific templates

2. **Historical Success Rates**
   - Show success rates for similar queries
   - Predict likelihood of information disclosure

3. **Multi-language Support**
   - Support Hindi and regional languages
   - Translate precedents

4. **Batch Optimization**
   - Optimize multiple queries at once
   - Export optimized queries

5. **Learning from Feedback**
   - Track which optimizations users accept
   - Improve rewriting based on user preferences
