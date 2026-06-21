"""
RAGAS-style Evaluation for RAG Pipeline

Implements evaluation metrics for Retrieval Augmented Generation:
- Context Relevance: How relevant are retrieved sources to query?
- Faithfulness: Is answer grounded in retrieved context?
- Answer Relevance: Does answer address the question?
"""
import numpy as np
import re
from typing import List, Dict
import logging
from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)


def _extract_score(text: str) -> float:
    """Extract numeric score from LLM response"""
    logger.debug(f"LLM score response: {text}")
    # Search for any digit 0-10
    match = re.search(r'([0-9]|10)', text)
    if match:
        score = float(match.group(1)) / 10.0
        return score
    return 0.5  # Neutral fallback


class RAGASEvaluator:
    """RAGAS-style evaluation metrics for RAG pipeline"""

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def evaluate_context_relevance(
        self,
        query: str,
        contexts: List[str],
        source_scores: List[float]
    ) -> float:
        """
        Evaluate how relevant retrieved contexts are to the query

        Combines:
        - Retrieval scores (BM25 + semantic)
        - LLM-based relevance judgment

        Args:
            query: User query
            contexts: Retrieved context texts
            source_scores: Retrieval scores for each context

        Returns:
            Context relevance score (0.0 to 1.0)
        """
        if not contexts:
            return 0.0

        # Component 1: Average retrieval score (50% weight)
        avg_retrieval_score = np.mean(source_scores) if source_scores else 0.0

        # Component 2: LLM-based relevance (50% weight)
        # Sample up to 3 contexts to avoid token limits
        sample_contexts = contexts[:3]

        relevance_prompt = f"""Rate the relevance of these retrieved contexts to the query on a scale of 0-10.

Query: {query}

Contexts:
{chr(10).join(f"{i+1}. {ctx[:200]}..." for i, ctx in enumerate(sample_contexts))}

Provide ONLY a single integer from 0 to 10:"""

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": relevance_prompt}],
                temperature=0.3,
                max_tokens=10
            )

            content = response.choices[0].message.content or "0"
            llm_score = _extract_score(content)
        except Exception as e:
            logger.warning(f"LLM relevance scoring failed: {e}")
            llm_score = 0.5  # Neutral fallback

        # Weighted combination
        context_relevance = 0.5 * avg_retrieval_score + 0.5 * llm_score

        return min(1.0, max(0.0, context_relevance))

    def evaluate_faithfulness(
        self,
        answer: str,
        contexts: List[str]
    ) -> float:
        """
        Evaluate if answer is grounded in retrieved contexts

        Checks:
        - Are claims in answer supported by contexts?
        - Does answer hallucinate information?

        Args:
            answer: Generated answer
            contexts: Retrieved contexts

        Returns:
            Faithfulness score (0.0 to 1.0)
        """
        if not contexts or not answer:
            return 0.0

        # Combine contexts (limit to avoid token overflow)
        combined_context = "\n\n".join(contexts[:5])[:2000]

        faithfulness_prompt = f"""Evaluate if the answer is faithful to the provided contexts. Rate from 0-10.

Contexts:
{combined_context}

Answer:
{answer[:500]}

Rate faithfulness (0=hallucinated, 10=fully grounded). Provide ONLY a single integer from 0 to 10:"""

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": faithfulness_prompt}],
                temperature=0.3,
                max_tokens=10
            )

            content = response.choices[0].message.content or "0"
            faithfulness_score = _extract_score(content)
        except Exception as e:
            logger.warning(f"Faithfulness scoring failed: {e}")
            faithfulness_score = 0.5

        return min(1.0, max(0.0, faithfulness_score))

    def evaluate_answer_relevance(
        self,
        query: str,
        answer: str
    ) -> float:
        """
        Evaluate if answer addresses the query

        Checks:
        - Does answer respond to what was asked?
        - Is answer on-topic?

        Args:
            query: User query
            answer: Generated answer

        Returns:
            Answer relevance score (0.0 to 1.0)
        """
        if not answer:
            return 0.0

        relevance_prompt = f"""Rate how well the answer addresses the query on a scale of 0-10.

Query: {query}

Answer: {answer[:500]}

Rate relevance (0=off-topic, 10=perfect). Provide ONLY a single integer from 0 to 10:"""

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": relevance_prompt}],
                temperature=0.3,
                max_tokens=10
            )

            content = response.choices[0].message.content or "0"
            relevance_score = _extract_score(content)
        except Exception as e:
            logger.warning(f"Answer relevance scoring failed: {e}")
            relevance_score = 0.5

        return min(1.0, max(0.0, relevance_score))

    def evaluate_full_pipeline(
        self,
        query: str,
        answer: str,
        contexts: List[str],
        source_scores: List[float]
    ) -> Dict[str, float]:
        """
        Run full RAGAS evaluation

        Args:
            query: User query
            answer: Generated answer
            contexts: Retrieved contexts
            source_scores: Retrieval scores

        Returns:
            Dict with all metrics and overall score
        """
        context_relevance = self.evaluate_context_relevance(query, contexts, source_scores)
        faithfulness = self.evaluate_faithfulness(answer, contexts)
        answer_relevance = self.evaluate_answer_relevance(query, answer)

        # Overall RAGAS score (harmonic mean)
        if context_relevance > 0 and faithfulness > 0 and answer_relevance > 0:
            ragas_score = 3 / (
                1/context_relevance + 1/faithfulness + 1/answer_relevance
            )
        else:
            ragas_score = 0.0

        results = {
            "context_relevance": round(context_relevance, 3),
            "faithfulness": round(faithfulness, 3),
            "answer_relevance": round(answer_relevance, 3),
            "ragas_score": round(ragas_score, 3)
        }

        logger.info(f"RAGAS evaluation: {results}")

        return results
