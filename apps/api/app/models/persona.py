import uuid
from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class PersonaProfile(Base):
    __tablename__ = "persona_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="draft")
    niche = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    goals = Column(JSON, default=list)
    persona_summary = Column(Text, nullable=True)
    voice_tone = Column(Text, nullable=True)
    positioning = Column(Text, nullable=True)
    content_pillars = Column(JSON, default=list)
    audience_pain_points = Column(JSON, default=list)
    credibility_signals = Column(JSON, default=list)
    content_opportunities = Column(JSON, default=list)
    avoid_topics = Column(JSON, default=list)
    raw_ai_output = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", backref="persona_profiles")
    sources = relationship("PersonaSource", back_populates="persona_profile", cascade="all, delete-orphan")
    insights = relationship("PersonaInsight", back_populates="persona_profile", cascade="all, delete-orphan")


class PersonaSource(Base):
    __tablename__ = "persona_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_profile_id = Column(String, ForeignKey("persona_profiles.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String, nullable=False)  # website, x, linkedin, youtube, instagram, manual
    url = Column(Text, nullable=True)
    manual_text = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed, skipped
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    persona_profile = relationship("PersonaProfile", back_populates="sources")
    documents = relationship("PersonaDocument", back_populates="source", cascade="all, delete-orphan")


class PersonaDocument(Base):
    __tablename__ = "persona_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_source_id = Column(String, ForeignKey("persona_sources.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    clean_text = Column(Text, nullable=True)
    markdown = Column(Text, nullable=True)
    metadata_ = Column(JSON, default=dict)  # 'metadata' is reserved in SQLAlchemy Base
    content_hash = Column(String, nullable=True)
    scraped_at = Column(DateTime, default=utc_now)

    source = relationship("PersonaSource", back_populates="documents")


class PersonaInsight(Base):
    __tablename__ = "persona_insights"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_profile_id = Column(String, ForeignKey("persona_profiles.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_summary = Column(JSON, default=dict)
    extracted_topics = Column(JSON, default=list)
    extracted_hooks = Column(JSON, default=list)
    extracted_offers = Column(JSON, default=list)
    extracted_audience = Column(JSON, default=list)
    extracted_voice_traits = Column(JSON, default=list)
    extracted_proof_points = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)

    persona_profile = relationship("PersonaProfile", back_populates="insights")
