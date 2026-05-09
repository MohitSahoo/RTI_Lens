# Query Optimization Flowchart

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUERY INPUT                            │
│              "Why was my RTI request denied?"                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ENTITY EXTRACTION                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ EntityExtractor.extract_entities(query)                      │  │
│  │                                                               │  │
│  │ • Extract sections: ["8(1)(j)", "8(1)(a)"]                   │  │
│  │ • Extract ministries: ["Ministry of Finance"]                │  │
│  │ • Extract dates: [2024, 2025]                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    HYBRID RETRIEVAL                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Step 1: BM25 Search                                          │  │
│  │ ├─ BM25Loader.search(query, top_k=10)                        │  │
│  │ └─ Returns: 10 keyword-matched precedents                    │  │
│  │                                                               │  │
│  │ Step 2: Vector Search + Hybrid Scoring                       │  │
│  │ ├─ VectorSearchLoader.hybrid_search()                        │  │
│  │ ├─ BM25 weight: 0.4                                          │  │
│  │ ├─ Semantic weight: 0.6                                      │  │
│  │ └─ Returns: Top 5 precedents with relevance scores           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  PRECEDENT ANALYSIS                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ For each precedent:                                          │  │
│  │ • Extract ministry                                           │  │
│  │ • Extract sections cited                                     │  │
│  │ • Extract order date                                         │  │
│  │ • Clean text (remove markdown)                               │  │
│  │ • Create preview (300 chars)                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌───────────────────────────┐  ┌──────────────────────────────┐
│  MINISTRY SUGGESTION      │  │  SECTION RECOMMENDATIONS     │
│  ┌─────────────────────┐  │  │  ┌────────────────────────┐  │
│  │ Count ministries in │  │  │  │ Count sections in      │  │
│  │ precedents:         │  │  │  │ precedents:            │  │
│  │                     │  │  │  │                        │  │
│  │ Finance: 4/5        │  │  │  │ 8(1)(j): 2/5          │  │
│  │ Home: 1/5           │  │  │  │ 8(1)(g): 1/5          │  │
│  │                     │  │  │  │                        │  │
│  │ Primary: Finance    │  │  │  │ Primary: 8(1)(j)      │  │
│  │ Confidence: 80%     │  │  │  │ Optional: 8(1)(g)     │  │
│  │ Reasoning: "Based   │  │  │  │ Reason: "Cited in     │  │
│  │ on 4/5 cases"       │  │  │  │ 2/5 similar cases"    │  │
│  └─────────────────────┘  │  │  └────────────────────────┘  │
└───────────────┬───────────┘  └──────────────┬───────────────┘
                │                             │
                └──────────┬──────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  QUERY OPTIMIZATION                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Step 1: Convert Questions to Document Requests               │  │
│  │ ├─ "Why was..." → "Provide records explaining..."            │  │
│  │ ├─ "What is..." → "Provide information regarding..."         │  │
│  │ └─ "How did..." → "Provide records showing..."               │  │
│  │                                                               │  │
│  │ Step 2: Add Document-Oriented Language                       │  │
│  │ └─ If missing: prepend "Provide records and documents..."    │  │
│  │                                                               │  │
│  │ Step 3: Track Improvements                                   │  │
│  │ └─ ["Converted question to document request"]                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    QUALITY SCORING                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Original Clarity Score (0-1)                                 │  │
│  │ ├─ Length check (20-600 chars)                               │  │
│  │ ├─ Has document keywords                                     │  │
│  │ ├─ Has dates                                                 │  │
│  │ └─ Not a question                                            │  │
│  │                                                               │  │
│  │ Optimized Clarity Score (0-1)                                │  │
│  │ └─ Same checks on optimized query                            │  │
│  │                                                               │  │
│  │ Legal Specificity Score (0-1)                                │  │
│  │ ├─ Has sections                                              │  │
│  │ ├─ Has ministries                                            │  │
│  │ └─ Has legal terms                                           │  │
│  │                                                               │  │
│  │ Retrieval Quality Prediction (0-1)                           │  │
│  │ └─ Average relevance score of precedents                     │  │
│  │                                                               │  │
│  │ Overall Confidence (0-1)                                     │  │
│  │ └─ Weighted average of all scores                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ISSUE DETECTION                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Check for:                                                   │  │
│  │ • Too short (< 20 chars) → HIGH severity                     │  │
│  │ • Emotional language → MEDIUM severity                       │  │
│  │ • Question format → MEDIUM severity                          │  │
│  │                                                               │  │
│  │ For each issue:                                              │  │
│  │ └─ Provide specific suggestion                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  METADATA EXTRACTION                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • Query length: 52 chars                                     │  │
│  │ • Has dates: false                                           │  │
│  │ • Has documents: false                                       │  │
│  │ • Extracted sections: ["8(1)(j)"]                            │  │
│  │ • Extracted ministries: []                                   │  │
│  │ • Date range: {start_year: 2024, end_year: 2024}            │  │
│  │ • Document types: ["records", "files"]                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FINAL RESPONSE                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ {                                                            │  │
│  │   "status": "optimized",                                     │  │
│  │   "original_query": "...",                                   │  │
│  │   "optimized_query": "...",                                  │  │
│  │   "ministry_suggestion": {...},                              │  │
│  │   "section_recommendations": {...},                          │  │
│  │   "relevant_precedents": [...],                              │  │
│  │   "issues_detected": [...],                                  │  │
│  │   "improvements_made": [...],                                │  │
│  │   "scores": {...},                                           │  │
│  │   "metadata": {...}                                          │  │
│  │ }                                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Decision Points

### 1. Hybrid Search Weighting
```
BM25 Score (0.4) + Semantic Score (0.6) = Final Relevance Score
```

### 2. Ministry Confidence Calculation
```
Confidence = (Most Common Ministry Count) / (Total Precedents)
Example: 4 Finance cases out of 5 total = 80% confidence
```

### 3. Section Recommendation Threshold
```
Primary Sections: Cited in ≥2 cases
Optional Sections: Cited in 1 case
```

### 4. Query Optimization Logic
```
IF query starts with question word (why, what, how)
  THEN convert to document request
ELSE IF missing document keywords
  THEN add "Provide records and documents regarding:"
```

### 5. Overall Confidence Formula
```
Overall = (
  0.3 × Optimized Clarity +
  0.3 × Legal Specificity +
  0.4 × Retrieval Quality
)
```

## Data Flow Summary

```
User Query
    ↓
[Entity Extraction] → sections, ministries, dates
    ↓
[BM25 Search] → 10 keyword matches
    ↓
[Vector Search] → semantic similarity
    ↓
[Hybrid Scoring] → 5 best precedents
    ↓
[Precedent Analysis] → ministry counts, section counts
    ↓
[Ministry Suggestion] ← precedent ministries
[Section Recommendations] ← precedent sections
    ↓
[Query Optimization] → improved phrasing
    ↓
[Quality Scoring] → confidence metrics
    ↓
[Issue Detection] → problems + suggestions
    ↓
[Metadata Extraction] → query statistics
    ↓
Final Optimized Response
```

## Processing Time Breakdown

```
Entity Extraction:     ~10ms
BM25 Search:          ~50ms
Vector Search:        ~100-200ms
Precedent Analysis:   ~20ms
Optimization:         ~10ms
Scoring:              ~10ms
─────────────────────────────
Total:                ~200-300ms (warm)
                      ~2-3s (cold start)
```
