import sys

with open('backend/routers/draft.py', 'r') as f:
    content = f.read()

# I suspect that _retrieve_precedents or create_session are somehow leaving the db session in an error state
# or that the DB session is getting shared and corrupted.
# Let's check how _retrieve_precedents uses DB.
# Actually, the error message:
# (psycopg2.errors.InFailedSqlTransaction) current transaction is aborted, commands ignored until end of transaction block
# This happens when a query fails, and then ANOTHER query is tried on the same transaction.
# So, one of the queries in the agents or before is failing.
# BUT I am not calling any DB methods in the agents anymore!
# Wait, check SessionManager.create_session.
# It calls db.commit(). This closes the transaction.
# The error happens in the groq agents... 
# Is it possible that  object itself is somehow used inside _run_groq_agent?
# Wait, let's check _run_groq_agent again. It doesn't call any DB methods?

with open('backend/routers/draft.py', 'r') as f:
    lines = f.readlines()

# Look at _run_groq_agent signature
# Oh! The  is passed to !
# Is it used inside?
# Let me re-read _run_groq_agent.
