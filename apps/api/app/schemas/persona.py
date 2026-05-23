from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

# Pydantic schemas for Persona Models

class PersonaSourceBase(BaseModel):
    source_type: str = Field(..., description="E.g., website, x, linkedin, youtube, instagram, manual")
    url: Optional[str] = None
    manual_text: Optional[str] = None

class PersonaSourceCreate(PersonaSourceBase):
    pass

class PersonaSourceResponse(PersonaSourceBase):
    id: str
    persona_profile_id: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonaDocumentBase(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    clean_text: Optional[str] = None
    markdown: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    content_hash: Optional[str] = None

class PersonaDocumentResponse(PersonaDocumentBase):
    id: str
    persona_source_id: str
    scraped_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class PersonaInsightBase(BaseModel):
    source_summary: Dict[str, Any] = Field(default_factory=dict)
    extracted_topics: List[str] = Field(default_factory=list)
    extracted_hooks: List[str] = Field(default_factory=list)
    extracted_offers: List[str] = Field(default_factory=list)
    extracted_audience: List[str] = Field(default_factory=list)
    extracted_voice_traits: List[str] = Field(default_factory=list)
    extracted_proof_points: List[str] = Field(default_factory=list)

class PersonaInsightResponse(PersonaInsightBase):
    id: str
    persona_profile_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PersonaProfileBase(BaseModel):
    status: str = "draft"
    niche: Optional[str] = None
    target_audience: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    persona_summary: Optional[str] = None
    voice_tone: Optional[str] = None
    positioning: Optional[str] = None
    content_pillars: List[str] = Field(default_factory=list)
    audience_pain_points: List[str] = Field(default_factory=list)
    credibility_signals: List[str] = Field(default_factory=list)
    content_opportunities: List[str] = Field(default_factory=list)
    avoid_topics: List[str] = Field(default_factory=list)

class PersonaProfileUpdate(BaseModel):
    niche: Optional[str] = None
    target_audience: Optional[str] = None
    goals: Optional[List[str]] = None
    persona_summary: Optional[str] = None
    voice_tone: Optional[str] = None
    positioning: Optional[str] = None
    content_pillars: Optional[List[str]] = None
    audience_pain_points: Optional[List[str]] = None
    credibility_signals: Optional[List[str]] = None
    content_opportunities: Optional[List[str]] = None
    avoid_topics: Optional[List[str]] = None

class PersonaProfileResponse(PersonaProfileBase):
    id: str
    user_id: str
    raw_ai_output: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    # We can optionally include nested objects
    sources: List[PersonaSourceResponse] = Field(default_factory=list)
    insights: List[PersonaInsightResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# Schema for strictly typed AI output
class AIPersonaExtraction(BaseModel):
    persona_summary: str = ""
    niche: str = ""
    target_audience: str = ""
    goals: List[str] = Field(default_factory=list)
    voice_tone: str = ""
    positioning: str = ""
    content_pillars: List[str] = Field(default_factory=list)
    audience_pain_points: List[str] = Field(default_factory=list)
    credibility_signals: List[str] = Field(default_factory=list)
    content_opportunities: List[str] = Field(default_factory=list)
    avoid_topics: List[str] = Field(default_factory=list)
    recommended_content_formats: List[str] = Field(default_factory=list)
    sample_hooks: List[str] = Field(default_factory=list)
    calendar_seed_ideas: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    missing_information: List[str] = Field(default_factory=list)
