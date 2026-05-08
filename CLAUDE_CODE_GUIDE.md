# Claude Code — Hướng Dẫn Sử Dụng Đầy Đủ

> Tài liệu tham khảo toàn bộ lệnh, tính năng, phím tắt, cấu hình và best practices của Claude Code CLI.

---

## Mục lục

1. [Slash Commands tích hợp sẵn](#1-slash-commands-tích-hợp-sẵn)
2. [Chế độ cấp quyền (Permission Modes)](#2-chế-độ-cấp-quyền-permission-modes)
3. [Phím tắt](#3-phím-tắt)
4. [CLI Flags khi khởi động](#4-cli-flags-khi-khởi-động)
5. [Tiền tố đặc biệt trong prompt](#5-tiền-tố-đặc-biệt-trong-prompt)
6. [Cấu hình settings.json](#6-cấu-hình-settingsjson)
7. [Skills có thể gọi bằng /](#7-skills-có-thể-gọi-bằng-)
8. [Tính năng nâng cao](#8-tính-năng-nâng-cao)
9. [Biến môi trường](#9-biến-môi-trường)
10. [CLAUDE.md — Best Practices](#10-claudemd--best-practices)
11. [Hooks System — Tự động hóa hành động](#11-hooks-system--tự-động-hóa-hành-động)
12. [MCP Servers — Kết nối công cụ bên ngoài](#12-mcp-servers--kết-nối-công-cụ-bên-ngoài)
13. [Multi-Agent & Subagent Patterns](#13-multi-agent--subagent-patterns)
14. [Memory System — Bộ nhớ liên session](#14-memory-system--bộ-nhớ-liên-session)
15. [Workflow Patterns & Automation](#15-workflow-patterns--automation)
16. [Tối ưu hiệu suất & chi phí](#16-tối-ưu-hiệu-suất--chi-phí)
17. [Bảo mật & Hardening](#17-bảo-mật--hardening)
18. [Setup cho Team & Enterprise](#18-setup-cho-team--enterprise)
19. [Config Templates đầy đủ](#19-config-templates-đầy-đủ)

---

## 1. Slash Commands tích hợp sẵn

### Quản lý phiên làm việc

| Lệnh | Mô tả |
|------|-------|
| `/clear` | Xóa hội thoại, bắt đầu mới (alias: `/reset`, `/new`) |
| `/continue` | Tiếp tục hội thoại theo ID hoặc tên |
| `/resume [session]` | Resume session cụ thể |
| `/branch [name]` | Tạo nhánh hội thoại (alias: `/fork`) |
| `/compact [hướng dẫn]` | Tóm tắt hội thoại để giải phóng context |
| `/rewind` | Quay lại checkpoint trước (alias: `/undo`) |
| `/rename [tên]` | Đổi tên session hiện tại |
| `/recap` | Tạo tóm tắt 1 dòng cho session hiện tại |
| `/context` | Hiển thị mức sử dụng context dạng grid màu |
| `/export [filename]` | Export hội thoại ra file text |

### Model & Hiệu suất

| Lệnh | Mô tả |
|------|-------|
| `/model [tên]` | Chọn hoặc đổi model AI |
| `/effort [mức]` | Đặt mức nỗ lực: `low`, `medium`, `high`, `xhigh`, `max`, `auto` |
| `/fast [on\|off]` | Bật/tắt Fast Mode (Opus 4.6, output nhanh hơn) |

### Quyền & Bảo mật

| Lệnh | Mô tả |
|------|-------|
| `/permissions` | Quản lý allow/ask/deny rules (alias: `/allowed-tools`) |
| `/security-review` | Phân tích thay đổi code về bảo mật |

### Code Review & Phân tích

| Lệnh | Mô tả |
|------|-------|
| `/review [PR]` | Review pull request cục bộ |
| `/ultrareview [PR]` | Deep review đa agent trên cloud sandbox |
| `/diff` | Xem uncommitted changes dạng interactive |
| `/debug` | Bật debug logging, chẩn đoán lỗi |

### Workflow & Lập kế hoạch

| Lệnh | Mô tả |
|------|-------|
| `/plan [mô tả]` | Vào chế độ lập kế hoạch (chỉ đọc, đề xuất trước) |
| `/loop [interval] [prompt]` | Chạy lệnh lặp lại theo chu kỳ |
| `/schedule` | Tạo/quản lý tác vụ lên lịch (cron) |
| `/ultraplan` | Soạn kế hoạch trên cloud, duyệt rồi thực thi local |
| `/autofix-pr` | Tự động fix lỗi CI trên PR |
| `/tasks` | Liệt kê và quản lý background tasks (alias: `/bashes`) |

### File & Context

| Lệnh | Mô tả |
|------|-------|
| `/add-dir <path>` | Thêm thư mục làm việc |
| `/copy [N]` | Copy response gần nhất vào clipboard |

### Hiển thị & Giao diện

| Lệnh | Mô tả |
|------|-------|
| `/config` | Mở Settings UI (alias: `/settings`) |
| `/theme [màu]` | Đổi giao diện màu; hỗ trợ `light`, `dark`, colorblind, ANSI |
| `/color [màu]` | Đổi màu thanh prompt cho session |
| `/tui [chế độ]` | Đặt renderer: `default` hoặc `fullscreen` |
| `/focus` | Toggle focus view (chỉ hiện prompt + response gần nhất) |
| `/statusline` | Cấu hình status line |

### Tool & Tích hợp

| Lệnh | Mô tả |
|------|-------|
| `/hooks` | Xem cấu hình hooks |
| `/mcp` | Quản lý MCP server connections và OAuth |
| `/ide` | Quản lý tích hợp IDE (VS Code, JetBrains) |
| `/chrome` | Cấu hình tích hợp Chrome browser |
| `/keybindings` | Mở/tạo file cấu hình phím tắt |
| `/skills` | Liệt kê tất cả skills có sẵn |
| `/plugin` | Quản lý plugins |
| `/reload-plugins` | Reload plugins không cần restart |
| `/agents` | Quản lý cấu hình agents |
| `/remote-control` | Bật Remote Control cho session (alias: `/rc`) |
| `/teleport` | Pull web session vào terminal (alias: `/tp`) |

### Tài khoản & Thông tin

| Lệnh | Mô tả |
|------|-------|
| `/login` | Đăng nhập tài khoản Anthropic |
| `/logout` | Đăng xuất |
| `/status` | Xem version, model, account, kết nối mạng |
| `/usage` | Xem chi phí session hiện tại (alias: `/cost`, `/stats`) |
| `/upgrade` | Mở trang nâng cấp plan |
| `/doctor` | Chẩn đoán và kiểm tra cài đặt; nhấn `f` để tự fix |
| `/release-notes` | Xem changelog theo phiên bản |
| `/insights` | Báo cáo phân tích các session đã dùng |
| `/feedback` | Gửi feedback hoặc báo lỗi (alias: `/bug`) |
| `/help` | Hiển thị trợ giúp |
| `/exit` | Thoát CLI (alias: `/quit`) |

### Các lệnh khác

| Lệnh | Mô tả |
|------|-------|
| `/btw <câu hỏi>` | Hỏi nhanh không ảnh hưởng lịch sử hội thoại |
| `/voice [hold\|tap\|off]` | Điều khiển nhập liệu bằng giọng nói |
| `/terminal-setup` | Cấu hình Shift+Enter trong terminal |
| `/desktop` | Tiếp tục session trong Desktop app (alias: `/app`) |
| `/mobile` | Hiển thị QR code tải app mobile |
| `/init` | Khởi tạo file CLAUDE.md cho dự án |
| `/install-github-app` | Cài Claude GitHub Actions app |
| `/install-slack-app` | Cài Claude Slack app |
| `/heapdump` | Ghi heap snapshot và phân tích bộ nhớ |
| `/team-onboarding` | Tạo hướng dẫn onboarding team từ lịch sử session |
| `/setup-bedrock` | Cấu hình Amazon Bedrock |
| `/setup-vertex` | Cấu hình Google Vertex AI |

---

## 2. Chế độ cấp quyền (Permission Modes)

Nhấn **`Shift+Tab`** để chuyển đổi tuần tự giữa các chế độ.

| Chế độ | Tự động làm gì | Khi nào dùng |
|--------|---------------|-------------|
| `default` | Chỉ đọc file | Bắt đầu, công việc nhạy cảm |
| `acceptEdits` | Đọc + sửa file + lệnh filesystem | Đang iterate code |
| `plan` | Chỉ đọc, đề xuất trước khi thực hiện | Khám phá trước khi thay đổi |
| `auto` | Gần như mọi thứ, có kiểm tra nền | Tác vụ dài, giảm số lần hỏi |
| `dontAsk` | Chỉ những tool đã pre-approve | Scripts, CI/CD |
| `bypassPermissions` | Tất cả, không kiểm tra | **Chỉ dùng trong container/VM cô lập** |

**Cách đặt mặc định trong settings.json:**
```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

**Cách đặt khi khởi động:**
```bash
claude --permission-mode acceptEdits
claude --permission-mode plan
claude --dangerously-skip-permissions
```

---

## 3. Phím tắt

### Điều hướng chung

| Phím | Tác dụng |
|------|----------|
| `Shift+Tab` | Chuyển chế độ quyền (default → acceptEdits → plan) |
| `Ctrl+C` | Hủy input đang nhập hoặc dừng generation |
| `Ctrl+D` | Thoát Claude Code |
| `Ctrl+L` | Vẽ lại màn hình |
| `Ctrl+R` | Tìm kiếm lịch sử lệnh (interactive) |
| `Esc + Esc` | Rewind về checkpoint trước |

### View & Panels

| Phím | Tác dụng |
|------|----------|
| `Ctrl+O` | Mở/đóng Transcript Viewer (xem chi tiết tool calls) |
| `Ctrl+T` | Mở/đóng danh sách Tasks |
| `Ctrl+B` | Chạy task nền (background) |

### Chuyển chế độ nhanh

| Phím | Tác dụng |
|------|----------|
| `Alt+M` | Chuyển chế độ quyền |
| `Alt+P` | Chuyển model |
| `Alt+T` | Toggle Extended Thinking |
| `Alt+O` | Toggle Fast Mode |

### Soạn thảo trong prompt

| Phím | Tác dụng |
|------|----------|
| `\` + Enter | Xuống dòng (multiline input) |
| `Shift+Enter` | Xuống dòng (nếu terminal hỗ trợ) |
| `Ctrl+A` | Di chuyển về đầu dòng |
| `Ctrl+E` | Di chuyển về cuối dòng |
| `Ctrl+K` | Xóa từ cursor đến cuối dòng |
| `Ctrl+U` | Xóa từ cursor về đầu dòng |
| `Ctrl+W` | Xóa từ trước cursor |
| `Ctrl+Y` | Paste text vừa xóa |
| `Alt+B` / `Alt+F` | Di chuyển lùi/tiến một từ |
| `Up/Down arrows` | Duyệt lịch sử lệnh |
| `Ctrl+G` | Mở prompt trong text editor mặc định |

### Trong Transcript Viewer (`Ctrl+O`)

| Phím | Tác dụng |
|------|----------|
| `v` | Mở hội thoại trong `$EDITOR` |
| `[` | Ghi vào scrollback của terminal |
| `q` / `Esc` | Đóng transcript viewer |

---

## 4. CLI Flags khi khởi động

### Session

```bash
claude                              # Bắt đầu session tương tác
claude "câu hỏi"                    # Bắt đầu với prompt ngay
claude -c                           # Tiếp tục session gần nhất
claude -r "tên-session" "query"     # Resume session theo tên
claude --name "tên"                 # Đặt tên cho session
claude --fork-session               # Fork thay vì resume
```

### Model & Hiệu suất

```bash
claude --model claude-sonnet-4-6
claude --model claude-opus-4-7
claude --model claude-haiku-4-5
claude --effort high                # low | medium | high | xhigh | max
```

### Chế độ quyền

```bash
claude --permission-mode plan
claude --permission-mode acceptEdits
claude --permission-mode auto
claude --permission-mode dontAsk
claude --permission-mode bypassPermissions
claude --dangerously-skip-permissions
```

### Thư mục & File

```bash
claude --add-dir ../docs --add-dir ../shared
```

### System Prompt tùy chỉnh

```bash
claude --system-prompt "Bạn là chuyên gia Python"
claude --system-prompt-file ./my-prompt.txt
claude --append-system-prompt "Luôn dùng TypeScript"
```

### Non-interactive / Print mode

```bash
claude -p "câu hỏi"                         # In ra rồi thoát
cat file.py | claude -p "giải thích code này"
claude -p --output-format json "query"       # json | text | stream-json
claude -p --max-budget-usd 2.00 "query"     # Giới hạn chi phí
claude --max-turns 5                         # Giới hạn số lượt
```

### Tools

```bash
claude --tools "Bash,Edit,Read"              # Chỉ cho phép tools này
claude --tools ""                            # Tắt tất cả tools
claude --allowedTools "Bash(npm test)" "Read"
claude --disallowedTools "Bash(git push *)"
```

### MCP & Plugins

```bash
claude --mcp-config ./mcp.json
claude --strict-mcp-config --mcp-config ./mcp.json
claude --plugin-dir ./my-plugin
claude --plugin-url https://example.com/plugin.zip
```

### Worktree (làm việc song song)

```bash
claude -w feature-name              # Tạo git worktree riêng
claude -w feature-name --tmux       # Kèm tmux session
```

### Remote & Cloud

```bash
claude --remote "Fix the login bug"          # Tạo web session
claude --remote-control "Project Name"       # Bật Remote Control
claude --teleport                            # Pull web session về local
```

### Debug

```bash
claude --debug
claude --debug "api,hooks"
claude --debug-file /tmp/debug.log
claude --verbose
```

### Khác

```bash
claude -v                           # Xem version
claude update                       # Cập nhật lên phiên bản mới nhất
claude install stable               # Cài phiên bản ổn định
claude --bare                       # Minimal mode, không auto-discovery
claude --init-only                  # Chạy setup hooks rồi thoát
```

---

## 5. Tiền tố đặc biệt trong prompt

| Tiền tố | Tác dụng | Ví dụ |
|---------|----------|-------|
| `/` | Gọi lệnh hoặc skill | `/clear`, `/model` |
| `!` | Chạy shell command trực tiếp | `! git status`, `! docker ps` |
| `@` | Mention file để autocomplete | `@backend/app/main.py` |

> **Mẹo:** Dùng `!` để chạy lệnh và đưa output vào context hội thoại ngay lập tức.

---

## 6. Cấu hình settings.json

### Vị trí file (ưu tiên từ cao → thấp)

| File | Phạm vi | Git |
|------|---------|-----|
| Managed (IT deploy) | Toàn tổ chức | Không thể override |
| `.claude/settings.local.json` | Dự án, local | Không commit |
| `.claude/settings.json` | Dự án | Commit |
| `~/.claude/settings.json` | Toàn user | — |

### Các tùy chọn quan trọng

```json
{
  "model": "claude-sonnet-4-6",
  "effortLevel": "medium",
  "language": "vi",

  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm test)",
      "Read(~/.zshrc)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Bash(curl *)",
      "Read(./.env)"
    ],
    "additionalDirectories": ["../docs/"]
  },

  "autoMemoryEnabled": true,
  "alwaysThinkingEnabled": false,
  "showThinkingSummaries": true,
  "fastModePerSessionOptIn": true,

  "env": {
    "MY_VAR": "value"
  }
}
```

### Cấu hình Sandbox

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": ["/tmp/build"],
      "denyRead": ["~/.aws/credentials"]
    },
    "network": {
      "allowedDomains": ["github.com", "npmjs.com"]
    }
  }
}
```

---

## 7. Skills có thể gọi bằng `/`

### OpenSpec Workflow (quản lý thay đổi có cấu trúc)

| Lệnh | Khi nào dùng |
|------|-------------|
| `/openspec-new-change` | Bắt đầu thay đổi mới (từng bước) |
| `/openspec-propose` | Đề xuất + tạo toàn bộ artifacts ngay |
| `/openspec-ff-change` | Fast-forward: tạo nhanh tất cả artifacts |
| `/openspec-apply-change` | Thực thi tasks từ change đang mở |
| `/openspec-continue-change` | Tiếp tục tạo artifact tiếp theo |
| `/openspec-verify-change` | Kiểm tra implementation đúng với spec |
| `/openspec-archive-change` | Lưu trữ change đã hoàn thành |
| `/openspec-explore` | Chế độ khám phá / tư duy trước khi code |

### Memory & Codebase (bộ nhớ liên session)

| Lệnh | Khi nào dùng |
|------|-------------|
| `/claude-mem:learn-codebase` | Đọc toàn bộ source để hiểu dự án |
| `/claude-mem:make-plan` | Lập kế hoạch thực thi nhiều bước |
| `/claude-mem:do` | Thực thi kế hoạch bằng subagents |
| `/claude-mem:mem-search` | Tìm kiếm trong bộ nhớ session trước |
| `/claude-mem:smart-explore` | Khám phá cấu trúc code hiệu quả (AST) |
| `/claude-mem:pathfinder` | Vẽ sơ đồ kiến trúc, phát hiện trùng lặp |
| `/claude-mem:knowledge-agent` | Xây knowledge base từ lịch sử quan sát |
| `/claude-mem:timeline-report` | Báo cáo timeline công việc |

### Tiện ích khác

| Lệnh | Khi nào dùng |
|------|-------------|
| `/simplify` | Review và tối ưu code vừa thay đổi |
| `/fewer-permission-prompts` | Giảm số lần hỏi quyền bằng allowlist |
| `/update-config` | Cấu hình hooks, permissions trong settings.json |
| `/claude-api` | Hỗ trợ xây dựng app với Anthropic SDK |
| `/init` | Khởi tạo CLAUDE.md cho dự án |
| `/review` | Review pull request |
| `/security-review` | Review bảo mật |

---

## 8. Tính năng nâng cao

### Bộ nhớ tự động (Auto Memory)

Claude Code tự lưu trí nhớ vào file sau mỗi session. Để nhớ điều gì đó cụ thể, nói:
> "Hãy nhớ rằng..."

Vị trí bộ nhớ: `~/.claude/projects/<project>/memory/`

### Transcript Viewer

Mở bằng `Ctrl+O` để xem chi tiết:
- Tất cả tool calls đã thực hiện
- MCP calls
- Thinking blocks
- Token usage per turn

### Background Tasks

- Nhấn `Ctrl+B` để chạy task nền
- Claude tiếp tục làm việc trong khi bạn nhập tiếp
- Theo dõi với `/tasks`

### Shell Mode

Gõ `!` trước lệnh để chạy trực tiếp trong shell:
```
! docker-compose ps
! git log --oneline -5
! python -m app.scripts.run_analysis
```
Output được tự động thêm vào context hội thoại.

### Extended Thinking

Bật để Claude suy nghĩ sâu hơn trước khi trả lời:
- Toggle bằng `Alt+T`
- Đặt mặc định: `"alwaysThinkingEnabled": true` trong settings

---

## 9. Biến môi trường

| Biến | Tác dụng |
|------|----------|
| `CLAUDE_CODE_USE_BEDROCK=1` | Bật tùy chọn Amazon Bedrock |
| `CLAUDE_CODE_USE_VERTEX=1` | Bật tùy chọn Google Vertex AI |
| `CLAUDE_CODE_DEBUG_LOGS_DIR` | Thư mục lưu debug logs |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` | Tắt background commands |
| `CLAUDE_CODE_ENABLE_TELEMETRY=1` | Bật telemetry |
| `CLAUDE_CODE_SIMPLE=1` | Startup nhanh hơn (set bởi `--bare`) |
| `MAX_MCP_OUTPUT_TOKENS` | Giới hạn token output của MCP tools |

---

## 10. CLAUDE.md — Best Practices

CLAUDE.md là **hợp đồng giữa bạn và Claude** — được load vào mỗi session và định nghĩa rules, conventions, kiến trúc. Viết tốt sẽ tiết kiệm hàng trăm token mỗi session.

### Nên viết gì (giữ dưới 200 dòng)

```markdown
# Project Setup
- Lệnh build, test, lint cụ thể của dự án
- Biến môi trường cần thiết
- Cách chạy migration, seed data

# Code Style (chỉ những gì khác default)
- Indentation: 2-space hay 4-space hay tab
- Naming conventions: camelCase/snake_case theo context
- Async patterns: async/await hay .then()
- Import style: ES modules hay CommonJS

# Kiến trúc
- Cấu trúc thư mục và vai trò từng layer
- Quy trình thêm tính năng mới (step-by-step)
- Database patterns: ORM, migration strategy
- Quy ước đặt tên file

# Git & PR Workflow
- Quy ước đặt tên branch (feat/, fix/, hotfix/)
- Format commit message
- Điều kiện merge

# Known Gotchas
- Những bug đã từng xảy ra mà không rõ nguyên nhân
- Quirks của thư viện/framework đang dùng
- Các lỗi thường gặp và cách fix
```

### Không nên viết gì

- Conventions phổ biến mà Claude đã biết
- Mô tả từng file đang có (Claude sẽ tự đọc)
- Tài liệu API chi tiết (chỉ cần link)
- Thông tin thay đổi thường xuyên
- Lời khuyên chung chung như "viết code sạch"

### Tổ chức file theo quy mô dự án

**Dự án nhỏ — 1 file:**
```
project/
└── CLAUDE.md
```

**Dự án lớn — tách theo chủ đề:**
```
project/
├── CLAUDE.md                    # Instructions chính, ngắn gọn
└── .claude/
    └── rules/
        ├── api-design.md        # Chỉ load khi làm việc với src/api/**
        ├── frontend.md          # Chỉ load khi làm việc với src/frontend/**
        ├── database.md          # Database patterns
        └── security.md          # Auth, secrets, injection prevention
```

**Path-scoped rules** (chỉ load khi làm việc với file phù hợp):
```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Design Rules
- URL paths: kebab-case (/api/v1/user-profiles)
- JSON properties: camelCase
- List endpoints phải có pagination: ?page=1&limit=50
- Version trong path: /v1/, /v2/
```

### Cấu trúc scope theo cấp độ

| Vị trí file | Scope | Git |
|-------------|-------|-----|
| `./CLAUDE.md` | Dự án | Commit — cả team thấy |
| `./CLAUDE.local.md` | Máy bạn | Không commit — chỉ bạn thấy |
| `~/.claude/CLAUDE.md` | Mọi dự án | Không commit — cá nhân |
| `/etc/claude-code/CLAUDE.md` | Toàn tổ chức | IT deploy |

### Import file khác bằng `@path`

```markdown
# Project Overview
@README.md

# Development Scripts
@package.json

# API Design
@docs/api-design.md
```

### Ví dụ CLAUDE.md tối giản nhưng hiệu quả

```markdown
# Build & Test
- `npm test` chạy toàn bộ tests
- `npm run build` build production
- `npm run type-check` kiểm tra TypeScript (phải pass trước khi commit)
- `npm run lint:fix` auto-fix linter

# Code Style
- 2-space indentation
- ES modules (import/export), không dùng CommonJS
- async/await, không dùng .then()

# Architecture
- `/src/api` — HTTP handlers
- `/src/services` — business logic
- `/src/db` — models và migrations
- Để thêm API endpoint: tạo handler → service → test → register route

# Git
- Branch: `feat/`, `fix/`, `chore/`
- Commit: `"type: mô tả ngắn"` (feat:, fix:, chore:...)
- Trước commit: chạy `npm run type-check && npm test`

# Known Gotchas
- UUID field phải có default `uuid()`, không auto-generate
- Transaction lồng nhau > 2 cấp có thể deadlock
```

---

## 11. Hooks System — Tự động hóa hành động

Hooks chạy shell commands tại các **điểm lifecycle cụ thể** — dùng cho những hành động **bắt buộc phải xảy ra mỗi lần, không có ngoại lệ**.

### Các loại Hook Events

| Event | Khi nào kích hoạt | Dùng để |
|-------|------------------|---------|
| `SessionStart` | Khi session bắt đầu hoặc resume | Load env, setup tools |
| `PreToolUse` | Trước khi tool nào đó chạy | Validate, block lệnh nguy hiểm |
| `PostToolUse` | Sau khi tool thành công | Auto-format, log, notify |
| `PostToolUseFailure` | Sau khi tool thất bại | Cleanup, retry |
| `PermissionRequest` | Trước khi hỏi quyền | Auto-approve hoặc escalate |
| `UserPromptSubmit` | Trước khi Claude xử lý prompt | Inject context, validate |
| `Stop` | Khi Claude kết thúc response | Verify tests pass |
| `PreCompact` | Trước khi compact context | Lưu state |
| `PostCompact` | Sau khi compact | Re-inject context quan trọng |
| `Notification` | Khi Claude cần sự chú ý | Desktop/Slack notification |
| `CwdChanged` | Khi thư mục làm việc thay đổi | Reload env vars |
| `FileChanged` | Khi file được watch thay đổi | Rebuild, reload |

### Exit Codes của Hook Script

| Code | Ý nghĩa |
|------|---------|
| `0` | Tiếp tục bình thường |
| `2` | Chặn hành động (viết lý do ra stderr) |
| Khác | Lỗi, hiển thị cho user |

### Ví dụ thực tế

**Auto-format sau khi sửa file:**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

**Chặn sửa file nhạy cảm:**
```bash
#!/bin/bash
# .claude/hooks/protect-files.sh
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

PROTECTED=(".env" "package-lock.json" ".git/" "migrations/")

for pattern in "${PROTECTED[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Bị chặn: $FILE_PATH là file được bảo vệ" >&2
    exit 2
  fi
done
exit 0
```

Đăng ký trong settings.json:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "./.claude/hooks/protect-files.sh" }]
      }
    ]
  }
}
```

**Desktop notification khi Claude cần input:**
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude cần chú ý\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

**Re-inject context sau khi compact:**
```json
{
  "hooks": {
    "PostCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'NHẮC NHỞ QUAN TRỌNG: 1. Dùng Bun, không dùng npm. 2. Chạy test trước khi commit. 3. Author field phải truncate 500 chars.'"
          }
        ]
      }
    ]
  }
}
```

**Reload direnv khi đổi thư mục:**
```json
{
  "hooks": {
    "CwdChanged": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "direnv export bash > \"$CLAUDE_ENV_FILE\""
          }
        ]
      }
    ]
  }
}
```

---

## 12. MCP Servers — Kết nối công cụ bên ngoài

MCP (Model Context Protocol) cho phép Claude dùng tool bên ngoài: GitHub, database, Slack, Sentry, Figma...

### Cài đặt MCP Server phổ biến

```bash
# GitHub — review PR, issues, repos
claude mcp add --transport http github \
  https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer YOUR_GITHUB_PAT"

# PostgreSQL / Database
claude mcp add --transport stdio db \
  -- npx -y @bytebase/dbhub \
  --dsn "postgresql://user:pass@host:5432/db"

# Sentry — error tracking
claude mcp add --transport http sentry \
  https://mcp.sentry.dev/mcp

# Notion
claude mcp add --transport http notion \
  https://mcp.notion.com/mcp

# Slack
claude mcp add --transport http slack \
  https://mcp.slack.com/mcp

# Figma
claude mcp add --transport http figma \
  https://mcp.figma.com/mcp

# Filesystem local
claude mcp add --transport stdio filesystem \
  -- npx -y @modelcontextprotocol/server-filesystem
```

### .mcp.json cho Team (commit vào git)

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_PAT}"
      },
      "alwaysLoad": true
    },
    "database": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub"],
      "env": {
        "DB_DSN": "${DATABASE_URL:-postgresql://localhost/dev}"
      }
    },
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp"
    }
  }
}
```

> Commit file này vào git để toàn team dùng cùng một bộ tools.

### Scope cài đặt MCP

| Scope | Vị trí | Dùng khi |
|-------|--------|---------|
| Local (per-project) | `~/.claude.json` | Credential cá nhân, thử nghiệm |
| Project | `.mcp.json` trong repo | Chia sẻ cho cả team |
| User (global) | `~/.claude.json` global | Dùng trên mọi dự án |

### Defer tools để tiết kiệm context

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "alwaysLoad": true
    }
  }
}
```

`alwaysLoad: true` — luôn load upfront, không defer. Dùng cho servers quan trọng dùng hàng ngày.

---

## 13. Multi-Agent & Subagent Patterns

### Khi nào dùng Subagents vs Agent Teams

| | Subagents | Agent Teams |
|---|-----------|-------------|
| Context | Window riêng | Window riêng |
| Giao tiếp | Báo cáo về main | Chat trực tiếp nhau |
| Tốt cho | Research, verification, task đơn | Phát triển song song, nhiều góc nhìn |
| Chi phí | Thấp (kết quả được tóm tắt) | Cao (mỗi agent là full session) |

### Tạo Subagent bằng file

Tạo `.claude/agents/security-reviewer.md`:

```markdown
---
name: security-reviewer
description: Review code bảo mật, tìm lỗ hổng
tools: Read, Grep, Glob, Bash
model: opus
---

Bạn là senior security engineer đang review code cho production.

Kiểm tra:
1. SQL injection, XSS, command injection
2. Lỗ hổng authentication/authorization
3. Secrets trong code
4. Xử lý dữ liệu không an toàn
5. CORS, CSRF protection
6. Thiếu input validation

Với mỗi vấn đề: đưa line reference, giải thích lỗ hổng, đề xuất fix cụ thể, đánh giá severity.
```

Gọi bằng: *"Dùng subagent review code này về bảo mật"*

### Sử dụng Subagents để bảo vệ main context

```
Implement OAuth flow. Dùng subagent để tìm hiểu cách auth system hiện tại 
handle token refresh — để không làm nhiễu context chính.
```

Subagent đọc code, trả về summary. Context chính vẫn sạch để implement.

### Agent Teams (thử nghiệm)

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude
```

```
Tạo agent team điều tra performance issue từ 3 góc độ:
- Một teammate phân tích database query patterns
- Một teammate profile HTTP handlers  
- Một teammate kiểm tra infrastructure capacity

Mỗi người điều tra độc lập rồi so sánh kết quả.
```

### Parallel Code Review với Agent Team

```
Tạo team 3 reviewers cho PR #456:
- Security reviewer: lỗ hổng, auth, data handling
- Performance reviewer: bottlenecks, queries thừa, memory leaks
- Testing reviewer: test coverage, edge cases, integration tests

Sau đó hội tụ thành danh sách ưu tiên cần fix.
```

---

## 14. Memory System — Bộ nhớ liên session

### CLAUDE.md vs Auto-Memory

| | CLAUDE.md | Auto-Memory |
|---|-----------|-------------|
| Ai viết | Bạn viết thủ công | Claude tự ghi lại |
| Nội dung | Rules, conventions, architecture | Learnings từ corrections của bạn |
| Load | Đầy đủ mỗi session | 200 dòng đầu mỗi session |
| Sync | Git (với team) | Chỉ máy bạn |
| Sau compact | Reload tự động | Reload tự động |

### Cấu trúc Auto-Memory

```
~/.claude/projects/my-project/memory/
├── MEMORY.md              # Index (200 dòng đầu load mỗi session)
├── build-commands.md      # Chi tiết build (load theo nhu cầu)
├── debugging-patterns.md  # Known fixes
├── code-style.md          # Preferences Claude học được
└── api-design.md          # API patterns từ codebase
```

### Enable/Disable Auto-Memory

```json
{
  "autoMemoryEnabled": false
}
```

Hoặc: `/memory` trong session để toggle.

### Khi instructions biến mất sau `/compact`

- CLAUDE.md ở project root → tự reload
- CLAUDE.md trong subdirectory → chỉ reload khi Claude đọc file trong thư mục đó
- Instructions chỉ trong hội thoại → **mất sau compact**

**Giải pháp:** Chuyển instructions quan trọng vào CLAUDE.md ở project root, hoặc dùng PostCompact hook để re-inject.

---

## 15. Workflow Patterns & Automation

### Quy trình 4 bước: Explore → Plan → Implement → Commit

**Bước 1: Khám phá (Plan Mode)**
```
/plan
Đọc /src/auth để hiểu cách handle session và token refresh.
OAuth tokens hiện tại được quản lý như thế nào?
```

**Bước 2: Lập kế hoạch**
```
Tạo implementation plan chi tiết cho việc thêm Google OAuth.
File nào thay đổi? Callback flow ra sao? Bao gồm edge cases.
```

**Bước 3: Implement (Default Mode)**
```
/model default
Implement OAuth flow theo plan đã duyệt.
Viết tests cho callback handler.
Chạy test suite và fix nếu có lỗi.
```

**Bước 4: Commit & PR**
```
Commit với message mô tả và mở PR.
```

### CI/CD với GitHub Actions

```yaml
# .github/workflows/claude-fix.yml
name: Claude Code Fix

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  fix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@main
        with:
          prompt: "Fix failing tests. Đảm bảo tất cả tests pass."
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          allowed-tools: "Edit,Bash(npm test),Bash(npm run lint)"
          permission-mode: "acceptEdits"
```

### Batch Migration tự động

```bash
#!/bin/bash
# migrate-all.sh
FILES=$(find src -name "*.py" -type f)

for file in $FILES; do
  echo "Processing $file..."
  claude -p "Migrate $file từ Python 2 sang Python 3." \
    --allowed-tools "Edit,Bash(python -m py_compile)" \
    --permission-mode auto \
    --output-format json | jq -r '.status'
done
```

### Headless/Scripted Mode

```bash
# Phân tích một lần
claude -p "Phân tích auth system về lỗ hổng bảo mật"

# Output JSON cho scripts
claude -p "Liệt kê tất cả API endpoints" --output-format json | jq '.'

# Streaming real-time
claude -p "Xử lý log file này" --output-format stream-json | \
  while IFS= read -r line; do echo "Processing: $line"; done
```

### Làm việc song song với Worktrees

```bash
# Terminal 1: implement feature chính
claude

# Terminal 2: review/test song song
git worktree add /tmp/review-branch
cd /tmp/review-branch
claude
```

---

## 16. Tối ưu hiệu suất & chi phí

### Context Window là bottleneck chính

| Nguồn tiêu tốn context | Cách giảm |
|------------------------|-----------|
| CLAUDE.md quá dài | Giữ dưới 200 dòng, dùng path-scoped rules |
| Hội thoại dài | `/clear` giữa các task không liên quan |
| File lớn được đọc | Chỉ đọc phần cần thiết |
| MCP output lớn | Đặt `MAX_MCP_OUTPUT_TOKENS` |
| Exploration | Dùng subagent thay vì main context |

### Chọn Model theo loại task

| Task | Model | Lý do |
|------|-------|-------|
| Research, hỏi đáp nhanh | Haiku | Nhanh, rẻ |
| Implementation thông thường | Sonnet (default) | Cân bằng tốt |
| Kiến trúc phức tạp, debug khó | Opus | Reasoning tốt nhất |
| Security review subagent | Opus | Cần phân tích sâu |
| Code formatting subagent | Haiku | Task đơn giản |

### Cấu trúc session hiệu quả

```
Session 1: Explore & Plan (rẻ, dùng fast mode)
→ Đọc code, đặt câu hỏi, tạo spec
→ /clear giữa các exploration riêng biệt

Session 2: Implement (có thể tốn hơn)
→ Context sạch, spec rõ ràng
→ Focus vào implementation

Session 3: Review & Refine (subagent)
→ Subagent review kết quả session 2
→ Objective hơn vì fresh context
```

### Giới hạn MCP output

```json
{
  "env": {
    "MAX_MCP_OUTPUT_TOKENS": "50000"
  }
}
```

---

## 17. Bảo mật & Hardening

### Deny list cơ bản (nên có trong mọi dự án)

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push *)",
      "Read(.env*)",
      "Read(./secrets/**)",
      "Read(~/.ssh/**)",
      "Read(~/.aws/credentials)",
      "Edit(.git/**)",
      "Edit(package-lock.json)",
      "Edit(migrations/**)"
    ]
  }
}
```

### .claudeignore — Ngăn Claude đọc file nhạy cảm

Tạo `.claudeignore` ở project root:
```
node_modules/
.env*
secrets/
.aws/
.git/
dist/
build/
coverage/
*.log
.terraform/
*.pem
*.key
```

### Xử lý API Keys an toàn

**Không bao giờ:**
- Paste secret vào prompt
- Để Claude đọc file `.env`
- Log API key ra stdout

**Thay vào đó — dùng `apiKeyHelper`:**
```json
{
  "apiKeyHelper": "/opt/bin/get-api-key.sh"
}
```

```bash
#!/bin/bash
# Script fetch token động từ secret manager
TOKEN=$(aws secretsmanager get-secret-value --secret-id claude-api-key \
  --query SecretString --output text)
echo "$TOKEN"
```

### Sandbox OS-level

```json
{
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "autoAllowBashIfSandboxed": true,
    "filesystem": {
      "denyRead": ["~/.aws", "~/.ssh", "/etc/shadow"],
      "denyWrite": ["/etc", "/usr/local/bin", ".git"]
    },
    "network": {
      "deniedDomains": ["*.internal.company.com"],
      "allowedDomains": ["github.com", "npmjs.org"]
    }
  }
}
```

---

## 18. Setup cho Team & Enterprise

### Cấu trúc thư mục chuẩn cho team

```
project-root/
├── CLAUDE.md                    # Instructions chính
├── .claudeignore                # File bị loại trừ
├── .mcp.json                    # MCP servers cho team (commit)
├── .claude/
│   ├── settings.json            # Permissions, hooks cho team (commit)
│   ├── settings.local.json      # Cá nhân (gitignore)
│   ├── rules/
│   │   ├── api-design.md
│   │   ├── frontend.md
│   │   ├── database.md
│   │   └── security.md
│   ├── agents/
│   │   ├── security-reviewer.md
│   │   └── test-runner.md
│   └── skills/
│       ├── fix-issue/SKILL.md
│       └── new-feature/SKILL.md
└── .gitignore                   # (bao gồm CLAUDE.local.md, settings.local.json)
```

### Managed Settings cho Enterprise

Deploy qua configuration management (Ansible, Chef):

```bash
# macOS
sudo cp managed-settings.json \
  "/Library/Application Support/ClaudeCode/settings.json"

# Linux
sudo cp managed-settings.json /etc/claude-code/settings.json

# Windows PowerShell
Copy-Item managed-settings.json "C:\Program Files\ClaudeCode\settings.json"
```

```json
{
  "allowManagedPermissionRulesOnly": true,
  "disableBypassPermissionsMode": "disable",
  "allowManagedMcpServersOnly": true,
  "permissions": {
    "deny": ["Bash(curl *)", "Read(.env*)"]
  }
}
```

### Loại trừ CLAUDE.md không liên quan trong monorepo

```json
{
  "claudeMdExcludes": [
    "*/api-team/CLAUDE.md",
    "*/mobile-team/**/.claude/**",
    "**/experimental/**"
  ]
}
```

### Onboarding checklist member mới

```
1. Cài Claude Code: npm install -g @anthropic-ai/sdk
2. Chạy /init để generate CLAUDE.md starter
3. Đọc CLAUDE.md và .claude/rules/
4. Copy settings: cp .claude/settings.json ~/.claude/settings.json
5. Authenticate MCP với /mcp
6. Test: "Chạy test suite và cho tôi xem kết quả"
7. Test: "Tạo một API endpoint mới theo quy trình của project"
```

---

## 19. Config Templates đầy đủ

### settings.json đầy đủ cho team

```json
{
  "model": "claude-sonnet-4-6",
  "effortLevel": "medium",
  "autoMemoryEnabled": true,

  "permissions": {
    "defaultMode": "acceptEdits",

    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)",
      "Bash(curl *)",
      "Bash(git push *)",
      "Read(.env*)",
      "Read(./secrets/**)",
      "Edit(.git/**)",
      "Edit(package-lock.json)"
    ],

    "ask": [
      "Bash(docker *)",
      "Edit(src/auth/**)",
      "Edit(package.json)"
    ],

    "allow": [
      "Bash(npm run *)",
      "Bash(npm test)",
      "Bash(git commit *)",
      "Bash(git add *)",
      "Bash(git status)",
      "Bash(git log *)",
      "Read(src/**)",
      "Read(docs/**)",
      "WebFetch(domain:github.com)"
    ]
  },

  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write 2>/dev/null || true"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Cần chú ý' 2>/dev/null || true"
          }
        ]
      }
    ]
  },

  "sandbox": {
    "enabled": true
  }
}
```

### .mcp.json đầy đủ cho team

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_PAT}"
      },
      "alwaysLoad": true
    },
    "database": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub"],
      "env": {
        "DB_DSN": "${DATABASE_URL:-postgresql://localhost/dev}"
      }
    },
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp"
    }
  }
}
```

---

## Luồng làm việc tổng hợp

### Phát triển tính năng mới

```
1. /openspec-propose     → Mô tả tính năng, Claude tạo design + tasks
2. /plan                 → Đọc code liên quan, không sửa gì
3. /openspec-apply-change → Thực thi code từng task
4. /openspec-verify-change → Kiểm tra implementation
5. /openspec-archive-change → Lưu trữ, đóng change
```

### Debug nhanh

```
1. ! docker-compose logs backend    (xem logs)
2. Mô tả lỗi cho Claude
3. Claude đọc code, đề xuất fix
4. Shift+Tab → acceptEdits          (sửa file tự động)
```

### Review code trước khi merge

```
1. /review                          (review local)
   hoặc
   /ultrareview <PR-number>         (deep review trên cloud)
```

### Khi context đầy

```
1. /compact                         (tóm tắt để tiết kiệm context)
   hoặc
2. /clear + bắt đầu session mới     (nếu task đã xong)
```

---

## 10 nguyên tắc vàng khi dùng Claude Code

1. **CLAUDE.md là hợp đồng** — Giữ dưới 200 dòng, cập nhật khi Claude mắc lỗi 2 lần.
2. **Hooks thực thi chính sách** — Dùng cho hành động bắt buộc phải xảy ra (format, chặn file nguy hiểm).
3. **Subagents bảo vệ context** — Delegate exploration/research để context chính sạch.
4. **MCP nhân giá trị lên nhiều lần** — Kết nối GitHub, DB, Sentry để Claude hành động trên dữ liệu thực.
5. **Permissions & sandbox = tin tưởng** — Đặt ranh giới hợp lý để dùng auto mode thoải mái.
6. **Context là bottleneck** — `/clear` aggressively giữa các task không liên quan.
7. **Plan mode tách exploration khỏi implementation** — Đọc, hỏi, lập kế hoạch trước; code sau.
8. **Chọn model theo task** — Haiku cho research, Sonnet cho implementation, Opus cho kiến trúc phức tạp.
9. **Auto-memory tích lũy theo thời gian** — Để Claude học về codebase, build system, debugging patterns của bạn.
10. **Settings có thứ tự ưu tiên** — Managed > Local > Project > User > Default.

---

*Cập nhật lần cuối: 2026-05-07 | Nguồn: Claude Code official documentation*
