"""
Streamlit Frontend for RTI-Lens API Testing
"""
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import os
from pyvis.network import Network
import tempfile
import sys
sys.path.insert(0, '.')
from backend.database import SessionLocal
from components.timeline_visualizer import TimelineVisualizer, create_sample_timeline_data

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")

# Initialize session state
if 'session_history' not in st.session_state:
    st.session_state.session_history = []

st.set_page_config(page_title="RTI-Lens Test UI", layout="wide")
st.title("🔍 RTI-Lens API Test Interface")

# Sidebar for API health and session info
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

    st.markdown("---")
    st.header("Session History")

    if st.button("Refresh Sessions"):
        try:
            db = SessionLocal()
            # Get recent sessions
            from backend.models.workflow import WorkflowSession
            sessions = db.query(WorkflowSession).order_by(
                WorkflowSession.created_at.desc()
            ).limit(10).all()

            st.session_state.session_history = [
                {
                    'session_id': s.session_id,
                    'thread_id': s.thread_id,
                    'type': s.workflow_type,
                    'stage': s.workflow_stage,
                    'created': s.created_at.strftime('%H:%M:%S') if s.created_at else 'N/A'
                }
                for s in sessions
            ]
            db.close()
            st.success(f"✅ Loaded {len(sessions)} sessions")
        except Exception as e:
            st.error(f"Failed to load sessions: {str(e)}")

    if st.session_state.session_history:
        st.caption(f"Recent {len(st.session_state.session_history)} sessions:")
        for sess in st.session_state.session_history[:5]:
            with st.expander(f"{sess['type']} - {sess['created']}"):
                st.text(f"Stage: {sess['stage']}")
                st.text(f"Session: {sess['session_id'][:8]}...")
                if sess['thread_id']:
                    st.text(f"Thread: {sess['thread_id'][:8]}...")
                    st.caption("🔗 Backboard enabled")

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 Q&A",
    "✨ RTI Query Assistant",
    "🎯 Predict Outcome",
    "📊 Analytics",
    "🕸️ Knowledge Graph",
    "📅 Timeline"
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
                        timeout=60
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

# Tab 2: RTI Query Assistant
with tab2:
    st.header("✨ RTI Query Assistant")
    st.markdown("Improve your RTI query quality with AI-powered optimization")

    # Import query optimizer
    import sys
    sys.path.insert(0, '/Users/mohitsahoo/Desktop/IDP')
    from app.services.query_optimizer import QueryOptimizer

    user_query = st.text_area(
        "Describe your issue or draft RTI query",
        placeholder="e.g., Why was electricity cut in my area?\n\nOr: I want information about road repair delays in my locality.",
        height=150,
        help="Enter your question or draft RTI request. The assistant will help make it more effective."
    )

    if st.button("🔍 Optimize RTI Query", key="optimize_query_btn"):
        if len(user_query) < 10:
            st.error("Query must be at least 10 characters")
        else:
            with st.spinner("Analyzing and optimizing your query..."):
                try:
                    optimizer = QueryOptimizer()
                    result = optimizer.optimize(user_query)

                    # Ministry and Section Recommendations (TOP)
                    st.subheader("📋 Filing Recommendations")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**🏛️ Suggested Ministry**")
                        ministry = result.get("ministry_suggestion", {})
                        confidence_color = "🟢" if ministry.get("confidence", 0) > 0.7 else "🟡" if ministry.get("confidence", 0) > 0.4 else "🔴"
                        st.info(f"{confidence_color} **{ministry.get('primary_ministry', 'N/A')}**")
                        st.caption(f"Confidence: {ministry.get('confidence', 0):.0%} | {ministry.get('reasoning', 'No reasoning available')}")

                        if ministry.get("alternative_ministries"):
                            with st.expander("Alternative ministries"):
                                for alt in ministry["alternative_ministries"]:
                                    st.text(f"• {alt}")

                    with col2:
                        st.markdown("**📜 Sections to Cite**")
                        sections = result.get("section_recommendations", {})

                        for sec in sections.get("primary_sections", []):
                            st.success(f"✓ **{sec.get('section', 'N/A')}**")
                            st.caption(sec.get('reason', ''))

                        if sections.get("optional_sections"):
                            with st.expander("Optional sections"):
                                for sec in sections["optional_sections"]:
                                    st.text(f"• {sec.get('section', 'N/A')}: {sec.get('reason', '')}")

                    st.markdown("---")

                    # Display issues detected
                    if result.get("issues_detected"):
                        st.subheader("⚠️ Issues Detected")
                        for issue in result["issues_detected"]:
                            severity_emoji = "🔴" if issue["severity"] == "high" else "🟡" if issue["severity"] == "medium" else "🟢"
                            with st.expander(f"{severity_emoji} {issue['type'].replace('_', ' ').title()}", expanded=True):
                                st.markdown(f"**Issue:** {issue['description']}")
                                st.markdown(f"**Suggestion:** {issue['suggestion']}")

                    st.markdown("---")

                    # Side-by-side comparison
                    st.subheader("📝 Query Comparison")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Original Query**")
                        st.info(result.get("original_query", user_query))

                    with col2:
                        st.markdown("**Optimized Query**")
                        st.success(result.get("optimized_query", user_query))

                    # Improvements made
                    if result.get("improvements_made"):
                        st.subheader("✅ Improvements Made")
                        for improvement in result["improvements_made"]:
                            st.markdown(f"- {improvement}")

                    st.markdown("---")

                    # Confidence scores (only if optimization completed)
                    if result.get("status") == "optimized" and "scores" in result:
                        st.subheader("📊 Quality Scores")
                        scores = result["scores"]

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Clarity Score",
                                f"{scores['optimized_clarity']:.0%}",
                                delta=f"{(scores['optimized_clarity'] - scores['original_clarity']):.0%}"
                            )

                        with col2:
                            st.metric(
                                "Legal Specificity",
                                f"{scores['legal_specificity']:.0%}"
                            )

                        with col3:
                            st.metric(
                                "Retrieval Quality",
                                f"{scores['retrieval_quality_prediction']:.0%}"
                            )
                    elif result.get("status") == "needs_clarification":
                        st.warning("⚠️ Additional information needed to complete optimization")
                        if result.get("clarification_request"):
                            st.info(result["clarification_request"])
                        if result.get("missing_fields"):
                            st.caption(f"Missing: {', '.join(result['missing_fields'])}")

                    # Relevant precedents
                    if result.get("relevant_precedents"):
                        st.markdown("---")
                        st.subheader("📚 Relevant Precedents")
                        st.caption("Similar cases from the CIC database that support your request")

                        for i, precedent in enumerate(result["relevant_precedents"], 1):
                            with st.expander(f"📄 Precedent {i}: {precedent.get('order_number', 'N/A')} (Relevance: {precedent.get('relevance_score', 0):.2f})", expanded=i==1):
                                col1, col2 = st.columns([2, 1])

                                with col1:
                                    st.markdown(f"**Ministry:** {precedent.get('ministry', 'N/A')}")
                                    if precedent.get('section_cited'):
                                        st.markdown(f"**Section Cited:** {precedent['section_cited']}")

                                with col2:
                                    if precedent.get('order_date'):
                                        st.markdown(f"**Date:** {precedent['order_date']}")

                                st.markdown("**Excerpt:**")
                                st.text(precedent.get('text_preview', 'No preview available'))

                                st.caption(f"💡 This precedent shows how similar requests were handled")

                    # Metadata extracted
                    if result.get("metadata"):
                        with st.expander("🔍 Extracted Metadata"):
                            st.json(result["metadata"])

                except Exception as e:
                    st.error(f"Optimization failed: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

    # Help section
    with st.expander("💡 Tips for Writing Effective RTI Queries"):
        st.markdown("""
        **Good RTI queries are:**
        - **Document-oriented**: Request specific records, files, or documents
        - **Specific**: Include dates, departments, and clear scope
        - **Neutral**: Use factual language, avoid emotional terms
        - **Actionable**: Ask for information that exists in records

        **Examples:**

        ❌ **Poor:** "Why was my electricity cut?"
        ✅ **Good:** "Provide records regarding power supply disruptions in Ward 5, including:
        1. Maintenance schedules for January-March 2024
        2. Complaint logs and resolution reports
        3. Communication with the electricity board"

        ❌ **Poor:** "Give me all information about road repairs"
        ✅ **Good:** "Provide documents regarding road repair works on MG Road between 2023-2024, including:
        1. Sanctioned project details
        2. Contractor assignment records
        3. Expenditure reports
        4. Project completion timelines"
        """)

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
                    if order_date is not None:
                        payload["order_date"] = str(order_date)

                    response = requests.post(
                        f"{API_BASE}/api/predict",
                        json=payload,
                        timeout=60
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
                        bgcolor="#1e1e1e"
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

# Tab 6: Timeline Visualization
with tab6:
    st.header("📅 Interactive Timeline Visualization")

    st.info("💡 Visualize RTI cases, workflows, and trends over time with interactive timelines.")

    # Initialize timeline visualizer
    visualizer = TimelineVisualizer()

    # Timeline mode selector
    timeline_mode = st.selectbox(
        "Select Timeline View",
        [
            "Case Timeline",
            "Workflow Progression",
            "Orbital Timeline",
            "Section Citation Timeline",
            "Demo: Sample Timeline"
        ]
    )

    if timeline_mode == "Case Timeline":
        st.subheader("📊 Case Timeline Analysis")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            limit = st.number_input("Number of cases", min_value=10, max_value=500, value=100)
        with col2:
            outcome_filter = st.selectbox("Filter by outcome", ["All", "allowed", "denied", "partially_allowed"])
        with col3:
            ministry_filter = st.text_input("Filter by ministry (optional)")

        if st.button("Load Case Timeline", key="load_case_timeline"):
            with st.spinner("Loading case data..."):
                try:
                    db = SessionLocal()
                    from backend.models import Case

                    # Build query
                    query = db.query(Case).filter(Case.order_date.isnot(None))

                    if outcome_filter != "All":
                        query = query.filter(Case.appeal_outcome == outcome_filter)

                    if ministry_filter:
                        from backend.models import Ministry
                        ministry = db.query(Ministry).filter(
                            Ministry.name.ilike(f"%{ministry_filter}%")
                        ).first()
                        if ministry:
                            query = query.filter(Case.ministry_id == ministry.id)

                    # Execute query
                    cases = query.order_by(Case.order_date.desc()).limit(limit).all()

                    if cases:
                        # Convert to dict format
                        case_data = [
                            {
                                'order_number': c.order_number,
                                'order_date': c.order_date,
                                'ministry': c.ministry.name if c.ministry else 'Unknown',
                                'section_cited': c.section_cited,
                                'appeal_outcome': c.appeal_outcome.value if c.appeal_outcome else 'unknown',
                                'appeal_level': c.appeal_level.value if c.appeal_level else 'unknown'
                            }
                            for c in cases
                        ]

                        st.success(f"✅ Loaded {len(case_data)} cases")
                        visualizer.render_case_timeline(case_data)
                    else:
                        st.warning("No cases found matching the criteria")

                    db.close()

                except Exception as e:
                    st.error(f"Failed to load case data: {str(e)}")
                    import traceback
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())

    elif timeline_mode == "Workflow Progression":
        st.subheader("🔄 Workflow Timeline")

        if st.button("Load Workflow Data", key="load_workflow_timeline"):
            with st.spinner("Loading workflow data..."):
                try:
                    db = SessionLocal()
                    from backend.models.workflow import WorkflowAction

                    # Get recent workflow actions
                    actions = db.query(WorkflowAction).order_by(
                        WorkflowAction.timestamp.desc()
                    ).limit(100).all()

                    if actions:
                        workflow_data = [
                            {
                                'session_id': a.session_id,
                                'stage': a.action_type,
                                'timestamp': a.timestamp,
                                'details': a.action_data
                            }
                            for a in actions
                        ]

                        st.success(f"✅ Loaded {len(workflow_data)} workflow actions")
                        visualizer.render_workflow_timeline(workflow_data)
                    else:
                        st.warning("No workflow data found")

                    db.close()

                except Exception as e:
                    st.error(f"Failed to load workflow data: {str(e)}")
                    st.caption("Note: Workflow tracking may not be enabled or no data exists yet")

    elif timeline_mode == "Orbital Timeline":
        st.subheader("🌐 Orbital Timeline View")
        st.caption("Circular visualization showing case progression and relationships")

        if st.button("Load Recent Cases for Orbital View", key="load_orbital"):
            with st.spinner("Loading case data..."):
                try:
                    db = SessionLocal()
                    from backend.models import Case

                    # Get recent cases
                    cases = db.query(Case).filter(
                        Case.order_date.isnot(None)
                    ).order_by(Case.order_date.desc()).limit(10).all()

                    if cases:
                        # Convert to orbital timeline format
                        timeline_items = []
                        for i, case in enumerate(cases):
                            status = 'completed' if case.appeal_outcome else 'pending'
                            if case.appeal_outcome:
                                if case.appeal_outcome.value == 'allowed':
                                    status = 'completed'
                                elif case.appeal_outcome.value == 'denied':
                                    status = 'pending'
                                else:
                                    status = 'in_progress'

                            # Calculate energy based on outcome
                            energy = 100 if status == 'completed' else 50 if status == 'in_progress' else 30

                            timeline_items.append({
                                'id': i + 1,
                                'title': case.order_number[:20] + '...' if len(case.order_number) > 20 else case.order_number,
                                'date': case.order_date.strftime('%b %Y') if case.order_date else 'N/A',
                                'content': f"{case.ministry.name if case.ministry else 'Unknown'} - {case.section_cited or 'No section'}",
                                'status': status,
                                'energy': energy,
                                'related_ids': [i] if i > 0 else []
                            })

                        st.success(f"✅ Loaded {len(timeline_items)} cases")
                        visualizer.render_orbital_timeline(timeline_items)
                    else:
                        st.warning("No cases found")

                    db.close()

                except Exception as e:
                    st.error(f"Failed to load case data: {str(e)}")

    elif timeline_mode == "Section Citation Timeline":
        st.subheader("📜 Section Citation Trends")

        if st.button("Load Section Timeline", key="load_section_timeline"):
            with st.spinner("Loading section data..."):
                try:
                    db = SessionLocal()
                    from backend.models import Case

                    # Get cases with sections
                    cases = db.query(Case).filter(
                        Case.section_cited.isnot(None),
                        Case.order_date.isnot(None)
                    ).order_by(Case.order_date.desc()).limit(500).all()

                    if cases:
                        section_data = [
                            {
                                'order_date': c.order_date,
                                'section_cited': c.section_cited,
                                'ministry': c.ministry.name if c.ministry else 'Unknown',
                                'outcome': c.appeal_outcome.value if c.appeal_outcome else 'unknown'
                            }
                            for c in cases
                        ]

                        st.success(f"✅ Loaded {len(section_data)} cases with section citations")
                        visualizer.render_section_timeline(section_data)
                    else:
                        st.warning("No section data found")

                    db.close()

                except Exception as e:
                    st.error(f"Failed to load section data: {str(e)}")

    elif timeline_mode == "Demo: Sample Timeline":
        st.subheader("🎨 Demo: Sample Timeline")
        st.caption("Interactive demonstration with sample data")

        # Create sample data
        sample_data = create_sample_timeline_data()

        st.success(f"✅ Loaded {len(sample_data)} sample timeline items")

        # Show all visualization types with sample data
        visualizer.render_orbital_timeline(sample_data)

        st.markdown("---")

        # Additional demo visualizations
        st.subheader("📊 Additional Views")

        demo_tabs = st.tabs(["Workflow View", "Statistics"])

        with demo_tabs[0]:
            st.caption("Sample workflow progression")
            sample_workflow = [
                {
                    'session_id': 'demo-session-001',
                    'stage': 'initiated',
                    'timestamp': pd.Timestamp.now() - pd.Timedelta(minutes=10)
                },
                {
                    'session_id': 'demo-session-001',
                    'stage': 'retrieval',
                    'timestamp': pd.Timestamp.now() - pd.Timedelta(minutes=8)
                },
                {
                    'session_id': 'demo-session-001',
                    'stage': 'generation',
                    'timestamp': pd.Timestamp.now() - pd.Timedelta(minutes=5)
                },
                {
                    'session_id': 'demo-session-001',
                    'stage': 'completed',
                    'timestamp': pd.Timestamp.now() - pd.Timedelta(minutes=2)
                }
            ]
            visualizer.render_workflow_timeline(sample_workflow)

        with demo_tabs[1]:
            st.caption("Timeline statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Items", len(sample_data))
            with col2:
                completed = len([x for x in sample_data if x['status'] == 'completed'])
                st.metric("Completed", completed, delta=f"{completed/len(sample_data)*100:.0f}%")
            with col3:
                avg_energy = sum(x['energy'] for x in sample_data) / len(sample_data)
                st.metric("Avg Energy", f"{avg_energy:.0f}%")

    # Help section
    with st.expander("💡 Timeline Visualization Guide"):
        st.markdown("""
        ### Timeline Views

        **Case Timeline**
        - Visualize RTI cases over time
        - Filter by outcome, ministry, or date range
        - See monthly distribution and trends

        **Workflow Progression**
        - Track workflow stages (initiated → retrieval → generation → completed)
        - View stage durations and bottlenecks
        - Monitor session performance

        **Orbital Timeline**
        - Circular visualization showing relationships
        - Node size represents "energy" or importance
        - Colors indicate status (green=completed, blue=in-progress, gray=pending)

        **Section Citation Timeline**
        - Track which RTI sections are cited over time
        - Identify trending sections
        - Compare citation patterns across ministries

        ### Tips
        - Use filters to focus on specific time periods or categories
        - Hover over data points for detailed information
        - Click and drag on charts to zoom in
        - Export data using the download buttons
        """)

# Footer
st.markdown("---")
st.caption("RTI-Lens API Test Interface | Make sure API is running on http://localhost:8001")
