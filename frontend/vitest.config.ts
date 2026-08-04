import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Test runner tối thiểu cho frontend — headless (jsdom), một lệnh `npm test`, không cần trình duyệt.
// Dựng lần đầu bởi change `chat-context-isolation` (điều phối với `chat-citation-integrity` task 2.4:
// change này land trước nên dựng runner; change sau chỉ thêm test, không cấu hình lại).
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
});
