"""Score the AI against the user's blind golden-set labels.

Reads evidence/golden_set.xlsx (user labels), joins the AI labels by id (story_class from
data/stories_v2.jsonl, codebook tags from data/tags_deep.jsonl) and reports agreement.
Rows with no story_class yet are skipped, so it can be run on a partly labelled file.

Matching rules:
- story_class: exact match; also Cohen's kappa (agreement beyond chance) and a confusion table.
- Tag fields are scored only where BOTH human and AI call it a story. Single-value fields
  (investor_experience, action) need an exact match. List fields (stop_trigger, root_cause,
  metric_branch) count as a match when the human's one main code is among the AI's codes,
  because the AI may list several.

Usage: python pipeline/score_golden.py
Writes evidence/golden_scores.md and data/golden_scored.jsonl (row-level, for the Evidence Log).
"""
import json
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["investor_experience", "action", "stop_trigger", "root_cause", "metric_branch"]
CLASSES = ["dropoff_story", "stayed_story", "not_a_story"]
PASS = 0.80  # agreement bar for the eval gate


def load(path):
    out = {}
    for l in open(path, encoding="utf-8"):
        if l.strip():
            x = json.loads(l)
            out[x["id"]] = x  # last one wins (re-tags overwrite)
    return out


def cell(v):
    return str(v).strip() if v not in (None, "") else ""


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(h == a for h, a in pairs) / n
    hc, ac = Counter(h for h, _ in pairs), Counter(a for _, a in pairs)
    pe = sum(hc[c] * ac[c] for c in set(hc) | set(ac)) / n / n
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def main():
    ws = load_workbook(ROOT / "evidence" / "golden_set.xlsx", read_only=True)["Label these"]
    rows = list(ws.iter_rows(values_only=True))
    head = [cell(h) for h in rows[0]]
    human = [dict(zip(head, r)) for r in rows[1:] if r and r[0] is not None]
    detect = load(ROOT / "data" / "stories_v2.jsonl")
    tags = load(ROOT / "data" / "tags_deep.jsonl")

    labelled = [h for h in human if cell(h["story_class"])]
    scored, pairs = [], []
    field_hits = {f: [0, 0] for f in FIELDS}
    misses = []
    for h in labelled:
        hid = cell(h["id"])
        hc, ac = cell(h["story_class"]), detect[hid]["story_class"]
        pairs.append((hc, ac))
        row = {"n": h["#"], "id": hid, "human_class": hc, "ai_class": ac, "class_match": hc == ac,
               "notes": cell(h.get("notes"))}
        if hc != ac:
            misses.append(f"#{h['#']} `{hid}`: human **{hc}**, AI **{ac}**")
        if hc != "not_a_story" and ac != "not_a_story" and hid in tags:
            for f in FIELDS:
                hv = cell(h.get(f))
                if not hv:
                    continue
                av = tags[hid].get(f)
                av = av if isinstance(av, list) else [av]
                ok = hv in av
                field_hits[f][0] += ok
                field_hits[f][1] += 1
                row[f] = {"human": hv, "ai": av, "match": ok}
                if not ok:
                    misses.append(f"#{h['#']} `{hid}` {f}: human **{hv}**, AI {av}")
        scored.append(row)

    with open(ROOT / "data" / "golden_scored.jsonl", "w", encoding="utf-8") as f:
        for r in scored:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(pairs)
    acc = sum(h == a for h, a in pairs) / n if n else None
    k = kappa(pairs)
    lines = ["# Golden set: AI vs human agreement", "",
             f"Labelled by the user: **{n} of {len(human)}** items. Pass bar: {PASS:.0%} agreement.", ""]
    if not n:
        lines.append("Nothing labelled yet.")
    else:
        lines += ["## Story detection (story_class)", "",
                  f"- Agreement: **{acc:.0%}** ({sum(h == a for h, a in pairs)}/{n}) "
                  f"{'PASS' if acc >= PASS else 'BELOW BAR'}",
                  f"- Cohen's kappa: **{k:.2f}**" if k is not None else "- Cohen's kappa: n/a", "",
                  "| human \\ AI | " + " | ".join(CLASSES) + " |", "|---" * (len(CLASSES) + 1) + "|"]
        conf = Counter(pairs)
        for hcls in CLASSES:
            lines.append(f"| {hcls} | " + " | ".join(str(conf[(hcls, a)]) for a in CLASSES) + " |")
        lines += ["", "## Codebook tags (items both call a story)", "", "| field | agreement | n |", "|---|---|---|"]
        for f in FIELDS:
            hit, tot = field_hits[f]
            lines.append(f"| {f} | {hit / tot:.0%} | {tot} |" if tot else f"| {f} | n/a | 0 |")
        lines += ["", "## Disagreements (review these for the Evidence Log)", ""]
        lines += [f"- {m}" for m in misses] or ["- none"]
    out = ROOT / "evidence" / "golden_scores.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
