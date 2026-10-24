"""CTS Secret Engine — End-to-End Cognitive, Anti-AI & Anti-Markdown Pipeline.

Implements:
1. Default auto-loading of core CTS research skills (`master-academic-writing`,
   `causal-jepa-world-model`, `avoid-ai-writing`, `claude-markdown-cleaner`).
2. Pre-delivery Self-Critique Stop Gate (`check_cts_quality_stop_gate`): catches
   severe AI clichés, Claude markdown patterns, and passive calques before turn end
   and nudges the model once to self-refine using Causal JEPA & MASTER PROMPT v5.4.1.
3. Deterministic Post-Processing Output Guard (`sanitize_cts_response`): scrubs
   residual Claude/AI Markdown traces (chatbot pleasantries, bold-colon bullet
   syndrome, raw LaTeX on simple numbers/units, em-dash numeric ranges, opening
   filler clichés) outside fenced code blocks before final delivery.
"""
from __future__ import annotations

import os
import re
from typing import Any, Optional

DEFAULT_CTS_AUTO_LOAD_SKILLS: tuple[str, ...] = (
    "master-academic-writing",
    "causal-jepa-world-model",
    "avoid-ai-writing",
    "claude-markdown-cleaner",
)

_FENCED_CODE_RE = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)", re.MULTILINE)

# Rule 41: Chatbot opening/closing pleasantries
_CHATBOT_OPENERS_RE = re.compile(
    r"\A\s*(?:"
    r"(?:Chắc chắn rồi|Tuyệt vời|Câu hỏi (?:rất )?hay|Bạn hoàn toàn đúng|Đây là một (?:chủ đề|vấn đề) (?:rất |vô cùng )?thú vị|"
    r"Dưới đây là (?:bản thảo|nội dung|phân tích|câu trả lời))[^\n]*\n+"
    r"|"
    r"(?:Certainly|Great question|Absolutely|Sure thing|I'd be happy to help|Here is the (?:revised|requested|detailed))[^\n]*\n+"
    r")+",
    re.IGNORECASE,
)

_CHATBOT_CLOSERS_RE = re.compile(
    r"\n+\s*(?:"
    r"(?:Hy vọng (?:rằng )?(?:những )?thông tin trên(?: sẽ)? hữu ích|Nếu (?:bạn )?cần (?:thêm )?hỗ trợ|Hãy cho tôi biết nếu bạn cần)[^\n]*$"
    r"|"
    r"(?:I hope this (?:information )?helps|Feel free to (?:ask|let me know)|Let me know if you need any (?:further|additional))[^\n]*$"
    r")\s*\Z",
    re.IGNORECASE,
)

# Rule 5: Formulaic opening clichés at the start of paragraphs
_VI_OPENING_CLICHE_STRIP_RE = re.compile(
    r"(^|\n\n)(?:Trong bối cảnh hiện nay,\s*khi mà\s*|Trong kỷ nguyên số hiện nay,\s*|Không thể phủ nhận rằng,?\s*|Có thể thấy rằng,?\s*)",
    re.IGNORECASE,
)

# Rule 47: Raw LaTeX on simple numbers/percentages/temperatures in prose
_SIMPLE_LATEX_UNIT_RE = re.compile(
    r"\$(\d+(?:[.,]\d+)?)\s*(?:\\%|%|\^\{\\circ\}\s*\\text\{([CF])\}|\^\\circ\s*\\text\{([CF])\}|\^\\circ\s*([CF])|\\text\{([a-zA-Z%°/]+)\})\$"
)
_SIMPLE_LATEX_PCT_RE = re.compile(r"\$(\d+(?:[.,]\d+)?)\\%\$")

# Rule 48: Claude's mechanical bold-colon bullet pattern `- **Label:** content`
_BOLD_COLON_BULLET_RE = re.compile(
    r"^(\s*(?:[-*•]|\d+\.)\s+)\*\*([^*\n]{2,70}?)\*\*\s*:\s+",
    re.MULTILINE,
)
_BOLD_INSIDE_COLON_BULLET_RE = re.compile(
    r"^(\s*(?:[-*•]|\d+\.)\s+)\*\*([^*\n]{2,70}?):\*\*\s+",
    re.MULTILINE,
)

# Severe AI clichés that trigger the internal self-refinement stop gate
_SEVERE_VI_CLICHES: tuple[str, ...] = (
    "trong bối cảnh hiện nay",
    "trong kỷ nguyên số",
    "trong thời đại công nghệ phát triển mạnh mẽ",
    "không thể phủ nhận rằng",
    "đóng vai trò vô cùng quan trọng",
    "là minh chứng rõ nét",
    "đánh dấu bước ngoặt",
    "mở ra kỷ nguyên mới",
    "khẳng định vị thế",
    "phát huy tối đa tiềm năng",
    "mặc dù còn nhiều thách thức, tương lai vẫn đầy hứa hẹn",
)

_SEVERE_EN_CLICHES: tuple[str, ...] = (
    "in today's rapidly changing world",
    "in today’s rapidly changing world",
    "it is important to note that",
    "it is widely acknowledged that",
    "delve into",
    "rich tapestry",
    "testament to",
)


def _strip_fenced_code(text: str) -> str:
    return _FENCED_CODE_RE.sub("", text)


def detect_cts_quality_violations(text: str) -> list[str]:
    """Audit candidate response text (outside code blocks) for severe AI-isms or Claude markdown traces."""
    if not text or len(text.strip()) < 160:
        return []
    prose = _strip_fenced_code(text)
    lower = prose.lower()
    violations: list[str] = []

    for phrase in _SEVERE_VI_CLICHES:
        if phrase in lower:
            violations.append(f"Sử dụng sáo ngữ AI tiếng Việt: '{phrase}' (vi phạm Quy tắc 5/7/8/46 MASTER PROMPT v5.4.1)")
    for phrase in _SEVERE_EN_CLICHES:
        if phrase in lower:
            violations.append(f"Sử dụng sáo ngữ AI tiếng Anh: '{phrase}' (vi phạm Quy tắc 5/7 MASTER PROMPT v5.4.1 & avoid-ai-writing)")

    bold_bullets = len(_BOLD_COLON_BULLET_RE.findall(prose)) + len(_BOLD_INSIDE_COLON_BULLET_RE.findall(prose))
    if bold_bullets >= 4:
        violations.append(
            f"Lạm dụng liệt kê mở dòng bằng nhãn in đậm và dấu hai chấm ('- **Nhãn:** ...' xuất hiện {bold_bullets} lần — vi phạm Quy tắc 48 MASTER PROMPT v5.4.1)"
        )

    passive_calques = len(re.findall(r"\bđược\s+\w+\s+bởi\b", lower))
    if passive_calques >= 3:
        violations.append(
            f"Lạm dụng cấu trúc bị động dịch phỏng tiếng Anh 'được ... bởi' ({passive_calques} lần — vi phạm Quy tắc 39 MASTER PROMPT v5.4.1)"
        )

    not_only_vi = len(re.findall(r"không chỉ\s+[^.\n]{3,80}\s+mà còn", lower))
    if not_only_vi >= 2:
        violations.append(
            f"Lặp cấu trúc phủ định song song 'không chỉ ... mà còn' ({not_only_vi} lần — vi phạm Quy tắc 10 MASTER PROMPT v5.4.1)"
        )

    return violations


def check_cts_quality_stop_gate(agent: Any, final_response: Any) -> Optional[str]:
    """Return a synthetic self-refinement nudge if the candidate response violates core CTS quality rules."""
    if os.environ.get("CTS_QUALITY_GATE", "1").strip().lower() in ("0", "false", "off", "no"):
        return None
    if not isinstance(final_response, str) or not final_response.strip():
        return None
    if getattr(agent, "_cts_quality_nudges", 0) >= 1:
        return None
    # Do not re-generate if the response was already live-streamed to the terminal unless forced
    if (
        os.environ.get("CTS_FORCE_QUALITY_GATE", "").strip() != "1"
        and hasattr(agent, "_interim_content_was_streamed")
        and agent._interim_content_was_streamed(final_response)
    ):
        return None

    violations = detect_cts_quality_violations(final_response)
    if not violations:
        return None

    bullet_list = "\n".join(f"- {v}" for v in violations)
    return (
        "[CTS Internal Quality Gate — MASTER PROMPT v5.4.1 & Avoid-AI-Writing Self-Refinement]\n"
        "Bản nháp vừa tạo của bạn vi phạm các tiêu chuẩn chống văn phong AI / chống dấu vết Markdown của Claude:\n"
        f"{bullet_list}\n\n"
        "Hãy viết lại bản trả lời cuối cùng ngay bây giờ sao cho:\n"
        "1. Loại bỏ triệt để các sáo ngữ, lời xã giao, cấu trúc 'không chỉ... mà còn...', bị động dịch phỏng 'được... bởi' và kiểu liệt kê '- **Nhãn in đậm:**'.\n"
        "2. Ưu tiên văn xuôi phân tích có chiều sâu cơ chế, nhân quả (Causal JEPA: tác động ngắn hạn t+1, phản hồi trung hạn t+2, cân bằng dài hạn t+H) và giữ nguyên 100% độ chính xác của dữ kiện/số liệu.\n"
        "3. Trả về trực tiếp bản hoàn chỉnh cuối cùng, tuyệt đối không nhắc lại thông báo nội bộ này."
    )


def _sanitize_prose_segment(segment: str) -> str:
    out = segment
    # 1. Clean simple LaTeX numbers/units in prose ($10\%$, $100^\circ\text{C}$) -> 10%, 100°C (Rule 47)
    def _latex_repl(m: re.Match) -> str:
        num = m.group(1)
        deg = m.group(2) or m.group(3) or m.group(4)
        unit = m.group(5)
        if deg:
            return f"{num}°{deg}"
        if unit:
            return f"{num} {unit}"
        return f"{num}%"

    out = _SIMPLE_LATEX_UNIT_RE.sub(_latex_repl, out)
    out = _SIMPLE_LATEX_PCT_RE.sub(r"\1%", out)

    # 2. Remove mechanical bold-colon bullet formatting when 3+ occur in the segment (Rule 48)
    bold_count = len(_BOLD_COLON_BULLET_RE.findall(out)) + len(_BOLD_INSIDE_COLON_BULLET_RE.findall(out))
    if bold_count >= 3:
        out = _BOLD_COLON_BULLET_RE.sub(r"\1\2: ", out)
        out = _BOLD_INSIDE_COLON_BULLET_RE.sub(r"\1\2: ", out)

    # 3. Normalize year/numeric ranges with em-dash to en-dash (Rule 47)
    out = re.sub(r"(\b\d{4})\s*—\s*(\d{4}\b)", r"\1–\2", out)
    return out


def sanitize_cts_response(text: str) -> str:
    """Deterministically scrub residual Claude/AI markdown traces and chatbot filler outside code blocks."""
    if not isinstance(text, str) or not text.strip():
        return text
    if os.environ.get("CTS_OUTPUT_SANITIZER", "1").strip().lower() in ("0", "false", "off", "no"):
        return text

    # Strip chatbot opening and closing pleasantries on the whole response (if not starting/ending with code)
    cleaned = _CHATBOT_OPENERS_RE.sub("", text)
    cleaned = _CHATBOT_CLOSERS_RE.sub("", cleaned)

    # Split by fenced code blocks so code is 100% untouched
    parts = _FENCED_CODE_RE.split(cleaned)
    out_parts: list[str] = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            # Fenced code block: preserve verbatim
            out_parts.append(part)
        else:
            out_parts.append(_sanitize_prose_segment(part))

    return "".join(out_parts)
