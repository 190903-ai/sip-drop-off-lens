"""Convert a Markdown file to .docx (headings, paragraphs, lists, pipe tables, **bold**).
Usage: python evidence/md_to_docx.py [name]   (default AI_Evidence_Log; reads evidence/<name>.md)
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

HERE = Path(__file__).resolve().parent
NAME = sys.argv[1] if len(sys.argv) > 1 else "AI_Evidence_Log"
SRC, OUT = HERE / f"{NAME}.md", HERE / f"{NAME}.docx"


def link(par, text, url):
    """A real, clickable hyperlink run (python-docx has no helper for this)."""
    rid = par.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    pr = OxmlElement("w:rPr")
    for tag, val in (("w:color", "1155CC"), ("w:u", "single")):
        e = OxmlElement(tag)
        e.set(qn("w:val"), val)
        pr.append(e)
    r.append(pr)
    t = OxmlElement("w:t")
    t.text = text
    r.append(t)
    h.append(r)
    par._p.append(h)


def runs(par, text):
    # [text](url) links, then **bold** inside the plain parts
    for j, chunk in enumerate(re.split(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", text)):
        if j % 3 == 1:
            continue
        if j % 3 == 2:
            link(par, re.split(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", text)[j - 1], chunk)
            continue
        for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", chunk)):
            if part:
                par.add_run(part).bold = bool(i % 2)


def main():
    doc = Document()
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(10.5)
    lines = SRC.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"-+", c) for c in cells):
                    rows.append(cells)
                i += 1
            t = doc.add_table(rows=len(rows), cols=len(rows[0]))
            t.style = "Table Grid"
            for r, cells in enumerate(rows):
                for c, text in enumerate(cells):
                    p = t.cell(r, c).paragraphs[0]
                    runs(p, f"**{text}**" if r == 0 and text else text)
                    for run in p.runs:
                        run.font.size = Pt(9)
            doc.add_paragraph()
            continue
        m = re.match(r"(#+) (.*)", line)
        if m:
            doc.add_heading(m.group(2), level=min(len(m.group(1)) - 1, 3) if len(m.group(1)) > 1 else 0)
        elif re.match(r"\d+\. ", line):
            runs(doc.add_paragraph(style="List Number"), re.sub(r"^\d+\. ", "", line))
        elif line.startswith("- "):
            runs(doc.add_paragraph(style="List Bullet"), line[2:])
        elif line.strip():
            runs(doc.add_paragraph(), line)
        i += 1
    doc.save(OUT)
    print("wrote", OUT.name)


if __name__ == "__main__":
    main()
