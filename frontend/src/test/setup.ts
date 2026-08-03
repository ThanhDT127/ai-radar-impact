// Mở rộng `expect` với matcher của jest-dom (toBeInTheDocument, …) cho mọi test file.
import '@testing-library/jest-dom/vitest';

// jsdom không cài `scrollIntoView`; widget gọi nó trong effect auto-scroll. No-op để test
// không vỡ vì lý do môi trường thay vì vì assertion.
Element.prototype.scrollIntoView = () => {};

// Mỗi test là một TAB MỚI (change `chat-session-persistence`).
//
// Chat nay lưu luồng hội thoại vào `sessionStorage`, mà các test trong cùng một file dùng
// chung một môi trường jsdom — nên không dọn thì trạng thái của test trước rò sang test sau:
// widget khôi phục `open: true` và không còn nút "Mở trợ lý hỏi đáp" để bấm. Đây là kiểu rò
// đọc ra thành "test viết sai" chứ không thành "sản phẩm sai", nên dọn ở ĐÂY một lần thay vì
// bắt từng file tự nhớ.
beforeEach(() => {
  window.sessionStorage.clear();
});
