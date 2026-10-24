---
name: claude-markdown-cleaner
description: "Audit, scrub, and convert AI/Claude Markdown traces into clean human-native academic/professional prose or editable Word (.docx) documents compliant with MASTER PROMPT v5.4.1 and Nghị định 30/2020/NĐ-CP."
---

# Claude & AI Markdown Trace Cleaner + DOCX Exporter

Use this skill whenever the user asks to:
1. Remove Claude/ChatGPT Markdown traces (`**bold**`, `- **Label:**`, `###`, raw `$LaTeX$` on simple numbers/units, excessive em-dashes `—`, chatbot pleasantries).
2. Audit a Vietnamese or English manuscript for AI writing clichés, passive English calques (`được... bởi`, `một cách...`), or formulaic structures.
3. Export a draft or report into a clean, editable Microsoft Word (`.docx`) document following **MASTER PROMPT v5.4.1 (Rule 58)** and **Nghị định 30/2020/NĐ-CP** (A4 Portrait, Times New Roman 13pt, Justified, 1.3x line spacing, Margins: Top/Bottom 2.5cm, Left 3.0cm, Right 2.0cm, real Word Heading styles).

## Bundled Scripts

### 1. Audit & Clean AI / Claude Markdown (`scripts/clean_ai_markdown.py`)
```bash
# Detect AI clichés, Claude markdown patterns, and passive calques (Audit mode):
python3 skills/research/claude-markdown-cleaner/scripts/clean_ai_markdown.py input.md --mode detect

# Clean Claude Markdown traces (bold-colon lists, raw TeX units, em-dashes, chatbot filler) while keeping clean Markdown structure:
python3 skills/research/claude-markdown-cleaner/scripts/clean_ai_markdown.py input.md -o cleaned.md

# Strip all raw Markdown formatting into clean, ready-to-paste human prose:
python3 skills/research/claude-markdown-cleaner/scripts/clean_ai_markdown.py input.md --strip-markdown -o prose.txt
```

### 2. Convert to Standard Editable Word `.docx` (`scripts/md_to_docx_nd30.py`)
```bash
# Generate a standard A4 Times New Roman 13pt DOCX (Rule 58 / Nghị định 30 compatible) with all Claude markdown traces automatically scrubbed:
python3 skills/research/claude-markdown-cleaner/scripts/md_to_docx_nd30.py input.md -o output.docx
```

## Key Cleaning Rules Enforced
1. **Zero Bold-Colon Bullet Lists (Rule 48):** Converts `- **Nhãn in đậm:** Nội dung...` into natural prose or clean bullets without mechanical bold labels.
2. **No Raw TeX on Simple Numbers/Units (Rule 47):** Converts `$10\%$`, `$100^\circ\text{C}$`, `$25\text{ km}$` to plain `10%`, `100°C`, `25 km`.
3. **Em-Dash Normalization (Rule 47):** Replaces overused ` — ` in Vietnamese prose with commas, colons, or parentheses according to grammatical function, and normalizes numeric/year ranges (`2026–2030`).
4. **Vietnamese Heading Capitalization (Rule 49):** Fixes English Title-Case after colons in Vietnamese headings.
5. **Chatbot Pleasantry Removal (Rule 41):** Strips opening/closing filler (*"Chắc chắn rồi, dưới đây là..."*, *"Hy vọng thông tin trên hữu ích..."*, *"Certainly! Here is..."*).

