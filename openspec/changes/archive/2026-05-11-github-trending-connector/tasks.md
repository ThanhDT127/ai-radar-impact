## 1. Implement GitHubTrendingConnector

- [x] 1.1 Tạo `backend/app/connectors/github_trending_connector.py` — class `GitHubTrendingConnector(BaseConnector)`
- [x] 1.2 Implement method `fetch(source) → list[ConnectorEntry]`:
  - Build URL từ `source.config`: `language`, `since`
  - HTTP GET với timeout 10s, User-Agent rõ ràng
  - Parse HTML bằng BeautifulSoup
  - Return list ConnectorEntry với metadata phong phú
- [x] 1.3 Implement helper `_parse_repo(article_element)` extract: name, url, description, language, stars_today, total_stars, forks, position
- [x] 1.4 Implement helper `_parse_stars(text)` handle "1.2k stars today" / "245 stars this week"
- [x] 1.5 Auto-register: `ConnectorRegistry.register("github_trending", GitHubTrendingConnector)` cuối module
- [x] 1.6 Cập nhật `connectors/__init__.py` import module mới để trigger registration

## 2. Resilience & Error Handling

- [x] 2.1 Try/except wrap toàn bộ HTTP + parse logic — không raise, return [] khi lỗi
- [x] 2.2 Log warning rõ ràng khi HTML structure không match selector
- [x] 2.3 Log info khi fetch thành công với count entries

## 3. Update Seed Sources

- [x] 3.1 Cập nhật `scripts/seed_sources.py` thêm 4 sources `source_type="github_trending"`:
  - GitHub Trending — All Daily
  - GitHub Trending — Python Daily
  - GitHub Trending — Weekly All
  - GitHub Trending — TypeScript Daily
- [x] 3.2 Mỗi source: `feed_url=None`, `region="global"`, `trust_tier="high"`, `target_roles=["Engineering","Data/AI"]`, `topics=["Công nghệ","Trí tuệ nhân tạo"]` cho Python/All; `["Quy trình phần mềm"]` thêm cho TypeScript
- [x] 3.3 `config = {language, since, max_items}` đúng theo design D4

## 4. Test & Verify

- [x] 4.1 Unit test `_parse_repo` với HTML fixture (snapshot từ trending page hiện tại)
- [x] 4.2 Test `_parse_stars` với các format khác nhau ("245 stars today", "1.2k stars this week", "12 stars this month")
- [x] 4.3 Integration test: chạy `run_ingestion` chỉ cho 1 source github_trending, verify ≥10 raw_documents được tạo
- [x] 4.4 Spot-check 1 raw_document: title format `owner/repo`, content có description, fingerprint generated
- [x] 4.5 Verify analyzer xử lý: `run_analysis` tạo insights cho repos đó (có thể confidence thấp với repo non-AI — acceptable)

## 5. Documentation

- [x] 5.1 Cập nhật `docs/system_overview.md` — thêm "GitHub Trending" vào layer connector
- [x] 5.2 Cập nhật `CLAUDE.md` "Connector Registry" mention `github_trending` source type
- [x] 5.3 Note trong PR description: HTML scraping rủi ro break nếu GitHub đổi UI, monitoring strategy nên có sau (defer)

## 6. Verification

- [x] 6.1 Sau 24h ingestion: query DB count raw_documents `source_type="github_trending"` ≠ 0
- [x] 6.2 Spot-check 5-10 insights từ trending repos: signal có ý nghĩa, không hallucinate
- [x] 6.3 Theo dõi distribution: repos non-AI lọt vào không (qua `confidence < 0.3` rate); nếu cao, cân nhắc topic filter

## 7. Future considerations (out of scope)

- Context injection cho analyzer khi `source_type="github_trending"` (cần `insight-prompt-revamp` archived trước)
- Frontend hiển thị stars/forks metadata cho GitHub-sourced insights
- Track re-trending events (cùng repo trending lại sau 1 tháng)
- Integration với GitHub REST API (nếu cần data sâu hơn — auth + rate limit)
