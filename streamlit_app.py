"""
Streamlit Frontend for RTI-Lens API Testing
"""
import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import date
import json
import pandas as pd
import os
from pyvis.network import Network
import tempfile

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")

st.set_page_config(page_title="RTI-Lens Test UI", layout="wide")
st.title("🔍 RTI-Lens API Test Interface")

# Sidebar for API health
with st.sidebar:
    st.header("System Status")
    if st.button("Check Health"):
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                st.success("✅ API Healthy")
                st.json(health)
            else:
                st.error(f"❌ API Error: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Connection Failed: {str(e)}")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Q&A",
    "📝 Draft Appeal",
    "🎯 Predict Outcome",
    "📊 Analytics",
    "🕸️ Knowledge Graph"
])

# Tab 1: Q&A
with tab1:
    st.header("Ask Questions About RTI Rulings")

    question = st.text_area(
        "Question",
        placeholder="e.g., What are common reasons for RTI denial under Section 8(1)(a)?",
        height=100
    )
    top_k = st.slider("Number of sources", 1, 20, 5)

    if st.button("Ask Question", key="qa_btn"):
        if len(question) < 10:
            st.error("Question must be at least 10 characters")
        else:
            with st.spinner("Searching rulings..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/api/qa",
                        json={"question": question, "top_k": top_k},
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Answer Generated")

                        st.subheader("Answer")
                        st.write(data["answer"])

                        if data.get("confidence"):
                            st.info(f"Confidence: {data['confidence']}")

                        st.subheader("Sources")
                        for i, source in enumerate(data["sources"], 1):
                            with st.expander(f"Source {i}: {source.get('order_number', 'N/A')}"):
                                st.json(source)
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")

# Tab 2: Draft Appeal
with tab2:
    st.header("Improve Appeal Draft")

    ministry = st.text_input("Ministry", placeholder="e.g., Ministry of Home Affairs")
    section = st.text_input("Section Cited", placeholder="e.g., 8(1)(a)")
    context = st.text_area(
        "Appeal Context",
        placeholder="Describe your RTI request and why it was denied...",
        height=200
    )

    if st.button("Generate Improvements", key="draft_btn"):
        if len(context) < 50:
            st.error("Context must be at least 50 characters")
        else:
            with st.spinner("Analyzing appeal..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/api/draft",
                        json={
                            "ministry": ministry,
                            "section_cited": section,
                            "context": context
                        },
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Improvements Generated")

                        st.subheader("Improved Query")
                        st.write(data["improved_query"])

                        st.subheader("Change Notes")
                        for note in data["change_notes"]:
                            st.info(f"**{note.get('original', 'Original')}** → **{note.get('revised', 'Revised')}**\n\n*Reason: {note.get('reason', '')}*")

                        st.subheader("Phrases to Avoid")
                        for phrase in data["avoid_phrases"]:
                            st.warning(f"❌ {phrase}")

                        st.subheader("Supporting Precedents")
                        for i, source in enumerate(data["sources"], 1):
                            with st.expander(f"Precedent {i}"):
                                st.markdown(f"**Case:** {source.get('order_number', 'N/A')}")
                                outcome = source.get('outcome', 'N/A')
                                outcome_color = "🟢" if outcome.lower() == "allowed" else "🔴" if outcome.lower() == "denied" else "⚪"
                                st.markdown(f"**Outcome:** {outcome_color} {outcome.title()}")
                                section = source.get('section', 'N/A')
                                if section and section != "NULL":
                                    st.markdown(f"**Section:** {section}")
                                st.markdown(f"**Relevance:** {source.get('relevance', 'N/A')}")
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")

# Tab 3: Predict Outcome
with tab3:
    st.header("Predict Appeal Outcome")

    col1, col2 = st.columns(2)

    with col1:
        pred_ministry = st.text_input("Ministry", key="pred_ministry")
        pred_section = st.text_input("Section Cited", key="pred_section")
        appeal_level = st.selectbox("Appeal Level", ["first_appeal", "second_appeal"])

    with col2:
        order_date = st.date_input("Order Date (optional)", value=None)

    raw_text = st.text_area(
        "Order Text",
        placeholder="Paste the full order text here (minimum 100 characters)...",
        height=200
    )

    if st.button("Predict Outcome", key="predict_btn"):
        if len(raw_text) < 100:
            st.error("Order text must be at least 100 characters")
        else:
            with st.spinner("Running prediction model..."):
                try:
                    payload = {
                        "ministry": pred_ministry,
                        "section_cited": pred_section,
                        "appeal_level": appeal_level,
                        "raw_text": raw_text
                    }
                    if order_date:
                        payload["order_date"] = order_date.isoformat()

                    response = requests.post(
                        f"{API_BASE}/api/predict",
                        json=payload,
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()

                        # Display prediction with color
                        if data["prediction"] == "allowed":
                            st.success(f"✅ Predicted: **{data['prediction'].upper()}**")
                        else:
                            st.error(f"❌ Predicted: **{data['prediction'].upper()}**")

                        st.metric("Probability", f"{data['probability']:.2%}")
                        st.info(f"Confidence: {data['confidence']}")
                        st.warning(data["disclaimer"])

                        if data.get("low_data_warning"):
                            st.warning("⚠️ Low data warning: Limited training data for this combination")

                        if data.get("model_card"):
                            with st.expander("Model Details"):
                                st.json(data["model_card"])
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")

# Tab 4: Analytics
with tab4:
    st.header("Analytics Dashboard")

    # Dashboard Overview Section
    st.subheader("📊 Dashboard Overview")
    if st.button("Load Dashboard Stats", key="dashboard_stats_btn"):
        with st.spinner("Loading dashboard statistics..."):
            try:
                response = requests.get(f"{API_BASE}/api/dashboard/stats", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Dashboard stats loaded")

                    # Overview metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Cases", data["overview"]["total_cases"])
                    with col2:
                        st.metric("Total Ministries", data["overview"]["total_ministries"])

                    # Outcome distribution
                    st.subheader("Outcome Distribution")
                    outcome_df = pd.DataFrame(data["overview"]["outcomes"])
                    st.dataframe(outcome_df, use_container_width=True)
                    st.bar_chart(outcome_df.set_index('outcome')['percentage'])

                    # Top sections
                    st.subheader("Top 5 Most Cited Sections")
                    sections_df = pd.DataFrame(data["top_sections"])
                    st.dataframe(sections_df, use_container_width=True)

                    # Top ministries
                    st.subheader("Top 5 Ministries by Case Volume")
                    ministries_df = pd.DataFrame(data["top_ministries"])
                    st.dataframe(ministries_df, use_container_width=True)
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Request failed: {str(e)}")

    st.markdown("---")
    st.subheader("📈 Detailed Analytics")

    analytics_type = st.selectbox(
        "Select Analytics",
        ["Denial Rates by Ministry", "Section Misuse Heatmap", "Override Trends"]
    )

    if analytics_type == "Denial Rates by Ministry":
        if st.button("Load Denial Rates"):
            with st.spinner("Loading data..."):
                try:
                    response = requests.get(f"{API_BASE}/api/analytics/denial-rates", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ Loaded {len(data)} ministries")

                        # Display as table
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)

                        # Bar chart
                        st.bar_chart(df.set_index('ministry')['denial_rate'])
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")

    elif analytics_type == "Section Misuse Heatmap":
        if st.button("Load Section Heatmap"):
            with st.spinner("Loading data..."):
                try:
                    response = requests.get(f"{API_BASE}/api/analytics/section-heatmap", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ Loaded {len(data)} section-ministry pairs")

                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")

    elif analytics_type == "Override Trends":
        if st.button("Load Override Trends"):
            with st.spinner("Loading data..."):
                try:
                    response = requests.get(f"{API_BASE}/api/analytics/override-trends", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ Loaded {len(data)} data points")

                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)

                        # Line chart
                        st.line_chart(df.set_index('date')['override_rate'])
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")

# Tab 5: Knowledge Graph
with tab5:
    st.header("Knowledge Graph Visualization")

    st.info("💡 Interactive graph showing relationships between ministries, RTI sections, and appeal outcomes.")

    if st.button("Load Enhanced Graph Data"):
        with st.spinner("Building enhanced knowledge graph..."):
            try:
                response = requests.get(f"{API_BASE}/api/dashboard/graph", timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ Enhanced graph loaded: {len(data['nodes'])} nodes, {len(data['edges'])} edges")

                    # Display metadata if available
                    if "metadata" in data:
                        st.subheader("Graph Statistics")
                        meta_cols = st.columns(3)
                        metadata = data["metadata"]
                        with meta_cols[0]:
                            st.metric("Total Nodes", metadata.get("total_nodes", len(data['nodes'])))
                        with meta_cols[1]:
                            st.metric("Total Edges", metadata.get("total_edges", len(data['edges'])))
                        with meta_cols[2]:
                            st.metric("Node Types", metadata.get("node_types", "N/A"))

                    # Create interactive visualization
                    st.subheader("Interactive Network Visualization")

                    # Legend first
                    legend_cols = st.columns(3)
                    with legend_cols[0]:
                        st.markdown("🔵 **Ministries** - Sized by case count")
                    with legend_cols[1]:
                        st.markdown("🟠 **RTI Sections** - Sized by citations")
                    with legend_cols[2]:
                        st.markdown("🟢🔴 **Outcomes** - Green=Allowed, Red=Denied")

                    # Create pyvis network with better readability settings
                    net = Network(
                        height="750px",
                        width="100%",
                        bgcolor="#1e1e1e",
                        font_color="white"
                    )

                    # Better physics for spacing and readability
                    net.barnes_hut(
                        gravity=-15000,
                        central_gravity=0.2,
                        spring_length=300,
                        spring_strength=0.001,
                        damping=0.15,
                        overlap=0
                    )

                    # Add nodes with better visibility
                    for node in data["nodes"]:
                        node_id = node.get("id", "")
                        node_label = node.get("label", node_id)
                        node_color = node.get("color", "#97c2fc")
                        node_size = max(node.get("size", 10) * 1.5, 20)  # Larger, more visible
                        node_title = f"<b>{node.get('type', 'unknown').upper()}</b><br>{node_label}"

                        net.add_node(
                            node_id,
                            label=node_label,
                            color=node_color,
                            size=node_size,
                            title=node_title,
                            font={"size": 16, "color": "white", "face": "arial", "bold": True}
                        )

                    # Add edges with better visibility
                    for edge in data["edges"]:
                        source = edge.get("source", "")
                        target = edge.get("target", "")
                        edge_color = edge.get("color", "#848484")
                        edge_width = max(edge.get("width", 1) * 2, 2)  # Thicker edges
                        edge_title = edge.get("label", f"{source} → {target}")

                        net.add_edge(
                            source,
                            target,
                            color=edge_color,
                            width=edge_width,
                            title=edge_title,
                            smooth={"type": "continuous"}
                        )

                    # Save and display
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w') as f:
                        net.save_graph(f.name)
                        with open(f.name, 'r') as html_file:
                            html_content = html_file.read()
                        components.html(html_content, height=800, scrolling=True)

                    st.caption("💡 Drag nodes to rearrange • Scroll to zoom • Click nodes for details")

                    # Node type breakdown
                    st.subheader("Node Type Distribution")
                    node_types = {}
                    for node in data["nodes"]:
                        node_type = node.get("type", "unknown")
                        node_types[node_type] = node_types.get(node_type, 0) + 1

                    type_df = pd.DataFrame([
                        {"type": k, "count": v} for k, v in node_types.items()
                    ])
                    st.dataframe(type_df, use_container_width=True)

                    # Detailed data in expanders
                    col1, col2 = st.columns(2)

                    with col1:
                        with st.expander("View Node Details"):
                            nodes_preview = data["nodes"][:10]
                            for node in nodes_preview:
                                st.json(node)
                            st.caption(f"Showing 10 of {len(data['nodes'])} nodes")

                    with col2:
                        with st.expander("View Edge Details"):
                            edges_preview = data["edges"][:10]
                            for edge in edges_preview:
                                st.json(edge)
                            st.caption(f"Showing 10 of {len(data['edges'])} edges")

                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Request failed: {str(e)}")

# Footer
st.markdown("---")
st.caption("RTI-Lens API Test Interface | Make sure API is running on http://localhost:8001")
