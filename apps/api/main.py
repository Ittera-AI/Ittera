from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, calendar, coach, radar, repurpose

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
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(repurpose.router, prefix="/api/v1/repurpose", tags=["repurpose"])
app.include_router(coach.router, prefix="/api/v1/coach", tags=["coach"])
app.include_router(radar.router, prefix="/api/v1/radar", tags=["radar"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "iterra-api"}
