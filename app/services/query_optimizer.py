"""
Enhanced Query Optimizer with Real Retrieval and LLM-based Optimization
Uses existing backend infrastructure to provide data-driven suggestions
"""
from typing import Dict, List, Optional, Tuple
import logging
import re
import json
from collections import Counter
from groq import Groq

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Query optimizer with real retrieval and LLM-based optimization"""

    def __init__(self):
        # Lazy load heavy dependencies
        self._bm25_loader = None
        self._vector_loader = None
        self._entity_extractor = None
        self._groq_client = None
        self._groq_api_key = None

    def _get_bm25_loader(self):
        """Lazy load BM25Loader"""
        if self._bm25_loader is None:
            from backend.utils.bm25_loader import BM25Loader
            self._bm25_loader = BM25Loader()
        return self._bm25_loader

    def _get_vector_loader(self):
        """Lazy load VectorSearchLoader"""
        if self._vector_loader is None:
            from backend.utils.vector_search import VectorSearchLoader
            self._vector_loader = VectorSearchLoader()
        return self._vector_loader

    def _get_entity_extractor(self):
        """Lazy load EntityExtractor"""
        if self._entity_extractor is None:
            from backend.utils.entity_extraction import EntityExtractor
            self._entity_extractor = EntityExtractor()
        return self._entity_extractor

    def _get_groq_client(self):
        """Lazy load Groq client"""
        if self._groq_client is None:
            if self._groq_api_key is None:
                from backend.config import GROQ_API_KEY, GROQ_MODEL
                self._groq_api_key = GROQ_API_KEY
                self._groq_model = GROQ_MODEL

            if self._groq_api_key:
                self._groq_client = Groq(api_key=self._groq_api_key)
        return self._groq_client

    def optimize(self, user_query: str) -> Dict:
        """
        Optimize RTI query with real data:
        1. Detect issues in query structure
        2. Retrieve relevant precedents
        3. Suggest ministry based on precedents
        4. Recommend sections based on precedents
        5. Optimize query phrasing
        """
        logger.info(f"Processing query: {user_query[:100]}...")

        # Basic issue detection
        issues = self._detect_basic_issues(user_query)

        # Extract entities
        entity_extractor = self._get_entity_extractor()
        extracted_sections = entity_extractor.extract_sections(user_query)
        extracted_ministries = entity_extractor.extract_ministries(user_query)

        # Extract date range
        date_range = self._extract_date_range(user_query)

        # Retrieve relevant precedents (with metadata filtering)
        precedents = self._retrieve_precedents(
            user_query,
            top_k=5,
            ministry_filter=extracted_ministries[0] if extracted_ministries else None,
            date_range=date_range
        )

        # Analyze precedents for ministry and section suggestions
        ministry_suggestion = self._suggest_ministry(precedents, extracted_ministries, user_query)
        section_recommendations = self._recommend_sections(precedents, extracted_sections, user_query)

        # Determine legal topic, query intent, and template
        query_lower = user_query.lower()
        legal_topic = "General Public Information"
        query_intent = "Standard Information Request"
        template_used = "General Document Request Template"

        # Topic detection
        if any(word in query_lower for word in ["road", "highway", "repair", "maintenance", "construction", "bridge", "pothole", "street"]):
            legal_topic = "Infrastructure & Public Works"
            template_used = "Road Maintenance Request Template"
        elif any(word in query_lower for word in ["tax", "income tax", "gst", "assessment", "pan", "finance", "audit"]):
            legal_topic = "Finance & Taxation"
            template_used = "Taxation & Personal Assessment Template"
        elif any(word in query_lower for word in ["defence", "military", "army", "navy", "air force", "national security"]):
            legal_topic = "National Security & Defence"
            template_used = "National Security Request Template"
        elif any(word in query_lower for word in ["school", "college", "university", "education", "exam", "result", "marksheet"]):
            legal_topic = "Education & Academics"
            template_used = "Education Request Template"
        elif any(word in query_lower for word in ["health", "hospital", "medical", "medicine", "doctor", "clinic"]):
            legal_topic = "Healthcare & Public Health"
            template_used = "Healthcare Request Template"
        elif any(word in query_lower for word in ["railway", "train", "station", "ticket", "pnr"]):
            legal_topic = "Rail Transport"
            template_used = "Railways Request Template"

        # Exemption detection
        exemption_names = {
            "8(1)(a)": "Sovereignty & Security of India Exemption",
            "8(1)(b)": "Contempt of Court Exemption",
            "8(1)(c)": "Breach of Privilege Exemption",
            "8(1)(d)": "Commercial Confidence / Trade Secrets Exemption",
            "8(1)(e)": "Fiduciary Relationship Exemption",
            "8(1)(f)": "Information received from Foreign Govt Exemption",
            "8(1)(g)": "Safety of person Exemption",
            "8(1)(h)": "Investigation Exemption",
            "8(1)(i)": "Cabinet Papers Exemption",
            "8(1)(j)": "Personal Information Exemption"
        }

        exemptions_detected = []
        for sec, name in exemption_names.items():
            pattern = rf"\b8\(1\)\({sec[-2]}\)"
            if sec in query_lower or re.search(pattern, query_lower):
                exemptions_detected.append({
                    "section": f"Section {sec}",
                    "exemption_name": name
                })

        if any(word in query_lower for word in ["denied", "rejected", "refused", "appeal", "appealed", "misapplying"]):
            query_intent = "First Appeal against Denial"
            template_used = "RTI First Appeal Template"

        # Generate guidance (what_to_avoid and what_to_include)
        what_to_avoid = [
            "Broad or open-ended questions that allow the PIO to deny on grounds of disproportionate diversion of resources (Section 7(9))"
        ]
        if user_query.strip().startswith(("why", "how", "what", "when", "where")):
            what_to_avoid.insert(0, "Phrasing requests as questions (use document-oriented language instead)")
        emotional_words = ["unfair", "corrupt", "biased", "harassment", "discrimination"]
        if any(word in query_lower for word in emotional_words):
            what_to_avoid.insert(0, "Using emotional, accusatory, or subjective language")
        if len(user_query.split()) < 10:
            what_to_avoid.insert(0, "Vague requests without specific date ranges or details")

        what_to_include = [
            "Specific date ranges (e.g., FY 2023-2024)",
            "Clear document types (e.g., certified copies of circulars, correspondence, work orders)",
            "Citing specific sections of the RTI Act under which information is sought (e.g., Section 6(1))"
        ]

        guidance = {
            "what_to_avoid": what_to_avoid,
            "what_to_include": what_to_include
        }

        # Build metadata for LLM
        metadata = {
            "extracted_sections": extracted_sections,
            "extracted_ministries": extracted_ministries,
            "date_range": date_range,
            "legal_topic": legal_topic,
            "query_intent": query_intent,
            "exemptions_detected": exemptions_detected
        }

        # Optimize query phrasing (with LLM using precedent context, ministry, sections, metadata)
        optimized_query, improvements = self._optimize_query_phrasing(
            user_query, precedents, ministry_suggestion, section_recommendations, metadata
        )

        # Calculate quality scores
        scores = self._calculate_scores(user_query, optimized_query, precedents)

        # Determine status
        status = "optimized"
        clarification_request = None
        missing_fields = []

        if not precedents:
            status = "needs_clarification"
            clarification_request = "Could not find relevant precedents. Please provide more context about your RTI request."
            missing_fields.append("context")

        return {
            "status": status,
            "original_query": user_query,
            "optimized_query": optimized_query,
            "issues_detected": issues,
            "improvements_made": improvements,
            "relevant_precedents": precedents,
            "template_used": template_used,
            "guidance": guidance,
            "metadata": {
                "query_length": len(user_query),
                "has_dates": any(word in user_query.lower() for word in ["2023", "2024", "2025"]),
                "has_documents": any(word in user_query.lower() for word in ["records", "documents", "files"]),
                "extracted_sections": extracted_sections,
                "extracted_ministries": extracted_ministries,
                "date_range": date_range,
                "document_types": self._extract_document_types(user_query),
                "legal_topic": legal_topic,
                "query_intent": query_intent,
                "exemptions_detected": exemptions_detected
            },
            "ministry_suggestion": ministry_suggestion,
            "section_recommendations": section_recommendations,
            "scores": scores,
            "clarification_request": clarification_request,
            "missing_fields": missing_fields
        }

    def _retrieve_precedents(
        self, query: str, top_k: int = 5, ministry_filter: Optional[str] = None, date_range: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Retrieve relevant precedents using hybrid search with metadata filtering
        Applies score threshold and deduplication like QA endpoint
        """
        try:
            bm25_loader = self._get_bm25_loader()
            vector_loader = self._get_vector_loader()

            # Retrieve more results for filtering and deduplication
            retrieve_k = top_k * 3 if (ministry_filter or date_range) else top_k * 2

            # BM25 search
            bm25_results = bm25_loader.search(query, top_k=retrieve_k)

            # Hybrid search
            hybrid_results = vector_loader.hybrid_search(
                query=query,
                bm25_results=bm25_results,
                top_k=retrieve_k,
                bm25_weight=0.4,
                semantic_weight=0.6
            )

            # Score threshold - raised to 0.35 to filter weak precedents
            MIN_SCORE_THRESHOLD = 0.35
            filtered_results = [r for r in hybrid_results if r.get("score", 0) >= MIN_SCORE_THRESHOLD]

            # Deduplicate by order_number (keep highest scoring paragraph per order)
            seen_orders = {}
            precedents = []

            for result in filtered_results:
                para = result["paragraph"]
                order_num = para.get("order_number", "N/A")

                # Skip if we've seen this order
                if order_num in seen_orders:
                    continue

                text = para.get("text", "")

                # Clean markdown artifacts from text preview
                text_clean = re.sub(r'#+\s*', '', text)  # Remove markdown headers
                text_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', text_clean)  # Remove bold
                text_clean = re.sub(r'\n+', ' ', text_clean)  # Replace newlines with spaces
                text_clean = text_clean.strip()

                precedent = {
                    "order_number": order_num,
                    "ministry": para.get("ministry", "Unknown"),
                    "section_cited": para.get("section_cited", ""),
                    "order_date": para.get("order_date", ""),
                    "text_preview": text_clean[:300],
                    "relevance_score": result.get("score", 0.0)
                }

                # Apply ministry filter
                if ministry_filter:
                    if ministry_filter.lower() not in precedent["ministry"].lower():
                        continue

                # Apply date range filter
                if date_range and precedent["order_date"]:
                    try:
                        # Extract year from order_date (format: DD/MM/YYYY or YYYY-MM-DD)
                        order_date_str = precedent["order_date"]
                        if "/" in order_date_str:
                            order_year = int(order_date_str.split("/")[-1])
                        elif "-" in order_date_str:
                            order_year = int(order_date_str.split("-")[0])
                        else:
                            order_year = None

                        if order_year:
                            start_year = date_range.get("start_year")
                            end_year = date_range.get("end_year")

                            if start_year and order_year < start_year:
                                continue
                            if end_year and order_year > end_year:
                                continue
                    except (ValueError, IndexError):
                        pass  # Skip date filtering if parsing fails

                seen_orders[order_num] = True
                precedents.append(precedent)

                # Stop if we have enough
                if len(precedents) >= top_k:
                    break

            logger.info(f"Retrieved {len(precedents)} unique precedents (score≥{MIN_SCORE_THRESHOLD}, filtered by ministry={ministry_filter}, date_range={date_range})")
            return precedents

        except Exception as e:
            logger.error(f"Failed to retrieve precedents: {e}")
            return []

    def _suggest_ministry(
        self, precedents: List[Dict], extracted_ministries: List[str], query: str = ""
    ) -> Dict:
        """
        Suggest ministry based on query context, precedents, and extracted entities
        Priority: extracted > query context > precedents
        """
        query_lower = query.lower()
        ministry_keywords = {
            "Ministry of Railways": ["railway", "train", "station", "irctc", "rail"],
            "Ministry of Defence": ["defence", "defense", "military", "army", "navy", "air force"],
            "Ministry of Home Affairs": ["police", "passport", "citizenship", "visa"],
            "Ministry of Finance": ["tax", "income tax", "gst", "customs", "finance", "treasury"],
            "Ministry of Health": ["health", "hospital", "medical", "medicine", "doctor"],
            "Ministry of Education": ["education", "school", "university", "college"],
            "Ministry of Road Transport": ["road", "highway", "transport", "vehicle"],
            "Ministry of Power": ["electricity", "power", "energy"],
            "Ministry of External Affairs": ["passport", "visa", "foreign", "embassy"],
        }

        # Analyze signal breakdown details
        in_metadata = len(extracted_ministries) > 0
        keyword_score = 0.0
        keyword_matched_ministry = None

        for ministry, keywords in ministry_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                keyword_score = 0.8
                keyword_matched_ministry = ministry
                break

        precedent_counts = Counter()
        for prec in precedents:
            m = prec.get("ministry", "Unknown")
            if m and m != "Unknown":
                precedent_counts[m] += 1

        primary_ministry = "Unable to determine"
        confidence = 0.0
        reasoning = ""

        if extracted_ministries:
            primary_ministry = extracted_ministries[0]
            confidence = 0.9
            reasoning = "Ministry explicitly mentioned in query"
        elif keyword_matched_ministry:
            primary_ministry = keyword_matched_ministry
            confidence = 0.8
            reasoning = f"Detected '{keyword_matched_ministry}' context from query keywords"
        elif precedents and precedent_counts:
            most_common = precedent_counts.most_common(1)
            primary_ministry, count = most_common[0]
            confidence = count / len(precedents)
            reasoning = f"Based on {count}/{len(precedents)} similar cases"
        else:
            reasoning = "No relevant precedents or keywords found. Please specify the ministry."

        # Compute breakdown
        precedent_count = precedent_counts.get(primary_ministry, 0)
        signal_breakdown = {
            "keyword_score": keyword_score,
            "in_metadata": in_metadata,
            "precedent_count": precedent_count
        }

        # Compute alternatives (list of dictionaries with keys: ministry, confidence)
        alternatives = []
        all_candidate_ministries = list(ministry_keywords.keys())
        if primary_ministry in all_candidate_ministries:
            all_candidate_ministries.remove(primary_ministry)
        for alt_m in all_candidate_ministries[:3]:
            alternatives.append({
                "ministry": alt_m,
                "confidence": 0.2
            })

        return {
            "primary_ministry": primary_ministry,
            "confidence": confidence,
            "reasoning": reasoning,
            "signal_breakdown": signal_breakdown,
            "alternatives": alternatives
        }

    def _recommend_sections(
        self, precedents: List[Dict], extracted_sections: List[str], query: str = ""
    ) -> Dict:
        """
        Recommend RTI sections based on precedents and query context
        Detects exemption claims and suggests counter-arguments
        """
        # Detect exemption/denial keywords in query
        query_lower = query.lower()
        exemption_keywords = {
            "8(1)(a)": ["national security", "sovereignty", "strategic", "defense", "8(1)(a)", "section 8(1)(a)"],
            "8(1)(d)": ["commercial", "trade secret", "competitive", "confidential information", "8(1)(d)", "section 8(1)(d)"],
            "8(1)(e)": ["fiduciary", "third party", "8(1)(e)", "section 8(1)(e)"],
            "8(1)(j)": ["personal information", "privacy", "invasion of privacy", "8(1)(j)", "section 8(1)(j)"],
            "8(1)(h)": ["investigation", "prosecution", "law enforcement", "8(1)(h)", "section 8(1)(h)"],
        }

        detected_exemptions = []
        for section, keywords in exemption_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_exemptions.append(section)

        # Check for denial/rejection keywords
        denial_mentioned = any(word in query_lower for word in [
            "denied", "rejected", "refused", "said", "they said", "exemption", "exempt"
        ])

        primary_sections = []
        optional_sections = []
        exemption_notes = []

        if extracted_sections:
            # User already mentioned sections
            primary_sections = [
                {"section": sec, "reason": "Mentioned in your query"}
                for sec in extracted_sections
            ]
        elif not precedents:
            # Default recommendation
            primary_sections = [{"section": "Section 6(1)", "reason": "Standard RTI request provision"}]
        else:
            # Count sections in precedents
            section_counts = Counter()
            for prec in precedents:
                section = prec.get("section_cited", "")
                if section and section.strip():
                    section_counts[section] += 1

            if section_counts:
                # Top 2 sections as primary
                for section, count in section_counts.most_common(2):
                    primary_sections.append({
                        "section": section,
                        "reason": f"Cited in {count}/{len(precedents)} similar cases"
                    })

                # Next 2 as optional
                for section, count in section_counts.most_common(4)[2:]:
                    optional_sections.append({
                        "section": section,
                        "reason": f"Sometimes relevant ({count} cases)"
                    })
            else:
                # Fallback
                primary_sections.append({
                    "section": "Section 6(1)",
                    "reason": "Standard RTI request provision"
                })

        # Add clean exemption note strings
        if denial_mentioned and detected_exemptions:
            for ex in detected_exemptions:
                counter = self._get_exemption_counter_argument(ex, query)
                exemption_notes.append(f"Exemption {ex}: {counter}")

        # Choose appropriate contextual guidance
        contextual_guidance = "Ensure your query cites Section 6(1) of the RTI Act and specifies the exact period of records requested. Keep the request focused and objective to minimize the risk of rejection."
        if detected_exemptions:
            contextual_guidance = f"Since a Section {detected_exemptions[0]} exemption has been cited, emphasize that the requested information relates to public interest or official duties of the public servant, or cite Section 8(2) which overrides exemptions if public interest outweighs harm."
        elif "road" in query_lower or "highway" in query_lower:
            contextual_guidance = "For public works and infrastructure requests, cite Section 4(1)(b) proactive disclosure requirements and ask for certified copies of the measurement book and work completion certificate."

        return {
            "primary_sections": primary_sections,
            "optional_sections": optional_sections,
            "exemption_notes": exemption_notes,
            "contextual_guidance": contextual_guidance
        }

    def _get_exemption_counter_argument(self, exemption_section: str, query: str = "") -> str:
        """Generate counter-argument for common exemption claims"""
        counter_arguments = {
            "8(1)(a)": "Information related to completed processes or publicly available data typically does not fall under national security exemptions.",
            "8(1)(d)": "Once a tender/contract is awarded or process is complete, commercial confidentiality concerns are significantly reduced. Public interest in transparency may override this exemption.",
            "8(1)(e)": "Fiduciary relationship exemption does not apply when information is in public interest or relates to completed transactions.",
            "8(1)(j)": "Personal information exemption does not apply to information about public officials in their official capacity or when public interest outweighs privacy.",
            "8(1)(h)": "Investigation exemption does not apply to completed investigations or when significant time has passed.",
        }

        return counter_arguments.get(exemption_section, "Consider citing public interest under Section 8(2) to override this exemption.")

    def _optimize_query_phrasing(
        self, query: str, precedents: Optional[List[Dict]] = None, ministry_suggestion: Optional[Dict] = None,
        section_recommendations: Optional[Dict] = None, metadata: Optional[Dict] = None
    ) -> Tuple[str, List[str]]:
        """
        Optimize query phrasing using LLM with precedent context
        Falls back to rule-based if LLM fails
        """
        # Try LLM-based optimization first
        groq_client = self._get_groq_client()
        if groq_client and precedents:
            try:
                return self._optimize_query_with_llm(
                    query, precedents, ministry_suggestion, section_recommendations, metadata
                )
            except Exception as e:
                logger.warning(f"LLM optimization failed, falling back to rule-based: {e}")

        # Fallback to rule-based optimization
        return self._optimize_query_rule_based(query)

    def _optimize_query_with_llm(
        self, query: str, precedents: List[Dict], ministry_suggestion: Optional[Dict] = None,
        section_recommendations: Optional[Dict] = None, metadata: Optional[Dict] = None
    ) -> Tuple[str, List[str]]:
        """
        Use Groq LLM to optimize query with precedent context
        """
        groq_client = self._get_groq_client()
        if not groq_client:
            raise ValueError("Groq client not initialized")

        # Build precedent context
        precedent_context = []
        for i, prec in enumerate(precedents[:3], 1):  # Top 3 precedents
            precedent_context.append(
                f"{i}. Order: {prec.get('order_number', 'N/A')}\n"
                f"   Ministry: {prec.get('ministry', 'Unknown')}\n"
                f"   Section: {prec.get('section_cited', 'N/A')}\n"
                f"   Preview: {prec.get('text_preview', '')[:200]}..."
            )

        precedent_text = "\n\n".join(precedent_context)

        # Build ministry and section context
        ministry_context = ""
        if ministry_suggestion:
            ministry_context = f"\nPREDICTED MINISTRY: {ministry_suggestion.get('primary_ministry', 'Unknown')} (Confidence: {ministry_suggestion.get('confidence', 0):.0%})"

        section_context = ""
        if section_recommendations and section_recommendations.get('primary_sections'):
            sections = [s['section'] for s in section_recommendations['primary_sections']]
            section_context = f"\nRELEVANT SECTIONS: {', '.join(sections)}"

        # Build metadata context
        metadata_context = ""
        if metadata:
            if metadata.get('extracted_sections'):
                metadata_context += f"\nSections mentioned in query: {', '.join(metadata['extracted_sections'])}"
            if metadata.get('date_range'):
                dr = metadata['date_range']
                metadata_context += f"\nDate range in query: {dr.get('start_year', '[start date]')} to {dr.get('end_year', '[end date]')}"

        # Create prompt
        prompt = f"""You are an RTI (Right to Information) query optimization expert. Improve this query to be more effective while keeping it CONCISE.

ORIGINAL QUERY:
{query}

RELEVANT PRECEDENTS:
{precedent_text}{ministry_context}{section_context}{metadata_context}

RULES:
1. Keep it SHORT and CLEAR (max 3-4 sentences)
2. Convert questions to document requests
3. Add 1-2 specific document types (orders, notices, correspondence)
4. Use placeholders for missing info: [start date], [end date], [reference number]
5. Cite ONE relevant precedent if applicable (from list above)
6. Use predicted ministry and sections provided
7. DO NOT invent dates, numbers, or details not in original query
8. DO NOT add unnecessary legal jargon

GOAL: Make it legally sound and harder to deny, but keep it CONCISE.

Respond in JSON:
{{
  "optimized_query": "The improved query (max 3-4 sentences)...",
  "improvements_made": [
    "Improvement 1",
    "Improvement 2"
  ],
  "reasoning": "Brief explanation"
}}

Respond ONLY with valid JSON, no other text."""

        # Call Groq
        response = groq_client.chat.completions.create(
            model=self._groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )

        # Parse response
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        content = content.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        optimized_query = result.get("optimized_query", query)
        improvements = result.get("improvements_made", [])

        logger.info(f"LLM optimization successful: {len(improvements)} improvements")

        return optimized_query, improvements

    def _optimize_query_rule_based(self, query: str) -> Tuple[str, List[str]]:
        """
        Rule-based query optimization (fallback)
        """
        improvements = []
        optimized = query

        # Convert questions to document requests
        converted_to_request = False
        if query.strip().lower().startswith(("why", "how", "what", "when", "where")):
            # Try to convert to document request
            if query.lower().startswith("why"):
                optimized = f"Provide records and documents explaining {query[4:].strip()}"
                improvements.append("Converted question to document request")
                converted_to_request = True
            elif query.lower().startswith("what"):
                optimized = f"Provide information and records regarding {query[5:].strip()}"
                improvements.append("Converted question to document request")
                converted_to_request = True
            elif query.lower().startswith("how"):
                optimized = f"Provide records and documents showing {query[4:].strip()}"
                improvements.append("Converted question to document request")
                converted_to_request = True

        # Add document-oriented language if missing (but not if we just converted)
        doc_keywords = ["records", "documents", "files", "copy", "information", "details"]
        if not converted_to_request and not any(word in query.lower() for word in doc_keywords):
            optimized = f"Provide records and documents regarding: {optimized}"
            improvements.append("Added document-oriented language")

        # Suggest adding time period
        date_keywords = ["2023", "2024", "2025", "date", "period", "year", "month"]
        if not any(word in query.lower() for word in date_keywords):
            improvements.append("Consider adding a specific time period (e.g., 'from January 2024 to March 2024')")

        # Suggest adding specificity
        if len(query.split()) < 10:
            improvements.append("Consider adding more specific details about what you need")

        return optimized, improvements

    def _calculate_scores(self, original: str, optimized: str, precedents: List[Dict]) -> Dict:
        """
        Calculate quality scores
        """
        # Original clarity score
        original_clarity = self._calculate_clarity_score(original)

        # Optimized clarity score
        optimized_clarity = self._calculate_clarity_score(optimized)

        # Legal specificity (based on sections/ministries mentioned)
        legal_specificity = self._calculate_legal_specificity(optimized)

        # Retrieval quality prediction (based on precedent relevance)
        retrieval_quality = self._calculate_retrieval_quality(precedents)

        # Overall confidence
        overall_confidence = (optimized_clarity + legal_specificity + retrieval_quality) / 3

        return {
            "original_clarity": original_clarity,
            "optimized_clarity": optimized_clarity,
            "legal_specificity": legal_specificity,
            "retrieval_quality_prediction": retrieval_quality,
            "overall_confidence": overall_confidence
        }

    def _calculate_clarity_score(self, text: str) -> float:
        """Calculate clarity score based on structure"""
        score = 0.5  # Base score

        # Length bonus
        word_count = len(text.split())
        if 10 <= word_count <= 50:
            score += 0.2
        elif word_count > 50:
            score += 0.1

        # Document keywords
        doc_keywords = ["records", "documents", "files", "copy", "information"]
        if any(word in text.lower() for word in doc_keywords):
            score += 0.15

        # Specific details (dates, numbers)
        if re.search(r'\d{4}', text):  # Year
            score += 0.1

        # Not a question
        if not text.strip().startswith(("why", "how", "what", "when", "where")):
            score += 0.05

        return min(score, 1.0)

    def _calculate_legal_specificity(self, text: str) -> float:
        """Calculate legal specificity score"""
        score = 0.3  # Base score

        # Section mentions
        sections = re.findall(r'\d+\(\d+\)\([a-z]\)', text.lower())
        if sections:
            score += 0.3

        # Ministry mentions
        if "ministry" in text.lower():
            score += 0.2

        # Legal terms
        legal_terms = ["rti", "information", "public authority", "disclosure", "exemption"]
        matches = sum(1 for term in legal_terms if term in text.lower())
        score += min(matches * 0.1, 0.2)

        return min(score, 1.0)

    def _calculate_retrieval_quality(self, precedents: List[Dict]) -> float:
        """Calculate predicted retrieval quality"""
        if not precedents:
            return 0.2

        # Average relevance score
        avg_score = sum(p.get("relevance_score", 0) for p in precedents) / len(precedents)

        # Normalize to 0-1 range (assuming scores are typically 0-2)
        normalized = min(avg_score / 2.0, 1.0)

        return normalized

    def _extract_date_range(self, query: str) -> Optional[Dict]:
        """Extract date range from query"""
        years = re.findall(r'\b(20\d{2}|19\d{2})\b', query)
        if not years:
            return None

        years = [int(y) for y in years]
        return {
            "start_year": min(years),
            "end_year": max(years)
        }

    def _extract_document_types(self, query: str) -> List[str]:
        """Extract document types mentioned in query"""
        doc_types = []
        query_lower = query.lower()

        type_keywords = {
            "records": "records",
            "files": "files",
            "documents": "documents",
            "correspondence": "correspondence",
            "emails": "emails",
            "letters": "letters",
            "reports": "reports",
            "minutes": "minutes",
            "orders": "orders",
            "notifications": "notifications"
        }

        for keyword, doc_type in type_keywords.items():
            if keyword in query_lower:
                doc_types.append(doc_type)

        return doc_types

    def _detect_basic_issues(self, query: str) -> List[Dict]:
        """Detect only obvious issues"""
        issues = []
        query_lower = query.lower()

        # Too short
        if len(query) < 20:
            issues.append({
                "type": "too_short",
                "severity": "high",
                "description": "Query is very short",
                "suggestion": "Provide more details about what information you need"
            })

        # Emotional language
        emotional_words = ["unfair", "corrupt", "biased", "harassment", "discrimination"]
        if any(word in query_lower for word in emotional_words):
            issues.append({
                "type": "emotional_language",
                "severity": "medium",
                "description": "Contains emotional language",
                "suggestion": "Keep the request factual and neutral"
            })

        # Question format
        if query.strip().startswith(("why", "how", "what", "when", "where")):
            issues.append({
                "type": "question_format",
                "severity": "medium",
                "description": "Phrased as a question",
                "suggestion": "RTI requests should ask for documents, not explanations"
            })

        return issues
