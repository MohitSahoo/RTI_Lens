"""
Session Persistence Layer for Workflow Management

Provides database operations for workflow sessions integrated with Backboard.io.
Handles session creation, restoration, updates, and history tracking.
"""
import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.workflow import WorkflowSession, WorkflowAction
from backend.utils.backboard_client import backboard_client

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages workflow sessions with Backboard.io integration.

    Responsibilities:
    - Create new workflow sessions
    - Restore existing sessions
    - Update session state
    - Track retrieval and generation history
    - Coordinate with Backboard for continuity
    """

    @staticmethod
    async def create_session(
        db: Session,
        workflow_type: str,
        user_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowSession:
        """
        Create a new workflow session, coordinating with Backboard.io.

        Args:
            db: Database session
            workflow_type: Type of workflow (e.g., "rti_qa", "rti_draft", "appeal")
            user_id: Optional user identifier
            user_ip: Optional user IP address
            metadata: Additional workflow metadata

        Returns:
            The created WorkflowSession object
        """
        thread_id = None
        try:
            thread_id = await backboard_client.create_workflow_session(
                workflow_type=workflow_type,
                user_id=user_id,
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Backboard thread creation failed: {e}")

        session_id = str(uuid.uuid4())
        new_session = WorkflowSession(
            session_id=session_id,
            thread_id=thread_id,
            workflow_type=workflow_type,
            user_id=user_id,
            user_ip=user_ip,
            workflow_stage="initiated",  # Initial stage
            session_metadata=metadata,
            retrieval_history=[], # Initialize empty lists for JSON fields
            generation_history=[]
        )

        try:
            db.add(new_session)
            db.commit()
            db.refresh(new_session)  # Ensure the object is populated with DB defaults like IDs
            logger.info(f"Created workflow session {session_id} with Backboard thread {thread_id}")
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to persist workflow session to DB: {e}")
            # Return the in-memory object so the workflow can continue

        return new_session

    @staticmethod
    def get_session(
        db: Session,
        session_id: str
    ) -> Optional[WorkflowSession]:
        """
        Retrieve workflow session by session_id.

        Args:
            db: Database session
            session_id: Session identifier

        Returns:
            WorkflowSession if found, None otherwise
        """
        return db.query(WorkflowSession).filter(
            WorkflowSession.session_id == session_id
        ).first()

    @staticmethod
    def get_session_by_thread(
        db: Session,
        thread_id: str
    ) -> Optional[WorkflowSession]:
        """
        Retrieve workflow session by Backboard thread_id.

        Args:
            db: Database session
            thread_id: Backboard thread identifier

        Returns:
            WorkflowSession if found, None otherwise
        """
        return db.query(WorkflowSession).filter(
            WorkflowSession.thread_id == thread_id
        ).first()

    @staticmethod
    async def update_stage(
        db: Session,
        session_id: str,
        stage: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the workflow stage and log the action, coordinating with Backboard.io.

        Args:
            db: Database session
            session_id: Session identifier
            stage: The new workflow stage (e.g., "drafting", "review")
            action: The action performed (e.g., "generated_draft", "submitted_for_review")
            context: Optional additional context about the action

        Returns:
            True if successful, False otherwise
        """
        session = db.query(WorkflowSession).filter(
            WorkflowSession.session_id == session_id
        ).first()

        if not session:
            logger.error(f"Workflow session not found: {session_id}")
            return False
        
        if not session.thread_id:
            if backboard_client.enabled:
                logger.error(f"Workflow session {session_id} has no Backboard thread_id.")
            else:
                logger.debug(f"Workflow session {session_id} has no Backboard thread_id (Backboard is disabled).")
            # Log action to DB even if Backboard fails
            SessionManager._log_action(
                db=db,
                session_id=session_id,
                action_type="stage_change",
                action_name=f"update_stage_no_thread",
                input_data={"stage": stage, "action": action, "context": context},
                output_data=None,
                success=False,
                error_message="Missing Backboard thread_id"
            )
            return False

        # Update Backboard
        backboard_success = await backboard_client.update_workflow_state(
            thread_id=session.thread_id,
            stage=stage,
            action=action,
            context=context
        )

        if not backboard_success:
            logger.error(f"Failed to update Backboard state for session {session_id}")
            # Log action to DB even if Backboard fails
            SessionManager._log_action(
                db=db,
                session_id=session_id,
                action_type="stage_change",
                action_name=f"update_stage_backboard_fail",
                input_data={"stage": stage, "action": action, "context": context},
                output_data=None,
                success=False,
                error_message="Backboard state update failed"
            )
            return False
        
        # Update session in database
        session.workflow_stage = stage
        # Potentially update session_metadata with new context if needed
        try:
            db.commit()
            db.refresh(session)
        except Exception as e:
            db.rollback()
            logger.error(f'Failed to commit retrieval: {e}')

        # Log action to DB
        SessionManager._log_action(
            db=db,
            session_id=session_id,
            action_type="stage_change",
            action_name=action, # Use action as name for logging
            input_data={"stage": stage, "context": context},
            output_data={"success": True},
            success=True
        )

        logger.info(f"Updated stage for session {session_id} to '{stage}' via action '{action}'")
        return True

    @staticmethod
    async def log_retrieval(
        db: Session,
        session_id: str,
        query: str,
        retrieval_method: str,
        num_results: int,
        top_sources: Optional[list] = None
    ) -> bool:
        """
        Log a retrieval operation, coordinating with Backboard.io and updating history.

        Args:
            db: Database session
            session_id: Session identifier
            query: User query
            retrieval_method: Method used (e.g., "hybrid_bm25_vector", "bm25_only")
            num_results: Number of results retrieved
            top_sources: Optional list of top source identifiers

        Returns:
            True if successful, False otherwise
        """
        session = db.query(WorkflowSession).filter(
            WorkflowSession.session_id == session_id
        ).first()

        if not session:
            logger.error(f"Workflow session not found for retrieval logging: {session_id}")
            return False

        if not session.thread_id:
            if backboard_client.enabled:
                logger.error(f"Workflow session {session_id} has no Backboard thread_id for retrieval logging.")
            else:
                logger.debug(f"Workflow session {session_id} has no Backboard thread_id for retrieval logging (Backboard is disabled).")
            SessionManager._log_action(
                db=db,
                session_id=session_id,
                action_type="retrieval",
                action_name="log_retrieval_no_thread",
                input_data={
                    "query": query,
                    "retrieval_method": retrieval_method,
                    "num_results": num_results,
                    "top_sources": top_sources
                },
                output_data=None,
                success=False,
                error_message="Missing Backboard thread_id"
            )
            return False

        # Log to Backboard
        backboard_success = await backboard_client.log_retrieval(
            thread_id=session.thread_id,
            query=query,
            retrieval_method=retrieval_method,
            num_results=num_results,
            top_sources=top_sources
        )

        if not backboard_success:
            logger.error(f"Failed to log retrieval to Backboard for session {session_id}")
            SessionManager._log_action(
                db=db,
                session_id=session_id,
                action_type="retrieval",
                action_name="log_retrieval_backboard_fail",
                input_data={
                    "query": query,
                    "retrieval_method": retrieval_method,
                    "num_results": num_results,
                    "top_sources": top_sources
                },
                output_data=None,
                success=False,
                error_message="Backboard retrieval logging failed"
            )
            return False

        # Update session history in database
        retrieval_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "retrieval_method": retrieval_method,
            "num_results": num_results,
            "top_sources": top_sources
        }
        if session.retrieval_history is None:
            session.retrieval_history = []
        session.retrieval_history.append(retrieval_entry)

        try:
            db.commit()
            db.refresh(session)
        except Exception as e:
            db.rollback()
            logger.error(f'Failed to commit retrieval: {e}')

        # Log action to DB
        SessionManager._log_action(
            db=db,
            session_id=session_id,
            action_type="retrieval",
            action_name=retrieval_method, # Use method as action name
            input_data={"query": query, "num_results": num_results, "top_sources": top_sources},
            output_data={"success": True},
            success=True
        )

        logger.info(f"Logged retrieval for session {session_id} to Backboard and DB")
        return True

    @staticmethod
    async def log_generation(
        db: Session,
        session_id: str,
        prompt_type: str,
        response_summary: str,
        model: str = "groq"
    ) -> bool:
        """Log generation to Backboard and DB with transaction safety."""
        try:
            session = db.query(WorkflowSession).filter(WorkflowSession.session_id == session_id).first()
            if not session:
                return False

            if session.thread_id:
                await backboard_client.log_generation(
                    thread_id=session.thread_id,
                    prompt_type=prompt_type,
                    response_summary=response_summary,
                    model=model
                )

            generation_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompt_type": prompt_type,
                "response_summary": response_summary,
                "model": model
            }
            if session.generation_history is None:
                session.generation_history = []
            session.generation_history.append(generation_entry)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Log generation failed: {e}")
            return False

    @staticmethod
    def _log_action(
        db: Session,
        session_id: str,
        action_type: str,
        action_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Log individual workflow action to database.

        Args:
            db: Database session
            session_id: Session identifier
            action_type: Type of action
            action_name: Name of action
            input_data: Input data
            output_data: Output data
            duration_ms: Duration in milliseconds
            success: Whether action succeeded
            error_message: Optional error message
        """
        action = WorkflowAction(
            session_id=session_id,
            action_type=action_type,
            action_name=action_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )

        try:
            db.add(action)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to log workflow action '{action_name}': {e}")

    @staticmethod
    def get_user_sessions(
        db: Session,
        user_id: str,
        limit: int = 10
    ) -> List[WorkflowSession]:
        """
        Get recent workflow sessions for a user.

        Args:
            db: Database session
            user_id: User identifier
            limit: Maximum number of sessions to return

        Returns:
            List of WorkflowSession instances
        """
        return db.query(WorkflowSession).filter(
            WorkflowSession.user_id == user_id
        ).order_by(desc(WorkflowSession.created_at)).limit(limit).all()

    @staticmethod
    async def complete_session(
        db: Session,
        session_id: str
    ) -> bool:
        """
        Mark a workflow session as completed, coordinating with Backboard.io.

        Args:
            db: Database session
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        session = db.query(WorkflowSession).filter(
            WorkflowSession.session_id == session_id
        ).first()

        if not session:
            logger.error(f"Workflow session not found for completion: {session_id}")
            return False

        if not session.thread_id:
            if backboard_client.enabled:
                logger.error(f"Workflow session {session_id} has no Backboard thread_id for completion.")
            else:
                logger.debug(f"Workflow session {session_id} has no Backboard thread_id for completion (Backboard is disabled).")
            SessionManager._log_action(
                db=db,
                session_id=session_id,
                action_type="session_completion",
                action_name="complete_session_no_thread",
                output_data=None,
                success=False,
                error_message="Missing Backboard thread_id"
            )
            return False

        # Update Backboard state to reflect completion
        backboard_success = await backboard_client.update_workflow_state(
            thread_id=session.thread_id,
            stage="completed",
            action="session_completed",
            context={"completed_at": datetime.now(timezone.utc).isoformat()}
        )

        if not backboard_success:
            logger.error(f"Failed to update Backboard state to 'completed' for session {session_id}")
            SessionManager._log_action(
                db=db,
                session_id=session_id,
                action_type="session_completion",
                action_name="complete_session_backboard_fail",
                output_data=None,
                success=False,
                error_message="Backboard state update to 'completed' failed"
            )
            return False

        # Update session in database
        session.workflow_stage = "completed"
        session.is_active = False
        session.completed_at = datetime.now(timezone.utc)
        
        try:
            db.commit()
            db.refresh(session)
        except Exception as e:
            db.rollback()
            logger.error(f'Failed to commit retrieval: {e}')

        # Log action to DB
        SessionManager._log_action(
            db=db,
            session_id=session_id,
            action_type="session_completion",
            action_name="session_completed",
            output_data={"success": True},
            success=True
        )

        logger.info(f"Completed workflow session {session_id} and updated Backboard.")
        return True
