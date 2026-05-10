# RTI-Lens API Documentation

Complete API reference for the RTI-Lens backend services.

**Base URL:** `http://localhost:8000`

---

## Table of Contents

- [Authentication](#authentication)
- [Query Assistant](#query-assistant)
- [Draft Generation](#draft-generation)
- [Q&A System](#qa-system)
- [Prediction](#prediction)
- [Analytics](#analytics)
- [Knowledge Graph](#knowledge-graph)
- [Blockchain](#blockchain)
- [Voice Interface](#voice-interface)
- [Error Handling](#error-handling)

---

## Authentication

Currently, the API does not require authentication. Rate limiting is applied per IP address.

**Rate Limits:**
- Standard endpoints: 100 requests/minute
- LLM endpoints: 10 requests/minute
- Blockchain endpoints: 5 requests/minute

---

## Query Assistant

### Optimize Query

Analyzes and improves RTI queries using hybrid RAG and LLM generation.

**Endpoint:** `POST /api/query-assistant/optimize`

**Request Body:**
```json
{
  "query": "string (required, min 10 chars)"
}
```

**Response:**
```json
{
  "original_query": "string",
  "improved_query": "string",
  "weaknesses": [
    {
      "type": "vague_wording | missing_dates | emotional_language | etc",
      "description": "string",
      "suggestion": "string"
    }
  ],
  "change_notes": [
    {
      "original": "string",
      "revised": "string",
      "reason": "string"
    }
  ],
  "ministry_suggestion": {
    "primary_ministry": "string",
    "confidence": "float (0-1)",
    "reasoning": "string"
  },
  "section_recommendations": {
    "primary_sections": [
      {
        "section": "string",
        "relevance_score": "float (0-1)",
        "reasoning": "string"
      }
    ]
  },
  "relevant_precedents": [
    {
      "order_number": "string",
      "ministry": "string",
      "outcome": "Allowed | Denied | Partially Allowed",
      "relevance_score": "float (0-1)",
      "excerpt": "string"
    }
  ],
  "avoid_phrases": ["string"],
  "section_statistics": {
    "section_id": {
      "total_cases": "int",
      "overturn_rate": "float (0-1)",
      "common_grounds": ["string"]
    }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/query-assistant/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I want information about railway projects"
  }'
```

**Status Codes:**
- `200 OK` - Query optimized successfully
- `400 Bad Request` - Invalid query (too short, empty, etc.)
- `500 Internal Server Error` - Processing error

---

## Draft Generation

### Generate Appeal Draft

Generates a complete RTI appeal draft using Groq LLM with precedent grounding.

**Endpoint:** `POST /api/draft`

**Request Body:**
```json
{
  "context": "string (required, min 50 chars)",
  "ministry": "string (required)",
  "section_cited": "string (required)",
  "appeal_level": "first | second (default: first)"
}
```

**Response:**
```json
{
  "draft": "string (markdown formatted)",
  "precedents_used": [
    {
      "order_number": "string",
      "relevance": "float (0-1)",
      "key_excerpt": "string"
    }
  ],
  "change_notes": [
    {
      "original": "string",
      "revised": "string",
      "reason": "string"
    }
  ],
  "confidence_score": "float (0-1)",
  "estimated_strength": "strong | moderate | weak",
  "blockchain_tx": "string (optional, Solana signature)"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/draft \
  -H "Content-Type: application/json" \
  -d '{
    "context": "My RTI request for railway project documents was denied under Section 8(1)(a) claiming confidential commercial information. However, the project is publicly funded and completed 2 years ago.",
    "ministry": "Ministry of Railways",
    "section_cited": "8(1)(a)",
    "appeal_level": "first"
  }'
```

**Status Codes:**
- `200 OK` - Draft generated successfully
- `400 Bad Request` - Invalid input parameters
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Generation error

---

## Q&A System

### Ask Question

Ask questions about RTI case law and get grounded answers with citations.

**Endpoint:** `POST /api/qa`

**Request Body:**
```json
{
  "question": "string (required, min 10 chars)",
  "max_precedents": "int (optional, default: 5, max: 10)"
}
```

**Response:**
```json
{
  "answer": "string",
  "confidence": "float (0-1)",
  "sources": [
    {
      "order_number": "string",
      "ministry": "string",
      "outcome": "string",
      "relevance_score": "float (0-1)",
      "excerpt": "string",
      "url": "string (optional)"
    }
  ],
  "faithfulness_score": "float (0-1)",
  "retrieval_method": "hybrid | bm25 | semantic"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are valid grounds for Section 8(1)(j) exemptions?",
    "max_precedents": 5
  }'
```

**Status Codes:**
- `200 OK` - Answer generated successfully
- `400 Bad Request` - Invalid question
- `404 Not Found` - No relevant precedents found
- `500 Internal Server Error` - Processing error

---

## Prediction

### Predict Outcome

Predict RTI appeal outcome using XGBoost model trained on historical data.

**Endpoint:** `POST /api/predict`

**Request Body:**
```json
{
  "ministry": "string (required)",
  "section_cited": "string (required)",
  "appeal_level": "first | second (required)",
  "query_features": {
    "word_count": "int (optional)",
    "has_specific_dates": "boolean (optional)",
    "has_document_list": "boolean (optional)"
  }
}
```

**Response:**
```json
{
  "prediction": "Allowed | Denied | Partially Allowed",
  "confidence": "float (0-1)",
  "probabilities": {
    "Allowed": "float (0-1)",
    "Denied": "float (0-1)",
    "Partially Allowed": "float (0-1)"
  },
  "feature_importance": {
    "ministry": "float",
    "section": "float",
    "appeal_level": "float"
  },
  "similar_cases": [
    {
      "order_number": "string",
      "outcome": "string",
      "similarity": "float (0-1)"
    }
  ],
  "model_version": "string"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ministry": "Ministry of Finance",
    "section_cited": "8(1)(a)",
    "appeal_level": "first"
  }'
```

**Status Codes:**
- `200 OK` - Prediction generated successfully
- `400 Bad Request` - Invalid input parameters
- `500 Internal Server Error` - Model error

---

## Analytics

### Get Dashboard Statistics

Retrieve aggregated statistics for dashboard visualizations.

**Endpoint:** `GET /api/analytics/dashboard`

**Query Parameters:**
- `ministry` (optional): Filter by ministry
- `section` (optional): Filter by section
- `year` (optional): Filter by year

**Response:**
```json
{
  "total_cases": "int",
  "outcome_distribution": {
    "Allowed": "int",
    "Denied": "int",
    "Partially Allowed": "int"
  },
  "ministry_stats": [
    {
      "ministry": "string",
      "total_cases": "int",
      "overturn_rate": "float (0-1)"
    }
  ],
  "section_stats": [
    {
      "section": "string",
      "usage_count": "int",
      "success_rate": "float (0-1)"
    }
  ],
  "temporal_trends": [
    {
      "month": "string (YYYY-MM)",
      "case_count": "int",
      "allowed_rate": "float (0-1)"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/analytics/dashboard?ministry=Ministry%20of%20Finance
```

**Status Codes:**
- `200 OK` - Statistics retrieved successfully
- `400 Bad Request` - Invalid filter parameters
- `500 Internal Server Error` - Database error

---

## Knowledge Graph

### Get Graph Data

Retrieve knowledge graph data for visualization.

**Endpoint:** `GET /api/graph`

**Query Parameters:**
- `ministry` (optional): Filter by ministry
- `max_nodes` (optional, default: 100): Maximum nodes to return

**Response:**
```json
{
  "nodes": [
    {
      "id": "string",
      "type": "ministry | section | case",
      "label": "string",
      "properties": {
        "case_count": "int",
        "outcome": "string"
      }
    }
  ],
  "edges": [
    {
      "source": "string (node id)",
      "target": "string (node id)",
      "type": "cites | relates_to | overturns",
      "weight": "float (0-1)"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/graph?ministry=Ministry%20of%20Railways&max_nodes=50
```

**Status Codes:**
- `200 OK` - Graph data retrieved successfully
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Database error

---

## Blockchain

### Anchor Document

Anchor an RTI document hash on Solana blockchain.

**Endpoint:** `POST /api/blockchain/anchor`

**Request Body:**
```json
{
  "document_hash": "string (required, SHA-256 hex)",
  "metadata": {
    "ministry": "string (optional)",
    "submission_date": "string (optional, ISO 8601)",
    "citizen_id": "string (optional)"
  }
}
```

**Response:**
```json
{
  "transaction_signature": "string",
  "explorer_url": "string",
  "timestamp": "string (ISO 8601)",
  "network": "devnet | mainnet",
  "status": "confirmed | simulated"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/blockchain/anchor \
  -H "Content-Type: application/json" \
  -d '{
    "document_hash": "a3c5e8d2f1b4a6c9e7d3f2a1b5c8e4d7f9a2b6c3e8d1f4a7b9c2e5d8f1a4b7c9",
    "metadata": {
      "ministry": "Ministry of Finance",
      "submission_date": "2024-05-10T10:30:00Z"
    }
  }'
```

**Status Codes:**
- `200 OK` - Document anchored successfully
- `400 Bad Request` - Invalid hash or metadata
- `503 Service Unavailable` - Blockchain connection error

### Verify Document

Verify a document hash exists on blockchain.

**Endpoint:** `GET /api/blockchain/verify/{document_hash}`

**Response:**
```json
{
  "exists": "boolean",
  "transaction_signature": "string (if exists)",
  "timestamp": "string (ISO 8601, if exists)",
  "metadata": "object (if exists)"
}
```

**Example:**
```bash
curl http://localhost:8000/api/blockchain/verify/a3c5e8d2f1b4a6c9e7d3f2a1b5c8e4d7f9a2b6c3e8d1f4a7b9c2e5d8f1a4b7c9
```

---

## Voice Interface

### Transcribe Audio

Convert speech to text using ElevenLabs or Groq Whisper.

**Endpoint:** `POST /api/voice/transcribe`

**Request Body:** `multipart/form-data`
- `audio`: Audio file (WAV, MP3, M4A, max 10MB)
- `language`: Language code (optional, default: "en")

**Response:**
```json
{
  "text": "string",
  "confidence": "float (0-1)",
  "duration_seconds": "float",
  "provider": "elevenlabs | groq"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "audio=@query.wav" \
  -F "language=en"
```

**Status Codes:**
- `200 OK` - Transcription successful
- `400 Bad Request` - Invalid audio file
- `413 Payload Too Large` - File exceeds 10MB
- `500 Internal Server Error` - Transcription error

---

## Error Handling

All endpoints return errors in the following format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)"
  }
}
```

**Common Error Codes:**
- `INVALID_INPUT` - Request validation failed
- `NOT_FOUND` - Resource not found
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `LLM_ERROR` - Groq API error
- `DATABASE_ERROR` - Database connection/query error
- `BLOCKCHAIN_ERROR` - Solana transaction error
- `INTERNAL_ERROR` - Unexpected server error

---

## Data Models

### Ministry

```typescript
{
  id: number
  name: string
  total_cases: number
  overturn_rate: number
}
```

### Section

```typescript
{
  id: string  // e.g., "8(1)(a)"
  description: string
  usage_count: number
  success_rate: number
}
```

### Case

```typescript
{
  id: number
  order_number: string
  ministry: string
  section_cited: string
  outcome: "Allowed" | "Denied" | "Partially Allowed"
  appeal_level: "first" | "second"
  decision_date: string  // ISO 8601
}
```

### Precedent

```typescript
{
  order_number: string
  ministry: string
  outcome: string
  relevance_score: number  // 0-1
  excerpt: string
  full_text: string
}
```

---

## Webhooks (Future)

Webhook support is planned for:
- Appeal outcome notifications
- Blockchain confirmation events
- Model retraining completion

---

## SDK Examples

### Python

```python
import requests

# Optimize query
response = requests.post(
    "http://localhost:8000/api/query-assistant/optimize",
    json={"query": "I want railway project information"}
)
result = response.json()
print(result["improved_query"])

# Generate draft
response = requests.post(
    "http://localhost:8000/api/draft",
    json={
        "context": result["improved_query"],
        "ministry": result["ministry_suggestion"]["primary_ministry"],
        "section_cited": "8(1)(a)",
        "appeal_level": "first"
    }
)
draft = response.json()
print(draft["draft"])
```

### JavaScript

```javascript
// Optimize query
const response = await fetch('http://localhost:8000/api/query-assistant/optimize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'I want railway project information' })
});
const result = await response.json();
console.log(result.improved_query);

// Generate draft
const draftResponse = await fetch('http://localhost:8000/api/draft', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    context: result.improved_query,
    ministry: result.ministry_suggestion.primary_ministry,
    section_cited: '8(1)(a)',
    appeal_level: 'first'
  })
});
const draft = await draftResponse.json();
console.log(draft.draft);
```

---

## Performance

**Typical Response Times:**
- Query optimization: 2-4 seconds
- Draft generation: 3-5 seconds
- Q&A: 1-3 seconds
- Prediction: <100ms
- Analytics: <200ms
- Blockchain anchoring: 1-2 seconds

**Throughput:**
- Standard endpoints: ~50 req/s
- LLM endpoints: ~10 req/s (limited by Groq API)

---

## Changelog

### v1.0.0 (Current)
- Initial API release
- Hybrid RAG pipeline
- Groq LLM integration
- XGBoost prediction
- Solana blockchain anchoring
- Voice interface

---

## Support

For API issues or questions:
- GitHub Issues: [Link to repo]
- Documentation: [Link to docs]
- Email: support@rti-lens.example.com
