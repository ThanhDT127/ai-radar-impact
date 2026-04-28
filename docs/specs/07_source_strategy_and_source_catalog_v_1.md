# 07. SOURCE STRATEGY & SOURCE CATALOG V1 — AI IMPACT RADAR

## 1. Mục tiêu của source strategy
Xây dựng danh mục nguồn đủ rộng để phát hiện tín hiệu quan trọng nhưng đủ chặt để đảm bảo:
- độ tin cậy
- khả năng truy vết
- khả năng tích hợp kỹ thuật
- khả năng vận hành ổn định
- tính phù hợp với doanh nghiệp

## 2. Nguyên tắc chọn nguồn
1. Ưu tiên nguồn chính thức hoặc có thẩm quyền cao
2. Ưu tiên nguồn có cấu trúc tốt: RSS, API, changelog, release notes, docs hub
3. Tách rõ nguồn “fact source” và nguồn “signal source”
4. Không để nguồn cộng đồng đi thẳng thành alert critical nếu chưa được corroborate
5. Phase 1 chỉ chọn nguồn có giá trị cao, ít nhiễu, dễ vận hành

## 3. Phân tầng nguồn
### Tier A - Official / Regulatory / Primary Source
- Website chính thức của vendor/platform
- Docs/changelog/release note chính thức
- Cổng thông tin chính phủ, cơ quan quản lý, cơ sở dữ liệu pháp luật chính thức
- Cơ sở dữ liệu học thuật hoặc metadata chính thống

### Tier B - Professional / Curated Technical Source
- Nguồn kỹ thuật uy tín, chuyên ngành, cộng đồng nghề nghiệp chính thống
- Tạp chí/kênh kỹ thuật thuộc tổ chức chuyên môn lớn

### Tier C - Community Signal Source
- Hacker News, Stack Exchange, Reddit, cộng đồng kỹ thuật mở
- Dùng để bắt tín hiệu sớm, pain point, phản ứng cộng đồng

### Tier D - Internal Source
- SOP nội bộ
- Danh sách tool đang dùng
- Repo nội bộ
- Tài liệu quy trình nội bộ
- mapping team/system/process

---

## 4. Danh mục nguồn chi tiết theo nhóm

### 4.1 Nhóm Official AI / Model Vendor / Platform
**S01. OpenAI News**
- Loại: Official vendor
- Mục đích: Theo dõi thông báo công ty, sản phẩm, an toàn, bảo mật, enterprise, model update
- Loại dữ liệu nên lấy: title, category, publish date, URL, summary sơ bộ
- Tích hợp khuyến nghị: parser web/RSS nếu có feed phù hợp
- Trust tier mặc định: Very High
- Broadcast policy: Có thể broadcast rộng nếu impact phù hợp
- Ưu tiên Phase 1: Rất cao

**S02. OpenAI Homepage / Product pages / Docs hub**
- Loại: Official vendor
- Mục đích: Theo dõi product launch, docs changes, platform capability change
- Trust tier: Very High
- Ưu tiên: Cao

**S03. Anthropic Newsroom**
- Loại: Official vendor
- Mục đích: Theo dõi model launch, policy, enterprise/security initiative, Claude ecosystem
- Trust tier: Very High
- Ưu tiên: Cao

**S04. Google AI / Google Blog - AI**
- Loại: Official vendor
- Mục đích: Theo dõi AI announcements, AI Studio, Gemini, research applications
- Trust tier: Very High
- Ưu tiên: Cao

**S05. Google DeepMind Blog**
- Loại: Official research/vendor
- Mục đích: Theo dõi breakthrough, model, safety, science collaboration
- Trust tier: Very High
- Ưu tiên: Cao

**S06. Google Developers Blog**
- Loại: Official developer platform
- Mục đích: Theo dõi API/tooling/platform updates tác động dev
- Trust tier: Very High
- Ưu tiên: Cao

**S07. Google Search Central News**
- Loại: Official SEO/Search source
- Mục đích: Theo dõi thay đổi Search/SEO/documentation/chính sách hiển thị nội dung
- Trust tier: Very High
- Ưu tiên: Rất cao nếu có content/SEO team

**S08. Google Search Central Documentation Updates**
- Loại: Official changelog
- Mục đích: Theo dõi thay đổi docs SEO/Search có thể tác động content/marketing/web team
- Trust tier: Very High
- Ưu tiên: Cao

**S09. Microsoft Learn**
- Loại: Official docs
- Mục đích: Theo dõi Microsoft AI, Azure, Teams, security, admin guidance
- Trust tier: Very High
- Ưu tiên: Rất cao nếu doanh nghiệp dùng Microsoft ecosystem

**S10. Microsoft Tech Community**
- Loại: Official community/professional
- Mục đích: Theo dõi cập nhật chuyên sâu, thông báo kỹ thuật, community guidance của Microsoft
- Trust tier: High
- Ưu tiên: Cao

**S11. Meta Newsroom**
- Loại: Official vendor
- Mục đích: Theo dõi AI product, platform, policy, enterprise announcements từ Meta
- Trust tier: Very High
- Ưu tiên: Trung bình-Cao

**S12. Meta AI**
- Loại: Official AI product presence
- Mục đích: Theo dõi khả năng, positioning và thay đổi sản phẩm AI của Meta
- Trust tier: High
- Ưu tiên: Trung bình

**S13. AWS Machine Learning Blog**
- Loại: Official cloud/vendor
- Mục đích: Theo dõi AI/ML platform, infrastructure, production guidance
- Trust tier: Very High
- Ưu tiên: Cao

**S14. AWS What's New**
- Loại: Official product update source
- Mục đích: Theo dõi dịch vụ mới, thay đổi pricing/capability/availability
- Trust tier: Very High
- Ưu tiên: Cao

**S15. Google Cloud Blog**
- Loại: Official cloud/vendor
- Mục đích: Theo dõi AI infrastructure, Vertex AI, cloud platform changes
- Trust tier: Very High
- Ưu tiên: Cao

**S16. NVIDIA Blog**
- Loại: Official vendor
- Mục đích: Theo dõi GPU/AI infra/model ecosystem announcements
- Trust tier: Very High
- Ưu tiên: Cao với team AI/hạ tầng

**S17. Cloudflare Blog**
- Loại: Official vendor
- Mục đích: Theo dõi network, security, edge, AI gateway, web platform changes
- Trust tier: Very High
- Ưu tiên: Trung bình-Cao

**S18. GitHub Changelog**
- Loại: Official platform changelog
- Mục đích: Theo dõi thay đổi API, repo, actions, developer workflow
- Trust tier: Very High
- Ưu tiên: Rất cao

**S19. GitHub REST API Docs**
- Loại: Official docs/API
- Mục đích: Connector chuẩn để lấy release/repo metadata/issues/discussions nếu được dùng
- Trust tier: Very High
- Ưu tiên: Rất cao

**S20. GitHub Repository Releases (theo repo chọn lọc)**
- Loại: Official repo source
- Mục đích: Theo dõi release note của framework/tool mà công ty đang dùng
- Trust tier: Very High
- Ưu tiên: Rất cao

### 4.2 Nhóm pháp lý, quy định, chính sách
**S21. Hệ thống văn bản Chính phủ Việt Nam (vanban.chinhphu.vn)**
- Loại: Official government source
- Mục đích: Theo dõi nghị định, quyết định, chỉ thị, văn bản quy phạm pháp luật và văn bản điều hành
- Trust tier: Very High
- Broadcast policy: Có thể dùng làm nguồn gốc pháp lý chính
- Ưu tiên: Rất cao

**S22. Cổng Pháp luật Quốc gia / Bộ Tư pháp**
- Loại: Official legal portal
- Mục đích: Theo dõi tra cứu văn bản, hiệu lực, văn bản liên quan
- Trust tier: Very High
- Ưu tiên: Rất cao

**S23. Cơ sở dữ liệu Luật Việt Nam của Quốc hội (vietlaw.quochoi.vn)**
- Loại: Official legislative source
- Mục đích: Theo dõi luật, nghị quyết, tình trạng văn bản, dữ liệu pháp lý chính thống
- Trust tier: Very High
- Ưu tiên: Rất cao

**S24. Thư Viện Pháp Luật**
- Loại: Curated legal reference
- Mục đích: Tra cứu nhanh, hệ thống hóa, theo dõi cách diễn giải/tổng hợp văn bản
- Trust tier: High
- Lưu ý: Không thay thế nguồn chính thức cho insight critical
- Ưu tiên: Cao

**S25. CISA Cybersecurity Advisories**
- Loại: Official government security advisories
- Mục đích: Theo dõi cảnh báo an ninh mạng, zero-day, exploited vulnerabilities, threat campaigns
- Trust tier: Very High
- Ưu tiên: Cao nếu công ty có nhu cầu security/compliance

**S26. NIST NVD**
- Loại: Official vulnerability database
- Mục đích: Theo dõi CVE, severity, impact metrics, vulnerability metadata
- Trust tier: Very High
- Ưu tiên: Cao nếu liên quan devops/security

**S27. OWASP**
- Loại: Professional security source
- Mục đích: Best practices, top risks, application security guidance
- Trust tier: High
- Ưu tiên: Trung bình-Cao

### 4.3 Nhóm học thuật và nghiên cứu
**S28. arXiv**
- Loại: Scholarly preprint archive
- Mục đích: Theo dõi paper mới về AI/ML/data/science/engineering
- Tích hợp khuyến nghị: arXiv API
- Trust tier: High cho research signal, không mặc định là production fact
- Ưu tiên: Cao

**S29. Crossref REST API**
- Loại: Scholarly metadata source
- Mục đích: DOI, metadata, abstract, update, retraction/correction link, publication metadata
- Trust tier: Very High cho metadata
- Ưu tiên: Cao

**S30. Nature**
- Loại: Peer-reviewed research publisher
- Mục đích: Theo dõi paper, commentary, science breakthrough ảnh hưởng công nghệ/AI
- Trust tier: Very High
- Ưu tiên: Trung bình-Cao

**S31. Science / ScienceDirect / AI Journal (AIJ)**
- Loại: Scholarly journal ecosystem
- Mục đích: Theo dõi kết quả nghiên cứu, bài review, xu hướng AI chính thống
- Trust tier: Very High
- Ưu tiên: Trung bình

**S32. ACM TechNews**
- Loại: Professional curated tech digest
- Mục đích: Theo dõi tin công nghệ dành cho chuyên gia máy tính, được ACM tổng hợp định kỳ
- Trust tier: High
- Ưu tiên: Trung bình-Cao

**S33. IEEE Spectrum**
- Loại: Professional engineering publication
- Mục đích: Theo dõi công nghệ, AI, hạ tầng, engineering trends, deep analysis
- Trust tier: High
- Ưu tiên: Cao

### 4.4 Nhóm tech press / business-tech press uy tín
**S34. Reuters Technology / business-tech reporting**
- Loại: Global newswire / business-tech press
- Mục đích: Theo dõi tin công nghệ, chính sách, doanh nghiệp, M&A, regulation, sự kiện lớn
- Trust tier: High
- Ưu tiên: Cao

**S35. Associated Press (AP)**
- Loại: News wire
- Mục đích: Theo dõi tin tức chính thống tốc độ cao, đặc biệt các sự kiện công nghệ/policy lớn
- Trust tier: High
- Ưu tiên: Trung bình

**S36. Ars Technica**
- Loại: Tech journalism
- Mục đích: Tin công nghệ, AI, policy, security, systems, explainers kỹ thuật
- Trust tier: High
- Ưu tiên: Cao

**S37. The Verge**
- Loại: Mainstream tech media
- Mục đích: Theo dõi tech news, AI, product moves, platform changes, policy narratives
- Trust tier: Medium-High
- Ưu tiên: Trung bình-Cao

**S38. WIRED**
- Loại: Tech/science/business media
- Mục đích: Theo dõi xu hướng, điều tra, phân tích, long-form về AI và công nghệ
- Trust tier: Medium-High
- Ưu tiên: Trung bình

**S39. TechCrunch**
- Loại: Startup/tech media
- Mục đích: Theo dõi startup, AI companies, funding, product launches, ecosystem moves
- Trust tier: Medium-High
- Ưu tiên: Trung bình

### 4.5 Nhóm cộng đồng kỹ thuật, diễn đàn, group mở
**S40. Hacker News**
- Loại: Community signal
- Mục đích: Bắt tín hiệu sớm về tooling, AI, infra, startup tech, phản ứng cộng đồng kỹ thuật
- Tích hợp: HN API chính thức
- Trust tier: Medium
- Broadcast policy: Không dùng làm sole source cho critical alerts
- Ưu tiên: Cao

**S41. Stack Exchange / Stack Overflow**
- Loại: Professional community Q&A
- Mục đích: Theo dõi pain points thực tế, lỗi phổ biến, xu hướng adoption, câu hỏi nhiều quan tâm
- Tích hợp: Stack Exchange API
- Trust tier: Medium-High cho vấn đề kỹ thuật thực hành
- Ưu tiên: Cao

**S42. Reddit (theo subreddit whitelist)**
- Loại: Community signal
- Mục đích: Theo dõi phản ứng cộng đồng, use case thực tế, phàn nàn/pain point, trend
- Tích hợp: Reddit Data API theo terms
- Trust tier: Medium-Low
- Lưu ý: Chỉ dùng theo whitelist subreddit; cần tuân thủ terms
- Ưu tiên: Trung bình

**S43. GitHub Discussions / Issues (theo repo chọn lọc)**
- Loại: Community + repo-operational signal
- Mục đích: Theo dõi bug nóng, regression, community pain point, feature requests
- Trust tier: Medium-High nếu thuộc repo chính thức
- Ưu tiên: Trung bình-Cao

**S44. Microsoft Tech Community forums/blog hubs**
- Loại: Official-professional community
- Mục đích: Theo dõi vấn đề vận hành thật, triển khai enterprise, guidance từ cộng đồng chuyên môn
- Trust tier: High
- Ưu tiên: Cao với hệ sinh thái Microsoft

**S45. Dev.to / Hashnode / Medium (whitelist tác giả)**
- Loại: Community publishing
- Mục đích: Theo dõi best practice thực chiến, giải pháp triển khai, tutorial adoption
- Trust tier: Medium
- Lưu ý: Chỉ nên whitelist tác giả/domain có chất lượng
- Ưu tiên: Thấp-Trung bình cho phase 1

### 4.6 Nhóm nguồn nội bộ cần có để impact analysis chính xác
**S46. Danh mục công cụ và nền tảng công ty đang sử dụng**
- Loại: Internal source
- Mục đích: Map thay đổi từ ngoài vào đúng hệ thống nội bộ
- Trust tier: Very High
- Ưu tiên: Rất cao

**S47. Danh mục repo, framework, dependency chiến lược nội bộ**
- Loại: Internal source
- Mục đích: Xác định repo/ứng dụng nào chịu tác động từ release, CVE, deprecation
- Ưu tiên: Rất cao

**S48. SOP / Quy trình vận hành / Quy trình phát triển phần mềm**
- Loại: Internal source
- Mục đích: Gợi ý SOP nào cần review khi insight xuất hiện
- Ưu tiên: Cao

**S49. Danh mục phòng ban, vai trò, owner hệ thống**
- Loại: Internal source
- Mục đích: Routing digest và impact mapping
- Ưu tiên: Rất cao

**S50. Policy nội bộ về AI, dữ liệu, bảo mật, truyền thông**
- Loại: Internal source
- Mục đích: So khớp thay đổi bên ngoài với quy định nội bộ hiện tại
- Ưu tiên: Cao

---

## 5. Community groups và kênh mở nên whitelist theo chủ đề

### AI/ML
- Hacker News các thread AI/LLM/tooling
- Reddit: r/MachineLearning, r/LocalLLaMA, r/artificial
- GitHub Discussions của các repo AI lớn mà công ty đang dùng

### Dev / Software Engineering
- Stack Overflow tags theo framework/tool đang dùng
- Hacker News thread về platform release, infra, dev tools
- GitHub Issues/Discussions của framework quan trọng

### SEO / Content / Search
- Google Search Central news là nguồn chính
- Có thể theo dõi thêm community thảo luận mở sau phase 1, nhưng không nên đưa Facebook group vào connector chính ngay

### Security
- CISA/NVD là nguồn chính
- Cộng đồng chuyên môn chỉ dùng như watchlist hoặc enrichment

### Community chưa khuyến nghị làm connector Phase 1
- Facebook Groups
- Community đóng hoặc private forum không có access policy rõ ràng
- Nguồn chỉ có giá trị cảm tính/viral nhưng ít metadata

---

## 6. Source Catalog v1 đề xuất chính thức

### 6.1 Danh sách ưu tiên Phase 1
1. OpenAI News
2. OpenAI docs/product pages
3. Anthropic Newsroom
4. Google AI Blog
5. Google DeepMind Blog
6. Google Developers Blog
7. Google Search Central News
8. Google Search Central Documentation Updates
9. Microsoft Learn
10. Microsoft Tech Community
11. GitHub Changelog
12. GitHub Releases của repo trọng yếu
13. GitHub REST API Docs
14. AWS What's New
15. AWS ML Blog
16. Google Cloud Blog
17. Cloudflare Blog
18. NVIDIA Blog
19. vanban.chinhphu.vn
20. Cổng Pháp luật/Bộ Tư pháp
21. vietlaw.quochoi.vn
22. Thư Viện Pháp Luật
23. arXiv API
24. Crossref REST API
25. Hacker News API
26. Stack Exchange API
27. CISA Advisories
28. NIST NVD
29. IEEE Spectrum
30. ACM TechNews

### 6.2 Danh sách Phase 2
31. Reddit whitelist subreddits
32. GitHub Discussions/Issues theo repo
33. Meta Newsroom
34. Meta AI
35. Ars Technica
36. Reuters Technology
37. AP
38. WIRED
39. The Verge
40. TechCrunch

---

## 7. Source metadata schema khuyến nghị cho catalog
Mỗi nguồn trong catalog nên có các trường:
- source_code
- source_name
- source_group
- source_type
- authority_level
- trust_tier_default
- target_departments
- target_topics
- purpose
- access_method
- ingest_method
- crawl_frequency
- verification_policy
- broadcast_policy
- geo_scope
- language
- phase_priority
- owner_internal
- notes

---

## 8. Chính sách sử dụng nguồn theo governance

### 8.1 Chính sách broadcast
- Tier A có thể sinh insight production trực tiếp
- Tier B có thể sinh insight production nếu nội dung rõ và có relevance cao
- Tier C chỉ sinh watchlist hoặc digest nội bộ nếu chưa có nguồn corroborate
- Tier D dùng để map impact, không phải nguồn broadcast ra bên ngoài tổ chức

### 8.2 Chính sách xác minh chéo
- Pháp lý/compliance critical: luôn ưu tiên nguồn chính thức và giữ link nguồn gốc
- Community signal high impact: cần ít nhất một nguồn chính thức hoặc nguồn chuyên môn mạnh corroborate trước khi alert rộng
- Research signal: không tự suy diễn thành “nên áp dụng ngay”; cần đi qua logic impact riêng

### 8.3 Chính sách phase
- Phase 1: chỉ dùng catalog v1 đã whitelist
- Phase 2: thêm community có kiểm soát và media chất lượng cao
- Phase 3: thêm internal mapping sâu và workflow hành động

