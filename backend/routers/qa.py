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
from backend.utils.ragas_evaluator import RAGASEvaluator
try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    RAGAS_AVAILABLE = True
except Exception as e:
    import logging
    logging.warning(f"Ragas evaluation imports failed: {e}")
    RAGAS_AVAILABLE = False
from langchain_groq import ChatGroq
import time
import logging

logger = logging.getLogger(__name__)

# Initialize router and limiter at module level before endpoint definitions
router = APIRouter(prefix="/api", tags=["qa"])
limiter = Limiter(key_func=get_remote_address)

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

@router.get("/qa/source")
async def get_source_details(order_number: str):
    """Retrieve full context and hierarchical details for a specific order number"""
    try:
        page_index = PageIndexLoader()
        details = page_index.get_full_context_by_order(order_number)
        
        if not details:
            raise HTTPException(status_code=404, detail="Case precedent not found in index")
            
        return {
            "order_number": order_number,
            "hierarchy": details.get("hierarchy", []),
            "full_text": details.get("full_text", ""),
            "metadata": details.get("metadata", {})
        }
    except Exception as e:
        logger.error(f"Error fetching source details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    """
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Q&A endpoint unavailable: GROQ_API_KEY not configured."
        )

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
        raise HTTPException(status_code=429, detail="Session limit exceeded")

    qa_session_calls[session_id]["count"] += 1
    qa_session_calls[session_id]["timestamp"] = time.time()

    question = sanitize_question(body.question)
    if not question:
        raise HTTPException(status_code=400, detail="Invalid question input")

    search_mode = body.search_mode or "hybrid"
    retrieval_start = time.time()

    await SessionManager.update_stage(db=db, session_id=workflow_session.session_id, stage="retrieval", action="start_retrieval")

    # Step 1: Hybrid retrieval
    top_k = body.top_k if body.top_k else 5
    bm25_results = []
    semantic_results = []

    if search_mode in ("bm25", "hybrid"):
        bm25_loader = BM25Loader()
        bm25_results = bm25_loader.search(question, top_k=top_k * 3)

    hybrid_results = []
    if search_mode == "bm25":
        hybrid_results = bm25_results[:top_k * 2]
    elif search_mode == "semantic":
        if VECTOR_SEARCH_AVAILABLE:
            try:
                vector_loader = VectorSearchLoader()
                semantic_results = vector_loader.search(query=question, top_k=top_k * 2)
                hybrid_results = semantic_results
            except Exception as e:
                logger.error(f"Semantic-only search failed: {e}")
                hybrid_results = bm25_results[:top_k * 2]
        else:
            logger.warning("Semantic-only requested but vector search unavailable, falling back to BM25")
            hybrid_results = bm25_results[:top_k * 2]
    else:  # hybrid
        if VECTOR_SEARCH_AVAILABLE:
            try:
                vector_loader = VectorSearchLoader()
                hybrid_results = vector_loader.hybrid_search(
                    query=question,
                    bm25_results=bm25_results,
                    top_k=top_k * 2,
                    bm25_weight=BM25_WEIGHT,
                    semantic_weight=SEMANTIC_WEIGHT
                )
                semantic_results = hybrid_results
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
                hybrid_results = bm25_results[:top_k * 2]
        else:
            hybrid_results = bm25_results[:top_k * 2]

    retrieval_elapsed = round(time.time() - retrieval_start, 3)

    # Deduplicate
    seen_orders = {}
    deduplicated_results = []
    for result in hybrid_results:
        order_num = result["paragraph"]["order_number"]
        if order_num not in seen_orders:
            seen_orders[order_num] = True
            deduplicated_results.append(result)
        if len(deduplicated_results) >= top_k:
            break
    
    hybrid_results = deduplicated_results
    order_numbers = [r["paragraph"]["order_number"] for r in hybrid_results]

    # Step 2: PageIndex verification layer
    pageindex_loader = PageIndexLoader()
    hierarchical_sections = pageindex_loader.get_relevant_sections_by_order_numbers(
        order_numbers,
        question,
        max_sections=top_k
    )

    context_parts = []
    sources = []

    # Map sections back to their order numbers
    hash_to_order = {pageindex_loader.get_hash_from_order_number(n): n for n in order_numbers if pageindex_loader.get_hash_from_order_number(n)}

    for i, section in enumerate(hierarchical_sections):
        order_num = hash_to_order.get(section.get("order_hash"), "Unknown")
        context_parts.append(
            f"[Source {i+1}] Order: {order_num}\n"
            f"Section: {section['hierarchy']}\n"
            f"{section['text']}\n"
        )
        sources.append({
            "order_number": order_num,
            "ministry": "Verified Source",
            "score": 0.9,
            "text": section["text"][:200]
        })

    context = "\n".join(context_parts)
    await SessionManager.update_stage(db=db, session_id=workflow_session.session_id, stage="generation", action="start_generation")

    # Step 3: LLM generation
    prompt = f"Answer this RTI question based on the context:\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        answer = response.choices[0].message.content or ""

        # RAGAS Evaluation using official ragas library or fallback
        context_texts = [s.get('text', '') for s in sources if s.get('text')]
        eval_results = {}

        if context_texts:
            if RAGAS_AVAILABLE:
                try:
                    llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY)
                    dataset = Dataset.from_list([{
                        "question": question,
                        "answer": answer,
                        "contexts": context_texts,
                        "ground_truth": ""
                    }])

                    result = evaluate(
                        dataset=dataset,
                        metrics=[faithfulness, context_precision, context_recall],
                        llm=llm
                    )

                    # Extract scores from ragas result
                    try:
                        df = result.to_pandas()
                        if hasattr(df, 'to_dict'):
                            result_dict = df.to_dict(orient="records")[0] if len(df) > 0 else {}
                        else:
                            result_dict = {}
                    except Exception:
                        result_dict = {}

                    eval_results = {
                        "faithfulness": float(result_dict.get("faithfulness", 0.0) or 0.0),
                        "context_precision": float(result_dict.get("context_precision", 0.0) or 0.0),
                        "context_recall": float(result_dict.get("context_recall", 0.0) or 0.0)
                    }
                except Exception as e:
                    logger.warning(f"RAGAS eval failed, using fallback: {e}")
                    # Fallback to custom evaluator
                    evaluator = RAGASEvaluator()
                    fallback_res = evaluator.evaluate_full_pipeline(
                        query=question,
                        answer=answer,
                        contexts=context_texts,
                        source_scores=[s.get('score', 0.5) for s in sources]
                    )
                    eval_results = {
                        "faithfulness": fallback_res.get("faithfulness", 0.5),
                        "context_precision": fallback_res.get("context_relevance", 0.5),
                        "context_recall": fallback_res.get("answer_relevance", 0.5)
                    }
            else:
                # Custom evaluator fallback when RAGAS is not installed
                try:
                    evaluator = RAGASEvaluator()
                    fallback_res = evaluator.evaluate_full_pipeline(
                        query=question,
                        answer=answer,
                        contexts=context_texts,
                        source_scores=[s.get('score', 0.5) for s in sources]
                    )
                    eval_results = {
                        "faithfulness": fallback_res.get("faithfulness", 0.5),
                        "context_precision": fallback_res.get("context_relevance", 0.5),
                        "context_recall": fallback_res.get("answer_relevance", 0.5)
                    }
                except Exception as e:
                    logger.error(f"Fallback evaluator failed: {e}")

        is_faithful = eval_results.get("faithfulness", 0.0) >= 0.7
        
        # Calculation: Base (30) + Faithfulness (30) + Sources (10 per source, max 40)
        score = 30
        if is_faithful: score += 30
        score += min(len(sources) * 10, 40)
        
        confidence_label = "high" if score > 80 else "medium" if score > 50 else "low"

        return QAResponse(
            answer=answer,
            sources=sources,
            confidence=confidence_label,
            confidence_score=score / 100.0,
            calls_remaining=MAX_QA_CALLS_PER_SESSION - qa_session_calls[session_id]["count"],
            faithful=is_faithful,
            deepeval_scores=eval_results,
            session_id=workflow_session.session_id,
            thread_id=workflow_session.thread_id,
            retrieval_info={
                "search_mode": search_mode,
                "bm25_results": len(bm25_results),
                "semantic_results": len(semantic_results),
                "final_sources": len(sources),
                "retrieval_time_s": retrieval_elapsed,
                "vector_search_active": VECTOR_SEARCH_AVAILABLE
            }
        )
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
