"""
Build Enhanced Knowledge Graph for Dashboard
Adds visual metadata, metrics, and dashboard-optimized structure
"""

import networkx as nx
import pickle
import json
from sqlalchemy import create_engine, text
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import DATABASE_URL

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "dashboard_graph.json"

def calculate_node_metrics(G):
    """Calculate centrality and importance metrics for nodes"""
    # PageRank for importance
    pagerank = nx.pagerank(G, weight='weight')

    # Degree centrality
    in_degree = dict(G.in_degree(weight='weight'))
    out_degree = dict(G.out_degree(weight='weight'))

    return {
        'pagerank': pagerank,
        'in_degree': in_degree,
        'out_degree': out_degree
    }

def get_node_color(node_type):
    """Assign colors based on node type"""
    colors = {
        'ministry': '#3B82F6',      # Blue
        'section': '#F59E0B',       # Amber
        'outcome': '#10B981'        # Green
    }
    return colors.get(node_type, '#6B7280')

def get_outcome_color(outcome_name):
    """Specific colors for outcomes"""
    colors = {
        'allowed': '#10B981',           # Green
        'denied': '#EF4444',            # Red
        'partially_allowed': '#F59E0B'  # Amber
    }
    return colors.get(outcome_name, '#6B7280')

def build_dashboard_graph():
    """Build enhanced knowledge graph with dashboard metadata"""
    engine = create_engine(DATABASE_URL)
    G = nx.DiGraph()

    print("Building enhanced knowledge graph for dashboard...")

    with engine.connect() as conn:
        # Get ministry stats for node sizing
        ministry_stats = {}
        query = text("""
            SELECT
                m.name,
                COUNT(c.id) as total_cases,
                ms.denial_rate,
                ms.override_rate
            FROM ministries m
            LEFT JOIN cases c ON c.ministry_id = m.id
            LEFT JOIN ministry_stats ms ON ms.ministry_id = m.id
            GROUP BY m.name, ms.denial_rate, ms.override_rate
        """)
        for row in conn.execute(query):
            ministry_stats[row.name] = {
                'total_cases': row.total_cases,
                'denial_rate': float(row.denial_rate) if row.denial_rate else 0,
                'override_rate': float(row.override_rate) if row.override_rate else 0
            }

        # Build ministry→section edges
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

        for row in conn.execute(query):
            ministry = row.ministry
            section = row.section
            citation_count = row.citation_count

            # Add ministry node with stats
            stats = ministry_stats.get(ministry, {})
            G.add_node(ministry,
                      node_type='ministry',
                      total_cases=stats.get('total_cases', 0),
                      denial_rate=stats.get('denial_rate', 0),
                      override_rate=stats.get('override_rate', 0))

            # Add section node
            G.add_node(section, node_type='section')

            # Add edge
            G.add_edge(ministry, section,
                      weight=citation_count,
                      edge_type='cites',
                      count=citation_count)

        # Get section stats
        section_stats = {}
        query = text("""
            SELECT
                section_cited,
                COUNT(*) as total_citations,
                SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END) as allowed_count,
                SUM(CASE WHEN appeal_outcome = 'denied' THEN 1 ELSE 0 END) as denied_count,
                ROUND(
                    SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END)::NUMERIC /
                    NULLIF(COUNT(*), 0),
                    4
                ) as success_rate
            FROM cases
            WHERE section_cited IS NOT NULL
            GROUP BY section_cited
        """)
        for row in conn.execute(query):
            section_stats[row.section_cited] = {
                'total_citations': row.total_citations,
                'allowed_count': row.allowed_count,
                'denied_count': row.denied_count,
                'success_rate': float(row.success_rate) if row.success_rate else 0
            }

        # Update section nodes with stats
        for section in [n for n, d in G.nodes(data=True) if d.get('node_type') == 'section']:
            stats = section_stats.get(section, {})
            G.nodes[section].update(stats)

        # Build section→outcome edges
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

        for row in conn.execute(query):
            section = row.section
            outcome = row.outcome
            outcome_count = row.outcome_count
            outcome_rate = float(row.outcome_rate)

            # Add outcome node
            G.add_node(outcome, node_type='outcome')

            # Add edge
            if G.has_node(section):
                G.add_edge(section, outcome,
                          weight=outcome_rate,
                          count=outcome_count,
                          edge_type='leads_to')

    # Calculate metrics
    print("Calculating node metrics...")
    metrics = calculate_node_metrics(G)

    # Build dashboard JSON
    graph_data = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "ministries": len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'ministry']),
            "sections": len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'section']),
            "outcomes": len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'outcome'])
        },
        "layout": "force-directed"  # Hint for frontend
    }

    # Convert nodes with enhanced metadata
    node_to_id = {node: idx for idx, node in enumerate(G.nodes())}

    for node, data in G.nodes(data=True):
        node_type = data.get('node_type', 'unknown')

        # Base node data
        node_data = {
            "id": node_to_id[node],
            "name": node,
            "type": node_type,
            "color": get_outcome_color(node) if node_type == 'outcome' else get_node_color(node_type),
            "importance": metrics['pagerank'].get(node, 0),
            "in_degree": metrics['in_degree'].get(node, 0),
            "out_degree": metrics['out_degree'].get(node, 0)
        }

        # Add type-specific metadata
        if node_type == 'ministry':
            node_data.update({
                "total_cases": data.get('total_cases', 0),
                "denial_rate": data.get('denial_rate', 0),
                "override_rate": data.get('override_rate', 0),
                "size": min(50 + data.get('total_cases', 0) / 5, 150)  # Scale size by cases
            })
        elif node_type == 'section':
            node_data.update({
                "total_citations": data.get('total_citations', 0),
                "success_rate": data.get('success_rate', 0),
                "allowed_count": data.get('allowed_count', 0),
                "denied_count": data.get('denied_count', 0),
                "size": min(30 + data.get('total_citations', 0) * 2, 100)
            })
        elif node_type == 'outcome':
            node_data.update({
                "size": 60
            })

        graph_data["nodes"].append(node_data)

    # Convert edges with visual metadata
    for source, target, data in G.edges(data=True):
        edge_type = data.get('edge_type', 'unknown')
        weight = data.get('weight', 1)

        edge_data = {
            "source": node_to_id[source],
            "target": node_to_id[target],
            "type": edge_type,
            "weight": weight,
            "count": data.get('count', weight),
            "thickness": min(1 + weight / 10, 10) if edge_type == 'cites' else min(1 + weight * 5, 8),
            "color": "#94A3B8" if edge_type == 'cites' else "#CBD5E1",
            "animated": edge_type == 'leads_to'
        }

        graph_data["edges"].append(edge_data)

    # Save to file
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(graph_data, f, indent=2)

    print(f"\n✅ Dashboard graph saved to {OUTPUT_PATH}")
    print(f"   Nodes: {graph_data['metadata']['node_count']}")
    print(f"   Edges: {graph_data['metadata']['edge_count']}")
    print(f"   Ministries: {graph_data['metadata']['ministries']}")
    print(f"   Sections: {graph_data['metadata']['sections']}")
    print(f"   Outcomes: {graph_data['metadata']['outcomes']}")

    return graph_data

if __name__ == "__main__":
    build_dashboard_graph()
