"""
RTI Appeal Draft Generation Endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from google import genai
from google.genai import types
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
import logging
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, RATE_LIMIT
from backend.database import get_db
from backend.schemas import DraftRequest, DraftResponse
from backend.utils.bm25_loader import BM25Loader
from backend.utils.sanitization import sanitize_context, validate_ministry_name, validate_section_cited

router = APIRouter(prefix="/api", tags=["draft"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

@router.post("/draft", response_model=DraftResponse)
@limiter.limit(RATE_LIMIT)
async def generate_draft(request: Request, body: DraftRequest, db: Session = Depends(get_db)):
    """
    Generate RTI appeal draft using BM25 retrieval + section stats + Gemini
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Draft endpoint unavailable: GEMINI_API_KEY not configured. Get a key from https://aistudio.google.com/apikey and add to .env file."
        )

    # Sanitize and validate inputs
    ministry = validate_ministry_name(body.ministry)
    if not ministry:
        raise HTTPException(status_code=400, detail="Invalid ministry name")

    section = validate_section_cited(body.section_cited)
    if not section:
        raise HTTPException(status_code=400, detail="Invalid section citation format")

    context = sanitize_context(body.context)
    if not context:
        raise HTTPException(status_code=400, detail="Invalid context input")

    # Get section statistics
    query = text("""
        SELECT
            ss.section_cited,
            ss.total_citations,
            ss.overturned_count,
            ss.misuse_rate,
            m.name AS ministry
        FROM section_stats ss
        JOIN ministries m ON m.id = ss.ministry_id
        WHERE ss.section_cited = :section
          AND m.name = :ministry
    """)

    section_stats = db.execute(query, {
        "section": section,
        "ministry": ministry
    }).fetchone()

    # Retrieve similar cases using BM25
    bm25_loader = BM25Loader()
    search_query = f"{ministry} {section} appeal"
    results = bm25_loader.search(search_query, top_k=3)

    # Build context
    stats_context = ""
    if section_stats:
        stats_context = f"""
Section {section_stats.section_cited} Statistics for {section_stats.ministry}:
- Total citations: {section_stats.total_citations}
- Overturned count: {section_stats.overturned_count}
- Misuse rate: {section_stats.misuse_rate * 100:.1f}%
"""

    similar_cases = "\n".join([
        f"- Order {r['paragraph']['order_number']}: {r['paragraph']['text'][:200]}..."
        for r in results[:2]
    ])

    # Generate draft using Gemini
    prompt = f"""You are an expert RTI appeal drafter in India.

Analyze and improve the following RTI query:

Ministry: {ministry}
Section Cited: {section}
Original Query: {context}

{stats_context}

Similar Cases:
{similar_cases}

Instructions:
- Rewrite the query to be more specific, legally sound, and harder to deny
- Identify what was vague or problematic in the original query
- Suggest phrases to avoid based on common denial patterns
- Reference relevant legal precedents

Return your response as JSON with this exact structure:
{{
  "improved_query": "The rewritten, improved RTI query...",
  "change_notes": [
    {{"original": "vague phrase from original", "revised": "specific phrase in improved", "reason": "why this change helps"}},
    {{"original": "another issue", "revised": "how it was fixed", "reason": "explanation"}}
  ],
  "avoid_phrases": ["phrase 1 that often leads to denial", "phrase 2", "phrase 3"],
  "sources": [
    {{"order_number": "CIC/...", "ministry": "...", "relevance": "why this case is relevant"}}
  ]
}}

Response:"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        response_text = response.text

        # Try to parse JSON response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            parsed = json.loads(response_text)
            improved_query = parsed.get("improved_query", context)
            change_notes = parsed.get("change_notes", [])
            avoid_phrases = parsed.get("avoid_phrases", [])
            sources = parsed.get("sources", [])
        except json.JSONDecodeError:
            # Fallback: use original context and generate basic response
            improved_query = context
            change_notes = [{
                "original": "original query",
                "revised": "improved query",
                "reason": "Unable to parse AI response"
            }]
            avoid_phrases = ["vague requests", "general information"]
            sources = []

        # Add context-specific avoid phrases from section stats
        if section_stats and section_stats.misuse_rate > 0.3:
            avoid_phrases.append(
                f"Avoid citing {section} without specific justification "
                f"(has {section_stats.misuse_rate * 100:.1f}% overturn rate)"
            )

        # Add sources from BM25 results
        for r in results[:2]:
            sources.append({
                "order_number": r['paragraph']['order_number'],
                "ministry": r['paragraph']['ministry'],
                "relevance": "Similar case with relevant precedent"
            })

        return DraftResponse(
            improved_query=improved_query,
            change_notes=change_notes[:5],  # Limit to 5
            avoid_phrases=avoid_phrases[:5],  # Limit to 5
            sources=sources[:3]  # Limit to 3
        )

    except ValueError as e:
        logger.error(f"Validation error in draft generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in draft generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error in draft generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while generating the draft. Please try again.")
