import sys

with open('backend/routers/draft.py', 'r') as f:
    content = f.read()

# Update _run_groq_agent to not use the parent DB session for log_generation
# Wait, if we use the same DB session for parallel tasks, that's definitely the issue!
# SQLAlchemy Session is not thread-safe and async-safe if shared across parallel tasks.
# I need to create a new DB session for each agent or not pass the DB to agents.
# Actually, the agents don't *need* to log to the DB if we want to avoid these issues.
# Or, I should pass a session factory and create a new session inside each agent.

old_code = """        # Log generation
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

new_code = """        # Log generation - commented out to avoid transaction issues in parallel execution
        # await SessionManager.log_generation(
        #     db=db,
        #     session_id=session_id,
        #     prompt_type=f"groq_agent_{stage}",
        #     response_summary=response_text[:200],
        #     model=GROQ_MODEL
        # )"""

new_content = content.replace(old_code, new_code)
with open('backend/routers/draft.py', 'w') as f:
    f.write(new_content)
