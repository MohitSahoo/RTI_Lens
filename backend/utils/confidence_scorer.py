"""
Confidence Scoring for RAG Responses

Multi-factor confidence calculation based on:
- Source quality (scores, variance)
- Answer faithfulness
- Citation presence
- Number of sources
"""
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Calculate confidence scores for RAG responses"""

    # Thresholds for confidence levels
    HIGH_THRESHOLD = 0.70
    MEDIUM_THRESHOLD = 0.45

    @classmethod
    def calculate_confidence(
        cls,
        sources: List[Dict],
        answer: str,
        is_faithful: bool,
        has_citations: bool
    ) -> tuple[str, float]:
        """
        Calculate confidence level and score

        Args:
            sources: List of source documents with scores
            answer: Generated answer text
            is_faithful: Whether answer is faithful to context
            has_citations: Whether answer cites sources

        Returns:
            Tuple of (confidence_level, confidence_score)
            confidence_level: "high", "medium", or "low"
            confidence_score: 0.0 to 1.0
        """
        if not sources:
            return "low", 0.0

        # Factor 1: Source quality (40% weight)
        source_quality_score = cls._calculate_source_quality(sources)

        # Factor 2: Faithfulness (30% weight)
        faithfulness_score = 1.0 if is_faithful else 0.3

        # Factor 3: Citation presence (15% weight)
        citation_score = 1.0 if has_citations else 0.5

        # Factor 4: Source count (15% weight)
        source_count_score = cls._calculate_source_count_score(len(sources))

        # Weighted aggregation
        confidence_score = (
            0.40 * source_quality_score +
            0.30 * faithfulness_score +
            0.15 * citation_score +
            0.15 * source_count_score
        )

        # Determine confidence level
        if confidence_score >= cls.HIGH_THRESHOLD:
            confidence_level = "high"
        elif confidence_score >= cls.MEDIUM_THRESHOLD:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        logger.info(
            f"Confidence calculation: "
            f"source_quality={source_quality_score:.2f}, "
            f"faithfulness={faithfulness_score:.2f}, "
            f"citations={citation_score:.2f}, "
            f"source_count={source_count_score:.2f} "
            f"-> {confidence_level} ({confidence_score:.2f})"
        )

        return confidence_level, confidence_score

    @classmethod
    def _calculate_source_quality(cls, sources: List[Dict]) -> float:
        """
        Calculate source quality score based on:
        - Average score
        - Score variance (consistency)
        - Minimum score (weakest link)

        Returns:
            Score between 0.0 and 1.0
        """
        scores = [src.get("score", 0.0) for src in sources]

        if not scores:
            return 0.0

        # Average score (60% weight)
        avg_score = np.mean(scores)

        # Score consistency - penalize high variance (20% weight)
        if len(scores) > 1:
            variance = np.var(scores)
            consistency_score = max(0.0, 1.0 - variance)
        else:
            consistency_score = 1.0

        # Minimum score - weakest link (20% weight)
        min_score = min(scores)

        quality_score = (
            0.60 * avg_score +
            0.20 * consistency_score +
            0.20 * min_score
        )

        return min(1.0, max(0.0, quality_score))

    @classmethod
    def _calculate_source_count_score(cls, num_sources: int) -> float:
        """
        Calculate score based on number of sources

        More sources = higher confidence, with diminishing returns

        Returns:
            Score between 0.0 and 1.0
        """
        if num_sources == 0:
            return 0.0
        elif num_sources == 1:
            return 0.4
        elif num_sources == 2:
            return 0.6
        elif num_sources == 3:
            return 0.8
        elif num_sources >= 4:
            return 1.0

        return 0.0

    @classmethod
    def should_request_clarification(
        cls,
        confidence_score: float,
        sources: List[Dict],
        clarification_threshold: float = 0.35
    ) -> bool:
        """
        Determine if system should request clarification instead of answering

        Args:
            confidence_score: Calculated confidence score
            sources: Retrieved sources
            clarification_threshold: Minimum confidence to answer

        Returns:
            True if clarification should be requested
        """
        # Request clarification if confidence is very low
        if confidence_score < clarification_threshold:
            return True

        # Request clarification if no sources found
        if not sources:
            return True

        # Request clarification if all sources have very low scores
        if sources:
            max_score = max(src.get("score", 0.0) for src in sources)
            if max_score < 0.25:
                return True

        return False
