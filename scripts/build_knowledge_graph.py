"""
Build Knowledge Graph for RTI-Lens
Creates a NetworkX graph with ministries, sections, and outcomes as nodes.
Edges represent relationships weighted by citation counts and overturn rates.
"""

import networkx as nx
import pickle
import json
from sqlalchemy import create_engine, text
from pathlib import Path

DB_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "knowledge_graph.pkl"
JSON_OUTPUT_PATH = Path(__file__).parent.parent / "data" / "knowledge_graph.json"

def build_knowledge_graph():
    """Build and save the knowledge graph"""
    engine = create_engine(DB_URL)
    G = nx.DiGraph()

    with engine.connect() as conn:
        # Add ministry nodes and ministry→section edges
        print("Building ministry→section edges...")
        query = text("""
            SELECT
                m.name AS ministry,
                c.section_cited AS section,
                COUNT(*) AS citation_count
            FROM cases c
            JOIN ministries m ON m.id = c.ministry_id
            WHERE c.section_cited IS NOT NULL
            GROUP BY m.name, c.section_cited
            HAVING COUNT(*) >= 2
        """)

        result = conn.execute(query).fetchall()

        for row in result:
            ministry = row.ministry
            section = row.section
            citation_count = row.citation_count

            # Add nodes
            G.add_node(ministry, node_type='ministry')
            G.add_node(section, node_type='section')

            # Add edge: ministry → section
            G.add_edge(ministry, section, weight=citation_count, edge_type='cites')

        print(f"Added {len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'ministry'])} ministry nodes")
        print(f"Added {len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'section'])} section nodes")

        # Add outcome nodes and section→outcome edges
        print("Building section→outcome edges...")
        query = text("""
            SELECT
                section_cited AS section,
                appeal_outcome AS outcome,
                COUNT(*) AS outcome_count,
                ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (PARTITION BY section_cited), 4) AS outcome_rate
            FROM cases
            WHERE section_cited IS NOT NULL
              AND appeal_outcome IS NOT NULL
            GROUP BY section_cited, appeal_outcome
            HAVING COUNT(*) >= 2
        """)

        result = conn.execute(query).fetchall()

        for row in result:
            section = row.section
            outcome = row.outcome
            outcome_count = row.outcome_count
            outcome_rate = float(row.outcome_rate)

            # Add outcome node
            G.add_node(outcome, node_type='outcome')

            # Add edge: section → outcome
            if G.has_node(section):  # Only add if section exists from previous step
                G.add_edge(section, outcome, weight=outcome_rate, count=outcome_count, edge_type='leads_to')

        print(f"Added {len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'outcome'])} outcome nodes")

    # Save graph as pickle
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'wb') as f:
        pickle.dump(G, f)

    # Save graph as JSON for API
    graph_json = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges()
        }
    }

    # Convert nodes to JSON format with IDs
    node_to_id = {node: idx for idx, node in enumerate(G.nodes())}
    for node, data in G.nodes(data=True):
        graph_json["nodes"].append({
            "id": node_to_id[node],
            "name": node,
            "type": data.get("node_type", "unknown")
        })

    # Convert edges to JSON format
    for source, target, data in G.edges(data=True):
        graph_json["edges"].append({
            "source": node_to_id[source],
            "target": node_to_id[target],
            "type": data.get("edge_type", "unknown"),
            "weight": data.get("weight", 1),
            "count": data.get("count", data.get("weight", 1))
        })

    with open(JSON_OUTPUT_PATH, 'w') as f:
        json.dump(graph_json, f, indent=2)

    print(f"\n✅ Knowledge graph saved to {OUTPUT_PATH}")
    print(f"✅ JSON graph saved to {JSON_OUTPUT_PATH}")
    print(f"   Total nodes: {G.number_of_nodes()}")
    print(f"   Total edges: {G.number_of_edges()}")

    # Print some statistics
    print("\nGraph Statistics:")
    print(f"   Ministries: {len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'ministry'])}")
    print(f"   Sections: {len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'section'])}")
    print(f"   Outcomes: {len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'outcome'])}")
    print(f"   Ministry→Section edges: {len([e for e in G.edges(data=True) if e[2].get('edge_type') == 'cites'])}")
    print(f"   Section→Outcome edges: {len([e for e in G.edges(data=True) if e[2].get('edge_type') == 'leads_to'])}")

if __name__ == "__main__":
    build_knowledge_graph()
