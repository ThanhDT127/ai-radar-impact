## Context

Dashboard của ứng dụng AI Radar Impact đang gặp một số bất cập lớn về mặt thiết kế giao diện (UI) và trải nghiệm người dùng (UX):
1. **Detail Page Hero Overlap**: Giao diện trang chi tiết (`InsightDetail.tsx`) sử dụng ảnh bài viết làm background cho phần Hero Header. Việc này khiến hình ảnh che khuất tiêu đề, các badges và các thông tin quan trọng khác, đặc biệt khi ảnh có độ sáng cao hoặc chứa nhiều họa tiết phức tạp.
2. **Thiếu Split View đối chiếu**: Bài viết gốc (tiếng Anh) và bản tóm tắt/dịch thuật (tiếng Việt) không được hiển thị song song. Người dùng phải kéo xuống dưới cùng để đọc bài viết gốc, gây khó khăn cho việc đối chiếu và kiểm chứng thông tin.
3. **Sidebar quá cồng kềnh**: Sidebar chiếm 30% diện tích trang chi tiết và chứa tới 6 thẻ thông tin (cards) riêng biệt: Điểm đánh giá (Scores), Thông tin chung (Info), Vai trò bị ảnh hưởng (Roles), Chủ đề chính (Topics), Chỉ số thực tế (Indicators), và Dòng thời gian (Timeline). Điều này khiến trang bị kéo dài không cần thiết, làm loãng trải nghiệm đọc.
4. **List Page không đồng đều**: `InsightList.tsx` hiển thị card nổi bật (featured card) chiếm 2 cột (span-2) trong grid. Khi bài viết không có hình ảnh, card này xuất hiện với một icon placeholder màu xám khổng lồ, trông rất mất cân đối và lãng phí không gian.
5. **API thiếu field `primary_image`**: Backend đã thực hiện extract URL hình ảnh chính (`primary_image`) từ RSS/bài viết gốc, tuy nhiên do Pydantic schema của danh sách (`InsightListItem`) thiếu trường này, API trả về không có ảnh dẫn đến việc danh sách dashboard hoàn toàn không có hình ảnh nào.

Change này thuộc **Module M6 (Dashboard)** và tập trung tái cấu trúc giao diện để giải quyết triệt để các vấn đề trên.

## Goals / Non-Goals

**Goals:**
- Tách biệt hoàn toàn hình ảnh chính khỏi nền chữ trong trang chi tiết. Chuyển hình ảnh thành dạng thumbnail nhỏ, nằm cạnh tiêu đề.
- Loại bỏ layout 70/30 và sidebar cồng kềnh trên trang chi tiết.
- Thiết kế một dải metadata ribbon compact nằm ngay bên dưới tiêu đề trang chi tiết, gộp gọn 6 cards thông tin cũ thành một dòng duy nhất (~80px chiều cao).
- Triển khai giao diện Split View song ngữ (50/50) trên trang chi tiết: Cột trái hiển thị nội dung tóm tắt & phân tích tiếng Việt của Gemini; Cột phải hiển thị nội dung bài viết gốc tiếng Anh. Cả hai cột có khả năng scroll độc lập.
- Thêm tóm tắt cốt lõi (`so_what`) ở vị trí nổi bật nhất ngay dưới tiêu đề.
- Đồng bộ hóa các card trong danh sách (`InsightList`): Tất cả có cùng kích thước, không sử dụng layout featured card.
- Thu nhỏ ảnh đại diện của card danh sách thành thumbnail inline nhỏ ở góc bên phải.
- Xử lý triệt để lỗi ảnh hỏng/thiếu định dạng bằng việc ẩn hẳn container ảnh khi không load được (dùng `onError` handler) hoặc khi bài viết không có ảnh, tránh việc hiển thị placeholder trống.
- Bổ sung trường `primary_image` vào Pydantic schema `InsightListItem` của backend để API trả về đầy đủ ảnh cho frontend.

**Non-Goals:**
- Không thay đổi logic phân tích, chấm điểm hay phân loại của AI pipeline (FastAPI/Gemini).
- Không sửa đổi cấu trúc cơ sở dữ liệu (PostgreSQL) — trường `primary_image` và `content_text` đã tồn tại sẵn trong bảng `insights`.
- Không thay đổi hoặc tối ưu hóa chức năng lọc (Filter), tìm kiếm (Search) hay sắp xếp (Sort).
- Không thực hiện responsive tối ưu cho mobile/tablet trong scope của thay đổi này (được dời sang một change spec riêng).
- Không tích hợp hay thay đổi bất kỳ flow delivery nào qua n8n.

## Decisions

### 1. Module M6 (Dashboard) & API Endpoints ảnh hưởng
- **Backend API Schema**: Sửa đổi Pydantic model `InsightListItem` trong `backend/app/schemas/insight.py` để bổ sung trường `primary_image: str | None = None`. Trường này sẽ được tự động map từ database record sang API response.
- **Database**: Không thay đổi bảng DB. Dữ liệu `primary_image` đã được lưu trữ sẵn trong bảng `insights` của PostgreSQL và map thông qua SQLAlchemy model.
- **Không tạo API endpoint mới**: Chỉ cập nhật schema đầu ra của endpoint GET `/api/v1/insights`.

### 2. Tái cấu trúc Layout Detail Page (`InsightDetail.tsx`)
- **Header Section**:
  - Bỏ background hero image và các gradient overlay. Thay bằng nền background phẳng của ứng dụng.
  - Sử dụng bố cục Flexbox ngang: Cột trái chứa Title, Metadata Ribbon và core summary (`so_what`). Cột phải chứa thumbnail ảnh bài viết (`primary_image`) kích thước cố định `180px x 120px` với `object-fit: cover` và bo góc nhẹ `border-radius: 8px`. Nếu không có ảnh, cột phải sẽ tự động co lại và cột trái chiếm toàn bộ width.
- **Core Summary (so_what)**:
  - Đưa phần "So What" (Ý nghĩa cốt lõi) lên vị trí đắt giá nhất ngay dưới tiêu đề, sử dụng font chữ lớn hơn, màu sắc nổi bật để tạo điểm nhấn trực quan (visual anchor).
- **Compact Metadata Ribbon**:
  - Loại bỏ hoàn toàn 6 thẻ sidebar độc lập.
  - Gộp tất cả thành một dải metadata ngang gọn gàng. Các thông tin sẽ được chia thành các nhóm nhỏ nằm ngang:
    - **Scores**: Điểm tin cậy (🛡️ Trust Score) và điểm khả thi (⚡ Actionability Score) hiển thị dạng phần trăm với màu sắc tương ứng.
    - **General Info**: Nhóm đối tượng (Roles) dưới dạng các badge nhỏ, Phân loại (Tier, Event Type).
    - **Practical Indicators**: Các icon/badge nhỏ thể hiện có code ví dụ (📝 Code), có benchmark (📊 Benchmark), có API thay đổi (⚙️ API).
    - **Timeline**: Nguồn bài viết, ngày xuất bản.
  - Dải này sẽ có đường viền bo quanh nhẹ và nền tối giản để phân biệt rõ ràng với phần nội dung bên dưới.
- **Split View 50/50**:
  - Layout chính bên dưới Header sẽ được chia thành 2 cột đều nhau (`grid-template-columns: 1fr 1fr; gap: 24px; height: calc(100vh - 280px);`).
  - **Cột trái (Bản dịch & Phân tích tiếng Việt)**: Hiển thị các block do Gemini phân tích: Tóm tắt chi tiết (Medium Summary), Tín hiệu thị trường (Signal), Lý do quan trọng (Why it matters), Khuyến nghị hành động (Recommendations), và Rủi ro (Risks). Cột này có `overflow-y: auto` để scroll độc lập.
  - **Cột phải (Bài viết gốc tiếng Anh)**: Hiển thị bài viết gốc (`content_text`). Cột này cũng có `overflow-y: auto` và scroll độc lập. Nếu `content_text` trống hoặc null, giao diện sẽ tự động co về layout 1 cột (chỉ hiện cột phân tích tiếng Việt) thay vì để một nửa màn hình trống rỗng.

### 3. Thiết kế lại List Card (`InsightCard.tsx` & `InsightList.tsx`)
- **Card đồng nhất**: Loại bỏ class `cardFeatured` và logic render card span 2 cột trong `InsightList.tsx`. Tất cả card giờ đây sẽ hiển thị đồng đều trong grid 3 cột hoặc 4 cột tùy màn hình.
- **Thumbnail Image**:
  - Không dùng ảnh nền tỷ lệ 16:9 ở trên đầu card nữa.
  - Chuyển ảnh đại diện thành một thumbnail nhỏ (`100px x 70px`) đặt bên phải của card content (bên trong flex layout).
  - Tích hợp `onError` event handler vào thẻ `<img>` của card. Khi có lỗi load ảnh (do link hỏng, định dạng không đúng), state `imageError` sẽ được set thành `true` và component sẽ ẩn hoàn toàn thẻ ảnh đó.
  - Đối với các bài viết không có ảnh (`primary_image` null hoặc `imageError` true): Ẩn hoàn toàn container ảnh, nội dung text của card sẽ tự động giãn ra chiếm trọn chiều rộng của card.

## Risks / Trade-offs

- **Lỗi hiển thị khi bài viết gốc quá dài**: Do split-view sử dụng hai cột scroll độc lập, nếu chiều cao viewport quá nhỏ, giao diện có thể tạo ra cảm giác ngột ngạt. Quyết định trade-off ở đây là chấp nhận giới hạn chiều cao cố định của vùng đọc để đảm bảo người dùng luôn nhìn thấy cả hai bản cùng lúc mà không phải scroll trang chính.
- **Dữ liệu bài viết gốc thô**: Dữ liệu `content_text` từ DB đôi khi bị gộp thành một khối văn bản liên tục không xuống dòng (wall of text). Để khắc phục vấn đề này mà không can thiệp backend parser, frontend sẽ render `content_text` thông qua một helper tự động tách đoạn dựa trên dấu chấm câu hoặc sử dụng style `white-space: pre-wrap;` để bảo toàn cấu trúc xuống dòng nguyên bản nếu có.
