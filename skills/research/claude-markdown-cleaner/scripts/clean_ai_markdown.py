#!/usr/bin/env python3
"""Audit and scrub Claude/LLM Markdown traces and AI writing patterns (MASTER PROMPT v5.4.1)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VI_CLICHES = [
    "trong bối cảnh hiện nay",
    "trong kỷ nguyên số",
    "trong thời đại công nghệ phát triển mạnh mẽ",
    "không thể phủ nhận rằng",
    "có thể thấy rằng",
    "điều này cho thấy rằng",
    "đóng vai trò vô cùng quan trọng",
    "là minh chứng rõ nét",
    "đánh dấu bước ngoặt",
    "mở ra kỷ nguyên mới",
    "có ý nghĩa chiến lược đặc biệt",
    "khẳng định vai trò tiên phong",
    "khẳng định vị thế",
    "tạo nền tảng vững chắc",
    "phát huy tối đa tiềm năng",
    "nâng tầm chất lượng",
    "thúc đẩy mạnh mẽ",
    "mang tính cách mạng",
]

EN_CLICHES = [
    "in today's rapidly changing world",
    "in today’s rapidly changing world",
    "it is important to note that",
    "it is widely acknowledged that",
    "delve into",
    "tapestry",
    "multifaceted",
    "pivotal",
    "transformative",
    "seamless",
    "groundbreaking",
    "paramount",
    "underscores",
    "testament to",
]

CHATBOT_OPENERS = [
    r"^(?:Chắc chắn rồi|Tuyệt vời|Câu hỏi rất hay|Bạn hoàn toàn đúng|Đây là một chủ đề rất thú vị|Dưới đây là bản thảo|Dưới đây là nội dung)[^\n]*\n+",
    r"^(?:Certainly!|Great question!|Absolutely!|Sure!|Here is the revised|Here's the)[^\n]*\n+",
]

CHATBOT_CLOSERS = [
    r"\n+(?:Hy vọng thông tin trên hữu ích|Nếu bạn cần thêm hỗ trợ|Nếu cần chỉnh sửa thêm|Hãy cho tôi biết nếu)[^\n]*\s*$",
    r"\n+(?:I hope this helps|Feel free to ask|Let me know if you need any further)[^\n]*\s*$",
]

# Rule 48: Bold-colon bullet `- **Label:** content` or `1. **Label**: content`
BOLD_COLON_BULLET_RE = re.compile(r"^(\s*(?:[-*•]|\d+\.)\s+)\*\*([^*\n]{2,80}?)\*\*\s*:\s+", re.MULTILINE)
BOLD_INSIDE_COLON_BULLET_RE = re.compile(r"^(\s*(?:[-*•]|\d+\.)\s+)\*\*([^*\n]{2,80}?):\*\*\s+", re.MULTILINE)

# Rule 47: Simple LaTeX numbers/units in prose like $10\%$, $100^\circ\text{C}$, $12,5\%$
SIMPLE_LATEX_UNIT_RE = re.compile(
    r"\$(\d+(?:[.,]\d+)?)\s*(?:\\%|%|\\^\{\\circ\}\s*\\text\{([CF])\}|\\^\circ\s*([CF])|\\text\{([a-zA-Z%°/]+)\})\$"
)


def audit_text(text: str) -> list[str]:
    findings: list[str] = []
    lower = text.lower()
    for phrase in VI_CLICHES:
        if phrase in lower:
            findings.append(f"[VI Cliché - Rule 5/7/8] Found '{phrase}'")
    for phrase in EN_CLICHES:
        if re.search(rf"\b{re.escape(phrase)}\b", lower):
            findings.append(f"[EN Cliché - Rule 5/7] Found '{phrase}'")
    bold_bullets = len(BOLD_COLON_BULLET_RE.findall(text)) + len(BOLD_INSIDE_COLON_BULLET_RE.findall(text))
    if bold_bullets:
        findings.append(f"[Claude Markdown Trace - Rule 48] {bold_bullets} bullet line(s) with '- **Bold Label:**' pattern")
    em_dashes = text.count("—")
    if em_dashes > 2:
        findings.append(f"[Typography - Rule 47] {em_dashes} em-dashes ('—') found; verify if commas/colons/parentheses are more natural")
    passive_calques = len(re.findall(r"\bđược\s+\w+\s+bởi\b", lower))
    if passive_calques:
        findings.append(f"[VI Passive Calque - Rule 39] {passive_calques} occurrence(s) of 'được ... bởi'")
    mot_cach = len(re.findall(r"\bmột cách\s+\w+", lower))
    if mot_cach > 1:
        findings.append(f"[VI Calque - Rule 39] {mot_cach} occurrence(s) of 'một cách + adj'")
    return findings


def clean_markdown(text: str, *, strip_markdown: bool = False) -> str:
    out = text
    # 1. Strip chatbot openers and closers (Rule 41)
    for pat in CHATBOT_OPENERS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    for pat in CHATBOT_CLOSERS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)

    # 2. Clean simple LaTeX numbers/units in prose (Rule 47)
    def _latex_repl(m: re.Match) -> str:
        num = m.group(1)
        deg = m.group(2) or m.group(3)
        unit = m.group(4)
        if deg:
            return f"{num}°{deg}"
        if unit:
            return f"{num} {unit}"
        return f"{num}%"

    out = SIMPLE_LATEX_UNIT_RE.sub(_latex_repl, out)
    out = re.sub(r"\$(\d+(?:[.,]\d+)?)\\%\$", r"\1%", out)

    # 3. Remove bold-colon mechanical list formatting (Rule 48)
    out = BOLD_COLON_BULLET_RE.sub(r"\1\2: ", out)
    out = BOLD_INSIDE_COLON_BULLET_RE.sub(r"\1\2: ", out)

    # 4. Normalize numeric/year ranges with em-dash to en-dash (Rule 47)
    out = re.sub(r"(\b\d{4})\s*—\s*(\d{4}\b)", r"\1–\2", out)

    if strip_markdown:
        # Remove headings ###, bold **, italic *, inline code `, blockquotes >
        out = re.sub(r"^#{1,6}\s+", "", out, flags=re.MULTILINE)
        out = re.sub(r"\*\*([^*\n]+)\*\*", r"\1", out)
        out = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", out)
        out = re.sub(r"`([^`\n]+)`", r"\1", out)
        out = re.sub(r"^>\s?", "", out, flags=re.MULTILINE)
        out = re.sub(r"^-{3,}\s*$", "", out, flags=re.MULTILINE)
        out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", out)

    return out.strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input file path (or '-' for stdin)")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument("--mode", choices=["clean", "detect"], default="clean")
    parser.add_argument("--strip-markdown", action="store_true", help="Strip all raw Markdown syntax to plain prose")
    args = parser.parse_args()

    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    if args.mode == "detect":
        findings = audit_text(raw)
        if not findings:
            print("Clean: no obvious Claude/AI markdown traces or clichés detected.")
            return 0
        for item in findings:
            print(f"- {item}")
        return 0

    cleaned = clean_markdown(raw, strip_markdown=args.strip_markdown)
    if args.output:
        Path(args.output).write_text(cleaned, encoding="utf-8")
        print(f"Saved cleaned output to {args.output}")
    else:
        sys.stdout.write(cleaned)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

