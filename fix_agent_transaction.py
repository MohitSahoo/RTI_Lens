import sys

with open('backend/routers/draft.py', 'r') as f:
    content = f.read()

# Update _run_groq_agent to handle transactions properly
old_code = """        # Log generation
        await SessionManager.log_generation(
            db=db,
            session_id=session_id,
            prompt_type=f"groq_agent_{stage}",
            response_summary=response_text[:200],
            model=GROQ_MODEL
        )"""

new_code = """        # Log generation
        try:
            await SessionManager.log_generation(
                db=db,
                session_id=session_id,
                prompt_type=f"groq_agent_{stage}",
                response_summary=response_text[:200],
                model=GROQ_MODEL
            )
        except Exception as e:
            logger.error(f"Failed to log generation for agent {agent_name}: {e}")
            # Do not re-raise, we want the agent result to return anyway"""

new_content = content.replace(old_code, new_code)
with open('backend/routers/draft.py', 'w') as f:
    f.write(new_content)
