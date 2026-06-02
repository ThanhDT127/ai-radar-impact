"""Gemini Flash client for article analysis — powered by Vertex AI."""

import json
import logging
import re
import time
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from app.ai.prompts import build_gate_prompt, build_prompt
from app.config import settings

logger = logging.getLogger(__name__)

MODEL_ID = settings.gemini_model_id


@dataclass
class GateResult:
    """Parsed result from Gemini gate pre-screening."""

    actionability_score: float = 0.0
    content_type: str = "noise"
    gate_reason: str = ""
    pass_gate: bool = False
    error: str | None = None


@dataclass
class AnalysisResult:
    """Parsed result from Gemini deep analysis."""

    topics: list[str] = field(default_factory=list)
    event_type: str | None = None
    nature: str | None = None
    summary_short: str | None = None
    summary_medium: str | None = None
    affected_roles: list[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_response: dict = field(default_factory=dict)
    error: str | None = None
    # v2 actionable fields
    signal: str | None = None
    why_it_matters: str | None = None
    recommendations: dict | None = None
    risks: list[str] | None = None
    # v3 taxonomy overhaul fields
    so_what: str | None = None
    adoption_ring: str | None = None
    practical_indicators: dict | None = None


class GeminiClient:
    """Wrapper around Google Gemini API (Vertex AI) for insight analysis."""

    def __init__(self) -> None:
        self._client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    def gate_analyze(self, title: str, content: str) -> GateResult:
        """Run lightweight gate pre-screening on an article.

        Returns GateResult. On error, returns result with error field set
        and pass_gate=True (fail-open so we don't lose content due to transient errors).
        """
        prompt = build_gate_prompt(title=title, content=content)
        _retry_delays = [3, 10]

        for attempt, delay in enumerate([0] + _retry_delays):
            if delay:
                logger.info("Retrying gate after %ds (attempt %d/2) for '%s'", delay, attempt, title[:50])
                time.sleep(delay)
            try:
                response = self._client.models.generate_content(
                    model=MODEL_ID,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        max_output_tokens=4096,
                        response_mime_type="application/json",
                    ),
                )
                raw_text = response.text or ""
                return self._parse_gate_response(raw_text)

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < len(_retry_delays):
                        logger.warning("Gate 429 rate-limit for '%s', will retry", title[:50])
                        continue
                logger.error("Gate error for '%s': %s", title[:50], e)
                return GateResult(pass_gate=True, error=err_str)

        return GateResult(pass_gate=True, error="Gate 429 RESOURCE_EXHAUSTED after retries")

    def _parse_gate_response(self, raw_text: str) -> GateResult:
        """Parse Gemini JSON gate response into GateResult."""
        # Extract JSON substring robustly starting from first '{' to last '}'
        start_idx = raw_text.find('{')
        if start_idx != -1:
            text = raw_text[start_idx:]
            end_idx = text.rfind('}')
            if end_idx != -1:
                text = text[:end_idx + 1]
        else:
            text = raw_text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse gate JSON: %s | raw: %s", e, text[:200])
            return GateResult(pass_gate=True, error=f"Gate JSON parse error: {e}")

        score = float(data.get("actionability_score", 0.0))
        content_type = data.get("content_type", "noise")
        if content_type not in ("practical", "strategic", "theoretical", "noise"):
            content_type = "noise"

        return GateResult(
            actionability_score=score,
            content_type=content_type,
            gate_reason=str(data.get("gate_reason", ""))[:100],
            pass_gate=bool(data.get("pass_gate", False)),
        )

    def analyze(self, title: str, content: str) -> AnalysisResult:
        """Classify and summarize an article using Gemini Flash via Vertex AI.

        Returns an AnalysisResult. On error, returns result with error field set.
        Retries up to 3 times on 429 rate-limit errors with exponential backoff.
        """
        prompt = build_prompt(title=title, content=content)
        _retry_delays = [5, 15, 45]

        for attempt, delay in enumerate([0] + _retry_delays):
            if delay:
                logger.info("Retrying Gemini after %ds (attempt %d/3) for '%s'", delay, attempt, title[:50])
                time.sleep(delay)
            try:
                response = self._client.models.generate_content(
                    model=MODEL_ID,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=4096,
                        response_mime_type="application/json",
                    ),
                )

                candidates = response.candidates or []
                if candidates:
                    finish_reason = candidates[0].finish_reason
                    if hasattr(finish_reason, "value") and finish_reason.value == 2:
                        logger.warning("Gemini response truncated (MAX_TOKENS) for '%s'", title[:50])

                raw_text = response.text or ""
                return self._parse_response(raw_text)

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < len(_retry_delays):
                        logger.warning("Gemini 429 rate-limit for '%s', will retry", title[:50])
                        continue
                logger.error("Vertex AI error for '%s': %s", title[:50], e)
                return AnalysisResult(error=err_str)

        return AnalysisResult(error="Gemini 429 RESOURCE_EXHAUSTED after 3 retries")

    def _parse_response(self, raw_text: str) -> AnalysisResult:
        """Parse Gemini JSON response into AnalysisResult."""
        # Extract JSON substring robustly starting from first '{' to last '}'
        start_idx = raw_text.find('{')
        if start_idx != -1:
            text = raw_text[start_idx:]
            end_idx = text.rfind('}')
            if end_idx != -1:
                text = text[:end_idx + 1]
        else:
            text = raw_text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse Gemini JSON response: %s | raw: %s", e, text[:300])
            return AnalysisResult(error=f"JSON parse error: {e}", raw_response={"raw": raw_text})

        # v2 actionable fields — graceful: missing/wrong type → None
        signal = data.get("signal")
        if not isinstance(signal, str) or not signal.strip():
            signal = None

        why_it_matters = data.get("why_it_matters")
        if not isinstance(why_it_matters, str) or not why_it_matters.strip():
            why_it_matters = None

        recommendations = data.get("recommendations")
        if not isinstance(recommendations, dict):
            recommendations = None

        risks = data.get("risks")
        if not isinstance(risks, list):
            risks = None
        else:
            risks = [r for r in risks if isinstance(r, str) and r.strip()]

        # v3 taxonomy overhaul fields — graceful degradation
        so_what = data.get("so_what")
        if not isinstance(so_what, str) or not so_what.strip():
            so_what = None

        adoption_ring = data.get("adoption_ring")
        if not isinstance(adoption_ring, str) or not adoption_ring.strip():
            adoption_ring = None

        practical_indicators = data.get("practical_indicators")
        if not isinstance(practical_indicators, dict):
            practical_indicators = None
        else:
            valid_keys = {"has_code_example", "has_benchmark", "has_api_change", "has_migration_guide", "has_security_patch"}
            practical_indicators = {
                k: bool(v) for k, v in practical_indicators.items() if k in valid_keys
            } or None

        return AnalysisResult(
            topics=data.get("topics", []),
            event_type=data.get("event_type"),
            nature=data.get("nature"),
            summary_short=data.get("summary_short"),
            summary_medium=data.get("summary_medium"),
            affected_roles=data.get("affected_roles", []),
            confidence=float(data.get("confidence", 0.0)),
            raw_response=data,
            signal=signal,
            why_it_matters=why_it_matters,
            recommendations=recommendations,
            risks=risks,
            so_what=so_what,
            adoption_ring=adoption_ring,
            practical_indicators=practical_indicators,
        )
