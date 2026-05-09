"""
Interactive Timeline Visualizer for RTI-Lens
Streamlit-native component for visualizing case timelines and workflow progression
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Optional


class TimelineVisualizer:
    """
    Interactive timeline visualization for RTI cases and workflows
    """

    def __init__(self):
        self.colors = {
            'completed': '#10b981',  # green
            'in_progress': '#3b82f6',  # blue
            'pending': '#6b7280',  # gray
            'denied': '#ef4444',  # red
            'allowed': '#10b981',  # green
            'partially_allowed': '#f59e0b',  # amber
        }

    def render_case_timeline(self, cases: List[Dict[str, Any]]):
        """
        Render an interactive timeline of RTI cases

        Args:
            cases: List of case dictionaries with order_date, ministry, outcome, etc.
        """
        if not cases:
            st.warning("No cases to display")
            return

        # Convert to DataFrame
        df = pd.DataFrame(cases)

        # Ensure order_date is datetime
        if 'order_date' in df.columns:
            df['order_date'] = pd.to_datetime(df['order_date'])
            df = df.sort_values('order_date')

        # Create timeline visualization
        st.subheader("📅 Case Timeline")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Cases", len(df))
        with col2:
            if 'appeal_outcome' in df.columns:
                allowed = len(df[df['appeal_outcome'] == 'allowed'])
                st.metric("Allowed", allowed, delta=f"{allowed/len(df)*100:.1f}%")
        with col3:
            if 'appeal_outcome' in df.columns:
                denied = len(df[df['appeal_outcome'] == 'denied'])
                st.metric("Denied", denied, delta=f"{denied/len(df)*100:.1f}%")
        with col4:
            if 'order_date' in df.columns:
                date_range = (df['order_date'].max() - df['order_date'].min()).days
                st.metric("Date Range", f"{date_range} days")

        # Interactive scatter plot timeline
        if 'order_date' in df.columns and 'appeal_outcome' in df.columns:
            fig = px.scatter(
                df,
                x='order_date',
                y='ministry' if 'ministry' in df.columns else 'section_cited',
                color='appeal_outcome',
                size=[10] * len(df),
                hover_data=['order_number', 'section_cited'] if 'order_number' in df.columns else None,
                title="Cases Over Time by Ministry",
                color_discrete_map={
                    'allowed': self.colors['allowed'],
                    'denied': self.colors['denied'],
                    'partially_allowed': self.colors['partially_allowed']
                }
            )
            fig.update_layout(
                height=500,
                xaxis_title="Order Date",
                yaxis_title="Ministry",
                hovermode='closest',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

        # Monthly distribution
        if 'order_date' in df.columns:
            st.subheader("📊 Monthly Case Distribution")
            df['month'] = df['order_date'].dt.to_period('M').astype(str)
            monthly_counts = df.groupby('month').size().reset_index(name='count')

            fig_bar = px.bar(
                monthly_counts,
                x='month',
                y='count',
                title="Cases per Month",
                labels={'month': 'Month', 'count': 'Number of Cases'}
            )
            fig_bar.update_traces(marker_color='#3b82f6')
            fig_bar.update_layout(height=300)
            st.plotly_chart(fig_bar, use_container_width=True)

    def render_workflow_timeline(self, workflow_data: List[Dict[str, Any]]):
        """
        Render workflow progression timeline (Gantt-style)

        Args:
            workflow_data: List of workflow actions with timestamps and stages
        """
        if not workflow_data:
            st.warning("No workflow data to display")
            return

        st.subheader("🔄 Workflow Progression")

        # Convert to DataFrame
        df = pd.DataFrame(workflow_data)

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

        # Create Gantt-style chart
        if 'stage' in df.columns and 'timestamp' in df.columns:
            # Group by session
            if 'session_id' in df.columns:
                sessions = df['session_id'].unique()

                # Show session selector if multiple sessions
                if len(sessions) > 1:
                    selected_session = st.selectbox(
                        "Select Session",
                        sessions,
                        format_func=lambda x: f"Session {x[:8]}..."
                    )
                    df_filtered = df[df['session_id'] == selected_session]
                else:
                    df_filtered = df

                # Create timeline visualization
                stages = df_filtered['stage'].unique()
                stage_colors = {
                    'initiated': '#6b7280',
                    'retrieval': '#3b82f6',
                    'generation': '#8b5cf6',
                    'completed': '#10b981',
                    'error': '#ef4444'
                }

                fig = go.Figure()

                for i, stage in enumerate(stages):
                    stage_data = df_filtered[df_filtered['stage'] == stage]
                    if not stage_data.empty:
                        fig.add_trace(go.Scatter(
                            x=stage_data['timestamp'],
                            y=[stage] * len(stage_data),
                            mode='markers+lines',
                            name=stage.title(),
                            marker=dict(
                                size=15,
                                color=stage_colors.get(stage, '#6b7280'),
                                symbol='circle'
                            ),
                            line=dict(
                                color=stage_colors.get(stage, '#6b7280'),
                                width=2
                            )
                        ))

                fig.update_layout(
                    title="Workflow Stage Progression",
                    xaxis_title="Time",
                    yaxis_title="Stage",
                    height=400,
                    hovermode='closest',
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

                # Stage duration metrics
                st.subheader("⏱️ Stage Durations")
                if len(df_filtered) > 1:
                    df_filtered['duration'] = df_filtered['timestamp'].diff().dt.total_seconds()

                    cols = st.columns(len(stages))
                    for i, stage in enumerate(stages):
                        stage_duration = df_filtered[df_filtered['stage'] == stage]['duration'].sum()
                        with cols[i]:
                            st.metric(
                                stage.title(),
                                f"{stage_duration:.1f}s" if stage_duration < 60 else f"{stage_duration/60:.1f}m"
                            )

    def render_orbital_timeline(self, timeline_items: List[Dict[str, Any]]):
        """
        Render an orbital/radial timeline visualization
        Streamlit-native alternative to the React component

        Args:
            timeline_items: List of items with id, title, date, status, energy, etc.
        """
        st.subheader("🌐 Orbital Timeline View")

        if not timeline_items:
            st.warning("No timeline items to display")
            return

        # Create circular layout using plotly
        import numpy as np

        n_items = len(timeline_items)
        angles = np.linspace(0, 2 * np.pi, n_items, endpoint=False)

        # Calculate positions
        radius = 1
        x_pos = radius * np.cos(angles)
        y_pos = radius * np.sin(angles)

        # Prepare data
        titles = [item.get('title', f"Item {i}") for i, item in enumerate(timeline_items)]
        statuses = [item.get('status', 'pending') for item in timeline_items]
        energies = [item.get('energy', 50) for item in timeline_items]
        dates = [item.get('date', 'N/A') for item in timeline_items]
        contents = [item.get('content', '') for item in timeline_items]

        # Color mapping
        status_colors = {
            'completed': self.colors['completed'],
            'in_progress': self.colors['in_progress'],
            'pending': self.colors['pending']
        }
        colors = [status_colors.get(s, '#6b7280') for s in statuses]

        # Create figure
        fig = go.Figure()

        # Add center node
        fig.add_trace(go.Scatter(
            x=[0],
            y=[0],
            mode='markers',
            marker=dict(size=30, color='#8b5cf6', line=dict(width=2, color='white')),
            name='Center',
            hoverinfo='skip'
        ))

        # Add orbital nodes
        fig.add_trace(go.Scatter(
            x=x_pos,
            y=y_pos,
            mode='markers+text',
            marker=dict(
                size=[e * 0.5 + 20 for e in energies],
                color=colors,
                line=dict(width=2, color='white')
            ),
            text=titles,
            textposition='top center',
            textfont=dict(size=10, color='white'),
            hovertemplate='<b>%{text}</b><br>' +
                         'Date: ' + '<br>'.join([str(d) for d in dates]) + '<br>' +
                         'Status: ' + '<br>'.join(statuses) + '<br>' +
                         'Energy: %{marker.size}<br>' +
                         '<extra></extra>',
            name='Timeline Items'
        ))

        # Add connecting lines to center
        for i in range(n_items):
            fig.add_trace(go.Scatter(
                x=[0, x_pos[i]],
                y=[0, y_pos[i]],
                mode='lines',
                line=dict(color='rgba(255,255,255,0.2)', width=1),
                hoverinfo='skip',
                showlegend=False
            ))

        # Update layout
        fig.update_layout(
            title="Orbital Timeline Visualization",
            showlegend=False,
            height=600,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-1.5, 1.5]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-1.5, 1.5]
            ),
            plot_bgcolor='#0f172a',
            paper_bgcolor='#0f172a',
            font=dict(color='white')
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display detailed cards below
        st.subheader("📋 Timeline Details")

        # Create columns for cards
        cols = st.columns(min(3, len(timeline_items)))
        for i, item in enumerate(timeline_items):
            with cols[i % 3]:
                status = item.get('status', 'pending')
                status_emoji = {
                    'completed': '✅',
                    'in_progress': '🔄',
                    'pending': '⏳'
                }.get(status, '⏳')

                with st.expander(f"{status_emoji} {item.get('title', 'Item')}"):
                    st.markdown(f"**Date:** {item.get('date', 'N/A')}")
                    st.markdown(f"**Status:** {status.replace('_', ' ').title()}")
                    st.markdown(f"**Content:** {item.get('content', 'No content')}")

                    if 'energy' in item:
                        st.progress(item['energy'] / 100)
                        st.caption(f"Energy: {item['energy']}%")

                    if 'related_ids' in item and item['related_ids']:
                        st.caption(f"🔗 Connected to: {len(item['related_ids'])} items")

    def render_section_timeline(self, section_data: List[Dict[str, Any]]):
        """
        Render timeline of section citations over time

        Args:
            section_data: List of cases with section_cited and order_date
        """
        st.subheader("📜 Section Citation Timeline")

        if not section_data:
            st.warning("No section data to display")
            return

        df = pd.DataFrame(section_data)

        if 'order_date' in df.columns and 'section_cited' in df.columns:
            df['order_date'] = pd.to_datetime(df['order_date'])
            df = df.sort_values('order_date')

            # Get top sections
            top_sections = df['section_cited'].value_counts().head(10).index.tolist()
            df_filtered = df[df['section_cited'].isin(top_sections)]

            # Create line chart
            section_timeline = df_filtered.groupby([
                df_filtered['order_date'].dt.to_period('M').astype(str),
                'section_cited'
            ]).size().reset_index(name='count')

            fig = px.line(
                section_timeline,
                x=section_timeline.columns[0],
                y='count',
                color='section_cited',
                title="Top 10 Section Citations Over Time",
                labels={section_timeline.columns[0]: 'Month', 'count': 'Citations'}
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Section summary
            with st.expander("📊 Section Statistics"):
                section_stats = df['section_cited'].value_counts().head(10).reset_index()
                section_stats.columns = ['Section', 'Count']
                st.dataframe(section_stats, use_container_width=True)


def create_sample_timeline_data() -> List[Dict[str, Any]]:
    """
    Create sample timeline data for demonstration
    """
    from datetime import datetime, timedelta

    base_date = datetime.now() - timedelta(days=120)

    return [
        {
            'id': 1,
            'title': 'Case Filed',
            'date': (base_date).strftime('%b %Y'),
            'content': 'RTI application submitted to Ministry of Finance',
            'status': 'completed',
            'energy': 100,
            'related_ids': [2]
        },
        {
            'id': 2,
            'title': 'PIO Response',
            'date': (base_date + timedelta(days=30)).strftime('%b %Y'),
            'content': 'PIO denied request citing Section 8(1)(a)',
            'status': 'completed',
            'energy': 90,
            'related_ids': [1, 3]
        },
        {
            'id': 3,
            'title': 'First Appeal',
            'date': (base_date + timedelta(days=60)).strftime('%b %Y'),
            'content': 'First appeal filed with FAA',
            'status': 'completed',
            'energy': 75,
            'related_ids': [2, 4]
        },
        {
            'id': 4,
            'title': 'FAA Hearing',
            'date': (base_date + timedelta(days=90)).strftime('%b %Y'),
            'content': 'Hearing scheduled and conducted',
            'status': 'in_progress',
            'energy': 60,
            'related_ids': [3, 5]
        },
        {
            'id': 5,
            'title': 'CIC Appeal',
            'date': (base_date + timedelta(days=120)).strftime('%b %Y'),
            'content': 'Second appeal filed with CIC',
            'status': 'pending',
            'energy': 30,
            'related_ids': [4]
        }
    ]
