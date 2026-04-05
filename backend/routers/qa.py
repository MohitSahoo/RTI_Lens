"""
Q&A API Endpoint with BM25 + PageIndex hierarchical retrieval and Gemini
"""
from fastapi import APIRouter, Request, HTTPException
from google import genai
from google.genai import types
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, MAX_QA_CALLS_PER_SESSION
from backend.schemas import QARequest, QAResponse
from backend.utils.bm25_loader import BM25Loader
from backend.utils.pageindex_loader import PageIndexLoader
import time

router = APIRouter(prefix="/api", tags=["qa"])

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
    """Get session ID from header or IP"""
    return request.headers.get("X-Session-ID", request.client.host)

@router.post("/qa", response_model=QAResponse)
async def answer_question(request: QARequest, http_request: Request):
    """
    Answer questions about RTI cases using BM25 + PageIndex hierarchical retrieval + Gemini
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    # Session call limiting
    session_id = get_session_id(http_request)
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

    # Step 1: Use BM25 to find relevant documents
    bm25_loader = BM25Loader()
    bm25_results = bm25_loader.search(request.question, top_k=request.top_k)

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
        request.question,
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

    # Generate answer using Gemini
    prompt = f"""You are an expert on India's Right to Information Act and CIC (Central Information Commission) orders.

Based on the following relevant excerpts from CIC orders (organized hierarchically by document sections), answer the user's question accurately and concisely.

Context:
{context}

Question: {request.question}

Instructions:
- Synthesize information from the provided context to answer the question
- Cite specific order numbers and sections when making claims
- If multiple sources provide relevant information, combine them into a coherent answer
- Be concise but thorough
- Use legal terminology appropriately
- Consider the hierarchical structure of the documents when reasoning
- Only state that information is unavailable if the context is truly empty or completely irrelevant

Answer:"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        answer = response.text

        # Faithfulness check: ensure answer references sources
        has_citations = any(src["order_number"] in answer for src in sources)

        # Second check: verify answer doesn't contradict context
        faithfulness_prompt = f"""Given this answer and context, is the answer faithful to the context? Answer only 'yes' or 'no'.

Context: {context[:500]}...

Answer: {answer}

Faithful (yes/no):"""

        faithfulness_response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=faithfulness_prompt
        )
        is_faithful = "yes" in faithfulness_response.text.lower()

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")
