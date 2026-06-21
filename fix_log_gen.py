import sys

# Read the file content
with open('backend/utils/session_manager.py', 'r') as f:
    content = f.read()

# Define the old and new content
# I will use a slightly more conservative approach to replace it
old_log_gen = """    @staticmethod
    async def log_generation(
        db: Session,
        session_id: str,
        prompt_type: str,
        response_summary: str,
        model: str = "groq"
    ) -> bool:
        \"\"\"
        Log a generation operation, coordinating with Backboard.io and updating history.

        Args:
            db: Database session
            session_id: Session identifier
            prompt_type: Type of generation (e.g., "rti_draft", "qa_response")
            response_summary: Summary of generated response
            model: Model used for generation

        Returns:
            True if successful, False otherwise
        \"\"\"
        session = db.query(WorkflowSession).filter(
            WorkflowSession.session_id == session_id
        ).first()

        if not session:
            logger.error(f"Workflow session not found for generation logging: {session_id}")
            return False

        if not session.thread_id:
            logger.error(f"Workflow session {session_id} has no Backboard thread_id for generation logging.")
            SessionManager._log_action(
                db=db,
                session_id=session_id,
                action_type="generation",
                action_name="log_generation_no_thread",
                input_data={"prompt_type": prompt_type, "response_summary": response_summary, "model": model},
                output_data=None,
                success=False,
                error_message="Missing Backboard thread_id"
            )
            return False

        # Log to Backboard
        backboard_success = await backboard_client.log_generation(
            thread_id=session.thread_id,
            prompt_type=prompt_type,
            response_summary=response_summary,
            model=model
        )

        if not backboard_success:
            logger.error(f"Failed to log generation to Backboard for session {session_id}")
            SessionManager._log_action(
                db=db,
                session_id=session_id,
                action_type="generation",
                action_name="log_generation_backboard_fail",
                input_data={"prompt_type": prompt_type, "response_summary": response_summary, "model": model},
                output_data=None,
                success=False,
                error_message="Backboard generation logging failed"
            )
            return False

        # Update session history in database
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
        db.refresh(session)

        # Log action to DB
        SessionManager._log_action(
            db=db,
            session_id=session_id,
            action_type="generation",
            action_name=prompt_type, # Use prompt_type as action name
            input_data={"response_summary": response_summary, "model": model},
            output_data={"success": True},
            success=True
        )

        logger.info(f"Logged generation for session {session_id} to Backboard and DB")
        return True"""

new_log_gen = """    @staticmethod
    async def log_generation(
        db: Session,
        session_id: str,
        prompt_type: str,
        response_summary: str,
        model: str = "groq"
    ) -> bool:
        \"\"\"Log generation to Backboard and DB with transaction safety.\"\"\"
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
            return False"""

new_content = content.replace(old_log_gen, new_log_gen)
with open('backend/utils/session_manager.py', 'w') as f:
    f.write(new_content)
