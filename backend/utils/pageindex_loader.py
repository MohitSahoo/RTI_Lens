"""
PageIndex Tree Loader for hierarchical document retrieval
"""
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

PAGEINDEX_DIR = Path("data/pageindex_trees")
MAPPING_FILE = Path("data/order_number_mapping.json")

class PageIndexLoader:
    """Load and search PageIndex hierarchical trees"""

    def __init__(self):
        self.trees_cache = {}
        self.order_number_to_hash = {}
        self._load_mapping()

    def _load_mapping(self):
        """Load pre-built order number to hash mapping"""
        if MAPPING_FILE.exists():
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                self.order_number_to_hash = json.load(f)
        else:
            # Fallback: build mapping on the fly (slow)
            logger.warning("order_number_mapping.json not found. Building mapping on the fly (this may be slow)...")
            self._build_mapping()

    def _build_mapping(self):
        """Build mapping from order_number to file hash by scanning TXT files (fallback)"""
        TXT_DIR = Path("data/cic_orders_txt")
        for txt_file in TXT_DIR.glob("*.txt"):
            order_hash = txt_file.stem
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = ''.join(f.readlines()[:500])
                match = re.search(r'(CIC/[A-Z]+/[A-Z]/\d{4}/\d+)', content)
                if match:
                    order_number = match.group(1)
                    self.order_number_to_hash[order_number] = order_hash
            except Exception:
                continue

    def get_hash_from_order_number(self, order_number: str) -> Optional[str]:
        """Get file hash from order number"""
        return self.order_number_to_hash.get(order_number)

    def load_tree(self, order_hash: str) -> Optional[Dict]:
        """Load PageIndex tree for a given order hash"""
        if order_hash in self.trees_cache:
            return self.trees_cache[order_hash]

        tree_path = PAGEINDEX_DIR / f"{order_hash}.json"
        if not tree_path.exists():
            return None

        with open(tree_path, 'r', encoding='utf-8') as f:
            tree = json.load(f)
            self.trees_cache[order_hash] = tree
            return tree

    def extract_section_text(self, md_path: Path, start_line: int, end_line: Optional[int] = None) -> str:
        """Extract text from markdown file between line numbers"""
        if not md_path.exists():
            return ""

        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if end_line is None:
            end_line = len(lines)

        # Extract lines (line_num is 1-indexed)
        section_lines = lines[start_line-1:end_line]
        return ''.join(section_lines).strip()

    def get_hierarchical_context(self, order_hash: str, max_sections: int = 5) -> List[Dict]:
        """
        Get hierarchical sections from a document
        Returns list of sections with title, hierarchy, and text
        """
        tree = self.load_tree(order_hash)
        if not tree or not tree.get("structure"):
            return []

        md_path = Path("data/cic_orders_md") / f"{order_hash}.md"
        if not md_path.exists():
            return []

        sections = []

        def traverse_nodes(nodes, parent_title="", depth=0):
            """Recursively traverse tree nodes"""
            for i, node in enumerate(nodes):
                title = node.get("title", "")
                line_num = node.get("line_num", 0)

                # Calculate end line (next sibling or parent's end)
                if i + 1 < len(nodes):
                    end_line = nodes[i + 1].get("line_num", None)
                else:
                    end_line = None

                # Build hierarchy path
                hierarchy = f"{parent_title} > {title}" if parent_title else title

                # Extract text for this section
                text = self.extract_section_text(md_path, line_num, end_line)

                if text and len(text) > 50:  # Only include substantial sections
                    sections.append({
                        "title": title,
                        "hierarchy": hierarchy,
                        "text": text[:1000],  # Limit section size
                        "depth": depth,
                        "line_num": line_num
                    })

                # Traverse child nodes
                if "nodes" in node and node["nodes"]:
                    traverse_nodes(node["nodes"], hierarchy, depth + 1)

        traverse_nodes(tree["structure"])

        # Return top sections (by depth and position)
        return sections[:max_sections]

    def get_relevant_sections_by_order_numbers(self, order_numbers: List[str], question: str, max_sections: int = 5) -> List[Dict]:
        """
        Get relevant sections from multiple documents using order numbers
        Converts order numbers to hashes and retrieves hierarchical sections
        """
        # Convert order numbers to hashes
        order_hashes = []
        for order_number in order_numbers:
            order_hash = self.get_hash_from_order_number(order_number)
            if order_hash:
                order_hashes.append(order_hash)

        if not order_hashes:
            return []

        return self.get_relevant_sections(order_hashes, question, max_sections)

    def get_relevant_sections(self, order_hashes: List[str], question: str, max_sections: int = 5) -> List[Dict]:
        """
        Get relevant sections from multiple documents.
        First leverages the hierarchical PageIndex tree json structures to score, 
        prioritize, and extract relevant sections from each document.
        Then splits those prioritized sections into 500-word chunks (100 overlap)
        and ranks them using keyword and citation boosts.
        Ensures diversity by limiting sections per order.
        """
        all_sections = []

        # Tokenization helper for keyword matching
        def get_keywords(text: str):
            text = text.lower()
            # Preserve section patterns (like Section 8(1)(j))
            section_pattern = re.compile(r'\b\d+\(?[\w\d]*\)?(?:\(?[\w\d]*\)?)*\b')
            sections = set(section_pattern.findall(text))
            # Other words
            words = set(re.sub(r'[^a-z0-9]', ' ', text).split())
            return sections | words

        question_keywords = get_keywords(question)
        section_pattern = re.compile(r'\b\d+\(?[\w\d]*\)?(?:\(?[\w\d]*\)?)*\b')
        q_sections = section_pattern.findall(question.lower())

        for order_hash in order_hashes:
            md_path = Path("data/cic_orders_md") / f"{order_hash}.md"
            if not md_path.exists():
                continue

            # Load PageIndex Tree JSON if available
            tree = self.load_tree(order_hash)
            
            # Extract title
            title = "Central Information Commission"
            if tree and tree.get("metadata"):
                title = tree["metadata"].get("title", title)
            else:
                # Fallback to file reading for title
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f.readlines() if line.strip()]
                    for line in lines[:5]:
                        if "vs" in line.lower() or "v." in line.lower():
                            title = line.strip("# ")
                            break
                except Exception:
                    pass

            doc_sections_to_process = []

            if tree and tree.get("structure"):
                # Hierarchical Node Scoring & Prioritization
                scored_nodes = []

                def traverse_and_score(nodes, parent_title="", depth=0):
                    for idx, node in enumerate(nodes):
                        node_title = node.get("title", "")
                        line_num = node.get("line_num", 0)
                        
                        # Next sibling line number determines boundary
                        if idx + 1 < len(nodes):
                            end_line = nodes[idx + 1].get("line_num", None)
                        else:
                            end_line = None

                        hierarchy = f"{parent_title} > {node_title}" if parent_title else node_title
                        
                        # Score this node
                        node_keywords = get_keywords(node_title)
                        title_overlap = len(question_keywords & node_keywords)
                        
                        # Section match bonus in headings
                        sec_bonus = 0
                        for q_sec in q_sections:
                            if q_sec in node_keywords:
                                sec_bonus += 15  # High priority bonus for headings matching requested sections

                        node_score = title_overlap + sec_bonus
                        
                        scored_nodes.append({
                            "node": node,
                            "hierarchy": hierarchy,
                            "depth": depth,
                            "line_num": line_num,
                            "end_line": end_line,
                            "score": node_score
                        })

                        if "nodes" in node and node["nodes"]:
                            traverse_and_score(node["nodes"], hierarchy, depth + 1)

                traverse_and_score(tree["structure"])
                
                # Sort nodes by score, pick top ones
                scored_nodes.sort(key=lambda x: x["score"], reverse=True)
                
                # Filter out overlapping/redundant sections (e.g. parent vs child if scores are identical)
                # Keep top 3 scoring branches
                top_branches = scored_nodes[:3]
                
                for branch in top_branches:
                    text = self.extract_section_text(md_path, branch["line_num"], branch["end_line"])
                    if text and len(text.strip()) > 50:
                        doc_sections_to_process.append({
                            "hierarchy": f"Central Information Commission > {title} > {branch['hierarchy']}",
                            "text": text,
                            "title": title
                        })
            
            # Fallback if no tree structure could be parsed/loaded
            if not doc_sections_to_process:
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        full_text = f.read()
                    doc_sections_to_process.append({
                        "hierarchy": f"Central Information Commission > {title}",
                        "text": full_text,
                        "title": title
                    })
                except Exception:
                    continue

            # Process the prioritized document sections into 500-word chunks with 100 overlap
            for doc_sec in doc_sections_to_process:
                words = doc_sec["text"].split()
                chunk_size = 500
                overlap = 100
                chunks = []

                if len(words) <= chunk_size:
                    chunks = [doc_sec["text"]]
                else:
                    i = 0
                    while i < len(words):
                        chunk_words = words[i:i + chunk_size]
                        chunks.append(" ".join(chunk_words))
                        if i + chunk_size >= len(words):
                            break
                        i += chunk_size - overlap

                for idx, chunk_text in enumerate(chunks):
                    all_sections.append({
                        "title": doc_sec["title"],
                        "hierarchy": f"{doc_sec['hierarchy']} > Chunk {idx+1}",
                        "text": chunk_text,
                        "order_hash": order_hash,
                        "depth": 1,
                        "line_num": idx * 400
                    })

        # Score the final chunks using the existing keyword matching & citation boosting
        for section in all_sections:
            text_keywords = get_keywords(section["text"])
            title_keywords = get_keywords(section["title"])

            text_overlap = len(question_keywords & text_keywords)
            title_overlap = len(question_keywords & title_keywords)

            section_match_bonus = 0
            for q_sec in q_sections:
                if q_sec in title_keywords:
                    section_match_bonus += 10
                if q_sec in text_keywords:
                    section_match_bonus += 5

            section["relevance_score"] = text_overlap + (title_overlap * 3) + section_match_bonus

        # Sort all chunks by relevance
        all_sections.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Ensure diversity: limit sections per order
        max_per_order = 2 if len(order_hashes) == 1 else 1
        order_counts = {}
        diverse_sections = []

        for section in all_sections:
            order_hash = section["order_hash"]
            count = order_counts.get(order_hash, 0)

            if count < max_per_order:
                diverse_sections.append(section)
                order_counts[order_hash] = count + 1

            if len(diverse_sections) >= max_sections:
                break

        return diverse_sections
    def get_full_context_by_order(self, order_number: str) -> Optional[Dict]:
        """Retrieve full hierarchical context and text for a specific order number"""
        order_hash = self.get_hash_from_order_number(order_number)
        if not order_hash:
            return None
            
        tree = self.load_tree(order_hash)
        if not tree:
            return None
            
        md_path = Path("data/cic_orders_md") / f"{order_hash}.md"
        full_text = ""
        if md_path.exists():
            with open(md_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
                
        return {
            "order_number": order_number,
            "hierarchy": tree.get("metadata", {}).get("hierarchy", ["CIC", "Central Information Commission"]),
            "full_text": full_text,
            "metadata": tree.get("metadata", {})
        }
