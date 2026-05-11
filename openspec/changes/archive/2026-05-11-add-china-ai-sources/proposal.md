## Why

Hệ thống hiện có 18 nguồn, **100% phương Tây**. Năm 2025-2026, hệ sinh thái AI Trung Quốc đã thành cực thứ hai của thế giới: DeepSeek-R1 disrupt thị trường reasoning model, Qwen là top open-source family, GLM/Yi/Kimi/Hunyuan đều có ảnh hưởng global. Bỏ qua layer này = bias rất nặng cho radar.

Đây là blind spot rõ ràng nhất trong coverage hiện tại, và là một trong những thay đổi có ROI cao nhất trong việc mở rộng nguồn — chỉ là thêm RSS data vào seed_sources.

## What Changes

Thêm **8-10 nguồn AI Trung Quốc + analyst newsletters** vào `seed_sources.py`:

**Tier 1 — China AI organizations** (qua HuggingFace org pages + GitHub):
- DeepSeek (HF: deepseek-ai)
- Qwen / Alibaba (HF: Qwen)
- GLM / Zhipu AI (HF: zai-org hoặc THUDM)
- Yi / 01.AI (HF: 01-ai)
- Kimi / Moonshot (HF: moonshotai)
- Tencent Hunyuan (HF: tencent)
- MiniMax (HF: MiniMaxAI)
- Baichuan (HF: baichuan-inc)

**Tier 2 — English-language analysts chuyên China AI** (rất quý vì đã filter):
- Interconnects (Nathan Lambert, Substack)
- ChinaTalk (Substack)

**Source schema enhancements** (cần cho radar đa-region):
- Thêm 2 cột vào `Source`: `region` (`global` | `china` | `vietnam`), `target_roles` (ARRAY[VARCHAR]) — chuẩn bị nền tảng cho changes 2A/2B sau

**Verify trước seed**:
- Test mỗi RSS URL còn sống và parse được
- Note nguồn nào chỉ có HF API polling (không phải RSS thuần) → flag config phù hợp

## Capabilities

### Modified Capabilities
- `rss-ingestion`: Source model có thêm `region` và `target_roles`; seed_sources mở rộng

### New Capabilities
- `source-region-tagging`: tagging theo region để filter/dashboard slice

## Impact

- **Backend code**: `models/source.py`, `schemas/source.py`, `scripts/seed_sources.py`
- **Database**: Alembic migration thêm 2 cột vào `sources`
- **Frontend**: Optional — có thể thêm filter "Theo region" vào dashboard (low priority)
- **API**: Source response thêm 2 fields (additive)
- **Dependencies**: Không thêm
- **Phase**: Phase 2

## Non-goals

- Không refactor RSSConnector hay ConnectorRegistry
- Không thêm web scraper cho các site Trung Quốc tiếng Trung
- Không build dashboard filter "by region" trong scope này (defer)
- Không thêm các nguồn ngoài China + 2 analyst newsletters

## Lưu ý quan trọng

- HuggingFace organization RSS endpoint chưa được verify chính thức. Cần test 2 paths:
  - `https://huggingface.co/api/organizations/{org}/papers/rss` (papers feed)
  - Fallback: poll org page → scrape model release dates
- Substack feeds standard: `<URL>/feed` — Interconnects và ChinaTalk đều dùng Substack
- `region = "china"` không có nghĩa nguồn ở TQ; nó nghĩa "thông tin về AI TQ". Interconnects/ChinaTalk có publisher Mỹ nhưng chuyên cover China AI → vẫn tag `china`
- Trust tier khuyến nghị:
  - DeepSeek/Qwen/GLM official: `very_high`
  - Yi/Kimi/Hunyuan/MiniMax/Baichuan: `high`
  - Interconnects/ChinaTalk: `high`
