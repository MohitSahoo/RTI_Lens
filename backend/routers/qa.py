"""
Q&A API Endpoint with BM25 + PageIndex hierarchical retrieval and Groq
"""
from fastapi import APIRouter, Request, HTTPException
from groq import Groq
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.config import GROQ_API_KEY, GROQ_MODEL, MAX_QA_CALLS_PER_SESSION, RATE_LIMIT
from backend.schemas import QARequest, QAResponse
from backend.utils.bm25_loader import BM25Loader
from backend.utils.pageindex_loader import PageIndexLoader
from backend.utils.sanitization import sanitize_question
import time
import logging

logger = logging.getLogger(__name__)

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
async def answer_question(request: Request, body: QARequest):
    """
    Answer questions about RTI cases using BM25 + PageIndex hierarchical retrieval + Groq
    """
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Q&A endpoint unavailable: GROQ_API_KEY not configured. Get a key from https://console.groq.com/keys and add to .env file."
        )

    # Session call limiting
    session_id = get_session_id(request)
    cleanup_qa_sessions()

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

    # Step 1: Use BM25 to find relevant documents
    bm25_loader = BM25Loader()
    bm25_results = bm25_loader.search(question, top_k=body.top_k)

    if not bm25_results:
        return QAResponse(
            answer="I couldn't find relevant information to answer your question.",
            sources=[],
            confidence="low"
        )

    # Step 2: Extract order numbers from BM25 results
    order_numbers = list(set([result["paragraph"]["order_number"] for result in bm25_results]))

    # Step 3: Use PageIndex to get hierarchical sections from relevant documents
    pageindex_loader = PageIndexLoader()
    hierarchical_sections = pageindex_loader.get_relevant_sections_by_order_numbers(
        order_numbers,
        question,
        max_sections=5
    )

    # Build context from hierarchical sections
    context_parts = []
    sources = []

    if hierarchical_sections:
        # Use hierarchical context
        # Build a mapping from order_hash back to order_number
        hash_to_order = {}
        for result in bm25_results:
            order_num = result["paragraph"]["order_number"]
            order_hash = pageindex_loader.get_hash_from_order_number(order_num)
            if order_hash:
                hash_to_order[order_hash] = result["paragraph"]

        for i, section in enumerate(hierarchical_sections):
            order_meta = hash_to_order.get(section["order_hash"])

            if order_meta:
                context_parts.append(
                    f"[Source {i+1}] Order: {order_meta['order_number']}, Ministry: {order_meta['ministry']}\n"
                    f"Section: {section['hierarchy']}\n"
                    f"{section['text']}\n"
                )
                sources.append({
                    "order_number": order_meta["order_number"],
                    "ministry": order_meta["ministry"],
                    "order_date": order_meta["order_date"],
                    "section": section["title"],
                    "score": section["relevance_score"],
                    "text": section["text"][:200]  # Add excerpt
                })
    else:
        # Fallback to flat BM25 paragraphs if PageIndex fails
        for i, result in enumerate(bm25_results):
            para = result["paragraph"]
            context_parts.append(
                f"[Source {i+1}] Order: {para['order_number']}, Ministry: {para['ministry']}\n"
                f"{para['text']}\n"
            )
            sources.append({
                "order_number": para["order_number"],
                "ministry": para["ministry"],
                "order_date": para["order_date"],
                "score": result["score"],
                "text": para["text"][:200]  # Add excerpt
            })

    context = "\n".join(context_parts)

    # Generate answer using Groq
    prompt = f"""You are an expert on India's Right to Information Act and CIC (Central Information Commission) orders.

Based on the following relevant excerpts from CIC orders (organized hierarchically by document sections), answer the user's question accurately and concisely.

Context:
{context}

Question: {question}

Instructions:
- Synthesize information from the provided context to answer the question.
- Cite specific order numbers and sections when making claims.
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
        answer = response.choices[0].message.content

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
        is_faithful = "yes" in faithfulness_response.choices[0].message.content.lower()

        # Determine confidence
        if has_citations and is_faithful and len(sources) >= 3:
            confidence = "high"
        elif has_citations or is_faithful:
            confidence = "medium"
        else:
            confidence = "low"

        # Calculate calls remaining
        calls_remaining = MAX_QA_CALLS_PER_SESSION - qa_session_calls[session_id]["count"]

        return QAResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            calls_remaining=calls_remaining,
            faithful=is_faithful
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
