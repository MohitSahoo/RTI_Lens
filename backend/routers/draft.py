"""
RTI Appeal Draft Generation Endpoint - Multi-Agent Architecture

Flow: User Input → RAG Retrieval → 3 Groq Agents → Prediction Model → Gemini Orchestration → Output
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from groq import Groq
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
import logging
import asyncio
import concurrent.futures
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from backend.config import (
    GROQ_MODEL, GROQ_API_KEYS, GEMINI_API_KEY, GEMINI_MODEL,
    RATE_LIMIT, BM25_WEIGHT, SEMANTIC_WEIGHT
)
from backend.database import get_db
from backend.schemas import DraftRequest, DraftResponse, PredictRequest, PredictResponse
from backend.utils.bm25_loader import BM25Loader
from backend.utils.sanitization import sanitize_context, validate_ministry_name, validate_section_cited
from backend.utils.session_manager import SessionManager
from backend.models.workflow import WorkflowAction, WorkflowSession

try:
    from backend.utils.vector_search import VectorSearchLoader
    VECTOR_SEARCH_AVAILABLE = True
except (ImportError, OSError) as e:
    VECTOR_SEARCH_AVAILABLE = False
    VectorSearchLoader = None
    logging.warning(f"Vector search unavailable: {e}")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = bool(GEMINI_API_KEY)
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_CLIENT = genai.GenerativeModel(GEMINI_MODEL) if GEMINI_AVAILABLE else None
except ImportError:
    GEMINI_AVAILABLE = False
    GEMINI_CLIENT = None
    genai = None

router = APIRouter(prefix="/api", tags=["draft"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from a single Groq agent"""
    agent_name: str
    response_text: str
    parsed_data: Optional[Dict]
    prediction: Optional[Dict]
    prediction_model: str
    api_key_label: Optional[str] = None


def _extract_agent_draft(parsed_data: Optional[Dict], fallback: str = "") -> str:
    """Read draft text from current or legacy agent output."""
    if not parsed_data:
        return fallback
    draft = parsed_data.get("draft") or parsed_data.get("improved_query")
    if isinstance(draft, dict):
        return _format_structured_draft(draft)
    if isinstance(draft, str):
        return draft
    return fallback


def _format_structured_draft(draft_obj: Any) -> str:
    """Convert structured JSON draft content into a readable appeal."""
    if isinstance(draft_obj, str):
        return draft_obj
    if not isinstance(draft_obj, dict):
        return _safe_text(draft_obj)

    lines: List[str] = []

    def append_section(label: str, value: Any) -> None:
        if value in (None, "", [], {}):
            return
        if isinstance(value, dict):
            lines.append(f"{label}:")
            for key, item in value.items():
                lines.append(f"{key}: {_safe_text(item)}")
            lines.append("")
            return
        if isinstance(value, list):
            lines.append(f"{label}:")
            for item in value:
                lines.append(f"- {_safe_text(item)}")
            lines.append("")
            return
        lines.append(f"{label}:")
        lines.append(_safe_text(value))
        lines.append("")

    for key in ["To", "Subject", "Facts", "Grounds", "Prayer/Reliefs", "Enclosures", "Place/Date", "Signature"]:
        if key in draft_obj:
            append_section(key, draft_obj[key])

    if not lines:
        return json.dumps(draft_obj, ensure_ascii=False, indent=2)

    return "\n".join(line for line in lines if line is not None).strip()


def _build_trace_step(step: str, status: str, detail: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {
        "step": step,
        "status": status,
        "detail": detail,
    }
    if extra:
        payload["extra"] = extra
    return payload


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _text_preview(value: Any, limit: int) -> str:
    return _safe_text(value)[:limit]


def _agent_prompt_label(index: int) -> str:
    return ["groq1_focused", "groq2_strategic", "groq3_comprehensive"][index]


def _agent_api_key(index: int) -> Optional[str]:
    if index < len(GROQ_API_KEYS):
        return GROQ_API_KEYS[index]
    return GROQ_API_KEYS[0] if GROQ_API_KEYS else None


def _agent_acceptance_score(agent: AgentResult) -> float:
    if agent.prediction and "probability" in agent.prediction:
        return float(agent.prediction.get("probability") or 0.0)
    if agent.parsed_data:
        confidence = agent.parsed_data.get("confidence") or agent.parsed_data.get("overall_confidence") or agent.parsed_data.get("strategy_confidence")
        if isinstance(confidence, (int, float)):
            return float(confidence)
    return 0.0


def _normalize_model_input(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return _safe_text(value)


def _derive_pipeline_guidance(
    context: str,
    precedents: List[Dict],
    requested_ministry: Optional[str] = None,
    requested_section: Optional[str] = None
) -> Dict[str, Any]:
    """Derive ministry/section hints from user input and retrieved precedents."""
    resolved_ministry = requested_ministry
    resolved_section = requested_section

    if not resolved_ministry:
        ministry_counts = {}
        for precedent in precedents:
            ministry = precedent.get("ministry")
            if ministry and ministry != "Unknown":
                ministry_counts[ministry] = ministry_counts.get(ministry, 0) + 1
        if ministry_counts:
            resolved_ministry = max(ministry_counts, key=ministry_counts.get)

    if not resolved_section:
        section_counts = {}
        for precedent in precedents:
            section = precedent.get("section")
            if section:
                section_counts[section] = section_counts.get(section, 0) + 1
        if section_counts:
            resolved_section = max(section_counts, key=section_counts.get)

    return {
        "context_preview": context[:160],
        "resolved_ministry": resolved_ministry or "Unknown",
        "resolved_section": resolved_section or "Unknown",
        "precedents_found": len(precedents),
        "used_user_ministry": bool(requested_ministry),
        "used_user_section": bool(requested_section)
    }


async def _retrieve_precedents(
    db: Session,
    session_id: str,
    context: str,
    ministry: Optional[str] = None
) -> tuple[List[Dict], str]:
    """
    Retrieve similar cases using Hybrid Search (BM25 + Semantic).
    Returns (results, retrieval_method).
    """
    # Update stage to retrieval
    await SessionManager.update_stage(
        db=db,
        session_id=session_id,
        stage="retrieval",
        action="retrieve_precedents"
    )

    search_query = f"{ministry or ''} {context[:100]}".strip()

    # Step 1: BM25 search
    bm25_loader = BM25Loader()
    bm25_results = bm25_loader.search(search_query, top_k=15)

    # Step 2: Hybrid search with semantic similarity
    retrieval_method = "hybrid_bm25_vector"
    hybrid_results = []

    if VECTOR_SEARCH_AVAILABLE:
        try:
            vector_loader = VectorSearchLoader()
            hybrid_results = vector_loader.hybrid_search(
                query=search_query,
                bm25_results=bm25_results,
                top_k=10,
                bm25_weight=BM25_WEIGHT,
                semantic_weight=SEMANTIC_WEIGHT
            )
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            retrieval_method = "bm25_fallback"
            hybrid_results = bm25_results[:10]
    else:
        hybrid_results = bm25_results[:10]
        retrieval_method = "bm25_only"

    # Log retrieval
    top_sources = [r['paragraph'].get('order_number') for r in hybrid_results[:3] if r.get('paragraph', {}).get('order_number')]
    await SessionManager.log_retrieval(
        db=db,
        session_id=session_id,
        query=search_query,
        retrieval_method=retrieval_method,
        num_results=len(hybrid_results),
        top_sources=top_sources
    )

    # Fetch full case details
    case_details = []
    from backend.utils.pageindex_loader import PageIndexLoader
    pageindex_loader = PageIndexLoader()

    order_numbers = [r['paragraph'].get('order_number') for r in hybrid_results[:5] if r.get('paragraph', {}).get('order_number')]

    try:
        for order_number in order_numbers:
            case_query = text("""
                SELECT order_number, section_cited, appeal_outcome, appeal_level, ministry
                FROM cases WHERE order_number = :order_number LIMIT 1
            """)
            case_row = db.execute(case_query, {"order_number": order_number}).fetchone()

            if case_row:
                sections = pageindex_loader.get_relevant_sections_by_order_numbers(
                    [order_number], context, max_sections=2
                )
                if sections:
                    case_text = "\n".join([f"[{s['hierarchy']}] {s['text'][:500]}" for s in sections])
                else:
                    para_query = text(
                        "SELECT text FROM paragraphs WHERE case_id = (SELECT id FROM cases WHERE order_number = :order_number) LIMIT 3"
                    )
                    paras = db.execute(para_query, {"order_number": order_number}).fetchall()
                    case_text = "\n".join([p.text[:300] for p in paras])

            case_details.append({
                "order_number": case_row.order_number,
                "section": case_row.section_cited,
                "outcome": case_row.appeal_outcome,
                "level": case_row.appeal_level,
                "ministry": case_row.ministry,
                "text": case_text,
                "text_preview": case_text[:280]
            })
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to fetch case details (rolled back transaction): {e}")
        for r in hybrid_results[:5]:
            para = r.get('paragraph', {})
            case_details.append({
                "order_number": para.get('order_number', 'Unknown'),
                "section": para.get('section_cited', ''),
                "outcome": para.get('appeal_outcome', 'Unknown'),
                "level": para.get('appeal_level', 'Unknown'),
                "ministry": para.get('ministry', 'Unknown'),
                "text": para.get('text', 'No text'),
                "text_preview": para.get('text', 'No text')[:280]
            })

    return case_details, retrieval_method


async def _run_groq_agent(
    agent_name: str,
    context: str,
    precedents: List[Dict],
    ministry: Optional[str],
    section: Optional[str],
    stage: str,
    session_id: str,
    api_key: Optional[str]
) -> AgentResult:
    """
    Run a single Groq agent with specific prompt and parameters.
    Returns AgentResult.
    """
    logger.info(f"Running {agent_name}...")

    if not api_key:
        return AgentResult(
            agent_name=agent_name,
            response_text="Missing Groq API key",
            parsed_data={"error": "Missing Groq API key"},
            prediction=None,
            prediction_model=GROQ_MODEL,
            api_key_label="missing"
        )

    # Build prompt based on agent role
    prompt_templates = {
        "groq1_focused": """You are an expert RTI first appeal drafter specializing in legal precision.

Draft a complete RTI first appeal from the user's facts. Do not simply rewrite the input.

User Facts:
{context}

Ministry: {ministry}
Section: {section}

Similar Cases:
{similar_cases}

Instructions:
1. Write a formal first appeal addressed to the First Appellate Authority
2. Include facts/background, grounds for appeal, reliefs sought, and verification
3. Use only facts present in the user input; mark missing details as placeholders
4. Recommend specific case citations that support the appeal
5. Predict appeal outcome (allowed/denied) with reasoning
6. Format the draft with To, Subject, Facts, Grounds, Prayer/Reliefs, Enclosures, Place/Date, and Signature

Return JSON: {{"draft": "...", "legal_issues_found": [], "improvements": [], "predicted_outcome": "allowed|denied", "confidence": 0.0-1.0, "sources_cited": []}}""",
        "groq2_strategic": """You are a strategic RTI first appeal drafter focusing on administrative accountability.

Draft a complete RTI first appeal from the user's facts. Do not simply rewrite the input.

User Facts:
{context}

Ministry: {ministry}
Section: {section}

Similar Cases:
{similar_cases}

Instructions:
1. Identify administrative loopholes the responder might exploit
2. Use strategic appeal phrasing to address delay, denial, incomplete reply, or improper exemption
3. Include specific reliefs and document types requested where supported by the facts
4. Write the appeal in a formal, ready-to-edit format
5. Predict outcome with strategic analysis
6. Format the draft with To, Subject, Facts, Grounds, Prayer/Reliefs, Enclosures, Place/Date, and Signature

Return JSON: {{"draft": "...", "risk_factors": [], "strategic_tactics": [], "predicted_outcome": "allowed|denied", "strategy_confidence": 0.0-1.0, "recommended_documents": []}}""",
        "groq3_comprehensive": """You are a comprehensive RTI first appeal drafter covering all angles.

Draft a complete RTI first appeal from the user's facts. Do not simply rewrite the input.

User Facts:
{context}

Ministry: {ministry}
Section: {section}

Similar Cases:
{similar_cases}

Instructions:
1. Review the facts for completeness and legal soundness
2. Check for consistency with precedents
3. Identify missing elements that could cause denial
4. Produce a structured appeal with placeholders for missing dates, names, and references
5. Format the draft with To, Subject, Facts, Grounds, Prayer/Reliefs, Enclosures, Place/Date, and Signature

Return JSON: {{"draft": "...", "completeness_score": 0-10, "missing_elements": [], "consistency_check": "pass|warning|fail", "predicted_outcome": "allowed|denied", "overall_confidence": 0.0-1.0, "final_notes": []}}"""
    }

    prompt = prompt_templates.get(stage, prompt_templates["groq1_focused"]).format(
        context=context,
        ministry=ministry or "Not specified",
        section=section or "Not specified",
        similar_cases="\n---\n".join([
            f"Case {i+1}: {c['order_number']} | Outcome: {c['outcome']} | Section: {c['section']}\nText: {_text_preview(c['text'], 400)}"
            for i, c in enumerate(precedents[:3])
        ])
    )

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert RTI appeal drafter. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7 if stage != "groq1_focused" else 0.5,
            response_format={"type": "json_object"}
        )
        response_text = _safe_text(response.choices[0].message.content)

        # Parse JSON
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            parsed = json.loads(response_text) if response_text else {}
        except (json.JSONDecodeError, ValueError):
            parsed = {"error": "Could not parse JSON", "raw_response": _text_preview(response_text, 200)}

        # Logging skipped for agents to prevent transaction aborts in parallel sessions.

        return AgentResult(
            agent_name=agent_name,
            response_text=response_text,
            parsed_data=parsed,
            prediction=None,
            prediction_model=GROQ_MODEL,
            api_key_label="configured"
        )

    except Exception as e:
        logger.error(f"{agent_name} failed: {e}")
        return AgentResult(
            agent_name=agent_name,
            response_text=str(e),
            parsed_data=None,
            prediction=None,
            prediction_model=GROQ_MODEL,
            api_key_label="error"
        )


async def _run_prediction_model(
    query: str,
    ministry: str,
    section: str,
    appeal_level: str = "first"
) -> Dict[str, Any]:
    """
    Run prediction on query to predict outcome probability.
    Returns prediction dict.
    """
    try:
        from backend.utils.pickle_security import load_pickle_with_verification
        from pathlib import Path
        import pandas as pd

        model_path = Path("data/model.pkl")
        hash_file = Path(str(model_path) + '.sha256')

        model = load_pickle_with_verification(
            model_path,
            hash_file=hash_file if hash_file.exists() else None
        )

        input_data = pd.DataFrame([{
            'ministry': _normalize_model_input(ministry),
            'section_cited': _normalize_model_input(section),
            'appeal_level': _normalize_model_input(appeal_level),
            'year': 2024,
            'raw_text': _normalize_model_input(query)
        }])

        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]

        outcome = "allowed" if prediction == 1 else "denied"
        probability = float(probabilities[1] if prediction == 1 else probabilities[0])

        confidence = "high" if probability >= 0.8 else "medium" if probability >= 0.6 else "low"

        return {
            "prediction": outcome,
            "probability": probability,
            "confidence": confidence,
            "ministry": _normalize_model_input(ministry),
            "section": _normalize_model_input(section)
        }

    except Exception as e:
        logger.error(f"Prediction model error: {e}")
        return {"error": str(e)}


async def _orchestrate_with_gemini(
    results: List[AgentResult],
    user_context: str,
    retrieved_precedents: List[Dict],
    accepted_results: Optional[List[AgentResult]] = None
) -> Dict[str, Any]:
    """
    Use Gemini to orchestrate and merge results from multiple agents.
    Returns final approved response with ministry/section predictions.
    """
    candidates = accepted_results if accepted_results else results

    if not candidates:
        return {
            "selected_draft": _safe_text(user_context),
            "change_notes": [],
            "avoid_phrases": [],
            "sources": [],
            "predicted_ministry": "Unknown",
            "predicted_section": "Unknown",
            "orchestration_method": "no_candidate_drafts"
        }

    if not GEMINI_AVAILABLE:
        # Fallback: Pick best result by confidence
        best = max(candidates, key=_agent_acceptance_score)
        return {
            "selected_draft": _safe_text(_extract_agent_draft(best.parsed_data, user_context)),
            "change_notes": [],
            "avoid_phrases": [],
            "sources": [],
            "predicted_ministry": "Unknown",
            "predicted_section": "Unknown",
            "orchestration_method": "fallback_single_agent"
        }

    try:
        gemini_client = GEMINI_CLIENT

        # Build agent result summaries (now includes prediction model output)
        agent_summaries = []
        for r in candidates:
            if r.parsed_data:
                pred_info = f" | ML Prediction: {_safe_text(r.prediction)}" if r.prediction else ""
                draft_preview = _text_preview(_extract_agent_draft(r.parsed_data, "N/A"), 200)
                summary = f"**{r.agent_name}**:\n- Draft: {draft_preview}...\n- Agent Prediction: {_safe_text(r.parsed_data.get('predicted_outcome', 'N/A'))}\n- ML Model Prediction: {_safe_text(r.prediction.get('prediction', 'N/A')) if r.prediction else 'N/A'}{pred_info}\n- Confidence: {_safe_text(r.parsed_data.get('confidence', r.parsed_data.get('strategy_confidence', r.parsed_data.get('overall_confidence', 0))))}\n- Notes: {_safe_text(r.parsed_data.get('legal_issues_found', r.parsed_data.get('strategic_tactics', r.parsed_data.get('completeness_score', []))))}"
                agent_summaries.append(summary)

        precedents_summary = "\n".join([
            f"Case {i+1}: {c['order_number']} | Section: {c['section']} | Outcome: {c['outcome']}"
            for i, c in enumerate(retrieved_precedents[:5])
        ])

        orchestration_prompt = f"""You are an expert RTI appeal orchestration system. Your job is to analyze multiple AI agent appeal drafts and select/create the best final draft.

User Facts:
{user_context}

Retrieved Precedents:
{precedents_summary}

Agent Analyses:
{chr(10).join(agent_summaries)}

Instructions:
1. Review all agent draft proposals
2. Use only the accepted drafts above if possible, and synthesize a superior final draft from their strongest parts
3. Predict the most likely ministry for this query
4. Predict the most likely RTI section cited
5. Identify phrases to avoid based on precedent patterns
6. Select 1-3 relevant sources from precedents
7. The final draft must be a formal, ready-to-edit appeal, not a rewritten version of the user input

Return JSON:
{{
  "selected_draft": "The best complete appeal draft",
  "predicted_ministry": "Ministry name",
  "predicted_section": "Section number (e.g., Section 6(1))",
  "change_notes": [{{"original": "...", "revised": "...", "reason": "..."}}],
  "avoid_phrases": ["phrase 1", "phrase 2"],
  "sources": [{{"order_number": "...", "outcome": "...", "relevance": "..."}}],
  "orchestration_reasoning": "Brief explanation of selection"
}}"""

        response = gemini_client.generate_content(orchestration_prompt)

        response_text = _safe_text(response.text)
        logger.debug(f"Gemini Raw Response: {response_text}")
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)
        except (json.JSONDecodeError, ValueError):
            # Fallback parsing
            return {
                "selected_draft": _safe_text(user_context),
                "predicted_ministry": "Unknown",
                "predicted_section": "Unknown",
                "change_notes": [],
                "avoid_phrases": [],
                "sources": [],
                "orchestration_reasoning": "Could not parse Gemini response",
                "raw_response": _text_preview(response_text, 500)
            }

    except Exception as e:
        logger.error(f"Gemini orchestration failed: {e}")
        return {
            "selected_draft": _safe_text(user_context),
            "predicted_ministry": "Unknown",
            "predicted_section": "Unknown",
            "change_notes": [],
            "avoid_phrases": [],
            "sources": [],
            "orchestration_reasoning": f"Gemini error: {str(e)}",
            "error": str(e)
        }


@router.post("/draft", response_model=Dict[str, Any])
@limiter.limit(RATE_LIMIT)
async def generate_draft(request: Request, body: DraftRequest, db: Session = Depends(get_db)):
    """
    Generate RTI appeal draft using Multi-Agent RAG Architecture:
    1. User input → RAG retrieval of precedents
    2. Three Groq agents analyze with different perspectives
    3. Each result passes through prediction model
    4. Gemini orchestrates and selects/merges best version
    5. Returns approved draft with predicted ministry/section
    """
    pipeline_trace: List[Dict[str, Any]] = []
    started_at = time.perf_counter()

    def trace(step: str, status: str, detail: str, extra: Optional[Dict[str, Any]] = None) -> None:
        pipeline_trace.append(_build_trace_step(step, status, detail, extra))

    try:
        if not GROQ_API_KEYS:
            raise HTTPException(
                status_code=503,
                detail="Drafting endpoint unavailable: GROQ API keys are not configured."
            )

        # Create workflow session
        trace("session", "running", "Creating workflow session and audit trail")
        workflow_session = await SessionManager.create_session(
            db=db,
            workflow_type="rti_draft",
            user_ip=get_remote_address(request),
            metadata={"context": body.context[:100]}
        )
        session_id = workflow_session.session_id
        trace("session", "complete", "Workflow session created", {"session_id": session_id})

        # Sanitize inputs
        trace("input", "running", "Sanitizing user context")
        context = sanitize_context(body.context)
        if not context:
            raise HTTPException(status_code=400, detail="Invalid context input")
        trace("input", "complete", "Context sanitized", {"length": len(context)})

        # Step 1: RAG retrieval
        trace("rag", "running", "Retrieving similar precedents with BM25 + vector search")
        logger.info("Step 1: Retrieving precedents...")
        case_details, retrieval_method = await _retrieve_precedents(
            db=db,
            session_id=session_id,
            context=context,
            ministry=body.ministry
        )

        if not case_details:
            raise HTTPException(
                status_code=404,
                detail="No similar cases found. Please try a different query."
            )
        trace(
            "rag",
            "complete",
            "Retrieved similar precedents",
            {"method": retrieval_method, "count": len(case_details)}
        )

        pipeline_guidance = _derive_pipeline_guidance(
            context=context,
            precedents=case_details,
            requested_ministry=body.ministry,
            requested_section=body.section_cited
        )
        resolved_ministry = pipeline_guidance["resolved_ministry"]
        resolved_section = pipeline_guidance["resolved_section"]
        trace(
            "classification",
            "complete",
            "Resolved ministry and section hints",
            {"ministry": resolved_ministry, "section": resolved_section}
        )

        try:
            await SessionManager.update_stage(
                db=db,
                session_id=session_id,
                stage="generation",
                action="start_agent_generation",
                context={"ministry": resolved_ministry, "section": resolved_section}
            )
        except Exception as stage_error:
            logger.warning(f"Unable to update generation stage: {stage_error}")

        # Step 2: Run 3 Groq agents in parallel
        logger.info("Step 2: Running 3 Groq agents in parallel...")
        trace("agents", "running", "Launching three Groq drafting agents")
        agent_tasks = []
        for idx, agent_name in enumerate(["groq1_focused", "groq2_strategic", "groq3_comprehensive"]):
            trace(
                "agents",
                "running",
                f"Queued {agent_name}",
                {"api_key_slot": idx + 1}
            )
            agent_tasks.append(
                _run_groq_agent(
                    agent_name,
                    context,
                    case_details,
                    resolved_ministry,
                    resolved_section,
                    agent_name,
                    str(session_id),
                    _agent_api_key(idx)
                )
            )

        # Execute Groq agent tasks
        groq_results = await asyncio.gather(*agent_tasks)
        trace(
            "agents",
            "complete",
            "Groq drafting agents completed",
            {
                "completed": len(groq_results),
                "succeeded": sum(1 for r in groq_results if r.parsed_data and not r.parsed_data.get("error"))
            }
        )

        # Step 3: Run prediction model on each agent's draft (BEFORE Gemini)
        logger.info("Step 3: Running prediction model on each agent output...")
        trace("prediction", "running", "Scoring each Groq draft with the prediction model")
        for result in groq_results:
            agent_draft = _extract_agent_draft(result.parsed_data)
            if agent_draft:
                try:
                    pred = await _run_prediction_model(
                        agent_draft,
                        result.parsed_data.get('predicted_ministry') or resolved_ministry,
                        result.parsed_data.get('predicted_section') or resolved_section,
                        "first"
                    )
                    result.prediction = pred
                except Exception as e:
                    logger.warning(f"Prediction model failed for {result.agent_name}: {e}")
        trace("prediction", "complete", "Prediction model finished scoring drafts")

        accepted_results = [r for r in groq_results if r.prediction and r.prediction.get("prediction") == "allowed"]
        if not accepted_results:
            accepted_results = sorted(groq_results, key=_agent_acceptance_score, reverse=True)[:2]
        rejected_results = [r for r in groq_results if r not in accepted_results]
        trace(
            "filtering",
            "complete",
            "Filtered drafts down to accepted candidates",
            {
                "accepted": [r.agent_name for r in accepted_results],
                "rejected": [r.agent_name for r in rejected_results]
            }
        )

        try:
            await SessionManager.update_stage(
                db=db,
                session_id=session_id,
                stage="review",
                action="start_gemini_orchestration",
                context={"accepted_agents": [r.agent_name for r in accepted_results]}
            )
        except Exception as stage_error:
            logger.warning(f"Unable to update review stage: {stage_error}")

        # Step 4: Gemini orchestration (uses agent predictions to select/merge best parts)
        logger.info("Step 4: Gemini orchestration with predictions...")
        trace("orchestration", "running", "Gemini is merging the strongest accepted drafts")
        orchestration_result = await _orchestrate_with_gemini(
            results=groq_results,  # Now includes predictions from step 3
            user_context=context,
            retrieved_precedents=case_details,
            accepted_results=accepted_results
        )
        trace(
            "orchestration",
            "complete",
            "Gemini produced the final merged draft"
        )

        # Extract predictions from Gemini orchestration
        final_draft = orchestration_result.get('selected_draft') or orchestration_result.get('selected_improved_query')
        if isinstance(final_draft, dict):
            final_draft = _format_structured_draft(final_draft)
        final_draft = _safe_text(final_draft).strip()

        if not final_draft or final_draft == context.strip() or "Subject:" not in final_draft or "Grounds:" not in final_draft:
            fallback_agent = max(accepted_results or groq_results, key=_agent_acceptance_score)
            final_draft = _extract_agent_draft(fallback_agent.parsed_data, context)
            final_draft = _safe_text(final_draft).strip()

        predicted_ministry = orchestration_result.get('predicted_ministry') or resolved_ministry
        predicted_section = orchestration_result.get('predicted_section') or resolved_section

        # Fallback: derive ministry/section from retrieved precedents if Gemini returned Unknown
        if predicted_ministry in ('Unknown', None, ''):
            from collections import Counter
            ministries = [c['ministry'] for c in case_details if c.get('ministry') and c['ministry'] != 'Unknown']
            if ministries:
                predicted_ministry = Counter(ministries).most_common(1)[0][0]
                logger.info(f"Derived ministry from precedents: {predicted_ministry}")
            elif body.ministry:
                predicted_ministry = body.ministry

        if predicted_section in ('Unknown', None, ''):
            from collections import Counter
            sections = [c['section'] for c in case_details if c.get('section') and c['section'] not in ('Unknown', None, '')]
            if sections:
                predicted_section = Counter(sections).most_common(1)[0][0]
                logger.info(f"Derived section from precedents: {predicted_section}")
            elif hasattr(body, 'section_cited') and body.section_cited:
                predicted_section = body.section_cited

        # Final prediction - use first agent's prediction (already computed per-agent)
        final_prediction = None
        for r in accepted_results or groq_results:
            if r.prediction:
                final_prediction = r.prediction
                break
        trace(
            "finalization",
            "running",
            "Packaging final response and audit metadata",
            {"draft_length": len(final_draft or "")}
        )

        # Step 5: Build sources from orchestration or fallback
        sources = orchestration_result.get('sources', [])
        if not sources:
            # Use top precedent as source if Gemini didn't provide any
            for c in case_details[:1]:
                sources.append({
                    "order_number": c['order_number'],
                    "outcome": c['outcome'],
                    "relevance": "Retrieved as highly relevant precedent"
                })

        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

        # Extract change notes from orchestration or generate from best agent (if needed)
        change_notes = orchestration_result.get('change_notes', [])
        if not change_notes and groq_results:
            # This part might need review: currently uses raw groq results for change_notes fallback
            # Consider if change_notes should be derived from Gemini's orchestration_reasoning or specific agent insights
            best_agent = max(groq_results, key=lambda r: r.parsed_data.get('confidence', 0) if r.parsed_data else 0)
            if best_agent.parsed_data:
                if 'legal_issues_found' in best_agent.parsed_data:
                    change_notes = [{"original": "query issue", "revised": "improved", "reason": r} for r in best_agent.parsed_data['legal_issues_found'][:3]]

        # Avoid phrases from orchestration or fallback
        avoid_phrases = orchestration_result.get('avoid_phrases', [])

        # Complete workflow
        try:
            await SessionManager.complete_session(db, session_id)
            db.commit()
        except Exception as e:
            logger.error(f'Failed to complete session: {e}')
            db.rollback()
        trace("finalization", "complete", "Workflow completed successfully", {"elapsed_ms": elapsed_ms})

        return {
            "session_id": session_id,
            "draft": final_draft,
            "improved_query": final_draft,
            "change_notes": change_notes[:5],
            "avoid_phrases": avoid_phrases[:5],
            "sources": sources[:3],
            "predicted_ministry": predicted_ministry,
            "predicted_section": predicted_section,
            "query_analysis": pipeline_guidance,
            "retrieved_precedents": case_details[:5],
            "outcome_prediction": final_prediction, # Include the final prediction model result
            "orchestration_method": "gemini_multi_agent_with_final_prediction",
            "accepted_agent_results": [
                {
                    "agent": r.agent_name,
                    "response_summary": _text_preview(r.response_text, 200),
                    "parsed_data_preview": {k: v for k, v in r.parsed_data.items() if k in ['draft', 'improved_query', 'predicted_outcome', 'confidence']} if r.parsed_data else {},
                    "draft_preview": _text_preview(_extract_agent_draft(r.parsed_data), 400),
                    "prediction_preview": r.prediction
                }
                for r in accepted_results
            ],
            "rejected_agent_results": [
                {
                    "agent": r.agent_name,
                    "response_summary": _text_preview(r.response_text, 200),
                    "parsed_data_preview": {k: v for k, v in r.parsed_data.items() if k in ['draft', 'improved_query', 'predicted_outcome', 'confidence']} if r.parsed_data else {},
                    "draft_preview": _text_preview(_extract_agent_draft(r.parsed_data), 400),
                    "prediction_preview": r.prediction
                }
                for r in rejected_results
            ],
            "agent_results": [ # Raw Groq agent results for debugging/transparency
                {
                    "agent": r.agent_name,
                    "response_summary": _text_preview(r.response_text, 200), # truncated for brevity
                    "parsed_data_preview": {k: v for k, v in r.parsed_data.items() if k in ['draft', 'improved_query', 'predicted_outcome', 'confidence']} if r.parsed_data else {},
                    "draft_preview": _text_preview(_extract_agent_draft(r.parsed_data), 400),
                    "prediction_preview": r.prediction
                }
                for r in groq_results
            ],
            "retrieval": {
                "method": retrieval_method,
                "precedents_count": len(case_details)
            },
            "pipeline_trace": pipeline_trace
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Draft generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Draft generation failed: {str(e)}")


@router.get("/draft/status/{session_id}")
async def get_draft_status(session_id: str, db: Session = Depends(get_db)):
    """Return the current workflow status and recent actions for a draft session."""
    session = db.query(WorkflowSession).filter(WorkflowSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")

    actions = (
        db.query(WorkflowAction)
        .filter(WorkflowAction.session_id == session_id)
        .order_by(WorkflowAction.created_at.asc())
        .limit(20)
        .all()
    )

    return {
        "session_id": session.session_id,
        "workflow_type": session.workflow_type,
        "workflow_stage": session.workflow_stage,
        "is_active": session.is_active,
        "thread_id": session.thread_id,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "completed_at": session.completed_at,
        "retrieval_history": session.retrieval_history or [],
        "generation_history": session.generation_history or [],
        "actions": [
            {
                "action_type": action.action_type,
                "action_name": action.action_name,
                "input_data": action.input_data,
                "output_data": action.output_data,
                "success": action.success,
                "error_message": action.error_message,
                "created_at": action.created_at,
            }
            for action in actions
        ],
    }
