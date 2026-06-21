import sys

with open('backend/utils/session_manager.py', 'r') as f:
    content = f.read()

# Replace the db.commit() in log_retrieval to be inside a try-except to prevent aborting transaction
# But actually, I suspect the issue is simply that db.commit() is being called too aggressively,
# or when the transaction is in a bad state from something else failing.

# Let's add try-except to db.commit() and db.refresh() blocks.
# I will do this for log_retrieval, update_stage, log_generation.

# This is a bit complex for a one-liner replace.
# I will just manually fix log_retrieval commit.
