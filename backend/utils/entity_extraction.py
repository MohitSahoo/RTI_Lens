"""
Entity Extraction for Query Filtering

Extracts structured entities (sections, ministries) from user queries
to enable metadata-aware retrieval.
"""
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract entities from RTI queries for metadata filtering"""

    # Common ministry patterns
    MINISTRY_PATTERNS = [
        r"Ministry of ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
        r"MoF\b",  # Ministry of Finance
        r"MHA\b",  # Ministry of Home Affairs
        r"MEA\b",  # Ministry of External Affairs
    ]

    MINISTRY_ALIASES = {
        "MoF": "Ministry of Finance",
        "MHA": "Ministry of Home Affairs",
        "MEA": "Ministry of External Affairs",
        "Finance": "Ministry of Finance",
        "Home Affairs": "Ministry of Home Affairs",
        "External Affairs": "Ministry of External Affairs",
    }

    # Section patterns - matches 8(1)(a), Section 8(1)(a), etc.
    SECTION_PATTERNS = [
        r"Section\s+(\d+\(\d+\)\([a-z]\))",
        r"section\s+(\d+\(\d+\)\([a-z]\))",
        r"(\d+\(\d+\)\([a-z]\))",  # Removed word boundary - was blocking matches
    ]

    @classmethod
    def extract_sections(cls, query: str) -> List[str]:
        """
        Extract RTI section citations from query

        Examples:
            "What is Section 8(1)(a)?" -> ["8(1)(a)"]
            "Difference between 8(1)(a) and 8(1)(g)" -> ["8(1)(a)", "8(1)(g)"]
        """
        sections = set()

        for pattern in cls.SECTION_PATTERNS:
            matches = re.findall(pattern, query)
            sections.update(matches)

        result = list(sections)
        if result:
            logger.info(f"Extracted sections from query: {result}")

        return result

    @classmethod
    def extract_ministries(cls, query: str) -> List[str]:
        """
        Extract ministry names from query

        Examples:
            "Ministry of Finance cases" -> ["Ministry of Finance"]
            "MoF denial rate" -> ["Ministry of Finance"]
        """
        ministries = set()

        for pattern in cls.MINISTRY_PATTERNS:
            matches = re.findall(pattern, query)
            for match in matches:
                if pattern.startswith(r"Ministry"):
                    ministries.add(f"Ministry of {match}")
                else:
                    # Alias match
                    if match in cls.MINISTRY_ALIASES:
                        ministries.add(cls.MINISTRY_ALIASES[match])

        result = list(ministries)
        if result:
            logger.info(f"Extracted ministries from query: {result}")

        return result

    @classmethod
    def build_mongo_filter(cls, query: str) -> Optional[Dict]:
        """
        Build MongoDB filter from extracted entities

        Returns:
            MongoDB filter dict or None if no entities found

        Examples:
            "Section 8(1)(a) cases" -> {"section_cited": {"$regex": "8\\(1\\)\\(a\\)"}}
            "Ministry of Finance 8(1)(j)" -> {
                "$and": [
                    {"ministry": {"$regex": "Ministry of Finance", "$options": "i"}},
                    {"section_cited": {"$regex": "8\\(1\\)\\(j\\)"}}
                ]
            }
        """
        sections = cls.extract_sections(query)
        ministries = cls.extract_ministries(query)

        if not sections and not ministries:
            return None

        filters = []

        # Add section filters
        if sections:
            if len(sections) == 1:
                # Single section - exact match with regex
                section = sections[0].replace("(", r"\(").replace(")", r"\)")
                filters.append({"section_cited": {"$regex": section}})
            else:
                # Multiple sections - OR condition
                section_filters = []
                for section in sections:
                    escaped = section.replace("(", r"\(").replace(")", r"\)")
                    section_filters.append({"section_cited": {"$regex": escaped}})
                filters.append({"$or": section_filters})

        # Add ministry filters
        if ministries:
            if len(ministries) == 1:
                filters.append({"ministry": {"$regex": ministries[0], "$options": "i"}})
            else:
                ministry_filters = [
                    {"ministry": {"$regex": m, "$options": "i"}} for m in ministries
                ]
                filters.append({"$or": ministry_filters})

        # Combine filters
        if len(filters) == 1:
            result = filters[0]
        else:
            result = {"$and": filters}

        logger.info(f"Built MongoDB filter: {result}")
        return result

    @classmethod
    def should_use_filter(cls, query: str, min_corpus_size: int = 50) -> bool:
        """
        Determine if metadata filtering should be applied

        Only use filtering when:
        1. Entities are detected in query
        2. Query is specific enough (mentions sections or ministries)
        3. Not a broad exploratory query

        Args:
            query: User query
            min_corpus_size: Minimum expected results after filtering

        Returns:
            True if filtering should be applied
        """
        sections = cls.extract_sections(query)
        ministries = cls.extract_ministries(query)

        # Don't filter broad queries
        broad_keywords = ["all", "every", "any", "general", "overview", "summary"]
        if any(keyword in query.lower() for keyword in broad_keywords):
            return False

        # Use filter if specific entities mentioned
        return bool(sections or ministries)
