"""
SQLAlchemy ORM Models for RTI-Lens
Replaces raw SQL queries with typed ORM models
"""
from sqlalchemy import Column, Integer, Text, Date, Float, Boolean, TIMESTAMP, ForeignKey, ARRAY, CheckConstraint, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
from backend.enums import AppealOutcome, AppealLevel, ExtractionMethod


class Ministry(Base):
    __tablename__ = "ministries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True)
    aliases = Column(ARRAY(Text))

    # Relationships
    cases = relationship("Case", back_populates="ministry")
    stats = relationship("MinistryStats", back_populates="ministry", uselist=False)
    section_stats = relationship("SectionStats", back_populates="ministry")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(Text, unique=True, nullable=False, index=True)
    order_url = Column(Text)
    ministry_id = Column(Integer, ForeignKey("ministries.id", ondelete="RESTRICT"), nullable=False, index=True)
    section_cited = Column(Text, index=True)
    appeal_outcome = Column(SAEnum(AppealOutcome, native_enum=False, values_callable=lambda x: [e.value for e in x], name="appeal_outcome_enum"))
    appeal_level = Column(SAEnum(AppealLevel, native_enum=False, values_callable=lambda x: [e.value for e in x], name="appeal_level_enum"))
    order_date = Column(Date, index=True)
    extraction_method = Column(SAEnum(ExtractionMethod, native_enum=False, values_callable=lambda x: [e.value for e in x], name="extraction_method_enum"), nullable=False)
    raw_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("length(trim(order_number)) > 0", name="check_case_order_number_not_blank"),
        CheckConstraint("raw_text <> ''", name="check_case_raw_text_not_empty"),
    )

    # Relationships
    ministry = relationship("Ministry", back_populates="cases")
    paragraphs = relationship("Paragraph", back_populates="case", cascade="all, delete-orphan")


class Paragraph(Base):
    __tablename__ = "paragraphs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    paragraph_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("case_id", "paragraph_index", name="uq_paragraph_case_index"),
        CheckConstraint("paragraph_index >= 0", name="check_paragraph_index_non_negative"),
        CheckConstraint("text <> ''", name="check_paragraph_text_not_empty"),
    )

    # Relationships
    case = relationship("Case", back_populates="paragraphs")


class MinistryStats(Base):
    __tablename__ = "ministry_stats"

    ministry_id = Column(Integer, ForeignKey("ministries.id"), primary_key=True)
    total_orders = Column(Integer)
    denied_count = Column(Integer)
    allowed_count = Column(Integer)
    partially_count = Column(Integer)
    denial_rate = Column(Float)
    override_rate = Column(Float)
    last_computed = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("total_orders IS NULL OR total_orders >= 0", name="check_ministry_stats_total_orders_non_negative"),
        CheckConstraint("denied_count IS NULL OR denied_count >= 0", name="check_ministry_stats_denied_count_non_negative"),
        CheckConstraint("allowed_count IS NULL OR allowed_count >= 0", name="check_ministry_stats_allowed_count_non_negative"),
        CheckConstraint("partially_count IS NULL OR partially_count >= 0", name="check_ministry_stats_partially_count_non_negative"),
        CheckConstraint("denial_rate IS NULL OR (denial_rate >= 0 AND denial_rate <= 1)", name="check_ministry_stats_denial_rate_range"),
        CheckConstraint("override_rate IS NULL OR (override_rate >= 0 AND override_rate <= 1)", name="check_ministry_stats_override_rate_range"),
    )

    # Relationships
    ministry = relationship("Ministry", back_populates="stats")


class SectionStats(Base):
    __tablename__ = "section_stats"

    section_cited = Column(Text, primary_key=True)
    ministry_id = Column(Integer, ForeignKey("ministries.id"), primary_key=True)
    total_citations = Column(Integer)
    overturned_count = Column(Integer)
    misuse_rate = Column(Float)

    __table_args__ = (
        CheckConstraint("total_citations IS NULL OR total_citations >= 0", name="check_section_stats_total_citations_non_negative"),
        CheckConstraint("overturned_count IS NULL OR overturned_count >= 0", name="check_section_stats_overturned_count_non_negative"),
        CheckConstraint("misuse_rate IS NULL OR (misuse_rate >= 0 AND misuse_rate <= 1)", name="check_section_stats_misuse_rate_range"),
    )

    # Relationships
    ministry = relationship("Ministry", back_populates="section_stats")


class BlockchainFiling(Base):
    __tablename__ = "blockchain_filings"

    id = Column(Integer, primary_key=True, index=True)
    filing_hash = Column(Text, nullable=False, unique=True, index=True)
    tx_hash = Column(Text)
    block_number = Column(Integer)
    applicant_name = Column(Text, nullable=False)
    authority = Column(Text, nullable=False)
    query_text = Column(Text, nullable=False)
    filing_ts = Column(TIMESTAMP(timezone=True), nullable=False)
    deadline_ts = Column(TIMESTAMP(timezone=True))
    deadline_breached = Column(Boolean, default=False)
    appeal_status = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("length(trim(filing_hash)) > 0", name="check_blockchain_filing_hash_not_blank"),
        CheckConstraint("length(trim(applicant_name)) > 0", name="check_blockchain_applicant_name_not_blank"),
        CheckConstraint("length(trim(authority)) > 0", name="check_blockchain_authority_not_blank"),
        CheckConstraint("length(trim(query_text)) > 0", name="check_blockchain_query_text_not_blank"),
        CheckConstraint("block_number IS NULL OR block_number >= 0", name="check_blockchain_block_number_non_negative"),
        CheckConstraint("appeal_status IN (0, 1, 2)", name="check_blockchain_appeal_status"),
        CheckConstraint("deadline_ts IS NULL OR deadline_ts >= filing_ts", name="check_blockchain_deadline_after_filing"),
    )
