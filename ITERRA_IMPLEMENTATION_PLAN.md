# Iterra — Phased Implementation Plan
## Based on CLAUDE.md Architecture

> **How to use this document:** Work through each phase in order. Each phase ends with a
> verifiable deliverable. Before starting a new session, tell Claude Code which phase you're
> on, paste CLAUDE.md, and reference this file. Each task specifies which agent to invoke.

---

## Conventions Applied Throughout

These come directly from CLAUDE.md and are enforced in every phase:

- **Contracts before code** — schemas/types are defined before any implementation
- **No logic in routes** — FastAPI routers delegate to `services/`
- **No API calls from components** — chain: `component → hook → store → service → api.ts`
- **AI engine is a package** — `from iterra_ai import Engine`, never HTTP between api and ai-engine
- **All prompts in `packages/ai-engine/iterra_ai/prompts/`** — versioned, never inlined
- **`make types` after every schema change** — shared-types is always generated, never hand-edited
- **Every model change needs an Alembic migration** with both `upgrade()` and `downgrade()`

---

## Phase Map

```
Phase 0  →  Repo scaffold + Docker + Makefile
Phase 1  →  FastAPI foundation + Auth + DB
Phase 2  →  iterra_ai package skeleton + base engine
Phase 3  →  LinkedIn OAuth + data sync (Celery)
Phase 4  →  Brand Profile engine + report UI        ← Core loop starts here
Phase 5  →  Trend Radar engine + radar UI
Phase 6  →  Content generation (Calendar + Repurpose)
Phase 7  →  AI Engagement Coach
Phase 8  →  Publishing + scheduling + calendar UI
Phase 9  →  Instagram (post-MVP)
```

---

## Phase 0 — Repo Scaffold + Infra
**Agent: `@architect`**
**Duration: 1 day**

This phase produces the skeleton every other phase builds into. No business logic.

### 0.1 — Initialize the monorepo

```bash
mkdir iterra && cd iterra
git init
```

Create the full directory tree:

```bash
mkdir -p \
  .agents .claude .github/workflows \
  apps/api/app/{routers,services,models,schemas,core} \
  apps/api/tests \
  apps/web/src/{app,components,hooks,lib,services,stores,types} \
  docs/adr \
  infra \
  packages/ai-engine/iterra_ai/{prompts,calendar,repurpose,coach,radar,core} \
  packages/shared-types/src \
  scripts \
  supabase/migrations \
  workers/celery/tasks
```

### 0.2 — docker-compose.yml

Services to define:

```yaml
services:
  web:       # Next.js — port 3000
  api:       # FastAPI + Uvicorn — port 8000
  worker:    # Celery worker (same image as api)
  beat:      # Celery beat scheduler
  db:        # PostgreSQL 15 — port 5432
  redis:     # Redis 7 — port 6379
```

All services read from a single `.env` file. Use `depends_on` with `condition: service_healthy` for db and redis.

### 0.3 — Makefile targets

```makefile
dev:        docker-compose up --build
stop:       docker-compose down
migrate:    docker-compose exec api alembic upgrade head
types:      docker-compose exec api python -m scripts.generate_types
test:       docker-compose exec api pytest && docker-compose exec web npm run test
lint:       docker-compose exec api ruff check . && docker-compose exec web npm run lint
seed:       docker-compose exec api python -m scripts.seed
logs:       docker-compose logs -f
```

### 0.4 — .env.example

```env
# Database
DATABASE_URL=postgresql://iterra:iterra@db:5432/iterra
REDIS_URL=redis://redis:6379/0

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Auth
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=10080

# Anthropic
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5

# LinkedIn
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_REDIRECT_URI=http://localhost:3000/api/auth/callback/linkedin

# Meta (Phase 9)
META_APP_ID=
META_APP_SECRET=

# Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

### 0.5 — scripts/setup.sh

```bash
#!/bin/bash
cp .env.example .env
cd apps/web && npm install
cd ../api && pip install -e .
cd ../../packages/ai-engine && pip install -e .
echo "Setup complete. Edit .env then run: make dev"
```

### 0.6 — .gitignore

Critical entries: `.env`, `__pycache__/`, `.next/`, `node_modules/`, `*.pyc`, `*.egg-info/`

### 0.7 — GitHub Actions CI (`.github/workflows/ci.yml`)

Jobs: `lint-python` (ruff), `lint-ts` (eslint), `test-api` (pytest), `test-web` (jest). Run on every PR to `main`.

### 0.8 — .agents/ directory

Create `.agents/ARCHITECT.md`, `.agents/FRONTEND.md`, `.agents/BACKEND.md`, `.agents/AI_ENGINEER.md` — each mirroring the relevant agent section from CLAUDE.md for quick invocation in Claude Code.

**✅ Phase 0 Deliverable:** `make dev` starts all containers. Web returns 200 at localhost:3000. API returns `{"status": "ok"}` at localhost:8000/health. No errors in docker-compose logs.

---

## Phase 1 — FastAPI Foundation + Auth + Database
**Agent: `@backend`**
**Duration: 2–3 days**

### 1.1 — FastAPI app setup (`apps/api/`)

**Files to create:**

```
apps/api/
├── app/
│   ├── main.py              # FastAPI app, CORS, router registration
│   ├── core/
│   │   ├── config.py        # Pydantic Settings reading from env
│   │   ├── database.py      # SQLAlchemy engine, session factory, get_db
│   │   ├── security.py      # JWT encode/decode, password hashing
│   │   └── dependencies.py  # get_current_user, get_db as FastAPI Depends
│   ├── models/
│   │   └── user.py          # SQLAlchemy User model (first model)
│   └── schemas/
│       └── auth.py          # Pydantic: LoginRequest, TokenResponse, UserOut
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/            # migrations go here
├── requirements.txt
└── pyproject.toml
```

**`apps/api/app/core/config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 10080
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
    LINKEDIN_CLIENT_ID: str
    LINKEDIN_CLIENT_SECRET: str
    LINKEDIN_REDIRECT_URI: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### 1.2 — Database models (define schemas FIRST, then models)

**Step 1: Write Pydantic schemas in `app/schemas/`**

```python
# app/schemas/user.py
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    niche: Optional[str]
    onboarding_complete: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# app/schemas/auth.py
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
```

**Step 2: Write SQLAlchemy models in `app/models/`**

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    full_name: Mapped[str]
    niche: Mapped[Optional[str]]
    goals: Mapped[Optional[str]]
    primary_platform: Mapped[str] = mapped_column(default="linkedin")
    onboarding_complete: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

# app/models/social_connection.py
class SocialConnection(Base):
    __tablename__ = "social_connections"
    id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    platform: Mapped[str]           # 'linkedin' | 'instagram'
    platform_user_id: Mapped[str]
    platform_username: Mapped[Optional[str]]
    access_token: Mapped[str]
    refresh_token: Mapped[Optional[str]]
    token_expires_at: Mapped[Optional[datetime]]
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String))
    last_synced_at: Mapped[Optional[datetime]]
    is_active: Mapped[bool] = mapped_column(default=True)

# app/models/post.py
class Post(Base):
    __tablename__ = "posts"
    id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    platform: Mapped[str]
    platform_post_id: Mapped[str]   # LinkedIn URN
    content: Mapped[str]
    content_type: Mapped[str]       # 'text' | 'image' | 'video' | 'article'
    published_at: Mapped[Optional[datetime]]
    impressions: Mapped[int] = mapped_column(default=0)
    likes: Mapped[int] = mapped_column(default=0)
    comments: Mapped[int] = mapped_column(default=0)
    shares: Mapped[int] = mapped_column(default=0)
    engagement_rate: Mapped[float] = mapped_column(default=0.0)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    tone: Mapped[Optional[str]]
    raw_api_response: Mapped[Optional[dict]] = mapped_column(JSONB)
    synced_at: Mapped[datetime] = mapped_column(default=func.now())

# app/models/brand_profile.py
class BrandProfile(Base):
    __tablename__ = "brand_profiles"
    id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    profile: Mapped[dict] = mapped_column(JSONB, default={})
    version: Mapped[int] = mapped_column(default=1)
    ai_confidence_score: Mapped[float] = mapped_column(default=0.0)
    is_confirmed: Mapped[bool] = mapped_column(default=False)
    analysis_based_on_posts: Mapped[int] = mapped_column(default=0)
    generated_at: Mapped[datetime] = mapped_column(default=func.now())
    confirmed_at: Mapped[Optional[datetime]]
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

# app/models/content_draft.py
class ContentDraft(Base):
    __tablename__ = "content_drafts"
    id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    platform: Mapped[str] = mapped_column(default="linkedin")
    content: Mapped[str]
    repurposed_versions: Mapped[dict] = mapped_column(JSONB, default={})
    prompt_used: Mapped[Optional[str]]
    trend_used: Mapped[Optional[str]]
    generation_model: Mapped[str] = mapped_column(default="claude-sonnet-4-5")
    status: Mapped[str] = mapped_column(default="draft")
    scheduled_for: Mapped[Optional[datetime]]
    celery_task_id: Mapped[Optional[str]]
    platform_post_id: Mapped[Optional[str]]
    published_at: Mapped[Optional[datetime]]
    publish_error: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

# app/models/trend_snapshot.py
class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"
    id: Mapped[UUID]
    niche: Mapped[str]
    trends: Mapped[list] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(default=func.now())
    __table_args__ = (UniqueConstraint("niche"),)
```

**Step 3: Create Alembic migration**

```bash
make migrate  # after writing models
# generates: alembic/versions/001_initial_schema.py
# Always implement both upgrade() and downgrade()
```

### 1.3 — Auth service + routes

**`app/services/auth_service.py`:**
- `register(db, data: UserCreate) -> User`
- `login(db, data: LoginRequest) -> TokenResponse`
- `get_user_by_id(db, user_id: UUID) -> User`

**`app/routers/auth.py`:**
```python
# Routes only — all logic in auth_service
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(data: UserCreate, db = Depends(get_db)):
    return await auth_service.register(db, data)

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db = Depends(get_db)):
    return await auth_service.login(db, data)

@router.get("/me", response_model=UserOut)
async def me(current_user = Depends(get_current_user)):
    return current_user
```

### 1.4 — Generate shared types

```bash
make types
# Reads FastAPI's OpenAPI schema → writes packages/shared-types/src/index.ts
```

The `scripts/generate_types.py` script should: fetch `GET /openapi.json` from the running API, run `openapi-typescript` to convert it, write to `packages/shared-types/src/index.ts`.

### 1.5 — Next.js frontend: Auth layer
**Agent: `@frontend`**

```
apps/web/src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx     # Protected — redirects to login if no session
│   │   └── page.tsx       # Placeholder home
│   └── layout.tsx
├── services/
│   └── api.ts             # Base fetch wrapper using NEXT_PUBLIC_API_URL
├── services/
│   └── auth.service.ts    # login(), register(), getMe() — calls api.ts
├── stores/
│   └── auth.store.ts      # Zustand: { user, token, login, logout }
├── hooks/
│   └── useAuth.ts         # Wraps auth store, exposes isLoading, error
└── middleware.ts           # Route protection
```

**Data flow check (enforced by @frontend):**
```
LoginPage → useAuth() → auth.store → auth.service.ts → api.ts → POST /auth/login
```

### 1.6 — Onboarding flow (frontend)

Pages: `(auth)/onboarding/step1` (name + niche + goals) → `(auth)/onboarding/step2` (LinkedIn connect button). On step2 completion, redirect to `/dashboard`.

Stores: `onboarding.store.ts` holds form state across steps.

**✅ Phase 1 Deliverable:** User can register, log in, complete onboarding, and land on the dashboard. JWT stored in http-only cookie. Protected routes redirect correctly. `make types` generates valid TypeScript types from the API.

---

## Phase 2 — iterra_ai Package Skeleton
**Agent: `@ai-engineer`**
**Duration: 1–2 days**

This phase creates the package structure and base tooling. No product logic yet — just the foundation every AI module will build on.

### 2.1 — Package setup

```
packages/ai-engine/
├── iterra_ai/
│   ├── __init__.py
│   ├── core/
│   │   ├── client.py          # Anthropic SDK wrapper
│   │   ├── base_engine.py     # Abstract base class for all engines
│   │   ├── cost_tracker.py    # Log prompt_tokens, completion_tokens, cost
│   │   └── exceptions.py      # EngineError, ParseError, RateLimitError
│   ├── prompts/               # All prompts live here — never elsewhere
│   │   └── __init__.py        # Exports all prompt constants
│   ├── calendar/              # Phase 6
│   ├── repurpose/             # Phase 6
│   ├── coach/                 # Phase 7
│   └── radar/                 # Phase 5
├── evals/
│   ├── framework.py           # Eval runner
│   └── cases/                 # Test cases per module
├── pyproject.toml
└── setup.py                   # pip install -e . → importable as iterra_ai
```

### 2.2 — Base engine class

```python
# iterra_ai/core/base_engine.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from pydantic import BaseModel

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

class BaseEngine(ABC, Generic[InputT, OutputT]):
    """
    All Iterra AI modules extend this class.
    Enforces: typed I/O, cost tracking, error handling, prompt versioning.
    """

    def __init__(self):
        from iterra_ai.core.client import get_anthropic_client
        from iterra_ai.core.cost_tracker import CostTracker
        self._client = get_anthropic_client()
        self._tracker = CostTracker()

    @abstractmethod
    def generate(self, input: InputT) -> OutputT:
        """Every engine must implement this."""
        ...

    def _call_llm(self, system: str, user: str, max_tokens: int = 2000) -> str:
        """
        Calls Anthropic API. Logs cost. Raises EngineError on failure.
        Returns raw text content from the response.
        """
        try:
            response = self._client.messages.create(
                model=self._get_model(),
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            self._tracker.log(
                engine=self.__class__.__name__,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            return response.content[0].text
        except Exception as e:
            from iterra_ai.core.exceptions import EngineError
            raise EngineError(f"{self.__class__.__name__} failed: {e}") from e

    def _parse_json_output(self, raw: str, schema: type[OutputT]) -> OutputT:
        """
        Parses LLM JSON output into a Pydantic model.
        Strips markdown fences if present. Raises ParseError on failure.
        """
        import json
        from iterra_ai.core.exceptions import ParseError
        cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return schema.model_validate_json(cleaned)
        except Exception as e:
            raise ParseError(f"Failed to parse {schema.__name__}: {e}\nRaw: {raw}") from e

    def _get_model(self) -> str:
        import os
        return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
```

### 2.3 — Cost tracker

```python
# iterra_ai/core/cost_tracker.py
import logging
from dataclasses import dataclass

logger = logging.getLogger("iterra_ai.cost")

# claude-sonnet-4-5 pricing as of 2025 (update if pricing changes)
INPUT_COST_PER_1K  = 0.003
OUTPUT_COST_PER_1K = 0.015

@dataclass
class UsageLog:
    engine: str
    input_tokens: int
    output_tokens: int
    cost_usd: float

class CostTracker:
    def log(self, engine: str, input_tokens: int, output_tokens: int):
        cost = (input_tokens / 1000 * INPUT_COST_PER_1K +
                output_tokens / 1000 * OUTPUT_COST_PER_1K)
        entry = UsageLog(engine=engine, input_tokens=input_tokens,
                         output_tokens=output_tokens, cost_usd=cost)
        logger.info(
            "LLM_USAGE engine=%s input_tokens=%d output_tokens=%d cost_usd=%.6f",
            engine, input_tokens, output_tokens, cost
        )
        # TODO Phase 4+: persist to DB for cost dashboard
        return entry
```

### 2.4 — Eval framework skeleton

```python
# evals/framework.py
from dataclasses import dataclass
from typing import Callable

@dataclass
class EvalCase:
    name: str
    input: dict
    expected_keys: list[str]       # output must contain these keys
    quality_checker: Callable | None = None  # optional fn(output) -> bool

class EvalRunner:
    def run(self, engine, cases: list[EvalCase]) -> dict:
        results = []
        for case in cases:
            try:
                output = engine.generate(engine.InputSchema(**case.input))
                output_dict = output.model_dump()
                passed = all(k in output_dict for k in case.expected_keys)
                if case.quality_checker:
                    passed = passed and case.quality_checker(output_dict)
                results.append({"case": case.name, "passed": passed, "output": output_dict})
            except Exception as e:
                results.append({"case": case.name, "passed": False, "error": str(e)})
        return {
            "total": len(cases),
            "passed": sum(1 for r in results if r["passed"]),
            "results": results,
        }
```

**✅ Phase 2 Deliverable:** `from iterra_ai.core.base_engine import BaseEngine` imports cleanly. `pip install -e packages/ai-engine` works. Eval framework runs against a stub engine without errors.

---

## Phase 3 — LinkedIn OAuth + Data Sync
**Agent: `@backend` (routes/services) + `@ai-engineer` (Celery task)**
**Duration: 3–4 days**

### 3.1 — LinkedIn OAuth flow

**Backend: `app/routers/social.py`**

Schemas first (`app/schemas/social.py`):
```python
class OAuthConnectResponse(BaseModel):
    authorization_url: str

class SyncJobResponse(BaseModel):
    task_id: str
    status: str = "queued"

class ConnectionStatus(BaseModel):
    platform: str
    is_connected: bool
    platform_username: Optional[str]
    last_synced_at: Optional[datetime]
```

Routes:
```python
@router.get("/connect/linkedin", response_model=OAuthConnectResponse)
async def connect_linkedin(current_user = Depends(get_current_user)):
    url = social_service.build_linkedin_oauth_url(state=str(current_user.id))
    return OAuthConnectResponse(authorization_url=url)

@router.get("/callback/linkedin")
async def linkedin_callback(code: str, state: str, db = Depends(get_db)):
    return await social_service.handle_linkedin_callback(db, code=code, user_id=state)

@router.post("/sync", response_model=SyncJobResponse)
async def trigger_sync(platform: str, current_user = Depends(get_current_user)):
    task = sync_linkedin_posts.delay(user_id=str(current_user.id))
    return SyncJobResponse(task_id=task.id)

@router.get("/status", response_model=list[ConnectionStatus])
async def connection_status(current_user = Depends(get_current_user), db = Depends(get_db)):
    return await social_service.get_connection_status(db, current_user.id)
```

**`app/services/social_service.py`:**
- `build_linkedin_oauth_url(state: str) -> str` — builds the OAuth URL with scopes: `openid profile email w_member_social r_basicprofile`
- `handle_linkedin_callback(db, code, user_id)` — exchanges code for token, upserts to `social_connections`
- `get_connection_status(db, user_id)` — returns connection state per platform
- `refresh_linkedin_token(db, connection)` — refreshes expired token

**LinkedIn API scopes to request:**
```
openid profile email w_member_social r_basicprofile
```
Apply for `r_organization_social` immediately, but don't block on it.

### 3.2 — LinkedIn API client (`apps/api/app/core/linkedin_client.py`)

```python
class LinkedInClient:
    BASE = "https://api.linkedin.com"

    def __init__(self, access_token: str):
        self._token = access_token
        self._headers = {"Authorization": f"Bearer {access_token}",
                         "Content-Type": "application/json"}

    def get_profile(self) -> dict:
        # GET /v2/me?projection=(id,localizedFirstName,localizedLastName)
        ...

    def get_posts(self, user_urn: str, count=50, start=0) -> dict:
        # GET /v2/ugcPosts?q=authors&authors=List({user_urn})&count={count}&start={start}
        ...

    def get_social_actions(self, post_urn: str) -> dict:
        # GET /v2/socialActions/{encoded_urn}
        # Returns: { likesSummary: { totalLikes }, commentsSummary: { totalFirstLevelComments } }
        ...

    def publish_post(self, user_urn: str, text: str) -> dict:
        # POST /v2/ugcPosts
        body = {
            "author": user_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        ...
```

### 3.3 — Celery setup (`workers/celery/`)

```python
# workers/celery/celery_app.py
from celery import Celery
import os

celery_app = Celery(
    "iterra",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
    include=["workers.celery.tasks.sync", "workers.celery.tasks.publish",
             "workers.celery.tasks.radar"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    beat_schedule={
        "refresh-trends-every-3h": {
            "task": "workers.celery.tasks.radar.refresh_all_trends",
            "schedule": 10800,  # 3 hours in seconds
        }
    }
)
```

### 3.4 — Sync Celery task (`workers/celery/tasks/sync.py`)

```python
@celery_app.task(bind=True, max_retries=3, name="tasks.sync_linkedin_posts")
def sync_linkedin_posts(self, user_id: str):
    """
    Fetches user's LinkedIn posts + metrics. Upserts to DB.
    Triggers brand profile generation on first sync.
    """
    from app.core.database import SessionLocal
    from app.models.social_connection import SocialConnection
    from app.models.post import Post

    db = SessionLocal()
    try:
        connection = db.query(SocialConnection).filter_by(
            user_id=user_id, platform="linkedin", is_active=True
        ).first()
        if not connection:
            raise ValueError(f"No LinkedIn connection for user {user_id}")

        client = LinkedInClient(connection.access_token)

        # Step 1: Fetch profile to get user URN
        profile = client.get_profile()
        user_urn = f"urn:li:person:{profile['id']}"

        # Step 2: Paginate posts (up to 50)
        all_posts = []
        start = 0
        while True:
            resp = client.get_posts(user_urn, count=50, start=start)
            elements = resp.get("elements", [])
            all_posts.extend(elements)
            if len(elements) < 50:
                break
            start += 50
            if start >= 50:  # MVP: cap at 50 posts
                break

        # Step 3: Fetch metrics + upsert
        for post_data in all_posts:
            post_urn = post_data.get("id", "")
            actions = client.get_social_actions(post_urn)

            likes = actions.get("likesSummary", {}).get("totalLikes", 0)
            comments = actions.get("commentsSummary", {}).get("totalFirstLevelComments", 0)
            impressions = 0  # Requires MDP approval — leave 0 for now
            engagement_rate = (likes + comments) / max(impressions, likes + comments, 1)

            content = (post_data.get("specificContent", {})
                       .get("com.linkedin.ugc.ShareContent", {})
                       .get("shareCommentary", {})
                       .get("text", ""))

            # Upsert post to DB
            existing = db.query(Post).filter_by(platform_post_id=post_urn).first()
            if existing:
                existing.likes = likes
                existing.comments = comments
                existing.engagement_rate = engagement_rate
            else:
                db.add(Post(
                    user_id=user_id,
                    platform="linkedin",
                    platform_post_id=post_urn,
                    content=content,
                    content_type="text",
                    published_at=datetime.fromtimestamp(
                        post_data.get("firstPublishedAt", 0) / 1000
                    ),
                    likes=likes,
                    comments=comments,
                    impressions=impressions,
                    engagement_rate=engagement_rate,
                    raw_api_response=post_data,
                ))

        connection.last_synced_at = datetime.utcnow()
        db.commit()

        # Trigger brand report on first sync (or refresh)
        from workers.celery.tasks.brand import generate_brand_report
        generate_brand_report.delay(user_id=user_id)

        return {"synced": len(all_posts)}

    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()
```

### 3.5 — Frontend: Connect + sync UI
**Agent: `@frontend`**

Add to `app/(dashboard)/settings/page.tsx`:
- Show connected accounts with status badge (connected/disconnected)
- "Connect LinkedIn" button → fetches OAuth URL from `GET /social/connect/linkedin` → redirects user
- "Sync now" button → calls `POST /social/sync` → shows task status polling

Data flow:
```
SettingsPage → useSocialConnections() → social.store → social.service.ts → api.ts
```

**✅ Phase 3 Deliverable:** User connects LinkedIn, triggers a sync, and their posts appear in the `posts` table. The Celery worker logs show successful task completion.

---

## Phase 4 — Brand Profile Engine + Report UI
**Agent: `@ai-engineer` (engine) + `@backend` (routes) + `@frontend` (report page)**
**Duration: 4–5 days**

This is the core of the product. Everything downstream depends on the quality of this phase.

### 4.1 — BrandProfile Pydantic schemas

Define in `packages/ai-engine/iterra_ai/brand/schemas.py` AND mirror in `apps/api/app/schemas/brand.py`. The AI engine schema is the source of truth. The API schema wraps it.

```python
# iterra_ai/brand/schemas.py
class BrandProfileData(BaseModel):
    voice_tone: str
    positioning: str
    audience_description: str
    goals: str
    content_pillars: list[str]
    posting_style: str
    typical_post_length: Literal["short", "medium", "long"]
    hashtag_strategy: Literal["none", "minimal", "moderate", "aggressive"]
    cta_style: Literal["none", "soft", "direct"]
    best_performing_topics: list[str]
    underperforming_topics: list[str]
    best_performing_formats: list[str]
    peak_engagement_times: list[str]
    brand_keywords: list[str]
    phrases_to_avoid: list[str]
    writing_patterns: str
    platforms_active: list[str]
    linkedin_follower_range: str
    analysis_based_on_posts: int
    ai_confidence_score: float = Field(ge=0.0, le=1.0)
    last_analyzed_at: str  # ISO format

class BrandAnalysisInput(BaseModel):
    posts: list[PostSummary]  # Stripped-down post data for prompt
    full_name: str
    niche: str
    goals: str

class BrandAnalysisOutput(BaseModel):
    profile: BrandProfileData
    summary: str  # 2-3 sentence plain-language summary for display
```

### 4.2 — Brand Analysis prompts

```python
# iterra_ai/prompts/brand_v1.py

BRAND_ANALYSIS_SYSTEM_V1 = """
You are an expert content strategist and brand analyst. You analyze a creator's
past content and produce a structured Brand Profile JSON document.

Rules:
- Base every claim on EVIDENCE from the posts — if you cannot cite a pattern
  from at least 3 posts, say "insufficient data" for that field.
- Be honest, not flattering. The creator will edit this document — accuracy
  matters more than impressivity.
- For best_performing_topics and formats, rank strictly by engagement_rate,
  not by recency or frequency.
- Output ONLY valid JSON matching the BrandProfileData schema. No preamble,
  no markdown fences, no explanation.

BrandProfileData schema:
{schema}
""".strip()

BRAND_ANALYSIS_USER_V1 = """
Creator: {full_name}
Niche: {niche}
Self-reported goals: {goals}

Posts (sorted by engagement rate, descending):
{posts_block}

Produce the BrandProfileData JSON now.
""".strip()
```

### 4.3 — BrandProfileEngine

```python
# iterra_ai/brand/engine.py
from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.brand.schemas import BrandAnalysisInput, BrandAnalysisOutput, BrandProfileData
from iterra_ai.prompts.brand_v1 import BRAND_ANALYSIS_SYSTEM_V1, BRAND_ANALYSIS_USER_V1
import json

class BrandProfileEngine(BaseEngine[BrandAnalysisInput, BrandAnalysisOutput]):

    def generate(self, input: BrandAnalysisInput) -> BrandAnalysisOutput:
        posts_block = self._format_posts(input.posts)
        system = BRAND_ANALYSIS_SYSTEM_V1.format(
            schema=json.dumps(BrandProfileData.model_json_schema(), indent=2)
        )
        user = BRAND_ANALYSIS_USER_V1.format(
            full_name=input.full_name,
            niche=input.niche,
            goals=input.goals or "Not specified",
            posts_block=posts_block,
        )
        raw = self._call_llm(system=system, user=user, max_tokens=3000)
        profile = self._parse_json_output(raw, BrandProfileData)

        summary = self._generate_summary(profile)
        return BrandAnalysisOutput(profile=profile, summary=summary)

    def _format_posts(self, posts) -> str:
        lines = []
        for i, p in enumerate(posts[:30], 1):  # cap at 30 for token budget
            lines.append(
                f"[{i}] engagement_rate={p.engagement_rate:.3f} "
                f"likes={p.likes} comments={p.comments}\n"
                f"Content: {p.content[:400]}{'...' if len(p.content) > 400 else ''}\n"
            )
        return "\n---\n".join(lines)

    def _generate_summary(self, profile: BrandProfileData) -> str:
        """One short Claude call to produce a human-readable summary."""
        prompt = (
            f"In 2-3 sentences, summarize this creator's brand profile for them to read:\n"
            f"{profile.model_dump_json(indent=2)}\n"
            f"Be specific, not generic. Mention their niche, tone, and top content pillar."
        )
        return self._call_llm(system="You summarize creator brand profiles concisely.", user=prompt, max_tokens=200)
```

### 4.4 — Brand report Celery task

```python
# workers/celery/tasks/brand.py
@celery_app.task(bind=True, max_retries=2, name="tasks.generate_brand_report")
def generate_brand_report(self, user_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        posts = (db.query(Post)
                 .filter_by(user_id=user_id, platform="linkedin")
                 .order_by(Post.engagement_rate.desc())
                 .limit(30).all())

        if len(posts) < 3:
            # Not enough data — create a minimal profile and mark low confidence
            ...

        from iterra_ai.brand.engine import BrandProfileEngine
        from iterra_ai.brand.schemas import BrandAnalysisInput, PostSummary

        engine = BrandProfileEngine()
        result = engine.generate(BrandAnalysisInput(
            posts=[PostSummary(
                content=p.content,
                engagement_rate=p.engagement_rate,
                likes=p.likes,
                comments=p.comments,
                published_at=p.published_at.isoformat() if p.published_at else "",
            ) for p in posts],
            full_name=user.full_name,
            niche=user.niche or "General",
            goals=user.goals or "",
        ))

        # Upsert brand profile
        existing = db.query(BrandProfile).filter_by(user_id=user_id).first()
        if existing:
            existing.profile = result.profile.model_dump()
            existing.version += 1
            existing.ai_confidence_score = result.profile.ai_confidence_score
            existing.analysis_based_on_posts = len(posts)
            existing.is_confirmed = False
            existing.generated_at = datetime.utcnow()
        else:
            db.add(BrandProfile(
                user_id=user_id,
                profile=result.profile.model_dump(),
                ai_confidence_score=result.profile.ai_confidence_score,
                analysis_based_on_posts=len(posts),
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=120)
    finally:
        db.close()
```

### 4.5 — Brand profile API routes

```python
# app/schemas/brand.py
class BrandProfileResponse(BaseModel):
    id: UUID
    profile: dict       # BrandProfileData as dict
    summary: str
    version: int
    is_confirmed: bool
    ai_confidence_score: float
    analysis_based_on_posts: int
    generated_at: datetime

class BrandProfileUpdateRequest(BaseModel):
    profile: dict       # Partial updates OK — merge server-side

# app/routers/brand.py
@router.get("/", response_model=BrandProfileResponse)
async def get_brand_profile(current_user = Depends(get_current_user), db = Depends(get_db)):
    return await brand_service.get_profile(db, current_user.id)

@router.put("/", response_model=BrandProfileResponse)
async def update_brand_profile(
    data: BrandProfileUpdateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    return await brand_service.update_profile(db, current_user.id, data.profile)

@router.post("/confirm", response_model=BrandProfileResponse)
async def confirm_brand_profile(current_user = Depends(get_current_user), db = Depends(get_db)):
    return await brand_service.confirm_profile(db, current_user.id)

@router.post("/regenerate", response_model=dict)
async def regenerate_brand_profile(current_user = Depends(get_current_user)):
    task = generate_brand_report.delay(user_id=str(current_user.id))
    return {"task_id": task.id}
```

### 4.6 — Brand report page (frontend)
**Agent: `@frontend`**

Page: `app/(dashboard)/report/page.tsx`

Components:
- `BrandReportHeader` — name, confidence score badge, "Re-analyze" button
- `BrandProfileSection` — renders each profile field as editable card
  - Click to edit → inline textarea → save on blur → calls `PUT /brand/`
- `BrandSummaryCard` — the AI-generated 2-3 sentence summary, displayed prominently
- `ConfirmBanner` — sticky bottom bar: "Does this look like you?" → "Yes, this is me" button → calls `POST /brand/confirm`
- `PostsAnalyzedBadge` — "Based on 28 posts"

Data flow:
```
ReportPage → useBrandProfile() → brand.store → brand.service.ts → api.ts
```

Guard: if `is_confirmed === false`, show the ConfirmBanner. If no profile exists yet, show loading skeleton with "Analyzing your posts..." message.

### 4.7 — Eval cases for BrandProfileEngine

```python
# evals/cases/brand_cases.py
BRAND_EVAL_CASES = [
    EvalCase(
        name="sufficient_data_produces_pillars",
        input={"posts": [...10 sample posts...], "full_name": "Alex", "niche": "AI/ML", "goals": "Build audience"},
        expected_keys=["profile", "summary"],
        quality_checker=lambda o: len(o["profile"]["content_pillars"]) >= 2
    ),
    EvalCase(
        name="low_post_count_returns_low_confidence",
        input={"posts": [...2 sample posts...], "full_name": "Alex", "niche": "AI/ML", "goals": ""},
        expected_keys=["profile"],
        quality_checker=lambda o: o["profile"]["ai_confidence_score"] < 0.5
    ),
]
```

Run with: `python -m evals.run brand`

**✅ Phase 4 Deliverable:** After syncing LinkedIn, users see their AI-generated Brand Profile. They can edit any field, then click "This is me" to confirm. The confirm gate blocks access to content generation until set. Eval suite passes 100%.

---

## Phase 5 — Trend Radar
**Agent: `@ai-engineer` (engine + task) + `@backend` (routes) + `@frontend` (radar UI)**
**Duration: 2–3 days**

### 5.1 — TrendRadar engine

```python
# iterra_ai/radar/schemas.py
class TrendItem(BaseModel):
    topic: str
    raw_score: int          # 0-100 from Google Trends
    niche_relevance: float  # 0-1, scored by Claude
    related_queries: list[str]
    content_angle: str      # Claude-generated: "how to use this topic in a post"

class RadarInput(BaseModel):
    niche: str
    brand_keywords: list[str]
    raw_trends: list[dict]  # From pytrends or RSS

class RadarOutput(BaseModel):
    trends: list[TrendItem]
    top_pick: TrendItem     # highest relevance × raw_score
    fetched_at: str

# iterra_ai/radar/engine.py
class TrendRadarEngine(BaseEngine[RadarInput, RadarOutput]):
    def generate(self, input: RadarInput) -> RadarOutput:
        # Filter out obviously irrelevant trends before calling LLM
        # Use a single Claude call to score all trends at once (cheaper than per-trend)
        ...
```

### 5.2 — Trend data fetcher

Option A (recommended): Deploy `scripts/trends_service.py` as a FastAPI app on Railway free tier. pytrends wraps Google Trends.

Option B (zero infra fallback): Fetch Google Trends RSS at `https://trends.google.com/trends/trendingsearches/daily/rss?geo=US` and parse XML with `feedparser`.

```python
# workers/celery/tasks/radar.py
@celery_app.task(name="tasks.refresh_all_trends")
def refresh_all_trends():
    """Celery beat runs this every 3 hours."""
    db = SessionLocal()
    try:
        niches = [row[0] for row in
                  db.execute(text("SELECT DISTINCT niche FROM users WHERE onboarding_complete=true")).fetchall()]
        for niche in niches:
            refresh_trends_for_niche.delay(niche=niche)
    finally:
        db.close()

@celery_app.task(bind=True, name="tasks.refresh_trends_for_niche")
def refresh_trends_for_niche(self, niche: str):
    raw = fetch_raw_trends(niche)  # pytrends or RSS
    engine = TrendRadarEngine()
    result = engine.generate(RadarInput(niche=niche, brand_keywords=[], raw_trends=raw))
    # Upsert trend_snapshots table
    ...
```

### 5.3 — Trend API route

```python
# app/schemas/trend.py
class TrendResponse(BaseModel):
    trends: list[dict]
    top_pick: dict
    niche: str
    fetched_at: datetime
    cache_age_minutes: int

# app/routers/trends.py
@router.get("/", response_model=TrendResponse)
async def get_trends(current_user = Depends(get_current_user), db = Depends(get_db)):
    return await trend_service.get_trends_for_user(db, current_user)
    # Returns cached snapshot if <3h old, else triggers refresh task
```

### 5.4 — Trend Radar sidebar (frontend)

Component: `TrendRadarPanel` — used inside the content creation page (Phase 6).

Displays top 5 trends as clickable chips. Clicking a chip populates the prompt input with the trend topic.

```
useTrends() → trend.store → trend.service.ts → GET /trends/
```

**✅ Phase 5 Deliverable:** Trend snapshots refresh every 3 hours via Celery beat. `GET /trends/` returns relevant, scored trends for the user's niche. The radar panel renders in the dashboard (even if the post editor isn't built yet).

---

## Phase 6 — Content Generation (Calendar + Repurpose)
**Agent: `@ai-engineer` (engines) + `@backend` (routes) + `@frontend` (post editor)**
**Duration: 5–6 days**

### 6.1 — ContentCalendarEngine

```python
# iterra_ai/calendar/schemas.py
class ContentSuggestion(BaseModel):
    hook: str           # First 1-2 lines — the scroll-stopper
    angle: str          # Core argument in 1 sentence
    format: Literal["listicle", "hot-take", "story", "how-to", "case-study", "thread"]
    trend_tie: str      # Which trend, or "evergreen"
    why_it_works: str   # 1-sentence rationale from brand profile

class CalendarInput(BaseModel):
    brand_profile: dict             # BrandProfileData as dict
    trending_topics: list[str]
    platform: str
    user_prompt: Optional[str]      # Optional explicit topic

class CalendarOutput(BaseModel):
    suggestions: list[ContentSuggestion]  # Always 3
```

Prompts in: `iterra_ai/prompts/calendar_v1.py`

The system prompt instructs Claude to produce exactly 3 suggestions as a JSON array. Enforce with `_parse_json_output`.

### 6.2 — ContentGenerationEngine

```python
# iterra_ai/calendar/generation_engine.py
class GenerationInput(BaseModel):
    brand_profile: dict
    platform: Literal["linkedin", "instagram", "twitter"]
    user_prompt: str
    trend_context: Optional[str] = None
    suggestion: Optional[ContentSuggestion] = None  # Use suggestion as seed if provided

class GenerationOutput(BaseModel):
    content: str
    word_count: int
    estimated_read_time_seconds: int
    platform_char_count: int
    within_platform_limit: bool  # LinkedIn: 3000 chars, Instagram: 2200, Twitter: 280
```

The system prompt (`iterra_ai/prompts/generation_v1.py`) must:
- Read voice_tone, writing_patterns, hashtag_strategy from brand_profile
- Include banned phrases list: "In today's fast-paced world", "Game-changer", "Excited to share", "Delve into", "Leverage"
- Output ONLY the post text — no label, no preamble

### 6.3 — RepurposeEngine

```python
# iterra_ai/repurpose/engine.py
class RepurposeInput(BaseModel):
    original_content: str
    source_platform: str
    target_platform: Literal["instagram", "twitter"]
    brand_profile: dict

class RepurposeOutput(BaseModel):
    content: str
    platform_notes: str  # e.g. "Split into 4 tweets" or "Add image prompt below"
```

Prompts in: `iterra_ai/prompts/repurpose_v1.py`

Platform conventions baked into the prompt:
- Instagram: line breaks every 1-2 sentences, 5-10 hashtags at end, 150-300 words
- Twitter: 280-char limit, thread format if needed `[1/n]`, no hashtags in body

### 6.4 — Content API routes

```python
# app/schemas/content.py
class SuggestRequest(BaseModel):
    platform: str = "linkedin"
    topic: Optional[str] = None

class SuggestResponse(BaseModel):
    suggestions: list[dict]  # ContentSuggestion list

class GenerateRequest(BaseModel):
    platform: str
    prompt: str
    trend_used: Optional[str] = None
    suggestion: Optional[dict] = None

class GenerateResponse(BaseModel):
    draft_id: UUID
    content: str
    word_count: int
    within_platform_limit: bool

class RepurposeRequest(BaseModel):
    draft_id: UUID
    target_platform: Literal["instagram", "twitter"]

class RepurposeResponse(BaseModel):
    draft_id: UUID
    content: str
    platform: str

# app/routers/content.py
@router.post("/suggest", response_model=SuggestResponse)
@router.post("/generate", response_model=GenerateResponse)
@router.post("/repurpose", response_model=RepurposeResponse)
```

**`app/services/content_service.py`:**
- `suggest(db, user, req)` — loads brand profile + trends, calls `CalendarEngine.generate()`, returns 3 suggestions
- `generate(db, user, req)` — loads brand profile, calls `GenerationEngine.generate()`, saves to `content_drafts`
- `repurpose(db, user, req)` — loads draft + brand profile, calls `RepurposeEngine.generate()`, updates `content_drafts.repurposed_versions`

### 6.5 — Post editor page (frontend)
**Agent: `@frontend`**

Page: `app/(dashboard)/create/page.tsx`

Layout: two-column on desktop, stacked on mobile.

**Left panel:**
- Platform selector tabs (LinkedIn | Instagram | Twitter)
- Prompt textarea: "What do you want to write about?"
- `TrendRadarPanel` — chips of top 5 trends, clickable to fill prompt
- "Suggest for me" button → calls `POST /content/suggest` → shows 3 suggestion cards
- Each suggestion card has: hook preview, format badge, "Use this" button

**Right panel:**
- TipTap rich text editor — initialized with generated content
- Character counter (color-coded: green → yellow → red as limit approaches)
- "Repurpose" button → `RepurposeModal` (shows Instagram/Twitter versions in tabs)
- "Publish now" / "Schedule" buttons → `PublishModal`

Data flow:
```
CreatePage
  → useContentCreation()
      → content.store
          → content.service.ts
              → POST /content/suggest
              → POST /content/generate
              → POST /content/repurpose
```

Hook: `useContentCreation.ts` manages: `suggestions`, `currentDraft`, `repurposedVersions`, `isGenerating`, `isSuggesting`

Guard: if `brand_profile.is_confirmed === false`, show a blocking message: "Complete your Brand Profile before creating content."

**✅ Phase 6 Deliverable:** User can click "Suggest for me" to get 3 trend-informed post ideas, click one to generate a full post, repurpose it for Instagram/Twitter, and see it saved as a draft. Eval suite for both engines passes.

---

## Phase 7 — AI Engagement Coach
**Agent: `@ai-engineer` (engine) + `@backend` (route) + `@frontend` (analytics page)**
**Duration: 3–4 days**

The Engagement Coach analyzes individual posts or the user's full post history and provides structured feedback on what's working and why.

### 7.1 — EngagementCoach engine

```python
# iterra_ai/coach/schemas.py
class PostAnalysis(BaseModel):
    post_id: str
    hook_score: int             # 1-10
    hook_feedback: str
    tone_match_score: int       # 1-10 vs brand profile
    structure_score: int        # 1-10 (clarity, flow, readability)
    cta_effectiveness: str      # "none" | "weak" | "strong"
    top_strength: str           # What this post does best
    top_improvement: str        # Single most impactful change
    predicted_engagement: str   # "low" | "medium" | "high"

class CoachInput(BaseModel):
    post_content: str
    post_metrics: dict          # likes, comments, engagement_rate
    brand_profile: dict
    platform: str

class CoachOutput(BaseModel):
    analysis: PostAnalysis
    rewrite_suggestion: Optional[str]  # If hook_score < 6, offer an improved opening
```

Prompts: `iterra_ai/prompts/coach_v1.py`

### 7.2 — Batch analysis

Add a Celery task `tasks.analyze_recent_posts` that runs the Coach on the user's last 10 unanalyzed posts and stores results. Trigger this after each sync in addition to brand report generation.

```python
# Store analysis results in a new table: post_analyses
# Or add columns to posts table: hook_score, tone_match_score, structure_score, coach_feedback JSONB
```

### 7.3 — Analytics API route

```python
# app/routers/analytics.py
@router.get("/posts", response_model=list[PostWithAnalysis])
async def get_post_analytics(
    limit: int = 20,
    platform: str = "linkedin",
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    return await analytics_service.get_posts_with_analysis(db, current_user.id, limit, platform)

@router.post("/analyze/{post_id}", response_model=PostAnalysis)
async def analyze_post(post_id: UUID, current_user = Depends(get_current_user), db = Depends(get_db)):
    return await analytics_service.analyze_single_post(db, current_user.id, post_id)
```

### 7.4 — Analytics page (frontend)
**Agent: `@frontend`**

Page: `app/(dashboard)/analytics/page.tsx`

Components:
- `PostPerformanceTable` — sortable table: date, content preview, likes, comments, engagement rate, hook score, coach badge
- `PostCoachDrawer` — slide-in panel on row click: full coach analysis, hook feedback, rewrite suggestion
- `EngagementTrendChart` — recharts LineChart of engagement rate over time (30-day window)
- `TopPostCard` — best performing post with full coach breakdown

Data flow:
```
AnalyticsPage → usePostAnalytics() → analytics.store → analytics.service.ts → GET /analytics/posts
```

**✅ Phase 7 Deliverable:** Analytics page shows post history with AI coach scores. Clicking any post opens the coach analysis drawer with specific, actionable feedback.

---

## Phase 8 — Publishing + Scheduling + Calendar UI
**Agent: `@backend` (routes + publish service) + `@ai-engineer` (Celery task) + `@frontend` (calendar)**
**Duration: 3–4 days**

### 8.1 — Publish service (`app/services/publish_service.py`)

```python
async def publish_now(db, user_id: UUID, draft_id: UUID) -> dict:
    draft = db.query(ContentDraft).filter_by(id=draft_id, user_id=user_id).first()
    connection = db.query(SocialConnection).filter_by(
        user_id=user_id, platform=draft.platform, is_active=True
    ).first()

    client = LinkedInClient(connection.access_token)
    profile = client.get_profile()
    user_urn = f"urn:li:person:{profile['id']}"

    result = client.publish_post(user_urn, draft.content)
    post_urn = result.get("id")

    draft.status = "published"
    draft.platform_post_id = post_urn
    draft.published_at = datetime.utcnow()
    db.commit()
    return {"platform_post_id": post_urn, "published_at": draft.published_at.isoformat()}

async def schedule_post(db, user_id: UUID, draft_id: UUID, scheduled_for: datetime) -> dict:
    draft = db.query(ContentDraft).filter_by(id=draft_id, user_id=user_id).first()
    task = publish_scheduled_post.apply_async(
        args=[str(draft_id), str(user_id)],
        eta=scheduled_for
    )
    draft.status = "scheduled"
    draft.scheduled_for = scheduled_for
    draft.celery_task_id = task.id
    db.commit()
    return {"celery_task_id": task.id, "scheduled_for": scheduled_for.isoformat()}

async def cancel_scheduled_post(db, user_id: UUID, draft_id: UUID) -> dict:
    from celery.result import AsyncResult
    draft = db.query(ContentDraft).filter_by(id=draft_id, user_id=user_id).first()
    if draft.celery_task_id:
        AsyncResult(draft.celery_task_id).revoke(terminate=True)
    draft.status = "draft"
    draft.scheduled_for = None
    draft.celery_task_id = None
    db.commit()
    return {"status": "cancelled"}
```

### 8.2 — Publish routes

```python
# app/schemas/content.py (add to existing)
class PublishRequest(BaseModel):
    draft_id: UUID

class ScheduleRequest(BaseModel):
    draft_id: UUID
    scheduled_for: datetime     # Must be in the future

class PublishResponse(BaseModel):
    platform_post_id: str
    published_at: datetime

class ScheduleResponse(BaseModel):
    celery_task_id: str
    scheduled_for: datetime
    suggested_times: list[datetime]  # Peak time suggestions

# app/routers/content.py (add to existing)
@router.post("/publish", response_model=PublishResponse)
@router.post("/schedule", response_model=ScheduleResponse)
@router.delete("/schedule/{draft_id}")
```

### 8.3 — Publish Celery task

```python
# workers/celery/tasks/publish.py
@celery_app.task(bind=True, max_retries=3, name="tasks.publish_scheduled_post")
def publish_scheduled_post(self, draft_id: str, user_id: str):
    db = SessionLocal()
    try:
        from app.services.publish_service import publish_now
        import asyncio
        asyncio.run(publish_now(db, UUID(user_id), UUID(draft_id)))
    except Exception as e:
        db.rollback()
        draft = db.query(ContentDraft).get(UUID(draft_id))
        draft.publish_error = str(e)
        db.commit()
        raise self.retry(exc=e, countdown=300)  # retry after 5 min
    finally:
        db.close()
```

### 8.4 — Peak time suggestions

MVP heuristic (replace with analytics data later):

```python
def get_peak_time_suggestions(user_id, platform="linkedin") -> list[datetime]:
    """
    MVP: Return 3 hardcoded optimal LinkedIn windows for the next 7 days.
    Future: Derive from user's own post analytics (best time = highest avg engagement).
    """
    base_times = [
        {"weekday": 1, "hour": 9},   # Tuesday 9am
        {"weekday": 2, "hour": 12},  # Wednesday 12pm
        {"weekday": 3, "hour": 9},   # Thursday 9am
    ]
    now = datetime.utcnow()
    suggestions = []
    for t in base_times:
        next_occurrence = _next_weekday(now, t["weekday"]).replace(hour=t["hour"], minute=0)
        suggestions.append(next_occurrence)
    return suggestions
```

### 8.5 — PublishModal (frontend)
**Agent: `@frontend`**

Component: `PublishModal.tsx`

Two tabs: "Post now" and "Schedule"

Post now tab:
- Platform badge (LinkedIn)
- Preview of post content
- "Post now" confirm button → `POST /content/publish`
- Success state: checkmark + "Published to LinkedIn"

Schedule tab:
- Date + time picker
- 3 "Suggested times" chips (from API response)
- "Schedule" confirm button → `POST /content/schedule`
- Confirmation state with scheduled time

### 8.6 — Content Calendar page (frontend)

Page: `app/(dashboard)/calendar/page.tsx`

Library: `react-big-calendar` in month view.

Events on calendar:
- Scheduled drafts → amber color, click → shows draft content + "Cancel" + "Edit" + "Post now" options
- Published posts → green color, click → shows post + engagement metrics

```
CalendarPage → useContentCalendar() → calendar.store → calendar.service.ts
                                                         → GET /content/drafts?status=scheduled
                                                         → GET /posts (published)
```

**✅ Phase 8 Deliverable:** Full posting loop is complete. User can generate a post, publish immediately or schedule it, see it on the calendar, and cancel/reschedule. Celery handles delayed publishing reliably.

---

## Phase 9 — Instagram (Post-MVP)
**Agent: `@architect` to plan, then `@backend` + `@frontend`**
**Start: 2–3 weeks after Phase 8 ships**

**Prerequisites before writing any code:**
- [ ] Apply for Meta Graph API access at developers.facebook.com
- [ ] User's Instagram must be a Business or Creator account linked to a Facebook Page
- [ ] Scopes needed: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
- [ ] Instagram API does NOT support text-only posts — every post needs an image

**Tasks (ordered):**
1. Add Instagram to `social_connections` OAuth flow (new callback route)
2. Build `InstagramClient` class (separate from `LinkedInClient`)
3. Update `RepurposeEngine` to always include an "image prompt" in Instagram output
4. Add image upload support via Supabase Storage
5. Build image preview UI in `RepurposeModal`
6. Add Instagram publishing to `publish_service.py`
7. Update calendar UI to show Instagram posts separately

---

## Cross-Phase Checklist

Run before every PR:

```bash
make lint     # ruff + eslint — zero tolerance for warnings
make test     # pytest (backend) + jest (frontend)
make types    # regenerate after any API schema change
```

After every model change:
```bash
make migrate
# Verify migration has both upgrade() and downgrade()
```

After every prompt change:
```bash
python -m evals.run {module}
# Must pass before shipping
```

---

## Per-Phase Startup Prompt Template

Use this when starting a new Claude Code session for each phase:

```
I'm building Iterra, an AI Content Strategy Platform.

Architecture context: [paste CLAUDE.md]
Implementation plan: I'm on Phase {N} — {Phase Name}.

The task for this session: {specific task from this plan}

Key constraints from CLAUDE.md:
- No logic in FastAPI routes — delegate to services/
- AI engine imported as a package, never called over HTTP
- All prompts in packages/ai-engine/iterra_ai/prompts/
- Contracts (Pydantic schemas) before any implementation
- run make types after schema changes

Let's start with the schema definitions first.
```

---

*Plan version: 1.0 | Architecture: FastAPI + Next.js 14 + Celery + Redis + Supabase + Anthropic*
*Agents: @architect · @backend · @frontend · @ai-engineer*
