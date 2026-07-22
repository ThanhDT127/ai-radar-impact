"""Audit độ phủ vai trò (target_roles) của các nguồn.

In bảng "vai trò → số nguồn active" theo bộ taxonomy target_roles (13 vai trò,
xem CLAUDE.md). Lưu ý: đây KHÁC với `ALLOWED_ROLES` trong `app/ai/prompts.py`
(bộ `affected_roles` do Gemini sinh) — target_roles là metadata nguồn.

Usage:
    docker-compose exec backend python -m app.scripts.audit_target_roles
"""

import asyncio
from collections import Counter

from sqlalchemy import select

from app.database import async_session_maker
from app.models.source import Source

# Bộ taxonomy target_roles (13) — thống nhất với spec source-region-tagging.
TARGET_ROLE_TAXONOMY = [
    "Executive",
    "Engineering",
    "Data/AI",
    "Product",
    "Content/Marketing",
    "Legal/Compliance",
    "HR/L&D",
    "DevOps",
    "Infrastructure",
    "Security",
    "BA/QA",
    "Designer/UX",
    "Toàn công ty",
]

# Vai trò kỹ thuật MUST không được 0 nguồn sau backfill (spec: Audit độ phủ vai trò).
TECHNICAL_ROLES = {
    "Engineering",
    "Data/AI",
    "Security",
    "DevOps",
    "Infrastructure",
    "BA/QA",
}


async def audit() -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(Source).where(Source.status == "active")
        )
        sources = result.scalars().all()

    counts: Counter[str] = Counter()
    unknown: Counter[str] = Counter()
    empty = 0
    for src in sources:
        roles = src.target_roles or []
        if not roles:
            empty += 1
        for role in roles:
            if role in TARGET_ROLE_TAXONOMY:
                counts[role] += 1
            else:
                unknown[role] += 1

    print(f"\nNguồn active: {len(sources)} | thiếu target_roles: {empty}\n")
    print(f"{'Vai trò':<20} {'Số nguồn':>8}")
    print("-" * 30)
    for role in TARGET_ROLE_TAXONOMY:
        flag = ""
        if role in TECHNICAL_ROLES and counts[role] == 0:
            flag = "  ⚠ KỸ THUẬT: 0 nguồn"
        elif counts[role] < 5:
            flag = "  (mỏng <5)"
        print(f"{role:<20} {counts[role]:>8}{flag}")

    if unknown:
        print("\n⚠ Tag ngoài taxonomy (cần ánh xạ):")
        for role, n in unknown.most_common():
            print(f"  {role}: {n}")

    thin_tech = [r for r in TECHNICAL_ROLES if counts[r] == 0]
    if thin_tech:
        print(f"\n❌ Vai trò kỹ thuật 0 nguồn: {', '.join(sorted(thin_tech))}")
    else:
        print("\n✓ Mọi vai trò kỹ thuật đều có ≥1 nguồn.")


if __name__ == "__main__":
    asyncio.run(audit())
