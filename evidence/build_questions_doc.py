"""The engine's answers to the brief's nine questions and the six starter questions, with their evidence.

Reads the saved answers the web app serves (webapp/site/data/cached.json) and writes
evidence/Questions_Answered.md; run md_to_docx.py Questions_Answered for the Word copy.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = json.load(open(ROOT / "webapp/site/data/cached.json", encoding="utf-8"))
BRIEF = [k for k in C if re.match(r"q\d_", k)]
STARTERS = [k for k in C if not re.match(r"q\d_", k)]


def section(n, v):
    out = [f"### {n}. {v['question']}", "",
           f"**Understood as:** {', '.join(c['text'] for c in v['chips'])} · {v['searched']:,} items searched · "
           f"written by {v['model']}, checked before showing", ""]
    for p in v["paragraphs"]:
        out += [re.sub(r"\[(\d+)\]", r"[\1]", p), ""]
    out += [f"**How sure is this?** {v['caveat']}", "", "**Evidence cited**", ""]
    for e in v["evidence"]:
        link = e["url"] if e.get("exact") and e.get("url") else "app review (no permalink)"
        quote = re.sub(r"\s+", " ", e["quote"]).replace("|", "/")
        out.append(f"- [{e['n']}] {e['source']}: \"{quote}\" ({link})")
    return out + [""]


lines = ["# Questions asked and answered: SIP Drop-off Lens", "",
         "These are the engine's saved answers, exactly as its Ask the Data page shows them. Each answer was "
         "written by an AI model from retrieved stories only, then checked before it was saved: every sentence "
         "cites a story or reports a count that matches the data, every percentage is checked against the counts, "
         "every quoted phrase is found word for word in its source, and advice is removed. Numbers in square "
         "brackets point to the evidence list under each answer.", "",
         "## Part 1: the brief's nine questions", ""]
for i, k in enumerate(BRIEF, 1):
    lines += section(i, C[k])
lines += ["## Part 2: starter questions on the Ask the Data page", ""]
for i, k in enumerate(STARTERS, 1):
    lines += section(i, C[k])
(ROOT / "evidence" / "Questions_Answered.md").write_text("\n".join(lines), encoding="utf-8")
print("wrote Questions_Answered.md:", len(BRIEF), "brief +", len(STARTERS), "starter questions")
