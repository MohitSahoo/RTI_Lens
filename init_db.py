"""
Initialize database tables using SQLAlchemy ORM models
"""
from backend.database import engine, Base
from backend.models import Ministry, Case, MinistryStats, SectionStats
from backend.models.workflow import WorkflowSession, WorkflowAction

def init_db():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Created tables: {', '.join(tables)}")

if __name__ == "__main__":
    init_db()
