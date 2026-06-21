import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Mock the database URL from config
DATABASE_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Test a simple query to see if it even works
    print("Testing case_query...")
    query = text("SELECT order_number FROM cases LIMIT 1")
    result = db.execute(query).fetchone()
    print(f"Result: {result}")
except Exception as e:
    print(f"Query failed: {e}")
finally:
    db.close()
