"""Gemini analysis prompts and response schema."""

ALLOWED_TOPICS = [
    "AI", "Technology", "Data", "Software Process", "Security",
    "Legal/Compliance", "Content/Marketing", "Service/Platform",
    "Market/Competitor", "Internal Governance",
]

ALLOWED_EVENT_TYPES = [
    "New release", "Policy change", "Regulation update", "Security alert",
    "Deprecation", "Trend signal", "Community discussion",
    "Research update", "Operational incident",
]

ALLOWED_NATURES = ["Risk", "Opportunity", "Compliance", "Informational", "Watchlist"]

ANALYSIS_PROMPT = """\
You are an AI analyst. Analyze the following article and return a JSON object.

RULES:
- Only use information explicitly stated in the article
- Do NOT speculate or add external knowledge
- summary_short must be 1-2 sentences, under 200 characters
- summary_medium must be 1 paragraph, under 500 characters
- topics must only contain values from the allowed list
- event_type must be exactly one value from the allowed list
- nature must be exactly one value from the allowed list
- If uncertain about classification, set confidence below 0.5

ALLOWED TOPICS: {topics}
ALLOWED EVENT TYPES: {event_types}
ALLOWED NATURES: {natures}

Return ONLY valid JSON matching this schema (no markdown, no code block):
{{
  "topics": ["<topic>"],
  "event_type": "<event_type>",
  "nature": "<nature>",
  "summary_short": "<1-2 sentences max 200 chars>",
  "summary_medium": "<1 paragraph max 500 chars>",
  "confidence": <0.0 to 1.0>
}}

ARTICLE TITLE: {title}

ARTICLE CONTENT:
{content}
"""


def build_prompt(title: str, content: str) -> str:
    """Build the analysis prompt with title and content substituted."""
    return ANALYSIS_PROMPT.format(
        topics=", ".join(ALLOWED_TOPICS),
        event_types=", ".join(ALLOWED_EVENT_TYPES),
        natures=", ".join(ALLOWED_NATURES),
        title=title,
        content=content[:6000],  # Limit content to avoid token overflow
    )
