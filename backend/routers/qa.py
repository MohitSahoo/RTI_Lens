"""
Q&A API Endpoint with Hybrid Search (BM25 + Semantic) + PageIndex verification and Groq
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from groq import Groq
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.config import (
    GROQ_API_KEY, GROQ_MODEL, MAX_QA_CALLS_PER_SESSION, RATE_LIMIT,
    BM25_WEIGHT, SEMANTIC_WEIGHT
)
from backend.database import get_db
from backend.schemas import QARequest, QAResponse
from backend.utils.bm25_loader import BM25Loader
try:
    from backend.utils.vector_search import VectorSearchLoader
    VECTOR_SEARCH_AVAILABLE = True
except (ImportError, OSError) as e:
    VECTOR_SEARCH_AVAILABLE = False
    VectorSearchLoader = None
    import logging
    logging.warning(f"Vector search unavailable: {e}")
from backend.utils.pageindex_loader import PageIndexLoader
from backend.utils.sanitization import sanitize_question
from backend.utils.session_manager import SessionManager
import time
import logging

logger = logging.getLogger(__name__)


def _generate_clarification_request(
    question: str,
    sources: list,
    extracted_entities = None
) -> str:
    """Generate clarification request when confidence is too low"""
    if not sources:
        return (
            f"I couldn't find relevant information in the RTI case database to answer: '{question}'. "
            f"Could you please:\n"
            f"- Specify which RTI section you're asking about (e.g., Section 8(1)(a))\n"
            f"- Mention a specific ministry if relevant\n"
            f"- Rephrase your question with more context"
        )

    avg_score = sum(s.get("score", 0) for s in sources) / len(sources) if sources else 0

    if avg_score < 0.3:
        return (
            f"I found some information but it may not be directly relevant to: '{question}'. "
            f"The retrieved cases have low relevance scores. Could you:\n"
            f"- Be more specific about what aspect you're interested in\n"
            f"- Provide more context or keywords\n"
            f"- Try rephrasing your question"
        )

    return (
        f"I'm not confident in my answer to: '{question}'. "
        f"Could you provide more details or rephrase your question?"
    )


router = APIRouter(prefix="/api", tags=["qa"])
limiter = Limiter(key_func=get_remote_address)

# Session call tracking (in-memory)
qa_session_calls = {}

def cleanup_qa_sessions():
    """Remove expired sessions (older than 1 hour)"""
    current_time = time.time()
    expired = [
        session_id for session_id, data in qa_session_calls.items()
        if current_time - data["timestamp"] > 3600
    ]
    for session_id in expired:
        del qa_session_calls[session_id]

def get_session_id(request: Request) -> str:
    """Get session ID from IP only (not user-supplied headers)"""
    return get_remote_address(request)

@router.post("/qa", response_model=QAResponse)
@limiter.limit(RATE_LIMIT)
async def answer_question(request: Request, body: QARequest, db: DBSession = Depends(get_db)):
    """
    Answer questions about RTI cases using Hybrid Search (BM25 + Semantic) + PageIndex verification + Groq

    Flow:
    1. BM25 keyword search
    2. Semantic vector search
    3. Hybrid merge with weighted scoring
    4. PageIndex verification layer for hierarchical context
    5. LLM answer generation
    """
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Q&A endpoint unavailable: GROQ_API_KEY not configured. Get a key from https://console.groq.com/keys and add to .env file."
        )

    # Session call limiting
    session_id = get_session_id(request)
    cleanup_qa_sessions()

    # Create workflow session with Backboard
    workflow_session = await SessionManager.create_session(
        db=db,
        workflow_type="rti_qa",
        user_ip=get_remote_address(request),
        metadata={"question": body.question[:100]}
    )

    if session_id not in qa_session_calls:
        qa_session_calls[session_id] = {"count": 0, "timestamp": time.time()}

    if qa_session_calls[session_id]["count"] >= MAX_QA_CALLS_PER_SESSION:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {MAX_QA_CALLS_PER_SESSION} Q&A calls per session exceeded. Please start a new session."
        )

    qa_session_calls[session_id]["count"] += 1
    qa_session_calls[session_id]["timestamp"] = time.time()

    # Sanitize user input
    question = sanitize_question(body.question)
    if not question:
        raise HTTPException(status_code=400, detail="Invalid question input")

    # Update stage to retrieval
    await SessionManager.update_stage(
        db=db,
        session_id=workflow_session.session_id,
        new_stage="retrieval"
    )

    # Step 1: Extract entities for metadata-aware retrieval
    from backend.utils.entity_extraction import EntityExtractor

    mongo_filter = None
    if EntityExtractor.should_use_filter(question):
        mongo_filter = EntityExtractor.build_mongo_filter(question)
        logger.info(f"Using metadata filter: {mongo_filter}")

    # Step 2: BM25 keyword search
    top_k = body.top_k if body.top_k else 5
    bm25_loader = BM25Loader()
    # Fetch more results to ensure diversity after deduplication
    bm25_results = bm25_loader.search(question, top_k=top_k * 3, metadata_filter=mongo_filter)

    # Step 3: Semantic vector search with metadata filtering
    retrieval_method = "hybrid_bm25_vector_filtered" if mongo_filter else "hybrid_bm25_vector"
    if VECTOR_SEARCH_AVAILABLE:
        try:
            vector_loader = VectorSearchLoader()
            hybrid_results = vector_loader.hybrid_search(
                query=question,
                bm25_results=bm25_results,
                top_k=top_k * 2,
                bm25_weight=BM25_WEIGHT,
                semantic_weight=SEMANTIC_WEIGHT,
                filter_dict=mongo_filter
            )
        except Exception as e:
            logger.warning(f"Vector search failed, falling back to BM25 only: {e}")
            hybrid_results = bm25_results[:body.top_k * 2]
            retrieval_method = "bm25_only"
    else:
        logger.info("Vector search not available, using BM25 only")
        hybrid_results = bm25_results[:body.top_k * 2]
        retrieval_method = "bm25_only"

    # Filter low-quality results (score threshold)
    MIN_SCORE_THRESHOLD = 0.3
    filtered_results = [r for r in hybrid_results if r.get("score", 0) >= MIN_SCORE_THRESHOLD]

    if not filtered_results:
        return QAResponse(
            answer="I couldn't find relevant information to answer your question.",
            sources=[],
            confidence="low"
        )

    # Deduplicate by order_number: keep only top-scoring paragraph per order
    seen_orders = {}
    deduplicated_results = []
    for result in filtered_results:
        order_num = result["paragraph"]["order_number"]
        if order_num not in seen_orders:
            seen_orders[order_num] = True
            deduplicated_results.append(result)
        if len(deduplicated_results) >= top_k:
            break

    hybrid_results = deduplicated_results

    # Log retrieval to Backboard
    top_sources = [r["paragraph"]["order_number"] for r in hybrid_results[:3]]
    await SessionManager.log_retrieval(
        db=db,
        session_id=workflow_session.session_id,
        query=question,
        retrieval_method=retrieval_method,
        num_results=len(hybrid_results),
        top_sources=top_sources
    )

    # Step 4: Extract order numbers from hybrid results
    order_numbers = list(set([result["paragraph"]["order_number"] for result in hybrid_results]))

    # Step 4: If filtered search returned no results, retry without filter
    if mongo_filter and not hybrid_results:
        logger.warning("Filtered search returned no results, retrying without filter")
        hybrid_results = vector_loader.hybrid_search(
            query=question,
            bm25_results=bm25_results,
            top_k=top_k,
            bm25_weight=BM25_WEIGHT,
            semantic_weight=SEMANTIC_WEIGHT,
            filter_dict=None
        )
        retrieval_method = "hybrid_bm25_vector_fallback"

    # Step 5: PageIndex verification layer - get hierarchical sections
    pageindex_loader = PageIndexLoader()
    hierarchical_sections = pageindex_loader.get_relevant_sections_by_order_numbers(
        order_numbers,
        question,
        max_sections=top_k
    )

    # Build context from hierarchical sections (PageIndex verification layer)
    context_parts = []
    sources = []

    if hierarchical_sections:
        # Use hierarchical context from PageIndex
        # Build mapping from order_hash to hybrid result metadata
        hash_to_result = {}
        for result in hybrid_results:
            order_num = result["paragraph"]["order_number"]
            order_hash = pageindex_loader.get_hash_from_order_number(order_num)
            if order_hash:
                hash_to_result[order_hash] = result

        for i, section in enumerate(hierarchical_sections):
            result = hash_to_result.get(section["order_hash"])

            if result:
                para = result["paragraph"]
                context_parts.append(
                    f"[Source {i+1}] Order: {para['order_number']}, Ministry: {para['ministry']}\n"
                    f"Section: {section['hierarchy']}\n"
                    f"Relevance: BM25={result.get('bm25_score', 0):.3f}, Semantic={result.get('semantic_score', 0):.3f}\n"
                    f"{section['text']}\n"
                )
                sources.append({
                    "order_number": para["order_number"],
                    "ministry": para["ministry"],
                    "order_date": para.get("order_date"),
                    "section": section["title"],
                    "score": result["score"],
                    "text": section["text"][:200]
                })
    else:
        # Fallback to flat hybrid results if PageIndex fails
        for i, result in enumerate(hybrid_results):
            para = result["paragraph"]
            context_parts.append(
                f"[Source {i+1}] Order: {para['order_number']}, Ministry: {para['ministry']}\n"
                f"Relevance: BM25={result.get('bm25_score', 0):.3f}, Semantic={result.get('semantic_score', 0):.3f}\n"
                f"{para['text']}\n"
            )
            sources.append({
                "order_number": para["order_number"],
                "ministry": para["ministry"],
                "order_date": para.get("order_date"),
                "score": result["score"],
                "text": para["text"][:200]
            })

    context = "\n".join(context_parts)

    # Update stage to generation
    await SessionManager.update_stage(
        db=db,
        session_id=workflow_session.session_id,
        new_stage="generation"
    )

    # Generate answer using Groq
    prompt = f"""You are an expert on India's Right to Information Act and CIC (Central Information Commission) orders.

Based on the following relevant excerpts from CIC orders (retrieved using hybrid search: keyword matching + semantic similarity, verified with hierarchical document structure), answer the user's question accurately and concisely.

Context:
{context}

Question: {question}

Instructions:
- Synthesize information from the provided context to answer the question.
- Cite specific order numbers and sections when making claims.
- The sources are ranked by both keyword relevance (BM25) and semantic similarity - consider both aspects.
- If multiple sources provide relevant information, combine them into a coherent answer.
- Be concise but thorough.
- Use legal terminology appropriately.
- Consider the hierarchical structure of the documents when reasoning.
- **INFERENCE ALLOWED**: If the specific definition or text (e.g., a specific RTI section like 8(1)(a)) is not verbatim in the context but is common knowledge in the RTI Act 2005, you may provide an explanation based on your internal knowledge, while clearly distinguishing it from the provided sources.
- Only state that information is unavailable if both the context AND your general legal knowledge are unable to address the query.

Answer:"""

    try:
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert on India's Right to Information Act and CIC orders. Provide accurate, well-cited answers."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            top_p=0.95
        )
        answer = response.choices[0].message.content or ""

        # Log generation to Backboard
        await SessionManager.log_generation(
            db=db,
            session_id=workflow_session.session_id,
            prompt_type="qa_response",
            response_summary=answer[:200],
            model=GROQ_MODEL
        )

        # Faithfulness check: ensure answer references sources
        has_citations = any(src["order_number"] in answer for src in sources)

        # Second check: verify answer doesn't contradict context
        faithfulness_prompt = f"""Given this answer and context, is the answer faithful to the context or a reasonable inference based on the RTI Act 2005? Answer only 'yes' or 'no'.

Context: {context[:500]}...

Answer: {answer}

Faithful (yes/no):"""

        faithfulness_response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": faithfulness_prompt
                }
            ],
            temperature=0.3
        )
        faithful_content = faithfulness_response.choices[0].message.content or ""
        is_faithful = "yes" in faithful_content.lower()

        # Multi-factor confidence calculation
        from backend.utils.confidence_scorer import ConfidenceScorer

        confidence, confidence_score = ConfidenceScorer.calculate_confidence(
            sources=sources,
            answer=answer,
            is_faithful=is_faithful,
            has_citations=has_citations
        )

        # Check if clarification should be requested instead of answering
        if ConfidenceScorer.should_request_clarification(confidence_score, sources):
            # Generate clarification request
            clarification_answer = _generate_clarification_request(
                question=question,
                sources=sources,
                extracted_entities=mongo_filter
            )

            return QAResponse(
                answer=clarification_answer,
                sources=[],
                confidence="low",
                calls_remaining=MAX_QA_CALLS_PER_SESSION - qa_session_calls[session_id]["count"],
                faithful=False,
                session_id=workflow_session.session_id,
                thread_id=workflow_session.thread_id
            )

        # Calculate calls remaining
        calls_remaining = MAX_QA_CALLS_PER_SESSION - qa_session_calls[session_id]["count"]

        # Complete workflow session
        SessionManager.complete_session(db, workflow_session.session_id)

        return QAResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            calls_remaining=calls_remaining,
            faithful=is_faithful,
            session_id=workflow_session.session_id,
            thread_id=workflow_session.thread_id
        )

    except ValueError as e:
        logger.error(f"Validation error in Q&A: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in Q&A: {e}", exc_info=True)
        error_msg = str(e)
        if "503" in error_msg or "overloaded" in error_msg.lower() or "high demand" in error_msg.lower():
            raise HTTPException(
                status_code=503, 
                detail="The AI model is currently experiencing high demand. Please try again in a few seconds."
            )
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while processing your question. Please try again."
        )
