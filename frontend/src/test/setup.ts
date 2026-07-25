// Mở rộng `expect` với matcher của jest-dom (toBeInTheDocument, …) cho mọi test file.
import '@testing-library/jest-dom/vitest';

// jsdom không cài `scrollIntoView`; widget gọi nó trong effect auto-scroll. No-op để test
// không vỡ vì lý do môi trường thay vì vì assertion.
Element.prototype.scrollIntoView = () => {};
