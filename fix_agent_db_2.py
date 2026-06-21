import sys

with open('backend/routers/draft.py', 'r') as f:
    content = f.read()

# Update _run_groq_agent to NOT pass db
old_code = """        # Log generation - commented out to avoid transaction issues in parallel execution
        # await SessionManager.log_generation(
        #     db=db,
        #     session_id=session_id,
        #     prompt_type=f"groq_agent_{stage}",
        #     response_summary=response_text[:200],
        #     model=GROQ_MODEL
        # )"""

new_code = """        # Logging skipped for agents to prevent transaction aborts in parallel sessions."""

new_content = content.replace(old_code, new_code)
with open('backend/routers/draft.py', 'w') as f:
    f.write(new_content)
