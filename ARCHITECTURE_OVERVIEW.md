# Ittera - Complete Architecture Overview

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Data Flow](#data-flow)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [AI Engine Architecture](#ai-engine-architecture)
8. [Frontend Architecture](#frontend-architecture)
9. [Authentication Flow](#authentication-flow)
10. [Module Deep Dive](#module-deep-dive)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ITTERA PLATFORM                              │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   Next.js 14     │────────▶│   FastAPI        │────────▶│   PostgreSQL     │
│   Frontend       │  HTTPS  │   Backend        │   SQL   │   Database       │
│   (Port 3000)    │◀────────│   (Port 8000)    │◀────────│   (Port 5432)    │
└──────────────────┘         └──────────────────┘         └──────────────────┘
        │                             │                             │
        │                             │                             │
        ▼                             ▼                             ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   Supabase       │         │   Iterra AI      │         │   Redis          │
│   Auth           │         │   Package        │         │   (Celery)       │
│                  │         │   (pip install)  │         │   (Port 6379)    │
└──────────────────┘         └──────────────────┘         └──────────────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │   Anthropic      │
                             │   Claude API     │
                             └──────────────────┘

External Integrations:
├── Google Drive (OAuth + Storage)
├── LinkedIn (OAuth + Scraping)
└── Google Trends / Reddit / YouTube (Trend Radar)
```


## Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Authentication**: Supabase Auth
- **API Client**: Custom typed API wrapper (`@/lib/api.ts`)
- **UI Components**: Custom components + shadcn/ui patterns

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Authentication**: Dual JWT (Supabase + custom tokens)
- **Validation**: Pydantic v2
- **Security**: passlib, python-jose

### AI Engine
- **Package**: `iterra_ai` (internal pip package)
- **LLM Provider**: Anthropic Claude (claude-sonnet-4-5)
- **Architecture**: Typed engines with BaseEngine pattern
- **Modules**: Calendar, Coach, Radar, Repurpose, Brand Profile

### Database
- **Primary**: PostgreSQL 16
- **Cache/Queue**: Redis (for Celery)
- **External Storage**: Google Drive (via OAuth)

### Background Jobs
- **Task Queue**: Celery
- **Broker**: Redis
- **Workers**: LinkedIn scraping, scheduled posts

### Infrastructure
- **Containerization**: Docker + docker-compose
- **Reverse Proxy**: Nginx
- **CI/CD**: GitHub Actions (api.yml, web.yml, ai-engine.yml)
- **Email**: SMTP (smtplib) for waitlist confirmation emails


## Project Structure

```
Ittera/
├── apps/
│   ├── api/                    # FastAPI Backend
│   │   ├── app/
│   │   │   ├── core/          # Security (JWT, encryption), database config
│   │   │   ├── db/            # Database session, migrations, datetime helpers
│   │   │   ├── dependencies/  # FastAPI dependencies (auth.py, db.py)
│   │   │   ├── middleware/    # Auth middleware, rate limiting
│   │   │   ├── models/        # SQLAlchemy models (10 models)
│   │   │   ├── modules/       # Feature modules (brand_profile/)
│   │   │   ├── routers/       # API route handlers (15 routers)
│   │   │   ├── schemas/       # Pydantic request/response schemas
│   │   │   └── services/      # Business logic layer (15 services + email + mock_data)
│   │   ├── config.py         # Settings via pydantic-settings (at api/ root)
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── requirements.txt  # Python dependencies
│   │   ├── requirements-dev.txt  # Dev/test dependencies
│   │   └── alembic.ini       # Database migration config
│   │
│   └── web/                   # Next.js Frontend
│       ├── src/
│       │   ├── app/          # Next.js 14 App Router
│       │   │   ├── (auth)/   # Auth pages (login, onboarding)
│       │   │   │   ├── login/
│       │   │   │   └── onboarding/
│       │   │   │       ├── context/
│       │   │   │       └── persona/
│       │   │   ├── (product)/ # Protected product pages
│       │   │   │   ├── analytics/
│       │   │   │   ├── calendar/
│       │   │   │   ├── coach/
│       │   │   │   ├── create/
│       │   │   │   ├── dashboard/
│       │   │   │   ├── radar/
│       │   │   │   └── settings/
│       │   │   ├── auth/     # OAuth callbacks
│       │   │   └── demo/     # Public demo
│       │   ├── components/   # React components
│       │   │   ├── auth/     # Auth-related components
│       │   │   ├── layout/   # Navbar, Footer
│       │   │   ├── motion/   # Animation wrapper components
│       │   │   ├── product/  # ProductShell, StatusPill
│       │   │   ├── sections/ # Landing page sections (14 sections)
│       │   │   └── ui/       # Reusable UI primitives (23 components)
│       │   ├── context/      # React Context (AuthContext, ThemeContext)
│       │   ├── features/     # Feature-specific components
│       │   ├── hooks/        # Custom React hooks (useAuth, useProduct)
│       │   ├── lib/          # Utilities (api.ts, supabase.ts, utils.ts, animations.ts, constants.ts)
│       │   ├── services/     # API service layer (api.ts fetch wrapper, product.service.ts)
│       │   └── stores/       # Zustand state (product.store.ts — single consolidated store)
│       └── package.json
│
├── packages/
│   ├── ai-engine/            # Iterra AI Package
│   │   ├── iterra_ai/
│   │   │   ├── brand_profile/ # Brand voice analysis
│   │   │   ├── calendar/      # Content calendar generation
│   │   │   ├── coach/         # Post analysis & scoring
│   │   │   ├── content/       # Content platform rules and generation
│   │   │   ├── core/          # Base engine, client, cost tracking, exceptions
│   │   │   ├── evals/         # LLM evaluation framework
│   │   │   ├── pipelines/     # Multi-step AI workflows
│   │   │   ├── prompts/       # All LLM prompts (brand_profile, calendar, coach, radar, repurpose)
│   │   │   ├── radar/         # Trend detection
│   │   │   └── repurpose/     # Cross-platform content adaptation
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── shared-types/         # Auto-generated TypeScript types from OpenAPI
│
├── workers/
│   └── celery/               # Background job workers
│       ├── tasks/
│       │   ├── scraper.py          # LinkedIn post scraping
│       │   ├── brand_profile.py    # Brand profile generation
│       │   ├── radar_scan.py       # Scheduled radar trend scans
│       │   ├── performance_sync.py # Performance data sync
│       │   └── weekly_reports.py   # Weekly report generation
│       ├── app.py           # Celery app configuration
│       └── beat_schedule.py # Celery Beat periodic task schedule
│
├── docker-compose.yml        # Local development infrastructure
├── CLAUDE.md                 # Agent personas & conventions
├── README.md                 # Project overview
└── ITERRA_IMPLEMENTATION_PLAN.md  # Phased rollout plan
```


## Data Flow

### Content Creation Flow
```
┌─────────────┐
│   User      │
│  (Frontend) │
└──────┬──────┘
       │ 1. Request content suggestions
       ▼
┌─────────────────────────────────────────┐
│  POST /api/v1/content/suggest           │
│  Router: content.py                     │
└──────┬──────────────────────────────────┘
       │ 2. Delegate to service
       ▼
┌─────────────────────────────────────────┐
│  ContentService.suggest()               │
│  - Fetch user trends                    │
│  - Generate 3 content suggestions       │
└──────┬──────────────────────────────────┘
       │ 3. Return suggestions
       ▼
┌─────────────┐
│   User      │
│  Selects    │
│  suggestion │
└──────┬──────┘
       │ 4. Generate full content
       ▼
┌─────────────────────────────────────────┐
│  POST /api/v1/content/generate          │
│  Router: content.py                     │
└──────┬──────────────────────────────────┘
       │ 5. Check brand profile confirmed
       ▼
┌─────────────────────────────────────────┐
│  ContentService.generate()              │
│  - Validate brand profile               │
│  - Generate content (mock or AI)        │
│  - Save to ContentDraft table           │
└──────┬──────────────────────────────────┘
       │ 6. Return draft
       ▼
┌─────────────┐
│   User      │
│  Reviews    │
│  draft      │
└──────┬──────┘
       │ 7. Publish or schedule
       ▼
┌─────────────────────────────────────────┐
│  POST /api/v1/content/publish           │
│  OR POST /api/v1/content/schedule       │
└──────┬──────────────────────────────────┘
       │ 8. Update draft status
       ▼
┌─────────────────────────────────────────┐
│  Database: content_drafts               │
│  status: 'published' or 'scheduled'     │
└─────────────────────────────────────────┘
```


### AI Calendar Generation Flow
```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ 1. Request calendar
       │    (niche, platforms, frequency)
       ▼
┌─────────────────────────────────────────┐
│  POST /api/v1/calendar/generate         │
│  Router: calendar.py                    │
└──────┬──────────────────────────────────┘
       │ 2. Delegate to service
       ▼
┌─────────────────────────────────────────┐
│  CalendarService.generate()             │
│  - Check if USE_ITERRA_AI_CALENDAR=true │
└──────┬──────────────────────────────────┘
       │ 3a. If AI enabled
       ▼
┌─────────────────────────────────────────┐
│  iterra_ai.calendar.CalendarEngine      │
│  - Format prompt with user input        │
│  - Call Claude API                      │
│  - Parse JSON response                  │
└──────┬──────────────────────────────────┘
       │ 3b. If AI disabled (fallback)
       ▼
┌─────────────────────────────────────────┐
│  Mock Calendar Generation               │
│  - Generate simple slots                │
│  - Return structured plan               │
└──────┬──────────────────────────────────┘
       │ 4. Return CalendarOutput
       ▼
┌─────────────┐
│   User      │
│  Views plan │
└─────────────┘
```

### LinkedIn Scraping Flow (Background Job)
```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ 1. Connect LinkedIn credentials
       ▼
┌─────────────────────────────────────────┐
│  POST /api/v1/social/credentials/       │
│       linkedin                          │
└──────┬──────────────────────────────────┘
       │ 2. Validate & encrypt credentials
       ▼
┌─────────────────────────────────────────┐
│  SocialService.store_linkedin_          │
│  credentials()                          │
│  - Test login with linkedin-api         │
│  - Encrypt username/password            │
│  - Save to social_connections table     │
└──────┬──────────────────────────────────┘
       │ 3. User triggers sync
       ▼
┌─────────────────────────────────────────┐
│  POST /api/v1/social/sync               │
└──────┬──────────────────────────────────┘
       │ 4. Enqueue Celery task
       ▼
┌─────────────────────────────────────────┐
│  Celery Task: scrape_linkedin_posts     │
│  - Decrypt credentials                  │
│  - Scrape user's posts                  │
│  - Save to Google Drive (if connected)  │
│  - Update social_connections metadata   │
└──────┬──────────────────────────────────┘
       │ 5. Task complete
       ▼
┌─────────────┐
│   User      │
│  Polls      │
│  /sync/     │
│  status     │
└─────────────┘
```


## API Endpoints

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Register new user with email/password | No |
| POST | `/login` | Login with email/password | No |
| POST | `/logout` | Logout current user (clears cookie) | No |
| GET | `/me` | Get current user profile | Yes |
| POST | `/onboarding` | Complete user onboarding (name, niche, goals, platform) | Yes |
| GET | `/google/start` | Initiate Google OAuth flow | No |
| GET | `/google/callback` | Handle Google OAuth callback | No |
| GET | `/linkedin/start` | Initiate LinkedIn OAuth flow (OpenID) | No |
| GET | `/linkedin/callback` | Handle LinkedIn OAuth callback | No |

> **Note**: The `/onboarding` endpoint lives under `/api/v1/auth/onboarding`, not a separate router. There is no standalone `/api/v1/onboarding` router.

### Waitlist (`/api/v1/waitlist`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Get waitlist stats | No |
| POST | `/` | Join waitlist | No |
| GET | `/me` | Get my waitlist status | Yes |

### Context (`/api/v1/context`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Get assembled context (Permanent + Persona + Report) | Yes |
| GET | `/prompt` | Get raw system prompt string (debugging) | Yes |
| PATCH | `/` | Update permanent context identity fields | Yes |

### Brand Profile (`/api/v1/brand-profile`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Get user's brand profile | Yes |
| POST | `/generate` | Generate AI brand profile from posts | Yes |
| PATCH | `/` | Update brand profile manually | Yes |
| POST | `/confirm` | Confirm brand profile | Yes |

### Content (`/api/v1/content`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/suggest` | Get content suggestions based on trends | Yes |
| POST | `/generate` | Generate full content from suggestion | Yes |
| POST | `/repurpose` | Repurpose draft for another platform | Yes |
| GET | `/drafts` | List all drafts (filter by status) | Yes |
| GET | `/drafts/{id}` | Get specific draft | Yes |
| PATCH | `/drafts/{id}` | Update draft content/status | Yes |
| POST | `/publish` | Publish draft immediately | Yes |
| POST | `/schedule` | Schedule draft for future | Yes |
| DELETE | `/schedule/{id}` | Cancel scheduled post | Yes |
| GET | `/calendar` | Get calendar events (scheduled/published) | Yes |

### Calendar (`/api/v1/calendar`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/generate` | Generate AI content calendar | Yes |
| GET | `/` | List saved calendars | Yes |


### Coach (`/api/v1/coach`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/analyze` | Analyze post quality & get suggestions | Yes |

### Radar (`/api/v1/radar`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/scan` | Scan for trending topics in niche | Yes |

### Repurpose (`/api/v1/repurpose`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/` | Repurpose content for multiple platforms | Yes |

### Trends (`/api/v1/trends`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Get trends for user's niche | Yes |
| POST | `/refresh` | Refresh trend data | Yes |

### Social Connections (`/api/v1/social`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/connect/linkedin` | Get LinkedIn OAuth URL | Yes |
| GET | `/callback/linkedin` | Handle LinkedIn OAuth callback | No |
| GET | `/connect/google-drive` | Get Google Drive OAuth URL | Yes |
| GET | `/callback/google-drive` | Handle Google Drive OAuth callback | No |
| POST | `/credentials/linkedin` | Store LinkedIn scraper credentials | Yes |
| GET | `/status` | Get all social connection statuses | Yes |
| POST | `/sync` | Trigger LinkedIn post scraping | Yes |
| GET | `/sync/status/{task_id}` | Check scraping task status | Yes |

### LinkedIn (`/api/v1/linkedin`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/status` | Get LinkedIn connection status | Yes |
| POST | `/connect/mock` | Mock LinkedIn connection (dev) | Yes |
| POST | `/sync` | Mock sync LinkedIn posts (dev) | Yes |

### Analytics (`/api/v1/analytics`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/posts` | List posts with analysis (filter by platform, limit) | Yes |
| POST | `/analyze/{post_id}` | Run/refresh analysis for a specific post | Yes |

### Storage (`/api/v1/storage`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/upload` | Upload file to Google Drive | Yes |
| GET | `/files` | List files in Drive | Yes |


## Database Schema

### Core Tables

#### `users`
```sql
id                    VARCHAR (UUID, PK)
email                 VARCHAR (UNIQUE, NOT NULL)
hashed_password       VARCHAR (NOT NULL)
name                  VARCHAR (NOT NULL)
full_name             VARCHAR
niche                 VARCHAR
goals                 TEXT
primary_platform      VARCHAR (default: 'linkedin')
storage_preference    VARCHAR (default: 'database')
onboarding_complete   BOOLEAN (default: false)
created_at            TIMESTAMP
updated_at            TIMESTAMP
```

#### `user_contexts`
```sql
id                VARCHAR (UUID, PK)
user_id           VARCHAR (FK -> users.id, INDEXED)
brand_name        VARCHAR (nullable)
bio               TEXT (nullable)
target_audience   TEXT (nullable)
content_mission   TEXT (nullable)
platform_facts    JSON (default: dict)
version           INTEGER (default: 1)
change_source     VARCHAR (default: 'onboarding')
change_summary    TEXT (nullable)
is_active         BOOLEAN (default: true)
created_at        TIMESTAMP
```

#### `brand_profiles`
```sql
id                      VARCHAR (UUID, PK)
user_id                 VARCHAR (FK → users.id, UNIQUE)
profile                 JSON (voice_tone, audience, core_topics, etc.)
version                 INTEGER (default: 1)
ai_confidence_score     FLOAT (default: 0.0)
is_confirmed            BOOLEAN (default: false)
analysis_based_on_posts INTEGER (default: 0)
drive_analysis_file_id  VARCHAR (nullable)
generated_at            TIMESTAMP
confirmed_at            TIMESTAMP (nullable)
updated_at              TIMESTAMP
```

#### `content_drafts`
```sql
id                   VARCHAR (UUID, PK)
user_id              VARCHAR (FK → users.id, INDEXED)
platform             VARCHAR (default: 'linkedin')
content              TEXT (nullable, can be in Drive)
drive_file_id        VARCHAR (nullable)
repurposed_versions  JSON (dict of platform → content)
prompt_used          TEXT (nullable)
trend_used           VARCHAR (nullable)
generation_model     VARCHAR (default: 'claude-sonnet-4-5')
status               VARCHAR (default: 'draft')
scheduled_for        TIMESTAMP (nullable)
celery_task_id       VARCHAR (nullable)
platform_post_id     VARCHAR (nullable)
published_at         TIMESTAMP (nullable)
publish_error        TEXT (nullable)
created_at           TIMESTAMP
updated_at           TIMESTAMP
```

#### `content_plans`
```sql
id          VARCHAR (UUID, PK)
user_id     VARCHAR (FK → users.id)
niche       VARCHAR (NOT NULL)
platforms   JSON (list of platforms)
slots       JSON (list of content slots)
created_at  TIMESTAMP
```


#### `social_connections`
```sql
id                   VARCHAR (UUID, PK)
user_id              VARCHAR (FK → users.id, INDEXED)
platform             VARCHAR (INDEXED: 'linkedin', 'google_drive')
platform_user_id     VARCHAR (NOT NULL)
platform_username    VARCHAR (nullable)
access_token         VARCHAR (NOT NULL)
refresh_token        VARCHAR (nullable)
token_expires_at     TIMESTAMP (nullable)
scopes               JSON (list of OAuth scopes)
last_synced_at       TIMESTAMP (nullable)
is_active            BOOLEAN (default: true)
metadata             JSON (platform-specific data)
created_at           TIMESTAMP
updated_at           TIMESTAMP
```

#### `posts`
```sql
id                VARCHAR (UUID, PK)
user_id           VARCHAR (FK → users.id, INDEXED)
platform          VARCHAR (NOT NULL)
platform_post_id  VARCHAR (nullable, INDEXED)
content           TEXT (NOT NULL)
content_type      VARCHAR (NOT NULL)
published_at      TIMESTAMP (nullable)
impressions       INTEGER (default: 0)
likes             INTEGER (default: 0)
comments          INTEGER (default: 0)
shares            INTEGER (default: 0)
engagement_rate   FLOAT (default: 0.0)
topics            JSON (list of topics)
tone              VARCHAR (nullable)
raw_api_response  JSON (nullable)
synced_at         TIMESTAMP (nullable)
created_at        TIMESTAMP
```

#### `post_analyses` (table name: `post_analyses`)
```sql
id                  VARCHAR (UUID, PK)
post_id             VARCHAR (FK → posts.id, UNIQUE, CASCADE DELETE)
hook_score          INTEGER (NOT NULL)
tone_match_score    INTEGER (NOT NULL)
structure_score     INTEGER (NOT NULL)
cta_effectiveness   VARCHAR (NOT NULL, e.g. 'strong' | 'weak')
coach_feedback      JSON (top_strength, top_improvement, predicted_engagement)
rewrite_suggestion  TEXT (nullable)
created_at          TIMESTAMP
```

#### `trend_snapshots`
```sql
id          VARCHAR (UUID, PK)
user_id     VARCHAR (FK → users.id, INDEXED)
niche       VARCHAR (NOT NULL)
trends      JSON (list of trend items)
source      VARCHAR (default: 'mock')
captured_at TIMESTAMP
```

#### `waitlist`
```sql
id          VARCHAR (UUID, PK)
email       VARCHAR (UNIQUE, NOT NULL)
name        VARCHAR (nullable)
profession  VARCHAR (nullable)
position    INTEGER (auto-increment)
joined_at   TIMESTAMP
```


### Database Relationships

```
users (1) ──────────────────────────────────────────────────────────┐
  │                                                                  │
  │ (1:N)                                                            │
  ├──▶ user_contexts                                                 │
  │                                                                  │
  │ (1:1)                                                            │
  ├──▶ brand_profiles                                                │
  │                                                                  │
  │ (1:N)                                                            │
  ├──▶ content_drafts                                                │
  ├──▶ content_plans                                                 │
  ├──▶ social_connections                                            │
  ├──▶ posts ──(1:1)──▶ post_analysis                               │
  └──▶ trend_snapshots                                               │
```


## AI Engine Architecture

### Package Structure: `iterra_ai`

The AI engine is a standalone pip package that can be imported directly into the FastAPI backend. It's NOT a microservice.

```
iterra_ai/
├── core/
│   ├── base_engine.py      # Abstract base class for all AI engines
│   ├── client.py           # Anthropic client singleton
│   ├── cost_tracker.py     # Token usage tracking
│   └── exceptions.py       # Custom exceptions
│
├── prompts/
│   ├── brand_profile.py    # Brand analysis prompts
│   ├── calendar.py         # Calendar generation prompts
│   ├── coach.py            # Post analysis prompts
│   ├── radar.py            # Trend detection prompts
│   └── repurpose.py        # Content repurposing prompts
│
├── calendar/
│   ├── engine.py           # CalendarEngine
│   └── schemas.py          # CalendarInput, CalendarOutput
│
├── coach/
│   ├── engine.py           # CoachEngine
│   └── schemas.py          # CoachInput, CoachOutput
│
├── radar/
│   ├── engine.py           # RadarEngine
│   └── schemas.py          # RadarInput, RadarOutput
│
├── repurpose/
│   ├── engine.py           # RepurposeEngine
│   └── schemas.py          # RepurposeInput, RepurposeOutput
│
├── brand_profile/
│   ├── engine.py           # BrandProfileEngine
│   └── schemas.py          # BrandProfileInput, BrandProfileOutput
│
├── content/
│   ├── engine.py           # Content generation engine
│   ├── platform_rules.py   # Platform-specific prompt rules
│   └── schemas.py          # Content generation schemas
│
├── pipelines/
│   └── base.py             # Multi-step AI workflows
│
└── evals/
    ├── framework.py        # LLM evaluation framework
    └── cases/              # Test cases for each engine
```


### BaseEngine Pattern

All AI engines inherit from `BaseEngine[InputT, OutputT]`:

```python
class BaseEngine(ABC, Generic[InputT, OutputT]):
    def __init__(self, client=None, tracker: CostTracker | None = None):
        self._client = client
        self._tracker = tracker or CostTracker()
    
    @abstractmethod
    def generate(self, input: InputT) -> OutputT:
        """Generate typed output for typed input."""
    
    def _call_llm(self, system: str, user: str, max_tokens: int = 2000) -> str:
        """Call Anthropic Claude API with cost tracking."""
    
    def _parse_json_output(self, raw: str, schema: type[OutputT]) -> OutputT:
        """Parse and validate LLM JSON response."""
```

### Engine Usage Example

```python
# In FastAPI service
from iterra_ai.calendar.engine import CalendarEngine
from iterra_ai.calendar.schemas import CalendarInput

engine = CalendarEngine()
engine_input = CalendarInput(
    niche="AI content strategy",
    platforms=["linkedin", "twitter"],
    posting_frequency=5
)
result = engine.generate(engine_input)
# result is typed as CalendarOutput
```

### AI Modules

1. **Calendar Engine** (`iterra_ai.calendar`)
   - Generates weekly/monthly content calendars
   - Input: niche, platforms, frequency, historical posts
   - Output: Structured content plan with topics, dates, formats

2. **Coach Engine** (`iterra_ai.coach`)
   - Analyzes post quality (hook, tone, CTA, structure)
   - Scores content 0.0-1.0
   - Provides platform-specific improvement suggestions

3. **Radar Engine** (`iterra_ai.radar`)
   - Detects trending topics in user's niche
   - Sources: Reddit, YouTube, Google Trends (planned)
   - Currently uses curated trend database

4. **Repurpose Engine** (`iterra_ai.repurpose`)
   - Adapts content for different platforms
   - Maintains core message, adjusts format/length
   - Experimental: template-based (LLM path in progress)

5. **Brand Profile Engine** (`iterra_ai.brand_profile`)
   - Analyzes user's past posts
   - Extracts voice, tone, topics, patterns
   - Generates brand profile for consistent content


## Frontend Architecture

### Next.js 14 App Router Structure

```
src/app/
├── (auth)/                 # Auth route group (no product layout)
│   └── login/
│       └── page.tsx       # Login page
│
├── (product)/             # Protected product routes (shared layout)
│   ├── layout.tsx         # Product layout (sidebar, nav)
│   ├── dashboard/
│   │   └── page.tsx       # Main dashboard
│   ├── calendar/
│   │   └── page.tsx       # Content calendar view
│   ├── create/
│   │   └── page.tsx       # Content creation wizard
│   ├── coach/
│   │   └── page.tsx       # Post analysis tool
│   ├── radar/
│   │   └── page.tsx       # Trend radar
│   ├── analytics/
│   │   └── page.tsx       # Analytics dashboard
│   └── settings/
│       └── page.tsx       # User settings
│
├── auth/
│   └── callback/
│       └── page.tsx       # OAuth callback handler
│
├── demo/
│   └── page.tsx           # Public demo page
│
├── layout.tsx             # Root layout (providers, fonts)
├── page.tsx               # Landing page
└── globals.css            # Global styles
```

### State Management (Zustand)

The frontend uses a **single consolidated Zustand store** (`stores/product.store.ts`) that manages all product state:

```typescript
// stores/product.store.ts — single store for all product state
type ProductState = {
  linkedin: LinkedInStatus | null;
  brandProfile: BrandProfile | null;
  trends: TrendResponse | null;
  suggestions: Suggestion[];
  drafts: Draft[];
  analytics: AnalyticsPost[];
  calendar: CalendarEvent[];
  currentDraft: Draft | null;
  coachResult: CoachResult | null;
  radarResult: RadarResult | null;
  isLoading: boolean;
  error: string | null;
  // Actions: loadDashboard, connectLinkedIn, syncLinkedIn,
  //   generateBrandProfile, confirmBrandProfile, updateBrandProfile,
  //   loadTrends, suggest, generate, repurpose, loadDrafts,
  //   selectDraft, publish, schedule, cancelSchedule,
  //   loadAnalytics, analyze, loadCalendar, coachAnalyze, scanRadar
};
```

Auth state is managed separately via `context/AuthContext.tsx` (React Context + Supabase).

### API Client Pattern

The frontend uses a **dual-layer API client**:

```typescript
// services/api.ts — low-level apiFetch wrapper (used by product.service.ts)
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T>

// lib/api.ts — fully typed namespace client (used for auth, waitlist, etc.)
import { supabase } from "@/lib/supabase";

async function request<T>(method, path, body?) {
  const token = await getToken(); // from Supabase session
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    credentials: "include", // also sends legacy iterra_token cookie
    body: body !== undefined ? JSON.stringify(body) : undefined
  });
  if (!res.ok) throw new ApiError(res.status, detail);
  return res.json() as Promise<T>;
}

export const api = {
  auth: { me, logout, onboarding },
  waitlist: { stats, myStatus, join },
  content: { listDrafts, getDraft, suggest, generate, repurpose, publishNow, schedule, calendarEvents },
  calendar: { generate, list },
  coach: { analyze },
  radar: { scan },
  repurpose: { generate },
  brandProfile: { get, upsert },
  analytics: { summary },
  trends: { list, refresh },
};
```

Product-level API calls go through `services/product.service.ts` which imports types from `@iterra/shared-types` (auto-generated OpenAPI types).


### Component Architecture

```
components/
├── auth/                  # Auth-related components
│
├── layout/
│   ├── Navbar.tsx         # Main navigation (with product links)
│   └── Footer.tsx         # Footer
│
├── motion/                # Animation wrapper components
│
├── product/               # Product shell components
│   ├── ProductShell.tsx   # Main product layout wrapper
│   └── StatusPill.tsx     # Status indicator pill
│
├── sections/              # Landing page sections (14 sections)
│   ├── Hero.tsx
│   ├── Features.tsx
│   ├── Problem.tsx
│   ├── Solution.tsx
│   ├── Transformation.tsx
│   ├── HowItWorks.tsx
│   ├── ProductShowcase.tsx
│   ├── Benefits.tsx
│   ├── DemoStrip.tsx
│   ├── SocialProof.tsx
│   ├── Founders.tsx
│   ├── Waitlist.tsx
│   ├── FAQ.tsx
│   └── FinalCTA.tsx
│
├── ui/                    # Reusable UI primitives (23 components)
│   ├── Button.tsx         # Variant-aware button
│   ├── GlassCard.tsx      # Glassmorphism card
│   ├── GradientText.tsx   # Gradient text
│   ├── Badge.tsx
│   ├── Accordion.tsx
│   ├── AnimatedCounter.tsx
│   ├── CursorGlow.tsx
│   ├── ScrollProgress.tsx
│   ├── GrainOverlay.tsx
│   ├── SectionLabel.tsx
│   ├── ThemeToggle.tsx
│   ├── alert.tsx, card.tsx, dialog.tsx, field.tsx
│   ├── input.tsx, label.tsx, separator.tsx
│   ├── sheet.tsx, skeleton.tsx, table.tsx
│   ├── tabs.tsx, textarea.tsx
│
└── features/              # Feature-specific components (populated per feature)
```

### Context Providers

```typescript
// context/AuthContext.tsx — wraps Supabase auth state
export function AuthProvider({ children }) { ... }

// context/ThemeContext.tsx — light/dark theme toggle
export function ThemeProvider({ children }) { ... }
```

### Custom Hooks

```typescript
// hooks/useAuth.ts — reads from AuthContext
export function useAuth() { return useContext(AuthContext); }

// hooks/useProduct.ts — thin wrapper around useProductStore
export function useProduct() { return useProductStore(); }
```

All product-level state and actions are accessed via `useProduct()`. Feature pages compose from this single hook rather than having per-feature hooks.


## Authentication Flow

### Dual JWT Authentication

Ittera supports two authentication methods:
1. **Supabase JWT** (primary, for new users)
2. **Custom JWT** (legacy, for backward compatibility)

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ 1. Login request
       ▼
┌─────────────────────────────────────────┐
│  Frontend: Supabase Auth                │
│  supabase.auth.signInWithPassword()     │
└──────┬──────────────────────────────────┘
       │ 2. Supabase returns JWT
       ▼
┌─────────────────────────────────────────┐
│  Frontend: Store token                  │
│  localStorage / session                 │
└──────┬──────────────────────────────────┘
       │ 3. API request with Bearer token
       ▼
┌─────────────────────────────────────────┐
│  Backend: Dual JWT Middleware           │
│  - Check Authorization header           │
│  - Verify Supabase JWT OR custom JWT    │
│  - Extract user_id from token           │
└──────┬──────────────────────────────────┘
       │ 4. Fetch user from database
       ▼
┌─────────────────────────────────────────┐
│  Database: users table                  │
│  SELECT * FROM users WHERE id = ?       │
└──────┬──────────────────────────────────┘
       │ 5. Inject user into request
       ▼
┌─────────────────────────────────────────┐
│  Route Handler                          │
│  current_user: User = Depends(          │
│    get_current_user                     │
│  )                                      │
└─────────────────────────────────────────┘
```

### OAuth Flows

#### Google OAuth
```
User clicks "Sign in with Google"
  ↓
Frontend: GET /api/v1/auth/google
  ↓
Backend: Redirect to Google OAuth
  ↓
User authorizes on Google
  ↓
Google: Redirect to /api/v1/auth/google/callback?code=...
  ↓
Backend: Exchange code for tokens
  ↓
Backend: Fetch user profile from Google
  ↓
Backend: Create or update user in database
  ↓
Backend: Generate custom JWT
  ↓
Backend: Redirect to frontend with token
  ↓
Frontend: Store token, redirect to dashboard
```

#### LinkedIn OAuth (for posting)
```
User clicks "Connect LinkedIn"
  ↓
Frontend: GET /api/v1/social/connect/linkedin
  ↓
Backend: Return LinkedIn OAuth URL
  ↓
User authorizes on LinkedIn
  ↓
LinkedIn: Redirect to /api/v1/social/callback/linkedin?code=...
  ↓
Backend: Exchange code for access token
  ↓
Backend: Store in social_connections table
  ↓
Backend: Redirect to frontend
```


## Module Deep Dive

### 1. Smart Content Calendar

**Purpose**: Generate data-informed content calendars based on niche, platforms, and historical performance.

**Flow**:
```
User Input (niche, platforms, frequency)
  ↓
CalendarService.generate()
  ↓
Check USE_ITERRA_AI_CALENDAR flag
  ↓
If enabled:
  CalendarEngine (AI)
    ↓
  Format prompt with user data
    ↓
  Call Claude API
    ↓
  Parse JSON response
    ↓
  Return structured calendar
Else:
  Mock calendar generation
    ↓
  Return simple slots
```

**Key Files**:
- `apps/api/app/routers/calendar.py` - API routes
- `apps/api/app/services/calendar_service.py` - Business logic
- `packages/ai-engine/iterra_ai/calendar/engine.py` - AI engine
- `packages/ai-engine/iterra_ai/prompts/calendar.py` - LLM prompts

**Database**: `content_plans` table

---

### 2. Content Repurposing Engine

**Purpose**: Adapt content for multiple platforms while maintaining core message.

**Flow**:
```
User provides original content + target platforms
  ↓
RepurposeService.repurpose()
  ↓
RepurposeEngine.generate()
  ↓
For each target platform:
  - Adjust length (Twitter: 280 chars, LinkedIn: 3000 chars)
  - Adapt format (thread, carousel, caption)
  - Maintain voice and message
  ↓
Return platform-specific versions
```

**Key Files**:
- `apps/api/app/routers/repurpose.py` - API routes
- `apps/api/app/services/repurpose_service.py` - Business logic
- `packages/ai-engine/iterra_ai/repurpose/engine.py` - AI engine
- `packages/ai-engine/iterra_ai/prompts/repurpose.py` - LLM prompts

**Status**: Experimental (template-based, LLM path in progress)


### 3. AI Engagement Coach

**Purpose**: Analyze post quality and provide actionable improvement suggestions.

**Flow**:
```
User submits content + platform + goal
  ↓
CoachService.analyze()
  ↓
Calculate scores:
  - Length appropriateness (0-15 points)
  - Word count sweet spot (0-15 points)
  - Structure (paragraphs, line breaks) (0-10 points)
  - Hook quality (first sentence) (0-5 points)
  - Base score: 55 points
  ↓
Total score: 0.0 - 1.0
  ↓
Generate platform-specific suggestions
  ↓
Return CoachOutput (score, suggestions, summary)
```

**Scoring Rubric**:
- **0.80-1.0**: Strong post, minor refinements
- **0.60-0.79**: Good foundation, needs tightening
- **0.0-0.59**: Needs significant refinement

**Platform-Specific Tips**:
- **LinkedIn**: Direct opening, short paragraphs, concrete takeaway
- **Twitter**: Counter-intuitive hook, <240 chars per tweet, line breaks
- **Instagram**: Compelling first 1-2 lines, 3-5 targeted hashtags

**Key Files**:
- `apps/api/app/routers/coach.py` - API routes
- `apps/api/app/services/coach_service.py` - Business logic
- `packages/ai-engine/iterra_ai/coach/engine.py` - AI engine

---

### 4. Trend Radar

**Purpose**: Early trend detection from Reddit, YouTube, Google Trends.

**Flow**:
```
User requests trends for niche
  ↓
RadarService.scan()
  ↓
Match niche to curated trend database
  ↓
Return top N trends with:
  - Topic
  - Score (0.0-1.0)
  - Platforms
  - Summary
  - Scanned timestamp
```

**Curated Niches**:
- AI (agentic workflows, fine-tuning, observability)
- Content (systems over volume, AI-assisted ideation)
- Marketing (zero-click content, founder-led growth)
- Technology (platform engineering, WebAssembly)
- Startup (vertical AI SaaS, revenue-first GTM)

**Key Files**:
- `apps/api/app/routers/radar.py` - API routes
- `apps/api/app/services/radar_service.py` - Business logic (curated trends)
- `packages/ai-engine/iterra_ai/radar/engine.py` - AI engine (future: real-time scraping)

**Database**: `trend_snapshots` table


### 5. Brand Profile System

**Purpose**: Analyze user's past posts to extract brand voice, tone, topics, and patterns.

**Flow**:
```
User triggers brand profile generation
  ↓
BrandProfileService.generate_profile()
  ↓
Fetch user's LinkedIn posts from database
  ↓
If AI enabled:
  BrandProfileEngine.generate()
    ↓
  Analyze posts for:
    - Voice & tone
    - Core topics
    - Writing patterns
    - Content pillars
    - Hashtag strategy
    ↓
  Generate BrandProfileData
Else:
  Generate mock profile based on niche
  ↓
Save to brand_profiles table
  ↓
Return profile with confidence score
```

**Profile Structure**:
```json
{
  "voice_tone": "Clear, analytical, and calmly opinionated",
  "audience": "Professionals interested in AI-powered content systems",
  "core_topics": ["Content Strategy", "AI Workflows", "Creator Systems"],
  "writing_patterns": [
    "Opens with a direct observation",
    "Uses short paragraphs for pace",
    "Connects strategy to operating habits"
  ],
  "content_pillars": [
    "Strategic clarity",
    "Repeatable systems",
    "Performance learning"
  ],
  "hashtag_strategy": "#ContentStrategy #LinkedInGrowth #AIWorkflow",
  "summary": "Your strongest lane is practical strategy..."
}
```

**Key Files**:
- `apps/api/app/routers/brand_profile.py` - API routes
- `apps/api/app/services/brand_profile_service.py` - Business logic
- `packages/ai-engine/iterra_ai/brand_profile/engine.py` - AI engine
- `apps/api/app/models/brand_profile.py` - Database model

**Database**: `brand_profiles` table

**Workflow**:
1. User generates profile (AI analyzes posts)
2. User reviews and edits profile
3. User confirms profile
4. Profile is used for content generation (ensures consistency)


### 6. LinkedIn Scraping Pipeline

**Purpose**: Scrape user's LinkedIn posts for brand profile analysis and performance tracking.

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│  User stores LinkedIn credentials (encrypted)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  POST /api/v1/social/credentials/linkedin                   │
│  - Validate credentials with linkedin-api                   │
│  - Encrypt username/password                                │
│  - Store in social_connections.metadata                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  User triggers sync: POST /api/v1/social/sync               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Enqueue Celery task: scrape_linkedin_posts.delay(user_id)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Celery Worker (workers/celery/tasks/scraper.py)            │
│  1. Decrypt credentials                                     │
│  2. Login to LinkedIn via linkedin-api                      │
│  3. Scrape user's posts                                     │
│  4. Save to posts table                                     │
│  5. If Google Drive connected:                              │
│     - Upload posts JSON to Drive                            │
│     - Store file_id in social_connections.metadata          │
│  6. Update last_synced_at                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  User polls: GET /api/v1/social/sync/status/{task_id}       │
│  Returns: { status: "SUCCESS", result: {...} }              │
└─────────────────────────────────────────────────────────────┘
```

**Security**:
- Credentials encrypted with `app.core.security.encrypt_value()`
- Decrypted only in Celery worker context
- Never exposed in API responses

**Key Files**:
- `apps/api/app/routers/social.py` - API routes
- `apps/api/app/services/social_service.py` - OAuth & credential management
- `workers/celery/tasks/scraper.py` - Scraping task
- `workers/celery/app.py` - Celery configuration


### 7. Google Drive Integration

**Purpose**: Store content drafts and analysis files in user's Google Drive.

**OAuth Flow**:
```
User clicks "Connect Google Drive"
  ↓
GET /api/v1/social/connect/google-drive
  ↓
Backend returns OAuth URL with scopes:
  - https://www.googleapis.com/auth/drive.file
  - access_type: offline
  - prompt: consent
  ↓
User authorizes on Google
  ↓
Google redirects to /api/v1/social/callback/google-drive?code=...
  ↓
Backend exchanges code for tokens
  ↓
Backend creates folder structure:
  Ittera/
  ├── Drafts/
  └── Analysis/
  ↓
Store folder IDs in social_connections.metadata:
  {
    "iterra_folder_id": "...",
    "drafts_folder_id": "...",
    "analysis_folder_id": "..."
  }
  ↓
Redirect to frontend with success message
```

**Storage Service**:
```python
class StorageService:
    def setup_iterra_folder(self) -> dict:
        # Create Iterra/ folder
        # Create Drafts/ and Analysis/ subfolders
        # Return folder IDs
    
    def upload_draft(self, content: str, filename: str) -> str:
        # Upload to Drafts/ folder
        # Return file_id
    
    def upload_analysis(self, data: dict, filename: str) -> str:
        # Upload to Analysis/ folder
        # Return file_id
```

**Key Files**:
- `apps/api/app/routers/social.py` - OAuth routes
- `apps/api/app/services/social_service.py` - OAuth handling
- `apps/api/app/services/storage_service.py` - Drive operations
- `apps/api/app/models/social_connection.py` - Connection storage

**Benefits**:
- User owns their data
- No database storage limits
- Easy export/backup
- Privacy-first approach


## Architecture Principles (from CLAUDE.md)

### 1. Contracts Before Code
- Define Pydantic schemas FIRST
- API contracts drive implementation
- Frontend types auto-generated from OpenAPI

### 2. No Business Logic in Routes
```python
# ❌ BAD
@router.post("/content/generate")
async def generate(payload: GenerateRequest, db: Session = Depends(get_db)):
    # Business logic here...
    draft = ContentDraft(...)
    db.add(draft)
    db.commit()
    return draft

# ✅ GOOD
@router.post("/content/generate")
async def generate(payload: GenerateRequest, db: Session = Depends(get_db)):
    return content_service.generate(db, current_user, payload)
```

### 3. AI Engine as Package, Not Microservice
- `iterra_ai` is a pip package
- Imported directly into FastAPI
- No network calls between API and AI
- Simpler deployment, faster execution

### 4. Frontend Data Flow
```
Component → Hook → Store → Service → API
```

**Never**:
```typescript
// ❌ BAD: API call in component
function MyComponent() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch('/api/v1/content/drafts').then(r => r.json()).then(setData);
  }, []);
}

// ✅ GOOD: Use hook + store + service
function MyComponent() {
  const { drafts, loading } = useContentDrafts();
}
```

### 5. All Prompts in One Place
- `packages/ai-engine/iterra_ai/prompts/`
- Version controlled
- Easy to review and iterate
- Centralized prompt engineering

### 6. Database Migrations
- Alembic for schema changes
- Never modify models without migration
- Migration naming: `001_description.py`


## Development Workflow

### Local Setup

> **Note**: The backend defaults to **SQLite** (`iterra.db`) locally for zero-setup development. Set `DATABASE_URL` to a PostgreSQL URL for production.

1. **Start Infrastructure** (optional for local SQLite dev):
```bash
docker-compose up -d
# Starts: PostgreSQL, Redis, Nginx
```

2. **Backend Setup**:
```bash
cd apps/api
pip install -r requirements.txt
pip install -e ../../packages/ai-engine
alembic upgrade head
uvicorn main:app --reload --port 8000
```

3. **Frontend Setup**:
```bash
cd apps/web
npm install
npm run dev
# Runs on http://localhost:3000
```

4. **Celery Worker** (optional — for background tasks):
```bash
cd workers/celery
celery -A app worker --loglevel=info
# For scheduled tasks (Beat):
celery -A app beat --loglevel=info
```

### Environment Variables

**Backend** (`apps/api/.env` — loaded by `config.py` at api/ root):
```bash
# Database (defaults to SQLite locally)
DATABASE_URL=postgresql://user:pass@localhost:5432/iterra
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Auth
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
SUPABASE_JWT_SECRET=...           # From Supabase Dashboard → Project Settings → API → JWT Settings
SUPABASE_URL=https://xxx.supabase.co

# AI
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5
USE_ITERRA_AI_CALENDAR=false      # Set true to enable real AI calendar generation

# OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
GOOGLE_DRIVE_REDIRECT_URI=http://localhost:8000/api/v1/social/callback/google-drive
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
LINKEDIN_REDIRECT_URI=...
LINKEDIN_SESSION_COOKIE=          # Alternative to username/password for scraper

# App
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
ENVIRONMENT=development
WAITLIST_TOTAL_SEATS=100

# Email (SMTP for waitlist confirmation)
SMTP_HOST=...
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_USE_TLS=true
MAIL_FROM=...
REPLY_TO_EMAIL=...
```

### Testing

**Backend**:
```bash
cd apps/api
pytest
```

**AI Engine**:
```bash
cd packages/ai-engine
pytest tests/
```

**Frontend**:
```bash
cd apps/web
npm run test
```


## Deployment Architecture

### Production Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer / CDN                    │
│                      (Cloudflare / AWS)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐         ┌──────────────────┐
│   Next.js App    │         │   FastAPI App    │
│   (Vercel)       │         │   (AWS ECS)      │
│   Port 3000      │         │   Port 8000      │
└──────────────────┘         └────────┬─────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
           │  PostgreSQL  │  │    Redis     │  │    Celery    │
           │  (RDS)       │  │ (ElastiCache)│  │   Workers    │
           │              │  │              │  │   (ECS)      │
           └──────────────┘  └──────────────┘  └──────────────┘
```

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/`):

1. **api.yml** - Backend CI/CD
   - Lint (ruff)
   - Type check (mypy)
   - Tests (pytest)
   - Build Docker image
   - Deploy to ECS

2. **web.yml** - Frontend CI/CD
   - Lint (eslint)
   - Type check (tsc)
   - Build (next build)
   - Deploy to Vercel

3. **ai-engine.yml** - AI Package CI/CD
   - Lint (ruff)
   - Tests (pytest)
   - Publish to PyPI (on release)

### Monitoring & Observability

- **Application Logs**: CloudWatch / Datadog
- **Error Tracking**: Sentry
- **Performance**: New Relic / Datadog APM
- **Uptime**: Pingdom / UptimeRobot
- **Cost Tracking**: `iterra_ai.core.CostTracker` for LLM usage


## Security Considerations

### Authentication
- **Dual JWT**: Supabase (primary) + custom tokens (legacy)
- **Token Expiry**: Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Password Hashing**: pbkdf2_sha256 + bcrypt via passlib
- **OAuth State**: JWT-signed state tokens (10-minute expiry)

### Data Protection
- **Credential Encryption**: LinkedIn credentials encrypted at rest
- **Secrets Management**: Environment variables, never in code
- **HTTPS Only**: All production traffic over TLS
- **CORS**: Configured for frontend domain only

### API Security
- **Rate Limiting**: Middleware in `app/middleware/rate_limit.py`
- **Input Validation**: Pydantic schemas for all requests
- **SQL Injection**: SQLAlchemy ORM (parameterized queries)
- **XSS Protection**: React auto-escapes, CSP headers

### Database Security
- **Row-Level Security**: User-scoped queries via `user_id` FK
- **Connection Pooling**: SQLAlchemy engine with pool limits
- **Backup Strategy**: Automated RDS snapshots (production)

### Third-Party Integrations
- **OAuth Scopes**: Minimal required scopes
  - Google Drive: `drive.file` only (not full Drive access)
  - LinkedIn: `openid profile email w_member_social`
- **Token Storage**: Encrypted in `social_connections` table
- **Token Refresh**: Automatic refresh token handling


## Performance Optimizations

### Backend
- **Database Indexing**: 
  - `user_id` indexed on all user-scoped tables
  - `platform` indexed on `social_connections`
  - Composite indexes on frequent query patterns

- **Query Optimization**:
  - Eager loading with `joinedload()` for relationships
  - Pagination for list endpoints
  - Database connection pooling

- **Caching**:
  - Redis for Celery task results
  - In-memory caching for trend data
  - LRU cache for Anthropic client singleton

### Frontend
- **Code Splitting**: Next.js automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Font Optimization**: `next/font` with variable fonts
- **Bundle Analysis**: `next-bundle-analyzer`

### AI Engine
- **Token Tracking**: `CostTracker` monitors usage
- **Prompt Optimization**: Concise prompts to reduce tokens
- **Response Caching**: Cache common AI responses (planned)
- **Batch Processing**: Process multiple requests together (planned)

### Database
- **Connection Pooling**: SQLAlchemy pool (5-20 connections)
- **Query Optimization**: Explain analyze for slow queries
- **Materialized Views**: For analytics (planned)


## Future Enhancements (from ITERRA_IMPLEMENTATION_PLAN.md)

### Phase 1: Foundation (Current)
- ✅ User authentication (Supabase + custom JWT)
- ✅ Basic content creation
- ✅ Brand profile generation
- ✅ Content calendar (AI + mock)
- ✅ Trend radar (curated)
- ✅ AI engagement coach

### Phase 2: Intelligence Layer
- 🔄 Real-time trend scraping (Reddit, YouTube, Google Trends)
- 🔄 Advanced brand voice analysis
- 🔄 Performance prediction models
- 🔄 Content A/B testing suggestions

### Phase 3: Automation
- ⏳ Scheduled publishing to LinkedIn
- ⏳ Auto-repurposing pipeline
- ⏳ Smart notification system
- ⏳ Batch content generation

### Phase 4: Analytics & Insights
- ⏳ Engagement tracking dashboard
- ⏳ Competitor analysis
- ⏳ ROI measurement
- ⏳ Custom reporting

### Phase 5: Collaboration
- ⏳ Team workspaces
- ⏳ Content approval workflows
- ⏳ Shared brand profiles
- ⏳ Multi-user calendars

### Phase 6: Enterprise
- ⏳ White-label solution
- ⏳ API access for integrations
- ⏳ Advanced security (SSO, SAML)
- ⏳ Custom AI model fine-tuning

**Legend**: ✅ Complete | 🔄 In Progress | ⏳ Planned


## Key Design Decisions

### Why Monorepo?
- **Shared types**: Auto-generate TypeScript from OpenAPI
- **Atomic changes**: Update API + frontend in single PR
- **Simplified CI/CD**: Single repository, coordinated deploys
- **Developer experience**: One clone, one IDE workspace

### Why AI Package Instead of Microservice?
- **Simplicity**: No network overhead, no service mesh
- **Speed**: Direct function calls, no HTTP latency
- **Development**: Easier debugging, single process
- **Deployment**: One container, fewer moving parts
- **Cost**: No separate infrastructure for AI service

### Why Supabase Auth?
- **Rapid development**: Auth out of the box
- **Security**: Battle-tested, maintained by experts
- **Features**: OAuth, magic links, email verification
- **Scalability**: Handles millions of users
- **Flexibility**: Can migrate to custom auth later

### Why FastAPI?
- **Performance**: Async/await, high throughput
- **Type Safety**: Pydantic validation, auto-docs
- **Developer Experience**: Auto-generated OpenAPI
- **Ecosystem**: Rich Python AI/ML libraries
- **Modern**: Built for async, microservices-ready

### Why Next.js 14 App Router?
- **Server Components**: Better performance, SEO
- **File-based Routing**: Intuitive, scalable
- **Built-in Optimization**: Images, fonts, code splitting
- **TypeScript**: First-class support
- **Deployment**: Vercel integration, edge functions

### Why PostgreSQL?
- **Reliability**: ACID compliance, data integrity
- **Features**: JSON columns, full-text search, extensions
- **Scalability**: Proven at scale (Instagram, Spotify)
- **Ecosystem**: Rich tooling, ORMs, monitoring
- **Cost**: Open source, no licensing fees


## Troubleshooting Common Issues

### Database Schema Out of Date
**Error**: `OperationalError` or `ProgrammingError` when accessing endpoints

**Solution**:
```bash
cd apps/api
alembic upgrade head
```

### AI Engine Import Errors
**Error**: `ModuleNotFoundError: No module named 'iterra_ai'`

**Solution**:
```bash
cd packages/ai-engine
pip install -e .
```

### Supabase Auth Not Working
**Error**: 401 Unauthorized on protected routes

**Solution**:
1. Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
2. Verify token in browser localStorage
3. Check token expiry (default: 60 minutes)

### Celery Tasks Not Running
**Error**: Tasks enqueued but never execute

**Solution**:
1. Check Redis connection: `redis-cli ping`
2. Start Celery worker: `celery -A app worker --loglevel=info`
3. Check task logs in worker output

### Google Drive OAuth Fails
**Error**: "redirect_uri_mismatch"

**Solution**:
1. Add redirect URI to Google Cloud Console:
   - `http://localhost:8000/api/v1/social/callback/google-drive` (dev)
   - `https://api.ittera.com/api/v1/social/callback/google-drive` (prod)
2. Verify `GOOGLE_DRIVE_REDIRECT_URI` in `.env`

### Frontend API Calls Fail
**Error**: CORS errors or 404 on API calls

**Solution**:
1. Check `NEXT_PUBLIC_API_URL` in `.env.local`
2. Verify backend is running on correct port
3. Check CORS middleware in `apps/api/main.py`


## Agent Personas (from CLAUDE.md)

Ittera uses four specialized agent personas for development:

### @architect
**Responsibilities**:
- System integrity and infrastructure
- Docker, docker-compose, CI/CD pipelines
- Database migrations and schema design
- Security and performance optimization
- Cross-cutting concerns (logging, monitoring)

**When to use**: Infrastructure changes, deployment issues, system design

---

### @frontend
**Responsibilities**:
- UI/UX implementation
- React components and Next.js pages
- State management (Zustand)
- API client integration
- Responsive design and accessibility

**When to use**: Frontend features, UI bugs, styling issues

---

### @backend
**Responsibilities**:
- API contracts (Pydantic schemas)
- FastAPI routes and services
- Database models and queries
- Authentication and authorization
- Business logic implementation

**When to use**: API endpoints, database changes, backend logic

---

### @ai-engineer
**Responsibilities**:
- LLM module development
- Prompt engineering and optimization
- AI engine architecture
- Evaluation frameworks
- Cost optimization

**When to use**: AI features, prompt improvements, LLM integration

---

## Conclusion

Iterra is a modern, AI-powered content strategy platform built with:
- **Scalable architecture**: Monorepo, microservices-ready
- **Type safety**: End-to-end TypeScript + Python typing
- **AI-first**: Integrated AI engine for content intelligence
- **Developer experience**: Hot reload, auto-docs, clear conventions
- **Production-ready**: CI/CD, monitoring, security best practices

The architecture prioritizes:
1. **Simplicity**: AI as package, not microservice
2. **Type safety**: Contracts before code
3. **Separation of concerns**: Routes → Services → Models
4. **User privacy**: Google Drive storage, encrypted credentials
5. **Scalability**: Async FastAPI, connection pooling, caching

For questions or contributions, refer to `CLAUDE.md` for conventions and agent personas.

---

**Last Updated**: 2026-05-23
**Version**: 1.1
**Maintainer**: Iterra Team
