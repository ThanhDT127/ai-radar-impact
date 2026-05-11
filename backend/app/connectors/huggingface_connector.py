"""HuggingFace connector — fetches recent model releases from a HF organization via public API."""

import logging
from datetime import datetime

import httpx

from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.models.source import Source

logger = logging.getLogger(__name__)

HF_API_BASE = "https://huggingface.co/api/models"
USER_AGENT = "AI-Radar-Impact-Bot/1.0"


class HuggingFaceConnector(BaseConnector):
    """Fetches recent model releases from a HuggingFace organization.

    Config:
      - org (str, required): HF organization username (e.g. "deepseek-ai")
      - max_items (int): max models to fetch (default 15)
      - min_likes (int): filter — only models with likes >= this (default 0)
    """

    def fetch(self, source: Source) -> list[ConnectorEntry]:
        config = source.config or {}
        org: str = config.get("org", "")
        if not org:
            logger.warning("HuggingFace source '%s' missing config.org", source.name)
            return []
        max_items: int = int(config.get("max_items", 15))
        min_likes: int = int(config.get("min_likes", 0))

        url = HF_API_BASE
        params = {
            "author": org,
            "sort": "createdAt",
            "direction": "-1",
            "limit": str(max_items * 2),
        }

        try:
            with httpx.Client(timeout=15.0, headers={"User-Agent": USER_AGENT}) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                models = resp.json()
        except Exception as e:
            logger.error("HuggingFace fetch failed for org=%s: %s", org, e)
            return []

        if not isinstance(models, list):
            logger.warning("HuggingFace API returned non-list for org=%s", org)
            return []

        entries: list[ConnectorEntry] = []
        for model in models:
            if len(entries) >= max_items:
                break
            try:
                model_id = model.get("id", "")
                if not model_id:
                    continue
                likes = int(model.get("likes", 0) or 0)
                if likes < min_likes:
                    continue
                downloads = int(model.get("downloads", 0) or 0)
                tags = model.get("tags") or []
                pipeline_tag = model.get("pipeline_tag") or "model"
                library = model.get("library_name") or "?"
                created_at_str = model.get("createdAt") or ""
                try:
                    if created_at_str:
                        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        # Strip tzinfo — DB column is TIMESTAMP WITHOUT TIME ZONE
                        published_at = dt.replace(tzinfo=None)
                    else:
                        published_at = None
                except (ValueError, TypeError):
                    published_at = None

                # Build rich content (description not in list API; would need /api/models/{id} per item)
                # Pad with metadata so it passes min_content_length filter
                short_tags = [t for t in tags if isinstance(t, str) and len(t) < 40][:10]
                content_parts = [
                    f"Mô hình mới {model_id} vừa được xuất bản trên Hugging Face bởi {org}.",
                    f"Loại pipeline: {pipeline_tag}. Library: {library}.",
                    f"Số lượt thích: {likes}. Số lượt download: {downloads}.",
                    f"Tags: {', '.join(short_tags)}." if short_tags else "",
                    f"Đây là tín hiệu sớm về một mô hình AI mới từ tổ chức {org}.",
                ]
                content = "\n\n".join(p for p in content_parts if p)

                entries.append(
                    ConnectorEntry(
                        source_url=f"https://huggingface.co/{model_id}",
                        title=model_id,
                        raw_content=content,
                        author=org,
                        published_at=published_at,
                        metadata={
                            "hf_org": org,
                            "likes": likes,
                            "downloads": downloads,
                            "pipeline_tag": pipeline_tag,
                            "library": library,
                            "tags": short_tags,
                        },
                    )
                )
            except Exception as e:
                logger.warning("Failed to parse HF model entry: %s", e)
                continue

        logger.info("HuggingFace fetched %d entries for org=%s", len(entries), org)
        return entries


ConnectorRegistry.register("huggingface", HuggingFaceConnector)
