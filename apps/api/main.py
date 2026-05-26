from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401
from app.config import settings
from app.routers import (
    analytics,
    auth,
    brand_profile,
    calendar,
    coach,
    content,
    context,
    linkedin,
    onboarding,
    persona,
    radar,
    repurpose,
    social,
    social_oauth,
    storage,
    trends,
)
from app.routers import waitlist

app = FastAPI(
    title="Iterra API",
    version="0.1.0",
    description="AI Content Strategy Platform API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(context.router, prefix="/api/v1/context", tags=["context"])
app.include_router(linkedin.router, prefix="/api/v1/linkedin", tags=["linkedin"])
app.include_router(brand_profile.router, prefix="/api/v1/brand-profile", tags=["brand-profile"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(waitlist.router, prefix="/api/v1/waitlist", tags=["waitlist"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(repurpose.router, prefix="/api/v1/repurpose", tags=["repurpose"])
app.include_router(coach.router, prefix="/api/v1/coach", tags=["coach"])
app.include_router(radar.router, prefix="/api/v1/radar", tags=["radar"])
app.include_router(social.router, prefix="/api/v1/social", tags=["social"])
app.include_router(social_oauth.router, prefix="/api/v1/connect", tags=["connect"])
app.include_router(persona.router, prefix="/api/v1/persona", tags=["persona"])
app.include_router(storage.router, prefix="/api/v1/storage", tags=["storage"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "iterra-api"}
