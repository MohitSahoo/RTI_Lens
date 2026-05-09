"""
Workflow Session Models for RTI Lens

Manages persistent workflow sessions with Backboard.io integration.
Stores session state, workflow stages, and retrieval history.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
from backend.database import Base


class WorkflowSession(Base):
    """
    Workflow session model for tracking RTI workflows with Backboard integration.

    Stores:
    - Session metadata
    - Backboard thread_id for continuity
    - Workflow stage tracking
    - User context
    - Retrieval and generation history
    """
    __tablename__ = "workflow_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    thread_id = Column(String(255), nullable=True, index=True)  # Backboard thread ID

    # Workflow metadata
    workflow_type = Column(String(50), nullable=False)  # "rti_qa", "rti_draft", "appeal"
    workflow_stage = Column(String(50), nullable=False, default="initiated")  # "initiated", "drafting", "review", "appeal", "completed"

    # User context
    user_id = Column(String(255), nullable=True, index=True)
    user_ip = Column(String(50), nullable=True)

    # Session state
    is_active = Column(Boolean, default=True, nullable=False)
    session_metadata = Column(JSON, nullable=True)  # Additional workflow-specific data

    # History tracking
    retrieval_history = Column(JSON, nullable=True)  # List of retrieval operations
    generation_history = Column(JSON, nullable=True)  # List of generation operations

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<WorkflowSession(id={self.id}, session_id={self.session_id}, type={self.workflow_type}, stage={self.workflow_stage})>"


class WorkflowAction(Base):
    """
    Individual workflow actions for detailed tracking.

    Stores each action taken during a workflow session.
    """
    __tablename__ = "workflow_actions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)

    # Action details
    action_type = Column(String(50), nullable=False)  # "retrieval", "generation", "stage_change"
    action_name = Column(String(100), nullable=False)  # Specific action name

    # Action data
    input_data = Column(JSON, nullable=True)  # Input to the action
    output_data = Column(JSON, nullable=True)  # Output from the action

    # Metadata
    duration_ms = Column(Integer, nullable=True)  # Action duration in milliseconds
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<WorkflowAction(id={self.id}, session_id={self.session_id}, type={self.action_type}, name={self.action_name})>"
