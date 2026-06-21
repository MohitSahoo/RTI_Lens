"""
Backboard.io Client Wrapper for Workflow Session Management

This module provides a wrapper around the Backboard SDK for managing
RTI workflow sessions, conversation continuity, and retrieval history.

Backboard sits ABOVE the retrieval pipeline as a session/workflow layer.
It does NOT replace MongoDB, BM25, vector search, or Groq generation.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

try:
    from backboard import BackboardClient as BackboardSDK
    BACKBOARD_SDK_AVAILABLE = True
except (ImportError, Exception) as e:
    BackboardSDK = None
    BACKBOARD_SDK_AVAILABLE = False
    logging.getLogger(__name__).warning(f"Backboard SDK unavailable: {e}")

from backend.config import BACKBOARD_API_KEY, BACKBOARD_ENABLED

logger = logging.getLogger(__name__)


class BackboardClient:
    """
    Wrapper for Backboard.io workflow session management.

    Responsibilities:
    - Create and manage workflow threads
    - Track RTI lifecycle stages
    - Maintain conversation continuity
    - Store retrieval history
    - Persist workflow state

    Does NOT:
    - Replace MongoDB storage
    - Replace BM25 or vector retrieval
    - Replace Groq generation
    - Modify the retrieval pipeline
    """

    def __init__(self):
        """Initialize Backboard client if enabled and API key is available."""
        self.enabled = BACKBOARD_SDK_AVAILABLE and BACKBOARD_ENABLED and BACKBOARD_API_KEY is not None
        self.client = None

        if self.enabled:
            try:
                if not BACKBOARD_API_KEY:
                    logger.warning("BACKBOARD_API_KEY not set, disabling Backboard integration")
                    self.enabled = False
                    return

                self.client = BackboardSDK(api_key=BACKBOARD_API_KEY)
                logger.info("Backboard client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Backboard client: {e}")
                self.enabled = False
        else:
            logger.info("Backboard integration disabled or API key not configured")

    async def create_workflow_session(
        self,
        workflow_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create a new workflow session with Backboard thread.

        Args:
            workflow_type: Type of workflow (e.g., "rti_qa", "rti_draft", "appeal")
            user_id: Optional user identifier
            metadata: Additional workflow metadata

        Returns:
            thread_id if successful, None otherwise
        """
        if not self.enabled or not self.client:
            return None

        try:
            initial_message = f"RTI workflow initiated: {workflow_type}"
            if user_id:
                initial_message += f"\nUser: {user_id}"
            if metadata:
                initial_message += f"\nMetadata: {metadata}"

            response = await self.client.send_message(
                content=initial_message,
                memory="auto",
                stream=False
            )

            # Response is ChatMessagesResponse when stream=False
            if hasattr(response, 'thread_id'):
                thread_id = str(response.thread_id)
                logger.info(f"Created Backboard thread {thread_id} for workflow {workflow_type}")
                return thread_id
            else:
                logger.error("Unexpected response format from Backboard")
                return None

        except Exception as e:
            logger.error(f"Failed to create Backboard workflow session: {e}")
            return None

    async def update_workflow_state(
        self,
        thread_id: str,
        stage: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update workflow state in Backboard thread.

        Args:
            thread_id: Backboard thread identifier
            stage: Current workflow stage (e.g., "drafting", "review", "appeal")
            action: Action performed (e.g., "generated_draft", "retrieved_cases")
            context: Additional context about the action

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not thread_id or not self.client:
            return False

        try:
            message = f"Workflow stage: {stage}\nAction: {action}"
            if context:
                message += f"\nContext: {context}"

            await self.client.add_message(
                thread_id=thread_id,
                content=message
            )

            logger.info(f"Updated Backboard thread {thread_id}: {stage} - {action}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Backboard workflow state: {e}")
            return False

    async def log_retrieval(
        self,
        thread_id: str,
        query: str,
        retrieval_method: str,
        num_results: int,
        top_sources: Optional[list] = None
    ) -> bool:
        """
        Log retrieval operation to Backboard thread.

        Args:
            thread_id: Backboard thread identifier
            query: User query
            retrieval_method: Method used (e.g., "hybrid_bm25_vector", "bm25_only")
            num_results: Number of results retrieved
            top_sources: Optional list of top source identifiers

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not thread_id or not self.client:
            return False

        try:
            message = f"Retrieval performed:\nQuery: {query}\nMethod: {retrieval_method}\nResults: {num_results}"
            if top_sources:
                message += f"\nTop sources: {', '.join(top_sources[:3])}"

            await self.client.add_message(
                thread_id=thread_id,
                content=message
            )

            logger.info(f"Logged retrieval to Backboard thread {thread_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to log retrieval to Backboard: {e}")
            return False

    async def log_generation(
        self,
        thread_id: str,
        prompt_type: str,
        response_summary: str,
        model: str = "groq"
    ) -> bool:
        """
        Log generation operation to Backboard thread.

        Args:
            thread_id: Backboard thread identifier
            prompt_type: Type of generation (e.g., "rti_draft", "qa_response")
            response_summary: Summary of generated response
            model: Model used for generation

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not thread_id or not self.client:
            return False

        try:
            message = f"Generation completed:\nType: {prompt_type}\nModel: {model}\nSummary: {response_summary}"

            await self.client.add_message(
                thread_id=thread_id,
                content=message
            )

            logger.info(f"Logged generation to Backboard thread {thread_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to log generation to Backboard: {e}")
            return False

    async def restore_workflow_context(
        self,
        thread_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Restore workflow context from Backboard thread.

        Args:
            thread_id: Backboard thread identifier

        Returns:
            Dictionary with workflow context if successful, None otherwise
        """
        if not self.enabled or not thread_id or not self.client:
            return None

        try:
            # Retrieve thread from Backboard
            thread = await self.client.get_thread(thread_id=thread_id)

            # Parse and return context
            context = {
                "thread_id": thread_id,
                "restored_at": datetime.now(timezone.utc).isoformat(),
                "history_available": True,
                "thread_data": thread
            }

            logger.info(f"Restored workflow context from Backboard thread {thread_id}")
            return context

        except Exception as e:
            logger.error(f"Failed to restore workflow context from Backboard: {e}")
            return None


# Global client instance
backboard_client = BackboardClient()
