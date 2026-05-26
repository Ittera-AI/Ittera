from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.user import User
from app.models.persona import PersonaProfile, PersonaSource, PersonaDocument, PersonaInsight
from app.schemas.persona import PersonaProfileResponse, PersonaProfileUpdate, PersonaSourceCreate, PersonaSourceResponse
from app.dependencies.auth import get_current_user
from app.services.scraper import ScraperService
from app.services.persona_ai import PersonaAIService

router = APIRouter(tags=["persona"])

@router.post("/onboarding/start", response_model=PersonaProfileResponse)
async def start_onboarding(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(PersonaProfile).filter(PersonaProfile.user_id == current_user.id).first()
    if not profile:
        profile = PersonaProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.post("/sources", response_model=PersonaSourceResponse)
async def add_source(source_in: PersonaSourceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(PersonaProfile).filter(PersonaProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona profile not found. Start onboarding first.")
    
    # Check limit
    source_count = db.query(PersonaSource).filter(PersonaSource.persona_profile_id == profile.id).count()
    from app.config import settings
    max_sources = getattr(settings, "PERSONA_MAX_SOURCES", 5)
    if source_count >= max_sources:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum of {max_sources} sources allowed.")

    if source_in.url and not ScraperService.validate_url(source_in.url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL provided.")

    source = PersonaSource(
        persona_profile_id=profile.id,
        user_id=current_user.id,
        source_type=source_in.source_type,
        url=source_in.url,
        manual_text=source_in.manual_text
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.get("/sources", response_model=List[PersonaSourceResponse])
async def list_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(PersonaSource).filter(PersonaSource.user_id == current_user.id).all()

@router.post("/scrape")
async def scrape_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sources = db.query(PersonaSource).filter(
        PersonaSource.user_id == current_user.id,
        PersonaSource.status == "pending"
    ).all()

    results = []
    for source in sources:
        try:
            if source.source_type.lower() == "manual":
                source.status = "completed"
                db.commit()
                continue

            source.status = "processing"
            db.commit()

            # Normalise: frontend may send "twitter" but scraper expects "x"
            effective_type = source.source_type.lower()
            if effective_type == "twitter":
                effective_type = "x"

            scraped_data = await ScraperService.scrape_url(source.url, effective_type)
            
            doc = PersonaDocument(
                persona_source_id=source.id,
                user_id=current_user.id,
                url=scraped_data["url"],
                title=scraped_data["title"],
                description=scraped_data["description"],
                clean_text=scraped_data["clean_text"],
                metadata_=scraped_data.get("metadata", {}),
                content_hash=scraped_data["content_hash"]
            )
            db.add(doc)
            
            source.status = "completed"
            db.commit()
            results.append({"id": source.id, "status": "completed"})
            
        except NotImplementedError as e:
            source.status = "skipped"
            source.error_message = str(e)
            db.commit()
            results.append({"id": source.id, "status": "skipped", "error": str(e)})
        except Exception as e:
            source.status = "failed"
            source.error_message = str(e)
            db.commit()
            results.append({"id": source.id, "status": "failed", "error": str(e)})

    return {"status": "finished", "results": results}

@router.post("/analyze", response_model=PersonaProfileResponse)
async def analyze_persona(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(PersonaProfile).filter(PersonaProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona profile not found")

    docs = db.query(PersonaDocument).filter(PersonaDocument.user_id == current_user.id).all()
    manual_sources = db.query(PersonaSource).filter(
        PersonaSource.user_id == current_user.id, 
        PersonaSource.source_type == "manual"
    ).all()
    
    # We could convert manual_sources to a pseudo-document, but for now we just pass docs.
    # We should create pseudo docs for manual text.
    all_docs = list(docs)
    for m in manual_sources:
        if m.manual_text:
            pd = PersonaDocument(
                persona_source_id=m.id,
                user_id=current_user.id,
                clean_text=m.manual_text,
                url="manual",
                title="Manual Context"
            )
            all_docs.append(pd)

    if not all_docs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No sources available to analyze.")

    try:
        extraction = await PersonaAIService.extract_persona(db, profile, all_docs)
        
        # Update profile
        profile.persona_summary = extraction.persona_summary
        profile.voice_tone = extraction.voice_tone
        profile.positioning = extraction.positioning
        profile.content_pillars = extraction.content_pillars
        profile.audience_pain_points = extraction.audience_pain_points
        profile.credibility_signals = extraction.credibility_signals
        profile.content_opportunities = extraction.content_opportunities
        profile.avoid_topics = extraction.avoid_topics
        profile.raw_ai_output = extraction.model_dump()
        
        # Update profile niche / target_audience if not set
        if not profile.niche:
            profile.niche = extraction.niche
        if not profile.target_audience:
            profile.target_audience = extraction.target_audience

        db.commit()
        db.refresh(profile)

        # Populate user fields so they're considered onboarded after persona flow
        if extraction.niche and not current_user.niche:
            current_user.niche = extraction.niche
        if not current_user.onboarding_complete:
            # Mark onboarding complete — persona flow IS the onboarding
            current_user.onboarding_complete = True
        db.commit()

        return profile
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("", response_model=PersonaProfileResponse)
async def get_persona(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(PersonaProfile).filter(PersonaProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    return profile

@router.patch("", response_model=PersonaProfileResponse)
async def update_persona(update_data: PersonaProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(PersonaProfile).filter(PersonaProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile

@router.post("/confirm", response_model=PersonaProfileResponse)
async def confirm_persona(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(PersonaProfile).filter(PersonaProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    
    profile.status = "confirmed"
    db.commit()
    db.refresh(profile)
    return profile
