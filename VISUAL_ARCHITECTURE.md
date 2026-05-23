# Ittera - Visual Architecture Guide

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ITTERA PLATFORM                                    │
│                     AI Content Strategy Engine                               │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │    USER      │
                              │   Browser    │
                              └──────┬───────┘
                                     │
                                     │ HTTPS
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND LAYER                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Next.js 14 App Router (TypeScript + Tailwind CSS)                   │  │
│  │  Port: 3000                                                           │  │
│  │                                                                        │  │
│  │  Routes:                                                               │  │
│  │  • Landing Page (/)                                                    │  │
│  │  • Auth Pages (/login, /auth/callback)                                │  │
│  │  • Product Pages (/dashboard, /calendar, /create, /coach, /radar)     │  │
│  │                                                                        │  │
│  │  State Management:                                                     │  │
│  │  • Zustand Stores (auth, content, brand profile, trends)              │  │
│  │  • React Context (AuthProvider, ThemeProvider)                        │  │
│  │                                                                        │  │
│  │  API Client: lib/api.ts (Typed fetch wrapper)                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ REST API (JSON)
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND LAYER                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI (Python 3.11+)                                               │  │
│  │  Port: 8000                                                           │  │
│  │                                                                        │  │
│  │  ┌────────────┐    ┌────────────┐    ┌────────────┐                 │  │
│  │  │  Routers   │───▶│  Services  │───▶│   Models   │                 │  │
│  │  │  (15)      │    │  (15)      │    │   (9)      │                 │  │
│  │  └────────────┘    └────────────┘    └────────────┘                 │  │
│  │       │                  │                  │                         │  │
│  │       │                  │                  │                         │  │
│  │       ▼                  ▼                  ▼                         │  │
│  │  HTTP Layer      Business Logic      Data Access                     │  │
│  │                                                                        │  │
│  │  Authentication: Dual JWT (Supabase + Custom)                         │  │
│  │  Validation: Pydantic Schemas                                         │  │
│  │  ORM: SQLAlchemy 2.0                                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
                │                    │                    │
                │                    │                    │
                ▼                    ▼                    ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   PostgreSQL     │    │   iterra_ai      │    │     Redis        │
│   Database       │    │   AI Package     │    │   (Celery)       │
│   Port: 5432     │    │   (pip install)  │    │   Port: 6379     │
│                  │    │                  │    │                  │
│  Tables (9):     │    │  Engines (5):    │    │  Background:     │
│  • users         │    │  • Calendar      │    │  • LinkedIn      │
│  • brand_profiles│    │  • Coach         │    │    scraping      │
│  • content_drafts│    │  • Radar         │    │  • Scheduled     │
│  • content_plans │    │  • Repurpose     │    │    posts         │
│  • social_conn   │    │  • BrandProfile  │    │                  │
│  • posts         │    │                  │    │                  │
│  • post_analysis │    │  LLM Provider:   │    │                  │
│  • trend_snap    │    │  Anthropic       │    │                  │
│  • waitlist      │    │  Claude API      │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                 │
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  External APIs   │
                        │                  │
                        │  • Anthropic     │
                        │  • Google OAuth  │
                        │  • LinkedIn OAuth│
                        │  • Google Drive  │
                        │  • Reddit (plan) │
                        │  • YouTube (plan)│
                        └──────────────────┘
```

