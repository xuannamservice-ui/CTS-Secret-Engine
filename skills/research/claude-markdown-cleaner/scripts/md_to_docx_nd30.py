#!/usr/bin/env python3
"""Convert Markdown/text into an editable Word (.docx) compliant with MASTER PROMPT v5.4.1 (Rule 58) & Nghị định 30/2020/NĐ-CP.

Default parameters (Rule 58):
- Paper: A4 Portrait (210mm x 297mm -> 11906 x 16838 twips)
- Font: Times New Roman, 13 pt (26 half-points)
- Alignment: Justified (both)
- Line spacing: Multiple 1.3 (312 / 240)
- Margins: Top 2.5 cm (1418 twips), Bottom 2.5 cm (1418 twips), Left 3.0 cm (1701 twips), Right 2.0 cm (1134 twips)
- Uses real Word Styles: Title, Heading1, Heading2, Heading3, Normal, ListParagraph
- Strips all raw Claude/Markdown syntax (**bold**, *italic*, ###, $10\%$) into native Word XML runs.
"""
from __future__ import annotations

import argparse
import html
import re
import zipfile
from pathlib import Path

from clean_ai_markdown import clean_markdown

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""

RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="26"/>
        <w:szCs w:val="26"/>
        <w:lang w:val="vi-VN" w:eastAsia="en-US" w:bidi="ar-SA"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:after="120" w:line="312" w:lineRule="auto"/>
        <w:jc w:val="both"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:keepNext/>
      <w:spacing w:before="120" w:after="240" w:line="312" w:lineRule="auto"/>
      <w:jc w:val="center"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="32"/>
      <w:szCs w:val="32"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:keepNext/>
      <w:keepLines/>
      <w:spacing w:before="240" w:after="120" w:line="312" w:lineRule="auto"/>
      <w:outlineLvl w:val="0"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="28"/>
      <w:szCs w:val="28"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:keepNext/>
      <w:keepLines/>
      <w:spacing w:before="180" w:after="120" w:line="312" w:lineRule="auto"/>
      <w:outlineLvl w:val="1"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="26"/>
      <w:szCs w:val="26"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:keepNext/>
      <w:keepLines/>
      <w:spacing w:before="120" w:after="80" w:line="312" w:lineRule="auto"/>
      <w:outlineLvl w:val="2"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:i/>
      <w:sz w:val="26"/>
      <w:szCs w:val="26"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph">
    <w:name w:val="List Paragraph"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:ind w:left="567" w:hanging="284"/>
      <w:spacing w:after="80" w:line="312" w:lineRule="auto"/>
    </w:pPr>
  </w:style>
</w:styles>
"""

INLINE_TOKEN_RE = re.compile(r"(\*\*[^*\n]+\*\*|(?<!\*)\*[^*\n]+\*(?!\*)|`[^`\n]+`)")


def _runs_from_inline(text: str) -> str:
    """Convert inline Markdown (**bold**, *italic*, `code`, [label](url)) into native Word XML <w:r> elements."""
    # Convert markdown links [label](url) -> label
    cleaned = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    parts = INLINE_TOKEN_RE.split(cleaned)
    xml_runs: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            val = html.escape(part[2:-2])
            xml_runs.append(f"<w:r><w:rPr><w:b/></w:rPr><w:t xml:space=\"preserve\">{val}</w:t></w:r>")
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            val = html.escape(part[1:-1])
            xml_runs.append(f"<w:r><w:rPr><w:i/></w:rPr><w:t xml:space=\"preserve\">{val}</w:t></w:r>")
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            val = html.escape(part[1:-1])
            xml_runs.append(f"<w:r><w:t xml:space=\"preserve\">{val}</w:t></w:r>")
        else:
            val = html.escape(part)
            xml_runs.append(f"<w:r><w:t xml:space=\"preserve\">{val}</w:t></w:r>")
    return "".join(xml_runs)


def _para_xml(text: str, style: str = "Normal") -> str:
    runs = _runs_from_inline(text)
    return f"<w:p><w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>{runs}</w:p>"


def _table_xml(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    tbl_pr = (
        "<w:tblPr>"
        "<w:tblW w:w=\"5000\" w:type=\"pct\"/>"
        "<w:tblBorders>"
        "<w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>"
        "</w:tblBorders>"
        "</w:tblPr>"
    )
    row_xmls: list[str] = []
    for idx, row in enumerate(rows):
        tr_pr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if idx == 0 else "<w:trPr><w:cantSplit/></w:trPr>"
        cells: list[str] = []
        for cell in row:
            cell_runs = _runs_from_inline(f"**{cell.strip()}**" if idx == 0 and not cell.strip().startswith("**") else cell.strip())
            cells.append(
                "<w:tc><w:tcPr><w:tcMar>"
                "<w:top w:w=\"80\" w:type=\"dxa\"/><w:bottom w:w=\"80\" w:type=\"dxa\"/>"
                "<w:left w:w=\"120\" w:type=\"dxa\"/><w:right w:w=\"120\" w:type=\"dxa\"/>"
                "</w:tcMar></w:tcPr>"
                f"<w:p><w:pPr><w:spacing w:after=\"60\" w:line=\"276\" w:lineRule=\"auto\"/></w:pPr>{cell_runs}</w:p></w:tc>"
            )
        row_xmls.append(f"<w:tr>{tr_pr}{''.join(cells)}</w:tr>")
    return f"<w:tbl>{tbl_pr}{''.join(row_xmls)}</w:tbl>"


def build_docx(markdown_text: str, output_path: Path) -> None:
    cleaned = clean_markdown(markdown_text, strip_markdown=False)
    lines = cleaned.splitlines()
    body_elements: list[str] = []
    table_buffer: list[list[str]] = []

    def flush_table() -> None:
        nonlocal table_buffer
        if table_buffer:
            body_elements.append(_table_xml(table_buffer))
            table_buffer = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.strip().startswith("|") and line.strip().endswith("|"):
            inner = [c.strip() for c in line.strip()[1:-1].split("|")]
            if all(re.fullmatch(r"[:\-]+", c or "-") for c in inner):
                continue
            table_buffer.append(inner)
            continue
        flush_table()
        if not line.strip() or re.fullmatch(r"-{3,}", line.strip()):
            continue
        if line.startswith("# "):
            body_elements.append(_para_xml(line[2:].strip(), style="Title"))
        elif line.startswith("## "):
            body_elements.append(_para_xml(line[3:].strip(), style="Heading1"))
        elif line.startswith("### "):
            body_elements.append(_para_xml(line[4:].strip(), style="Heading2"))
        elif line.startswith("#### "):
            body_elements.append(_para_xml(line[5:].strip(), style="Heading3"))
        elif re.match(r"^\s*[-*•]\s+", line):
            content = re.sub(r"^\s*[-*•]\s+", "– ", line)
            body_elements.append(_para_xml(content, style="ListParagraph"))
        elif re.match(r"^\s*\d+\.\s+", line):
            body_elements.append(_para_xml(line.strip(), style="ListParagraph"))
        else:
            body_elements.append(_para_xml(line.strip(), style="Normal"))
    flush_table()

    # Rule 58 Page Setup: A4 Portrait (11906 x 16838 twips), Margins Top/Bottom 2.5cm (1418), Left 3.0cm (1701), Right 2.0cm (1134)
    sect_pr = (
        "<w:sectPr>"
        "<w:pgSz w:w=\"11906\" w:h=\"16838\" w:orient=\"portrait\"/>"
        "<w:pgMar w:top=\"1418\" w:right=\"1134\" w:bottom=\"1418\" w:left=\"1701\" w:header=\"709\" w:footer=\"709\" w:gutter=\"0\"/>"
        "</w:sectPr>"
    )
    document_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
        f"<w:body>{''.join(body_elements)}{sect_pr}</w:body>"
        "</w:document>"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", RELS_XML)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS_XML)
        zf.writestr("word/styles.xml", STYLES_XML)
        zf.writestr("word/document.xml", document_xml)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input Markdown/text file")
    parser.add_argument("-o", "--output", required=True, help="Output .docx file path")
    args = parser.parse_args()
    text = Path(args.input).read_text(encoding="utf-8")
    build_docx(text, Path(args.output))
    print(f"Created standard A4 Times New Roman 13pt DOCX (Rule 58 / Nghị định 30): {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

