"""Golden set as a shareable spreadsheet for the AI Evidence Log.

One row per hand-labelled post: the post, its link, and for each field the human's blind label, the AI's
label, the final answer after review, and whether the AI matched the final answer. Codes are shown in the
plain-English names the web app uses (webapp/site/lib/labels.ts).

Usage: python evidence/build_golden_sheet.py
Reads data/golden_scored.jsonl (blind labels + AI labels), data/golden_review.json (final answers),
data/clean.jsonl (post text). Writes evidence/Golden_Set.xlsx.
"""
import json
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parent.parent
FIELDS = [("story_class", "Story or not"), ("investor_experience", "New vs experienced"),
          ("action", "What they did"), ("stop_trigger", "Event (trigger)"), ("root_cause", "Real reason")]
CLASS = {"dropoff_story": "Drop-off story", "stayed_story": "Stayed story", "not_a_story": "Not a story"}
SOURCE = {"rd": "Reddit", "ps": "Play Store", "as": "App Store", "yt": "YouTube", "tq": "TradingQ&A", "bl": "Blog"}

LABELS = dict(re.findall(r'"?([a-z0-9_]+)"?: "([^"]+)"', (ROOT / "webapp/site/lib/labels.ts").read_text(encoding="utf-8")))
name = lambda c: CLASS.get(c) or LABELS.get(c) or (c or "").replace("_", " ")


def scrub(text):
    text = re.sub(r"(?<![\w/])/?u/[\w-]+", "[user]", text)
    return re.sub(r"@[\w.-]{2,}", "[user]", re.sub(r"\s+", " ", text)).strip()


def main():
    scored = [json.loads(l) for l in open(ROOT / "data/golden_scored.jsonl", encoding="utf-8")]
    review = json.load(open(ROOT / "data/golden_review.json", encoding="utf-8"))
    ids = {r["id"] for r in scored}
    posts = {}
    for line in open(ROOT / "data/clean.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["id"] in ids:
            posts[r["id"]] = r

    wb = Workbook()
    ws = wb.active
    ws.title = "Golden set"
    head = ["#", "Source", "Post (usernames removed)", "Link"]
    for _, title in FIELDS:
        head += [f"{title}: human (blind)", f"{title}: AI", f"{title}: final", f"{title}: AI right?"]
    ws.append(head)
    totals = {f: [0, 0] for f, _ in FIELDS}
    for r in sorted(scored, key=lambda r: r["n"]):
        p = posts.get(r["id"], {})
        src = SOURCE.get(r["id"][:2], "")
        if p.get("app"):
            src += f" · {LABELS.get(p['app'], p['app'])}"
        text = scrub(p.get("text", ""))
        row = [r["n"], src, text[:1500] + ("…" if len(text) > 1500 else ""), p.get("url") or "(app review: no permalink)"]
        for f, _ in FIELDS:
            if f == "story_class":
                human, ai = r["human_class"], [r["ai_class"]]
            elif f in r:
                human, ai = r[f]["human"], r[f]["ai"]
            else:  # not scored: one side said not-a-story, or no label for this field
                row += ["", "", "", ""]
                continue
            final = review.get(r["id"], {}).get(f, {}).get("final", human)
            right = final in ai
            totals[f][0] += right
            totals[f][1] += 1
            row += [name(human), ", ".join(name(a) for a in ai), name(final), "Yes" if right else "No"]
        ws.append(row)

    bold, wrap = Font(bold=True), Alignment(wrap_text=True, vertical="top")
    for c in ws[1]:
        c.font, c.alignment = bold, wrap
        c.fill = PatternFill("solid", fgColor="E6F7F2")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = wrap
            if c.value == "No":
                c.fill = PatternFill("solid", fgColor="FDEEE9")
    for col, width in zip("ABCD", (5, 18, 70, 30)):
        ws.column_dimensions[col].width = width
    for i in range(5, len(head) + 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = 16
    ws.freeze_panes = "C2"

    s = wb.create_sheet("Agreement")
    s.append(["Field", "Posts scored", "AI right vs final answer"])
    for f, title in FIELDS:
        hit, tot = totals[f]
        s.append([title, tot, f"{hit}/{tot} ({hit / tot:.0%})"])
    s.append([])
    s.append(["Blind agreement and the full method are in the AI Evidence Log."])
    for c in s[1]:
        c.font = bold
    s.column_dimensions["A"].width, s.column_dimensions["B"].width, s.column_dimensions["C"].width = 24, 14, 26

    out = ROOT / "evidence" / "Golden_Set.xlsx"
    wb.save(out)
    print("wrote", out.name, {f: f"{h}/{t}" for f, (h, t) in totals.items()})


if __name__ == "__main__":
    main()
