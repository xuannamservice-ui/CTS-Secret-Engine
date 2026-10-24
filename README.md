<p align="center">
  <img src="assets/banner.png" alt="CTS Secret Engine — Creative Technologies and Simulation" width="100%">
</p>

<h1 align="center">CTS Secret Engine [CTS]</h1>
<p align="center">
  <b>Creative Technologies and Simulation — Autonomous AI Engineering, Simulation & Multi-Platform Agent</b>
</p>

<p align="center">
  <a href="#-english-documentation"><img src="https://img.shields.io/badge/Language-English-0A66C2?style=for-the-badge" alt="English"></a>
  <a href="#-tài-liệu-tiếng-việt"><img src="https://img.shields.io/badge/Ngôn_ngữ-Tiếng_Việt-DA251D?style=for-the-badge" alt="Tiếng Việt"></a>
  <a href="README.vi.md"><img src="https://img.shields.io/badge/Bản_độc_lập-README.vi.md-FFD700?style=for-the-badge" alt="README.vi.md"></a>
  <a href="https://github.com/xuannamservice-ui/CTS-Secret-Engine/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-2ea44f?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/xuannamservice-ui/CTS-Secret-Engine"><img src="https://img.shields.io/badge/Built_by-CTS_(Creative_Technologies_&_Simulation)-8A2BE2?style=for-the-badge" alt="Built by CTS"></a>
</p>

---

# 🌐 English Documentation

**CTS Secret Engine** is an autonomous, self-evolving AI engineering and simulation system built by **Creative Technologies and Simulation (CTS)**. Designed with a continuous learning loop, CTS Secret Engine synthesizes reusable skills from real-world execution, persists long-term cross-session memory, orchestrates subagents, and operates seamlessly across Terminal (CLI & TUI), Web Dashboard, Desktop, and Messaging Gateways.

### ✨ Key Capabilities

| Capability | Description |
| :--- | :--- |
| **Interactive Terminal (CLI & TUI)** | Full terminal user interface (`cts --tui` & `cts`) with multiline editing, slash-command autocomplete, streaming tool execution, and real-time status telemetry. |
| **Creative Technologies & Simulation** | Specialized system identity (`SOUL.md`) and bundled skills (`cts-simulation-architect` + 68 built-in skills) for mathematical modeling, simulation architectures, and full-stack software engineering. |
| **Human-Native Academic Writing & Anti-AI Suite (`MASTER PROMPT v5.4.1`)** | Built-in **MASTER PROMPT v5.4.1 (79 Rules)**, **Avoid AI Writing** (`conorbronsdon/avoid-ai-writing`), **Claude Markdown Trace Cleaner**, and **Nghị định 30/2020/NĐ-CP Word/DOCX Exporter** for native Vietnamese & English research papers, grant proposals, and policy documents. |
| **Self-Evolving Memory & Skills** | Automatically creates, refines, and curates procedural skills in `~/.cts/skills/` (or `~/.hermes/skills/`) and searches past conversations via FTS5 full-text indexing. |
| **Model & Provider Agnostic** | Connect effortlessly to OpenRouter, OpenAI, Anthropic Claude, Google Gemini, xAI Grok, local vLLM/Ollama endpoints, or custom OpenAI-compatible servers via `cts model`. |
| **Multi-Platform Gateway** | Operate a single unified gateway (`cts gateway`) across Telegram, Discord, Slack, Microsoft Teams, Google Chat, WhatsApp, Signal, Matrix, and Webhooks. |
| **Sandboxed Execution** | Execute code and shell operations across local environments, Docker containers, SSH remotes, Modal, Singularity, or Daytona workspaces. |

### 🚀 Quick Start (English)

#### 1. Clone & Install
```bash
git clone https://github.com/xuannamservice-ui/CTS-Secret-Engine.git
cd CTS-Secret-Engine
bash scripts/install.sh --dir "$(pwd)"
```

#### 2. Essential CTS CLI Commands
```bash
cts                        # Launch interactive CTS Secret Engine session
cts --tui                  # Launch modern full-screen CTS Terminal UI
cts chat -q "Hello CTS"    # Run a single query in one-shot mode
cts setup                  # Run the interactive CTS configuration wizard
cts model                  # Select default AI provider and model
cts tools                  # Configure enabled toolsets and integrations
cts web                    # Launch the CTS Web Dashboard (http://127.0.0.1:9119)
cts gateway status         # Check multi-platform messaging gateway status
cts skills list            # List all installed and bundled CTS skills
cts doctor                 # Run system diagnostics and health checks
cts --version              # Display CTS Secret Engine version info
cts --help                 # View full CTS CLI command reference
```

#### 3. Architecture & Directory Structure
- `agent/` — Core reasoning engine, prompt builder, context compressor, and auxiliary model router.
- `hermes_cli/` — CTS CLI command suite, ASCII `CTS` banner, skin engine, and Web UI server.
- `ui-tui/` — React/Ink full-screen Terminal User Interface with `CTS` emblem and gold/bronze theme.
- `web/` — React/Vite Web Dashboard for visual session management, configuration, and analytics.
- `apps/desktop/` — Tauri native desktop application with `CTS` system tray and app icons.
- `gateway/` — Multi-platform messaging gateway (Telegram, Discord, Slack, Teams, Google Chat, WhatsApp, Matrix).
- `skills/` — Bundled procedural skills including `creative/cts-simulation-architect`.
- `assets/` — Master vector (`CTS` emblem SVG) and raster icon assets across all platforms.

---

# 🇻🇳 Tài liệu Tiếng Việt

**CTS Secret Engine** là hệ thống AI tự hành chuyên sâu về công nghệ sáng tạo, kỹ thuật phần mềm và mô phỏng hệ thống, được phát triển bởi **Creative Technologies and Simulation (CTS)**. Hệ thống sở hữu vòng lặp tự học liên tục: tự động đúc kết kỹ năng (Skills) từ quá trình giải quyết vấn đề thực tế, ghi nhớ ngữ cảnh dài hạn xuyên suốt nhiều phiên làm việc, điều phối đa tác tử (Subagents) và vận hành đồng bộ trên Terminal (CLI & TUI), Web Dashboard, Desktop App và các nền tảng nhắn tin.

### ✨ Điểm nổi bật của CTS Secret Engine

| Tính năng | Mô tả chi tiết |
| :--- | :--- |
| **Giao diện Terminal & TUI mang nhận diện `[CTS]`** | Hỗ trợ cả giao diện dòng lệnh cổ điển (`cts`) và giao diện TUI hiện đại (`cts --tui`) với biểu tượng chữ **CTS**, soạn thảo đa dòng, gợi ý lệnh `/help` và hiển thị tiến trình công cụ theo thời gian thực. |
| **Chuyên biệt cho Công nghệ Sáng tạo & Mô phỏng** | Tích hợp nhân cách cốt lõi [`SOUL.md`](SOUL.md) và kỹ năng chuyên dụng `cts-simulation-architect` cùng 68 bộ kỹ năng dựng sẵn cho mô hình hóa toán học, thuật toán tối ưu hóa, kiến trúc hệ thống và phát triển phần mềm toàn diện. |
| **Chuẩn Viết Học thuật Bản địa & Chống Văn phong AI (`MASTER PROMPT v5.4.1`)** | Nhúng trực tiếp **MASTER PROMPT v5.4.1 (13 Phần / 79 Quy tắc)** vào lõi hệ thống kèm bộ kỹ năng `master-academic-writing`, `avoid-ai-writing` (`conorbronsdon/avoid-ai-writing`), và `claude-markdown-cleaner` (xóa dấu vết Markdown của Claude, chuẩn hóa tiếng Việt/Anh học thuật và xuất file Word `.docx` chuẩn Nghị định 30/2020/NĐ-CP). |
| **Bộ nhớ dài hạn & Tự tiến hóa kỹ năng** | Tự động tạo mới, cải tiến và quản lý các kỹ năng trong `~/.cts` (`CTS_HOME`), đồng thời tìm kiếm lại lịch sử hội thoại bằng chỉ mục toàn văn FTS5 tốc độ cao. |
| **Đa mô hình, không phụ thuộc nhà cung cấp** | Chuyển đổi linh hoạt giữa OpenAI, Anthropic Claude, Google Gemini, OpenRouter, xAI, hoặc mô hình nội bộ (Ollama / vLLM / Custom Endpoint) chỉ bằng lệnh `cts model`. |
| **Cổng kết nối đa nền tảng (CTS Gateway)** | Kết nối trực tiếp Agent với Telegram, Discord, Slack, Microsoft Teams, Google Chat, WhatsApp, Signal, Matrix và Email thông qua một tiến trình `cts gateway` duy nhất. |
| **Khởi động mượt mà, không cảnh báo rác** | Đã tối ưu hóa toàn bộ luồng nạp toolset (`teams`, `google_chat`) và cơ chế kiểm tra ngầm giúp CLI khởi chạy tức thì, sạch sẽ và ổn định. |

### 🚀 Hướng dẫn cài đặt & Sử dụng nhanh (Tiếng Việt)

#### 1. Tải mã nguồn & Cài đặt
```bash
git clone https://github.com/xuannamservice-ui/CTS-Secret-Engine.git
cd CTS-Secret-Engine
bash scripts/install.sh --dir "$(pwd)"
```

#### 2. Các câu lệnh `cts` (CTS CLI) thông dụng
```bash
cts                        # Khởi động phiên trò chuyện tương tác với CTS Secret Engine
cts --tui                  # Mở giao diện CTS TUI toàn màn hình hiện đại
cts chat -q "Xin chào CTS" # Chạy truy vấn nhanh một lần (One-shot mode)
cts setup                  # Mở trình hướng dẫn cài đặt CTS Secret Engine Wizard
cts model                  # Chọn nhà cung cấp AI (Provider) và Model mặc định
cts auth list              # Quản lý danh sách khóa API / thông tin xác thực
cts tools                  # Cấu hình bật/tắt các bộ công cụ (Toolsets)
cts web                    # Khởi chạy giao diện quản trị CTS Web Dashboard (cổng 9119)
cts gateway                # Khởi chạy cổng kết nối đa nền tảng (Telegram, Discord, Slack...)
cts sessions list          # Xem danh sách các phiên làm việc trước đó
cts -c                     # Tiếp tục phiên làm việc gần nhất
cts skills list            # Xem danh sách 59 kỹ năng (Skills) sẵn có của hệ thống
cts doctor                 # Kiểm tra sức khỏe hệ thống và chẩn đoán cấu hình
cts update                 # Cập nhật CTS Secret Engine từ kho lưu trữ chính thức
cts --version              # Kiểm tra phiên bản CTS Secret Engine
cts --help                 # Xem toàn bộ danh mục lệnh của CTS CLI
```

#### 3. Các lệnh nội bộ trong phiên Chat (Slash Commands)
Khi đang ở trong giao diện `cts` hoặc `cts --tui`, bạn có thể gõ trực tiếp:
- `/help` — Hiển thị bảng lệnh `[CTS] Available Commands`
- `/model` — Đổi nhanh mô hình AI ngay trong phiên trò chuyện
- `/skills` — Tìm kiếm và nạp thêm kỹ năng chuyên môn
- `/skin` — Thay đổi giao diện màu sắc (mặc định: *Classic CTS Secret Engine — gold and bronze*)
- `/clear` hoặc `/new` — Làm mới phiên trò chuyện
- `/rollback` — Khôi phục trạng thái tệp tin từ checkpoint

#### 4. Biến môi trường & Thư mục dữ liệu
- Thư mục cấu hình: `~/.cts` (được liên kết đồng bộ với `~/.hermes` để đảm bảo tương thích ngược toàn diện).
- Biến môi trường tùy chỉnh thư mục gốc: `export CTS_HOME=/duong/dan/tuy/chinh`.
- Để tạo lại toàn bộ 99 tệp biểu tượng `CTS` (SVG, PNG, ICO, ICNS) từ file vector gốc:
  ```bash
  ./scripts/run-in-hermes-env python3 scripts/generate_icons.py
  ./scripts/run-in-hermes-env python3 scripts/generate_icons.py --check
  ```

---

## 📄 License / Giấy phép
Released under the [MIT License](LICENSE). Customize, extend, and deploy freely for Creative Technologies and Simulation workflows.
