"""Gemini Flash client for article analysis — powered by Vertex AI."""

import json
import logging
import re
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from app.ai.prompts import build_prompt
from app.config import settings

logger = logging.getLogger(__name__)

MODEL_ID = settings.gemini_model_id


@dataclass
class AnalysisResult:
    """Parsed result from Gemini analysis."""

    topics: list[str] = field(default_factory=list)
    event_type: str | None = None
    nature: str | None = None
    summary_short: str | None = None
    summary_medium: str | None = None
    affected_roles: list[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_response: dict = field(default_factory=dict)
    error: str | None = None


class GeminiClient:
    """Wrapper around Google Gemini API (Vertex AI) for insight analysis."""

    def __init__(self) -> None:
        # Vertex AI auth uses Application Default Credentials (ADC) via SA key.
        # project/location come explicitly from settings — not from env vars.
        self._client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    def analyze(self, title: str, content: str) -> AnalysisResult:
        """Classify and summarize an article using Gemini Flash via Vertex AI.

        Returns an AnalysisResult. On error, returns result with error field set.
        """
        prompt = build_prompt(title=title, content=content)

        try:
            response = self._client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,      # Low temp for consistent classification
                    max_output_tokens=4096,
                    response_mime_type="application/json",  # Prevent Unicode escaping + ensure valid JSON
                ),
            )

            # Check for truncation
            candidates = response.candidates or []
            if candidates:
                finish_reason = candidates[0].finish_reason
                # finish_reason 2 = MAX_TOKENS (truncated)
                if hasattr(finish_reason, "value") and finish_reason.value == 2:
                    logger.warning("Gemini response truncated (MAX_TOKENS) for '%s'", title[:50])

            raw_text = response.text or ""
            return self._parse_response(raw_text)

        except Exception as e:
            logger.error("Vertex AI error for '%s': %s", title[:50], e)
            return AnalysisResult(error=str(e))

    def _parse_response(self, raw_text: str) -> AnalysisResult:
        """Parse Gemini JSON response into AnalysisResult."""
        # Strip markdown code fences if present (response_mime_type usually avoids this)
        text = re.sub(r"```(?:json)?\s*", "", raw_text).strip()
        text = text.rstrip("`").strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse Gemini JSON response: %s | raw: %s", e, text[:300])
            return AnalysisResult(error=f"JSON parse error: {e}", raw_response={"raw": raw_text})

        return AnalysisResult(
            topics=data.get("topics", []),
            event_type=data.get("event_type"),
            nature=data.get("nature"),
            summary_short=data.get("summary_short"),
            summary_medium=data.get("summary_medium"),
            affected_roles=data.get("affected_roles", []),
            confidence=float(data.get("confidence", 0.0)),
            raw_response=data,
        )
