from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.schemas.radar import RadarInput, RadarOutput, TrendItem

_NICHE_TRENDS: dict[str, list[dict]] = {
    "ai": [
        {"topic": "Agentic AI workflows", "score": 0.97, "summary": "Autonomous multi-step AI agents are replacing brittle pipelines. Teams are shifting from prompts to orchestration."},
        {"topic": "LLM fine-tuning on proprietary data", "score": 0.91, "summary": "Generic models lose to niche specialists. Domain fine-tuning is becoming table stakes for B2B AI."},
        {"topic": "AI observability & evals", "score": 0.87, "summary": "As AI ships to production, evaluation frameworks and tracing tools are the new DevOps."},
        {"topic": "Retrieval-Augmented Generation (RAG) maturity", "score": 0.83, "summary": "RAG patterns are maturing: hybrid search, re-ranking, and citation grounding are differentiation layers."},
        {"topic": "On-device AI inference", "score": 0.78, "summary": "Apple Silicon, Snapdragon X, and quantized models are making cloud-free AI real for consumer apps."},
    ],
    "content": [
        {"topic": "Content systems over content volume", "score": 0.95, "summary": "Creators shifting from 'post more' to 'build a repeatable production loop'. Quality compounds over quantity."},
        {"topic": "AI-assisted ideation with human voice", "score": 0.90, "summary": "The breakout formula: AI for research/structure, human for tone/perspective. Pure AI content is getting filtered out by audiences."},
        {"topic": "Dark social & community-first distribution", "score": 0.84, "summary": "Slack, Discord, and private newsletters outperform public timelines in conversion. Distribution is moving inward."},
        {"topic": "Micro-niching for audience trust", "score": 0.80, "summary": "Generalist content creators are getting squeezed. Hyper-specific niches build faster trust and better monetization."},
        {"topic": "Repurposing as a primary strategy", "score": 0.75, "summary": "One long-form asset → 10 platform-native pieces. Repurposing efficiency is a competitive advantage."},
    ],
    "marketing": [
        {"topic": "Zero-click content strategies", "score": 0.94, "summary": "Platforms suppress external links. Content that delivers full value inline (carousels, threads, docs) is outperforming click-bait."},
        {"topic": "Founder-led growth", "score": 0.89, "summary": "B2B buyers trust people more than brands. Founder and team personal brands are becoming primary acquisition channels."},
        {"topic": "Revenue attribution in a cookieless world", "score": 0.85, "summary": "GA4, server-side tracking, and mixed-media models are displacing last-click. Marketing ops is becoming a data engineering role."},
        {"topic": "Community-led product growth (CLG)", "score": 0.80, "summary": "Products with thriving communities retain 40% better. CLG is the new PLG for retention-focused teams."},
        {"topic": "Video SEO for AI search engines", "score": 0.72, "summary": "ChatGPT and Perplexity cite YouTube as a source. Optimizing video transcripts for AI search is an emerging SEO frontier."},
    ],
    "technology": [
        {"topic": "Platform engineering & internal developer platforms", "score": 0.93, "summary": "IDPs are reducing cognitive load for engineering teams. Golden paths, not golden cages."},
        {"topic": "WebAssembly for edge compute", "score": 0.86, "summary": "WASM is enabling serverless functions with near-native performance. Edge runtimes on Cloudflare, Fastly are maturing rapidly."},
        {"topic": "Observability-first culture", "score": 0.83, "summary": "Teams shipping fast are investing in distributed tracing (OpenTelemetry), structured logging, and SLO management as core practice."},
        {"topic": "AI-augmented code review", "score": 0.79, "summary": "GitHub Copilot PRs, CodeRabbit, and Graphite Stack are changing how teams think about code review throughput."},
        {"topic": "Database-per-service in microservices", "score": 0.71, "summary": "Shared databases are the hidden coupling in microservices. Teams are migrating toward service-owned polyglot persistence."},
    ],
    "startup": [
        {"topic": "Vertical AI SaaS", "score": 0.96, "summary": "AI products built for one industry vertical (legal, healthcare, construction) are closing Series A rounds in 9 months. Specificity is the moat."},
        {"topic": "Revenue-first GTM strategies", "score": 0.88, "summary": "Seed-stage companies skipping the 'build audience first' phase. Direct sales and micro-conversions from Day 1."},
        {"topic": "AI-native operations (no ops team)", "score": 0.83, "summary": "Founders running $2M ARR businesses with 2-3 people using AI for support, finance, and growth. Leverage is the new headcount."},
        {"topic": "Consumption-based pricing models", "score": 0.77, "summary": "Per-seat SaaS is being disrupted by usage-based pricing — better aligns value, reduces churn risk, increases enterprise adoption."},
        {"topic": "Open-source as distribution", "score": 0.72, "summary": "OSS repo → GitHub stars → community trust → enterprise contract. Open-core is the fastest B2B brand-building strategy."},
    ],
}

_DEFAULT_TRENDS = [
    {"topic": "AI productivity tools", "score": 0.90, "summary": "Productivity tooling augmented by AI is the fastest growing SaaS category across every vertical."},
    {"topic": "Cross-platform distribution", "score": 0.84, "summary": "Single-platform strategies are risky. Multi-platform presence with adapted content is the new baseline."},
    {"topic": "Systems thinking in creative work", "score": 0.78, "summary": "The most successful creators and companies treat their output as systems — repeatable, measurable, improvable."},
    {"topic": "Human-first brand voice", "score": 0.73, "summary": "In an AI-saturated landscape, authentic and opinionated human voice is a differentiation signal, not a nice-to-have."},
    {"topic": "Community as competitive moat", "score": 0.68, "summary": "Communities slow churn, accelerate referrals, and provide qualitative feedback loops products cannot buy."},
]


def _find_trends(niche: str) -> list[dict]:
    niche_lower = niche.lower()
    for key, trends in _NICHE_TRENDS.items():
        if key in niche_lower or niche_lower in key:
            return trends
    return _DEFAULT_TRENDS


class RadarService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def scan(self, input: RadarInput) -> RadarOutput:
        raw_trends = _find_trends(input.niche)
        limit = min(input.limit, len(raw_trends))

        items = [
            TrendItem(
                topic=t["topic"],
                score=round(t["score"], 2),
                platforms=input.platforms or ["linkedin", "twitter"],
                summary=t["summary"],
            )
            for t in raw_trends[:limit]
        ]

        return RadarOutput(trends=items, scanned_at=datetime.now(tz=timezone.utc))

