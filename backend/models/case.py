"""
ORM Models for RTI Cases, Ministries, and Statistics
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, ARRAY, Float, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class Ministry(Base):
    """Ministry/Department model"""
    __tablename__ = "ministries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True)
    aliases = Column(Text)  # JSON string for SQLite compatibility

    # Relationships
    cases = relationship("Case", back_populates="ministry")
    stats = relationship("MinistryStats", back_populates="ministry", uselist=False)
    section_stats = relationship("SectionStats", back_populates="ministry")


class Case(Base):
    """RTI Case/Order model"""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(Text, nullable=False, unique=True, index=True)
    order_url = Column(Text)
    ministry_id = Column(Integer, ForeignKey("ministries.id"))
    section_cited = Column(Text)
    appeal_outcome = Column(Text)
    appeal_level = Column(Text)
    order_date = Column(Date)
    extraction_method = Column(Text)
    raw_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ministry = relationship("Ministry", back_populates="cases")

    __table_args__ = (
        CheckConstraint(
            "appeal_level IN ('first_appeal', 'second_appeal')",
            name="cases_appeal_level_check"
        ),
        CheckConstraint(
            "appeal_outcome IN ('allowed', 'denied', 'partially_allowed')",
            name="cases_appeal_outcome_check"
        ),
        CheckConstraint(
            "extraction_method IN ('txt', 'pdfplumber', 'ocr')",
            name="cases_extraction_method_check"
        ),
    )


class MinistryStats(Base):
    """Aggregated statistics per ministry"""
    __tablename__ = "ministry_stats"

    ministry_id = Column(Integer, ForeignKey("ministries.id"), primary_key=True)
    total_orders = Column(Integer)
    denied_count = Column(Integer)
    allowed_count = Column(Integer)
    partially_count = Column(Integer)
    denial_rate = Column(Float)
    override_rate = Column(Float)
    last_computed = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ministry = relationship("Ministry", back_populates="stats")


class SectionStats(Base):
    """Statistics per RTI section per ministry"""
    __tablename__ = "section_stats"

    section_cited = Column(Text, primary_key=True)
    ministry_id = Column(Integer, ForeignKey("ministries.id"), primary_key=True)
    total_citations = Column(Integer)
    overturned_count = Column(Integer)
    misuse_rate = Column(Float)

    # Relationships
    ministry = relationship("Ministry", back_populates="section_stats")
