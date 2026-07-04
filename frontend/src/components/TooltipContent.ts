export const TOOLTIP = {
  tier: {
    Tactical:
      'Hành động ngay: Thông tin kỹ thuật thực hành (như công cụ mới, bản vá lỗi, code mẫu) cần lập trình viên/kỹ sư xem xét áp dụng sớm.',
    Operational:
      'Lên kế hoạch vận hành: Ảnh hưởng đến quy trình làm việc hàng ngày của các đội nhóm, cần quản lý đánh giá và lên lịch điều chỉnh.',
    Strategic:
      'Tầm nhìn chiến lược: Xu hướng công nghệ dài hạn, nghiên cứu mới hoặc chính sách quan trọng giúp định hướng tương lai, chưa cần làm ngay.',
    Informational:
      'Tham khảo thêm: Tin tức công nghệ chung để cập nhật kiến thức, không yêu cầu hành động cụ thể.',
  },
  urgency: {
    critical:
      'Mức độ cấp thiết: Rất khẩn cấp — Đòi hỏi phải xem xét và xử lý ngay trong ngày để vá lỗ hổng hoặc sửa lỗi hệ thống nghiêm trọng.',
    high: 'Mức độ cấp thiết: Ưu tiên cao — Cần xem xét và lên kế hoạch giải quyết sớm trong tuần này.',
    medium: 'Mức độ cấp thiết: Trung bình — Cần theo dõi sát sao, sắp xếp xử lý khi có thời gian thích hợp (không bắt buộc xử lý gấp).',
    low: 'Mức độ cấp thiết: Thấp — Đọc để cập nhật thông tin chung, lưu lại tham khảo khi cần thiết.',
  },
  impact: {
    'Nghiêm trọng':
      'Mức độ ảnh hưởng: Nghiêm trọng — Tác động cực kỳ lớn! Có thể gây ngừng hoạt động toàn hệ thống hoặc thay đổi hoàn toàn kế hoạch của dự án.',
    Cao: 'Mức độ ảnh hưởng: Cao — Tác động lớn! Đòi hỏi phải chuẩn bị phương án điều chỉnh quy trình làm việc hoặc sửa đổi mã nguồn.',
    'Trung bình':
      'Mức độ ảnh hưởng: Trung bình — Tác động vừa phải! Có thể giải quyết trong các đợt cập nhật hoặc bảo trì định kỳ tiếp theo.',
    Thấp: 'Mức độ ảnh hưởng: Thấp — Tác động rất ít! Hầu như không ảnh hưởng gì đến công việc và dự án hiện tại.',
    'Theo dõi':
      'Mức độ ảnh hưởng: Cần theo dõi thêm — Chưa có đủ dữ liệu hoặc số liệu để đưa ra đánh giá chính xác.',
    Critical:
      'Mức độ ảnh hưởng: Nghiêm trọng — Tác động cực kỳ lớn! Có thể gây ngừng hoạt động toàn hệ thống hoặc thay đổi hoàn toàn kế hoạch của dự án.',
    High: 'Mức độ ảnh hưởng: Cao — Tác động lớn! Đòi hỏi phải chuẩn bị phương án điều chỉnh quy trình làm việc hoặc sửa đổi mã nguồn.',
    Medium: 'Mức độ ảnh hưởng: Trung bình — Tác động vừa phải! Có thể giải quyết trong các đợt cập nhật hoặc bảo trì định kỳ tiếp theo.',
    Low: 'Mức độ ảnh hưởng: Thấp — Tác động rất ít! Hầu như không ảnh hưởng gì đến công việc và dự án hiện tại.',
    Watch: 'Mức độ ảnh hưởng: Cần theo dõi thêm — Chưa có đủ dữ liệu hoặc số liệu để đưa ra đánh giá chính xác.',
  },
  momentum: {
    new: 'Mới phát hành: Tín hiệu công nghệ mới xuất hiện trong 24-48 giờ qua, cần cập nhật sớm.',
    rising:
      'Đang rất "hot": Chủ đề đang được nhiều trang tin và cộng đồng công nghệ thảo luận sôi nổi gần đây.',
    mature: 'Đã ổn định: Công nghệ hoặc chủ đề đã được khẳng định, được thảo luận đều đặn và phổ biến rộng rãi.',
  },
  vietnam: {
    high: 'Liên quan cao đến Việt Nam: Tác động trực tiếp đến các sản phẩm, dự án hoặc cộng đồng công nghệ tại Việt Nam.',
    medium: 'Liên quan vừa: Tác động gián tiếp hoặc có khả năng ảnh hưởng đến thị trường Việt Nam trong tương lai.',
    low: 'Ít liên quan: Tin tức công nghệ toàn cầu, hầu như không ảnh hưởng trực tiếp đến bối cảnh Việt Nam.',
  },
  role: {
    'Data Analyst': 'Data Analyst: Cần biết để phân tích và trực quan hóa dữ liệu hiệu quả hơn.',
    'Data Scientist': 'Data Scientist: Cần biết để cập nhật mô hình, thuật toán hoặc phương pháp nghiên cứu mới.',
    'AI Engineer': 'AI Engineer: Cần biết để cập nhật framework, triển khai và tối ưu hóa hệ thống AI/ML.',
    'Data Engineer': 'Data Engineer: Cần biết để tối ưu hóa luồng dữ liệu, lưu trữ hoặc quy trình ETL.',
    Security: 'Đội ngũ Bảo mật: Cần biết để vá lỗ hổng, ứng phó sự cố hoặc bảo vệ hệ thống.',
    Dev: 'Đội ngũ Lập trình (Dev): Cần xem xét để sửa code, tích hợp hoặc cập nhật thư viện.',
    'Tech Lead': 'Tech Lead: Cần biết để đánh giá kiến trúc, đưa ra quyết định công nghệ và dẫn dắt team.',
    'Người dùng phổ thông': 'Người dùng phổ thông: Cần biết để cập nhật ứng dụng, hiểu sự thay đổi của sản phẩm.',
    'Toàn công ty': 'Toàn thể nhân viên: Tin tức chung có ảnh hưởng rộng rãi đến tất cả mọi người trong công ty.',
  },
  score: {
    actionability:
      'Điểm hành động (0–100%): Điểm càng cao nghĩa là bài viết càng có nhiều hướng dẫn chi tiết, code mẫu và bước thực hiện rõ ràng để làm theo được ngay.',
    trust:
      'Độ tin cậy nguồn tin (0–100%): Đánh giá dựa trên độ uy tín của nguồn (Nguồn từ hãng công nghệ lớn hoặc tài liệu chính thức sẽ cao hơn blog cá nhân).',
    confidence:
      'Độ tin cậy của AI (0–100%): Mức độ tự tin của mô hình Gemini khi phân tích bài viết. Điểm dưới 50% có nghĩa là thông tin có thể cần con người kiểm chứng lại.',
  },
  adoption: {
    Adopt: 'Nên dùng ngay: Công nghệ/giải pháp đã cực kỳ ổn định, rất an toàn để đưa vào dự án thực tế.',
    Trial: 'Nên thử nghiệm: Có tiềm năng lớn, khuyên dùng thử ở dự án nhỏ trước khi triển khai rộng.',
    Assess: 'Cần đánh giá thêm: Công nghệ triển vọng nhưng cần nghiên cứu kỹ độ phù hợp và rủi ro.',
    Hold: 'Tạm hoãn: Chưa chín muồi hoặc rủi ro quá cao, nên chờ thêm một thời gian.',
  },
  practicalIndicators: {
    has_code: '💻 Bài viết có kèm sẵn code mẫu hoặc hướng dẫn kỹ thuật chi tiết.',
    has_benchmark: '📊 Có số liệu đo đạc, so sánh hiệu năng thực tế (Benchmark).',
    has_api_change: '🔗 Có thay đổi về API, cổng kết nối (cần cập nhật code nếu đang dùng).',
    has_migration: '📖 Có hướng dẫn nâng cấp, chuyển đổi từ phiên bản cũ lên phiên bản mới.',
    has_security: '🛡️ Cảnh báo bảo mật quan trọng hoặc vá lỗi lỗ hổng nguy hiểm.',
  },
  kpi: {
    total: 'Tổng số bài viết mà AI đã phân tích trong 7 ngày gần nhất, bao gồm tất cả nguồn tin đang hoạt động.',
    critical: 'Số bài viết có mức ảnh hưởng "Cao" hoặc "Nghiêm trọng" — cần ưu tiên xem xét trước.',
    opportunity: 'Số bài viết có cơ hội hành động cao — chứa hướng dẫn, code mẫu hoặc giải pháp áp dụng được.',
    sources: 'Số nguồn tin đang hoạt động và cập nhật thường xuyên.',
  },
} as const;
