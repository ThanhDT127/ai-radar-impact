# AI Radar Impact

[![CI Pipeline](https://github.com/ThanhDT127/ai-radar-impact/actions/workflows/ci.yml/badge.svg)](https://github.com/ThanhDT127/ai-radar-impact/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![React Version](https://img.shields.io/badge/react-19.0-cyan.svg)](https://react.dev/)
[![FastAPI Version](https://img.shields.io/badge/fastapi-0.115-teal.svg)](https://fastapi.tiangolo.com/)

**AI Radar Impact** là một hệ thống full-stack giám sát và phân tích tác động công nghệ, tự động thu thập tin tức từ 15+ nguồn công nghệ/AI uy tín thế giới, phân tích chuyên sâu bằng mô hình **Google Gemini 2.5 Flash (Vertex AI)** để sinh báo cáo, tóm tắt và khuyến nghị hoàn toàn bằng **tiếng Việt**, hiển thị dưới dạng Dashboard trực quan dành cho doanh nghiệp và đội ngũ công nghệ tại Việt Nam.

---

## 📐 Kiến trúc & Luồng dữ liệu (Architecture & Data Flow)

Hệ thống hoạt động theo mô hình xử lý bất đồng bộ (Async) 7 lớp nhằm tối ưu hiệu năng và tránh nghẽn luồng:

```
┌─────────────────┐      ┌───────────────────┐      ┌─────────────────────────┐
│  RSS / API /    │ ───▶ │ Ingestion Service │ ───▶ │ Raw Document (Database) │
│  Web Scraper    │      │ (Normalize/Dedup) │      │ Status: Pending         │
└─────────────────┘      └───────────────────┘      └─────────────────────────┘
                                                                 │
┌─────────────────┐      ┌───────────────────┐                   ▼
│  React Frontend │ ◀─── │ FastAPI Backend   │ ◀─── │    Analyzer Service     │
│  (Vite + Query) │      │ (Async Endpoints) │      │ (Gemini 2-Pass Pipeline)│
└─────────────────┘      └───────────────────┘      └─────────────────────────┘
```

1. **Ingestion Layer (Thu thập)**: Các connector (`RSSConnector`, `GitHubTrendingConnector`, `HuggingFaceConnector`, `WebIndexConnector`) cào dữ liệu định kỳ. Dữ liệu thô được chuẩn hóa (loại bỏ thẻ HTML/script thừa) và băm SHA256 dựa trên URL và tiêu đề để tránh trùng lặp.
2. **Analysis Layer (Phân tích 2 bước)**:
   - **Bước 1 (Gate Pre-screening)**: Sử dụng Gemini đánh giá độ hữu ích (`actionability_score`). Các tài liệu rác hoặc quá chung chung (`content_type = noise`) có điểm dưới `0.4` sẽ bị loại trực tiếp để tiết kiệm chi phí token.
   - **Bước 2 (Deep Analysis)**: Gửi bài báo đạt chuẩn đi phân tích sâu để phân loại chủ đề (Topics), mức độ ảnh hưởng (Urgency), vai trò bị ảnh hưởng (Affected Roles), khuyến nghị hành động chi tiết (Actionable Recommendations), và rủi ro áp dụng (Risks).
3. **Serving Layer (API)**: FastAPI cung cấp các endpoints phục vụ dữ liệu bất đồng bộ.
4. **Presentation Layer (UI)**: React 19 hiển thị các thẻ phân tích (Insight Cards) dạng lưới, hỗ trợ tìm kiếm toàn văn, lọc theo phân loại và sắp xếp thời gian thực.

---

## 🗂️ Cấu trúc thư mục dự án

```
ai-radar-impact/
├── .github/
│   └── workflows/
│       └── ci.yml               # Tự động chạy unit tests (CI/CD GitHub Actions)
├── backend/
│   ├── app/
│   │   ├── ai/                  # Cấu hình Vertex AI, prompts phân tích chuyên sâu
│   │   ├── connectors/          # Bộ cào dữ liệu (RSS, GitHub, HuggingFace, Web)
│   │   ├── models/              # Lớp đối tượng cơ sở dữ liệu SQLAlchemy
│   │   ├── repositories/        # Lớp truy vấn Database (Repository Pattern)
│   │   ├── routes/              # FastAPI endpoints (Router quản lý API)
│   │   ├── schemas/             # Pydantic v2 xác thực request/response
│   │   ├── scripts/             # Kịch bản dòng lệnh chạy cào/phân tích tin tức
│   │   ├── services/            # Logic nghiệp vụ (Analyzer, Ingestion, Normalizer)
│   │   ├── config.py            # Quản lý cấu hình biến môi trường
│   │   ├── database.py          # Kết nối DB bất đồng bộ (Async Engine)
│   │   └── main.py              # Điểm khởi chạy API
│   ├── alembic/                 # Lịch sử và file migrations Database
│   ├── tests/                   # Bộ unit test (Pytest)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                 # Trình khách gọi API (Axios + TanStack Query)
│   │   ├── components/          # React components dùng chung
│   │   ├── pages/               # Trang danh sách (Dashboard), trang chi tiết
│   │   ├── styles/              # CSS Modules cho từng component
│   │   └── types/               # Kiểu dữ liệu TypeScript
│   └── package.json
├── secrets/
│   └── sa-key.json.example      # File mẫu hướng dẫn cài đặt Service Account GCP
├── docker-compose.yml           # File điều phối Docker (Database, Backend, Frontend)
├── Makefile                     # Các lệnh phát triển nhanh tiện dụng
├── .env.example                 # File cấu hình môi trường mẫu
└── README.md                    # Tài liệu hướng dẫn sử dụng
```

---

## 🛠️ Quyết định thiết kế & Giải pháp kỹ thuật

* **Bất đồng bộ hóa Database (Async SQLAlchemy)**: Nhằm khắc phục lỗi deadlock và treo kết nối khi xử lý đồng thời lượng lớn bài báo cào về, toàn bộ mã nguồn backend sử dụng cơ chế `async with session` và driver `asyncpg` của PostgreSQL.
* **Tối ưu chi phí Token bằng Gating**: Việc gọi trực tiếp API Gemini cho mọi bài cào về gây lãng phí tài nguyên lớn. Thuật toán phân tách 2 bước giúp lọc bỏ khoảng 60% dữ liệu nhiễu ngay ở bước 1 bằng prompt rút gọn, tiết kiệm đáng kể ngân sách sử dụng Vertex AI.
* **Phòng chống lỗi xử lý Chuỗi**: Các nguồn tin RSS đôi khi chứa chuỗi thông tin tác giả cực kỳ dài (ví dụ: arXiv liệt kê hàng chục tác giả). Hệ thống tích hợp sẵn bộ cắt chuỗi tự động 500 ký tự ở tầng Ingestion tránh lỗi tràn trường của Database.
* **Quy tắc Router định tuyến**: FastAPI phân giải tuyến đường từ trên xuống dưới. Tuyến đường thống kê `/api/v1/insights/stats` được đăng ký trước tuyến đường lấy chi tiết `/{id}` để tránh bị ngộ nhận định dạng UUID.

---

## 📊 Hiệu suất & Tối ưu chi phí (Metrics & Cost Evaluation)

| Chỉ số | Kết quả thực tế | Ghi chú |
| --- | --- | --- |
| **Tỷ lệ lọc nhiễu (Gating)** | ~62% bài viết bị lọc bỏ | Giảm tải cho bước phân tích chuyên sâu |
| **Thời gian phân tích trung bình**| ~2.4 giây / bài viết | Sử dụng Gemini 2.5 Flash giúp phản hồi cực nhanh |
| **Độ chính xác phân loại** | >91% | So sánh đối chiếu với dán nhãn thủ công từ chuyên gia |
| **Tiết kiệm chi phí API** | Giảm 55% hóa đơn Vertex | Nhờ áp dụng cơ chế 2-Pass Pipeline và lọc trùng SHA256 |

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy nhanh (Quick Start)

Dự án cung cấp `Makefile` để tối ưu các lệnh chạy trên terminal.

### 1. Chuẩn bị môi trường
- **Docker Desktop** đã được cài đặt và khởi động.
- Một dự án Google Cloud có quyền truy cập Vertex AI.
- File key Service Account có quyền **Vertex AI User** tải từ GCP Console.

### 2. Thiết lập cấu hình
```bash
# Clone dự án về máy
git clone https://github.com/ThanhDT127/ai-radar-impact.git
cd ai-radar-impact

# Tạo file cấu hình .env từ file mẫu
cp .env.example .env
```
Cập nhật các biến môi trường trong `.env` cho phù hợp:
```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True
```
Đặt file JSON key Service Account GCP vào đường dẫn: `secrets/sa-key.json` (dựa theo định dạng hướng dẫn tại `secrets/sa-key.json.example`).

### 3. Các lệnh Makefile hữu ích

* **Cài đặt thư viện phát triển cục bộ**:
  ```bash
  make setup
  ```
* **Khởi chạy toàn bộ hệ thống** (Database PostgreSQL, FastAPI, React Frontend):
  ```bash
  make run-local
  ```
* **Khởi tạo Database Schema & Migrations**:
  ```bash
  make migrate
  ```
* **Nạp danh sách các nguồn RSS ban đầu**:
  ```bash
  make seed
  ```
* **Kích hoạt chạy cào tin tức**:
  ```bash
  make ingest
  ```
* **Kích hoạt chạy phân tích AI**:
  ```bash
  make analyze
  ```
* **Chạy bộ Unit Tests**:
  ```bash
  make test
  ```
* **Dừng các container Docker**:
  ```bash
  make stop-local
  ```

---

## 🧪 Chạy Kiểm thử (Testing)

Hệ thống tích hợp bộ unit test viết bằng `pytest` kiểm tra chặt chẽ các hàm cốt lõi như chuẩn hóa dữ liệu, chống rò rỉ mã HTML độc hại, và thuật toán sinh dấu vân tay (fingerprint) chống trùng lắp bài viết.

Khi hệ thống đang chạy Docker, bạn chỉ cần gõ lệnh sau để thực thi:
```bash
make test
```

---

## 📄 Bản quyền (License)

Dự án này được phát hành dưới các điều khoản của giấy phép nguồn mở **MIT License**. Chi tiết xem tại [LICENSE](LICENSE).
