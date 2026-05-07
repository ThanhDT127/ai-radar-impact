"""Seed initial sources into the database.

Usage:
    docker-compose exec backend python -m app.scripts.seed_sources
"""

import asyncio
import logging

from sqlalchemy import select

from app.database import async_session_maker
from app.models.source import Source

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INITIAL_SOURCES = [
    {
        "name": "GitHub Changelog",
        "source_type": "rss",
        "feed_url": "https://github.blog/changelog/feed/",
        "trust_tier": "very_high",
        "topics": ["Technology", "Software Process", "AI"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "OpenAI Blog",
        "source_type": "rss",
        "feed_url": "https://openai.com/blog/rss.xml",
        "trust_tier": "very_high",
        "topics": ["Trí tuệ nhân tạo"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "Microsoft AI Blog",
        "source_type": "rss",
        "feed_url": "https://blogs.microsoft.com/ai/feed/",
        "trust_tier": "very_high",
        "topics": ["Trí tuệ nhân tạo", "Công nghệ"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "Google AI Blog",
        "source_type": "rss",
        "feed_url": "https://blog.google/technology/ai/rss/",
        "trust_tier": "very_high",
        "topics": ["Trí tuệ nhân tạo"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "Google DeepMind",
        "source_type": "rss",
        "feed_url": "https://deepmind.google/blog/rss.xml",
        "trust_tier": "very_high",
        "topics": ["Trí tuệ nhân tạo", "Dữ liệu"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "AWS What's New",
        "source_type": "rss",
        "feed_url": "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
        "trust_tier": "very_high",
        "topics": ["Dịch vụ/Nền tảng"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "AWS ML Blog",
        "source_type": "rss",
        "feed_url": "https://aws.amazon.com/blogs/machine-learning/feed/",
        "trust_tier": "very_high",
        "topics": ["Trí tuệ nhân tạo", "Dữ liệu"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "NVIDIA Blog",
        "source_type": "rss",
        "feed_url": "https://blogs.nvidia.com/feed/",
        "trust_tier": "very_high",
        "topics": ["Trí tuệ nhân tạo", "Công nghệ"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "Cloudflare Blog",
        "source_type": "rss",
        "feed_url": "https://blog.cloudflare.com/rss/",
        "trust_tier": "very_high",
        "topics": ["An ninh mạng", "Dịch vụ/Nền tảng"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "arXiv CS.AI",
        "source_type": "rss",
        "feed_url": "https://rss.arxiv.org/rss/cs.AI",
        "trust_tier": "high",
        "topics": ["Trí tuệ nhân tạo"],
        "status": "active",
        "config": {"max_items": 15, "language": "en"},
    },
    {
        "name": "arXiv CS.CL",
        "source_type": "rss",
        "feed_url": "https://rss.arxiv.org/rss/cs.CL",
        "trust_tier": "high",
        "topics": ["Trí tuệ nhân tạo", "Dữ liệu"],
        "status": "active",
        "config": {"max_items": 15, "language": "en"},
    },
    {
        "name": "arXiv CS.LG",
        "source_type": "rss",
        "feed_url": "https://rss.arxiv.org/rss/cs.LG",
        "trust_tier": "high",
        "topics": ["Trí tuệ nhân tạo", "Dữ liệu"],
        "status": "active",
        "config": {"max_items": 15, "language": "en"},
    },
    {
        "name": "IEEE Spectrum",
        "source_type": "rss",
        "feed_url": "https://spectrum.ieee.org/feeds/feed.rss",
        "trust_tier": "high",
        "topics": ["Công nghệ", "Trí tuệ nhân tạo"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "Ars Technica",
        "source_type": "rss",
        "feed_url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "trust_tier": "high",
        "topics": ["Công nghệ", "An ninh mạng"],
        "status": "active",
        "config": {"max_items": 20, "language": "en"},
    },
    {
        "name": "VnExpress Số hóa",
        "source_type": "rss",
        "feed_url": "https://vnexpress.net/rss/so-hoa.rss",
        "trust_tier": "medium",
        "topics": ["Công nghệ", "Trí tuệ nhân tạo"],
        "status": "active",
        "config": {"max_items": 20, "language": "vi"},
    },
]


async def seed() -> None:
    """Insert seed sources if they don't already exist."""
    async with async_session_maker() as session:
        for data in INITIAL_SOURCES:
            result = await session.execute(
                select(Source).where(Source.name == data["name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info("Source already exists: %s - skipping", data["name"])
                continue

            source = Source(**data)
            session.add(source)
            await session.commit()
            logger.info("Created source: %s (id=%s)", source.name, source.id)

    logger.info("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
