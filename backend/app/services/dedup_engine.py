"""Semantic deduplication engine — TF-IDF cosine similarity clustering."""

import logging
import uuid
from datetime import date, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.models.source import Source

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.6
TRUST_TIER_ORDER = {"very_high": 0, "high": 1, "medium": 2, "low": 3, "unverified": 4}


def compute_momentum(cluster_size: int, cluster_age_days: float) -> str:
    """Rule D2: derive momentum from cluster size + age."""
    if cluster_size <= 1:
        return "new" if cluster_age_days < 3 else "mature"
    if cluster_size >= 3 and cluster_age_days < 7:
        return "rising"
    return "mature"


class DeduplicationEngine:
    """Groups semantically similar insights into clusters and marks one as primary."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def find_clusters(self, insights: list[dict]) -> list[list[int]]:
        """Return groups of insight indices where similarity >= SIMILARITY_THRESHOLD.

        Each group is a connected component in the similarity graph.
        Singletons (no similar pair) are included as single-element groups.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        n = len(insights)
        if n < 2:
            return [[i] for i in range(n)]

        texts = [
            f"{ins['title']} {ins.get('summary_short') or ''}" for ins in insights
        ]

        try:
            matrix = TfidfVectorizer(min_df=1).fit_transform(texts)
            sim = cosine_similarity(matrix)
        except Exception as exc:
            logger.warning("TF-IDF failed: %s — skipping dedup", exc)
            return [[i] for i in range(n)]

        # Union-Find for connected components
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i in range(n):
            for j in range(i + 1, n):
                if sim[i, j] >= SIMILARITY_THRESHOLD:
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[ri] = rj

        groups: dict[int, list[int]] = {}
        for i in range(n):
            root = find(i)
            groups.setdefault(root, []).append(i)

        return list(groups.values())

    def select_primary(self, cluster: list[dict]) -> uuid.UUID:
        """Return the id of the primary insight in a cluster.

        Priority: trust_tier (lower order = better) → earliest published_at → highest confidence.
        """
        def sort_key(ins: dict):
            tier = TRUST_TIER_ORDER.get(ins.get("trust_tier", "unverified"), 99)
            pub = ins.get("published_at") or date.max
            conf = -(ins.get("confidence") or 0.0)
            return (tier, pub, conf)

        return sorted(cluster, key=sort_key)[0]["id"]

    async def get_cluster_metadata(self, cluster_id: uuid.UUID) -> dict:
        """Return {size, earliest_published_at} for a given cluster_id."""
        result = await self.session.execute(
            select(Insight.published_at)
            .where(Insight.cluster_id == cluster_id)
            .where(Insight.status == "published")
        )
        rows = list(result.scalars().all())
        if not rows:
            return {"size": 0, "earliest_published_at": None}
        valid = [p for p in rows if p is not None]
        earliest = min(valid) if valid else None
        return {"size": len(rows), "earliest_published_at": earliest}

    async def run_dedup(self) -> dict[str, int]:
        """Re-cluster all insights from the last 7 days.

        Algorithm:
        1. Load recent insights with source trust_tier
        2. Reset all cluster_id/is_primary to defaults
        3. Find clusters using TF-IDF similarity
        4. For multi-insight clusters: assign shared cluster_id, mark primary
        Returns counts: { clusters_created, duplicates_marked }.
        """
        cutoff = date.today() - timedelta(days=7)

        result = await self.session.execute(
            select(
                Insight.id,
                Insight.title,
                Insight.summary_short,
                Insight.confidence,
                Insight.published_at,
                Source.trust_tier,
            )
            .join(RawDocument, Insight.raw_document_id == RawDocument.id)
            .join(Source, RawDocument.source_id == Source.id)
            .where(Insight.status == "published")
            .where(Insight.created_at >= cutoff)
        )
        rows = [dict(r._mapping) for r in result]

        if not rows:
            return {"clusters_created": 0, "duplicates_marked": 0}

        # Reset all cluster fields first
        all_ids = [r["id"] for r in rows]
        await self.session.execute(
            update(Insight)
            .where(Insight.id.in_(all_ids))
            .values(cluster_id=None, is_primary=True)
        )

        groups = self.find_clusters(rows)

        clusters_created = 0
        duplicates_marked = 0
        today = date.today()

        for group_indices in groups:
            cluster_insights = [rows[i] for i in group_indices]
            size = len(cluster_insights)

            pub_dates: list[date] = []
            for ins in cluster_insights:
                p = ins.get("published_at") or today
                # datetime is a subclass of date — use .date() to coerce
                if hasattr(p, "hour"):  # datetime, not date
                    p = p.date()
                pub_dates.append(p)
            earliest = min(pub_dates) if pub_dates else today
            age_days = (today - earliest).days
            momentum = compute_momentum(size, age_days)

            if size < 2:
                # Singleton — only update momentum, leave cluster_id null
                await self.session.execute(
                    update(Insight)
                    .where(Insight.id == cluster_insights[0]["id"])
                    .values(momentum=momentum)
                )
                continue

            cluster_id = uuid.uuid4()
            primary_id = self.select_primary(cluster_insights)

            for ins in cluster_insights:
                is_primary = ins["id"] == primary_id
                await self.session.execute(
                    update(Insight)
                    .where(Insight.id == ins["id"])
                    .values(
                        cluster_id=cluster_id,
                        is_primary=is_primary,
                        momentum=momentum,
                    )
                )
                if not is_primary:
                    duplicates_marked += 1

            clusters_created += 1

        await self.session.commit()
        logger.info(
            "Dedup complete — %d clusters created, %d duplicates marked",
            clusters_created,
            duplicates_marked,
        )
        return {"clusters_created": clusters_created, "duplicates_marked": duplicates_marked}
