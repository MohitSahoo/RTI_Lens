"""
RTI Appeal Draft Generation Endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from groq import Groq
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
import logging
from backend.config import GROQ_API_KEY, GROQ_MODEL, RATE_LIMIT
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
    Generate RTI appeal draft using BM25 retrieval + section stats + Groq
    """
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Draft endpoint unavailable: GROQ_API_KEY not configured. Get a key from https://console.groq.com/keys and add to .env file."
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
    results = bm25_loader.search(search_query, top_k=5)

    from backend.utils.pageindex_loader import PageIndexLoader
    pageindex_loader = PageIndexLoader()

    # Fetch full case details and hierarchical text
    case_details = []
    order_numbers = [r['paragraph']['order_number'] for r in results[:3]]
    
    for order_number in order_numbers:
        case_query = text("""
            SELECT
                order_number,
                section_cited,
                appeal_outcome,
                appeal_level
            FROM cases
            WHERE order_number = :order_number
            LIMIT 1
        """)
        case_row = db.execute(case_query, {"order_number": order_number}).fetchone()

        if case_row:
            # Use PageIndex to get relevant sections based on the draft context
            sections = pageindex_loader.get_relevant_sections_by_order_numbers(
                [order_number],
                context,
                max_sections=2
            )
            
            if sections:
                case_text = "\n".join([f"[{s['hierarchy']}] {s['text'][:500]}" for s in sections])
            else:
                # Fallback to DB paragraphs if PageIndex fails
                para_query = text("SELECT text FROM paragraphs WHERE case_id = (SELECT id FROM cases WHERE order_number = :order_number) LIMIT 3")
                paras = db.execute(para_query, {"order_number": order_number}).fetchall()
                case_text = "\n".join([p.text[:300] for p in paras])

            case_details.append({
                "order_number": case_row.order_number,
                "section": case_row.section_cited,
                "outcome": case_row.appeal_outcome,
                "level": case_row.appeal_level,
                "text": case_text
            })

    # Build context
    stats_context = ""
    if section_stats:
        stats_context = f"""
Section {section_stats.section_cited} Statistics for {section_stats.ministry}:
- Total citations: {section_stats.total_citations}
- Overturned count: {section_stats.overturned_count}
- Misuse rate: {section_stats.misuse_rate * 100:.1f}%
"""

    similar_cases = ""
    for i, case in enumerate(case_details, 1):
        similar_cases += f"""
Case {i}: {case['order_number']}
Section: {case['section']} | Outcome: {case['outcome']} | Level: {case['level']}
Text: {case['text']}
---
"""

    # Generate draft using Groq
    prompt = f"""You are an expert RTI appeal drafter in India.

Analyze and improve the following RTI query:

Ministry: {ministry}
Section Cited: {section}
Original Query: {context}

{stats_context}

Similar CIC Cases (REAL CASES - DO NOT INVENT):
{similar_cases}

Instructions:
- Rewrite the query to be more specific, legally sound, and harder to deny
- Identify what was vague or problematic in the original query
- Suggest phrases to avoid based on common denial patterns
- For sources: ONLY use the case numbers provided above. Extract relevance DIRECTLY from the case text shown. DO NOT fabricate cases or relevance descriptions.

Return your response as JSON with this exact structure:
{{
  "improved_query": "The rewritten, improved RTI query...",
  "change_notes": [
    {{"original": "vague phrase from original", "revised": "specific phrase in improved", "reason": "why this change helps"}},
    {{"original": "another issue", "revised": "how it was fixed", "reason": "explanation"}}
  ],
  "avoid_phrases": ["phrase 1 that often leads to denial", "phrase 2", "phrase 3"],
  "sources": [
    {{"order_number": "MUST be from cases above", "outcome": "allowed/denied from above", "relevance": "extract ONLY from case text above, quote specific phrases"}}
  ]
}}

CRITICAL: Only reference cases provided above. Do not invent case numbers or relevance.

Response:"""

    try:
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert RTI appeal drafter in India. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        response_text = response.choices[0].message.content

        # Try to parse JSON response
        try:
            if not response_text:
                raise ValueError("Empty response from AI model")

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
        except (json.JSONDecodeError, ValueError):
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

        # Validate sources - only keep if they match actual retrieved cases
        valid_case_numbers = {case['order_number'] for case in case_details}
        validated_sources = []
        for src in sources:
            if src.get('order_number') in valid_case_numbers:
                # Add outcome from actual case data
                matching_case = next((c for c in case_details if c['order_number'] == src['order_number']), None)
                if matching_case:
                    src['outcome'] = matching_case['outcome']
                    src['section'] = matching_case['section']
                    validated_sources.append(src)

        sources = validated_sources[:3]  # Limit to 3 validated sources

        return DraftResponse(
            improved_query=improved_query,
            change_notes=change_notes[:5],  # Limit to 5
            avoid_phrases=avoid_phrases[:5],  # Limit to 5
            sources=sources[:3]  # Limit to 3
        )

    except ValueError as e:
        logger.error(f"Validation error in draft generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in draft generation: {e}", exc_info=True)
        error_msg = str(e)
        if "503" in error_msg or "overloaded" in error_msg.lower() or "high demand" in error_msg.lower():
            raise HTTPException(
                status_code=503, 
                detail="The AI model is currently experiencing high demand. Please try again in a few seconds."
            )
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while generating the draft. Please try again."
        )
