import sys

with open('backend/routers/draft.py', 'r') as f:
    content = f.read()

# I suspect the issue is here:
# case_row = db.execute(case_query, {"order_number": order_number}).fetchone()
# If this fails, the whole transaction is aborted. 
# But this is before the agents run.
# Let's wrap these db.execute calls in try/except too.

old_code = """            case_row = db.execute(case_query, {"order_number": order_number}).fetchone()

            if case_row:
                sections = pageindex_loader.get_relevant_sections_by_order_numbers(
                    [order_number], context, max_sections=2
                )
                if sections:
                    case_text = "\n".join([f"[{s['hierarchy']}] {s['text'][:500]}" for s in sections])
                else:
                    para_query = text(
                        "SELECT text FROM paragraphs WHERE case_id = (SELECT id FROM cases WHERE order_number = :order_number) LIMIT 3"
                    )
                    paras = db.execute(para_query, {"order_number": order_number}).fetchall()
                    case_text = "\n".join([p.text[:300] for p in paras])"""

new_code = """            try:
                case_row = db.execute(case_query, {"order_number": order_number}).fetchone()
                if case_row:
                    sections = pageindex_loader.get_relevant_sections_by_order_numbers(
                        [order_number], context, max_sections=2
                    )
                    if sections:
                        case_text = "\n".join([f"[{s['hierarchy']}] {s['text'][:500]}" for s in sections])
                    else:
                        para_query = text(
                            "SELECT text FROM paragraphs WHERE case_id = (SELECT id FROM cases WHERE order_number = :order_number) LIMIT 3"
                        )
                        paras = db.execute(para_query, {"order_number": order_number}).fetchall()
                        case_text = "\n".join([p.text[:300] for p in paras])
            except Exception as e:
                logger.error(f"Error fetching case {order_number}: {e}")
                case_row = None
                case_text = "" """

new_content = content.replace(old_code, new_code)
with open('backend/routers/draft.py', 'w') as f:
    f.write(new_content)
