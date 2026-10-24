"""Build the golden set: 25 items the user labels BLIND (no AI labels in the file), to score
detection (story or not, drop-off vs stayed) and tagging (key codebook fields) against a human.

Selection: from the three-way detector's labels, stratified by AI class (11 drop-off, 7 stayed,
7 not-a-story), round-robin across sources so every source appears. Stories come from the deep-
tagging chunks, so their codebook tags can be compared too. Seeded, so it is reproducible.

Usage: python pipeline/make_golden.py
Writes evidence/golden_set.xlsx (for the user) and data/golden_key.jsonl (ids + strata only;
AI labels are joined at scoring time, never shown in the workbook).
"""
import json
import random
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parent.parent
QUOTA = {"dropoff_story": 11, "stayed_story": 7, "not_a_story": 7}
FIELDS = ["investor_experience", "action", "stop_trigger", "root_cause", "metric_branch"]


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main():
    rng = random.Random(7)
    cb = {f["name"]: f for f in json.load(open(ROOT / "pipeline" / "codebook.json", encoding="utf-8"))["fields"]}
    texts = {r["id"]: r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))}
    in_chunks = {x["id"] for p in (ROOT / "data" / "samples" / "chunks").glob("chunk_s*.jsonl") for x in load(p)}
    labels = load(ROOT / "data" / "stories_v2.jsonl")

    picked = []
    for cls, n in QUOTA.items():
        by_src = {}
        for x in labels:
            if x["story_class"] == cls and (cls == "not_a_story" or x["id"] in in_chunks):
                by_src.setdefault(f"{x['source']}/{x.get('app') or '-'}", []).append(x)
        for pool in by_src.values():
            rng.shuffle(pool)
        srcs = sorted(by_src)
        rng.shuffle(srcs)
        while len([p for p in picked if p["stratum"] == cls]) < n and any(by_src.values()):
            for s in srcs:
                if by_src[s] and len([p for p in picked if p["stratum"] == cls]) < n:
                    picked.append({"id": by_src[s].pop()["id"], "stratum": cls})
    rng.shuffle(picked)  # mix classes so the order gives nothing away

    wb = Workbook()
    ws = wb.active
    ws.title = "Label these"
    head = ["#", "id", "source", "text", "story_class"] + FIELDS + ["notes"]
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDE7F0")
    for n, p in enumerate(picked, 1):
        r = texts[p["id"]]
        src = r["source"] + (f" ({r['app']})" if r.get("app") else "") + (f" | video: {r['video_title']}" if r.get("video_title") else "")
        ws.append([n, p["id"], src, r["text"][:1500]] + [""] * (len(FIELDS) + 2))
    widths = [4, 16, 18, 90] + [20] * (len(FIELDS) + 1) + [30]
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    codes = wb.create_sheet("Codes")
    lists = {"story_class": [("dropoff_story", "writer's own SIP stopped/paused/failed/considering stopping"),
                             ("stayed_story", "writer kept their own SIP going through a loss/doubt, nearly stopped, stepped up, restarted"),
                             ("not_a_story", "advice, question with no personal situation, planning, market talk")]}
    for f in FIELDS:
        lists[f] = [(v["code"], v["definition"]) for v in cb[f]["values"]]
    col = 1
    for name, vals in lists.items():
        codes.cell(1, col, name).font = Font(bold=True)
        codes.cell(1, col + 1, "meaning").font = Font(bold=True)
        for i, (code, d) in enumerate(vals, 2):
            codes.cell(i, col, code)
            codes.cell(i, col + 1, d)
        codes.column_dimensions[chr(64 + col)].width = 24
        codes.column_dimensions[chr(65 + col)].width = 60
        letter = chr(64 + col)
        dv = DataValidation(type="list", formula1=f"=Codes!${letter}$2:${letter}${len(vals) + 1}", allow_blank=True)
        ws.add_data_validation(dv)
        target = chr(65 + head.index(name))
        dv.add(f"{target}2:{target}{len(picked) + 1}")
        col += 2

    guide = wb.create_sheet("How to label", 0)
    for line in [
        "Golden set: label each item yourself, BEFORE looking at any AI tags.",
        "1. Read the text in 'Label these'. Pick story_class from the dropdown.",
        "2. If it is a story, fill investor_experience, action, stop_trigger, root_cause, metric_branch.",
        "   For root_cause / stop_trigger / metric_branch pick the ONE main code (the AI may list several).",
        "3. If not_a_story, leave the other columns blank.",
        "4. 'unknown' is a correct answer when the text does not say. The 'Codes' sheet explains every code.",
        "5. Use 'notes' for anything you are unsure about. Save the file; Claude scores it afterwards.",
    ]:
        guide.append([line])
    guide.column_dimensions["A"].width = 110

    out = ROOT / "evidence" / "golden_set.xlsx"
    wb.save(out)
    with open(ROOT / "data" / "golden_key.jsonl", "w", encoding="utf-8") as f:
        for n, p in enumerate(picked, 1):
            f.write(json.dumps({"n": n, **p}) + "\n")
    print(f"wrote {out} with {len(picked)} items:", {k: sum(p['stratum'] == k for p in picked) for k in QUOTA})
    print("sources:", sorted({texts[p['id']]['source'] + '/' + (texts[p['id']].get('app') or '-') for p in picked}))


if __name__ == "__main__":
    main()
