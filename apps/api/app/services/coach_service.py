from sqlalchemy.orm import Session

from app.schemas.coach import CoachInput, CoachOutput

_PLATFORM_TIPS: dict[str, list[str]] = {
    "linkedin": [
        "Open with a direct claim or observation — LinkedIn rewards specificity in the first line.",
        "Use white space deliberately: short paragraphs (1-3 lines) improve dwell time on mobile.",
        "End with a question or a concrete takeaway — not a call-to-follow.",
        "Avoid passive voice. 'Teams that ship fast' > 'Shipping fast is done by teams that...'",
        "Your hook should make the reader feel slightly unsettled or curious within 12 words.",
    ],
    "twitter": [
        "Lead with the most surprising or counter-intuitive sentence — you have one chance.",
        "Keep each tweet under 240 characters for easy quote-tweeting.",
        "A strong thread opens with a premise, then delivers three proofs, then closes with a principle.",
        "Cut filler words. 'In order to' → 'To'. 'Very unique' → 'Unique'.",
        "Use line breaks between ideas — dense text is skipped on Twitter.",
    ],
    "instagram": [
        "The first 1-2 lines before 'more' must compel a tap — treat them as the subject line of an email.",
        "Use 3-5 targeted hashtags, not 25 random ones — quality of audience matters more than reach.",
        "Strike a personal tone: Instagram rewards authenticity over polish.",
        "End with a save-worthy takeaway, a list, or a reflection.",
        "Match caption energy to the image — tension between them feels off.",
    ],
}

_DEFAULT_TIPS = [
    "Lead with the strongest idea, not context or preamble.",
    "Every sentence should earn its place — if removing it loses nothing, cut it.",
    "Use concrete nouns over abstract ones wherever possible.",
]


class CoachService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def analyze(self, input: CoachInput) -> CoachOutput:
        content = input.content.strip()
        platform = input.platform.lower()
        word_count = len(content.split())
        char_count = len(content)

        # ── Score calculation ─────────────────────────────────────────────
        base = 0.55

        # Length appropriateness per platform
        limits = {"linkedin": 3000, "twitter": 280, "instagram": 2200}
        limit = limits.get(platform, 3000)
        fill_ratio = min(char_count / limit, 1.0)
        length_score = 0.15 if 0.1 <= fill_ratio <= 0.75 else 0.05

        # Word count (sweet spot: 80–400 for most platforms)
        if 80 <= word_count <= 400:
            word_score = 0.15
        elif 40 <= word_count < 80 or 400 < word_count <= 600:
            word_score = 0.08
        else:
            word_score = 0.02

        # Structure: paragraphs, line breaks
        line_count = len([line for line in content.splitlines() if line.strip()])
        structure_score = 0.10 if line_count >= 3 else 0.04

        # Hook quality heuristic: first sentence < 80 chars
        first_sentence = content.split(".")[0]
        hook_score = 0.05 if len(first_sentence) <= 80 else 0.02

        score = round(min(base + length_score + word_score + structure_score + hook_score, 1.0), 2)

        # ── Suggestions ───────────────────────────────────────────────────
        tips = _PLATFORM_TIPS.get(platform, _DEFAULT_TIPS)
        goal = input.goal
        selected: list[str] = []

        if goal:
            selected.append(f"Since your goal is '{goal}', make sure every sentence serves that outcome directly.")

        # Pick 2-3 most relevant tips
        selected += tips[:3]

        # ── Summary ───────────────────────────────────────────────────────
        if score >= 0.80:
            summary = (
                f"Strong {platform} post. The structure is solid and the length is well-calibrated. "
                "Focus now on sharpening the hook and ensuring the final line gives readers a clear next feeling."
            )
        elif score >= 0.60:
            summary = (
                f"Good foundation for a {platform} post. There is room to tighten the opening and increase "
                "specificity — vague claims dilute engagement even when the idea is strong."
            )
        else:
            summary = (
                f"This draft needs refinement before publishing on {platform}. "
                "Start by rewriting the first two lines to be more direct and specific, "
                "then check that each paragraph moves the reader forward."
            )

        return CoachOutput(score=score, suggestions=selected[:5], summary=summary)

