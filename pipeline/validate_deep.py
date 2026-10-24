"""Validate subagent deep-tag chunks and merge them.

Per item: codes must exist in the codebook (else -> unknown, logged); evidence_quote must be a
verbatim substring of the source text (else blanked, logged as a hallucination); every input item
must have an output row. Adds stratum + weight from the sample.

Usage: python pipeline/validate_deep.py
Reads data/tags_deep/chunk_*.jsonl, writes data/tags_deep.jsonl and data/tags_deep_issues.jsonl,
prints a per-chunk quality report.
"""
import json
from collections import Counter
from pathlib import Path

from tag import CODEBOOK, validate

ROOT = Path(__file__).resolve().parent.parent
FIELDS = [f["name"] for f in CODEBOOK["fields"]]
EXTRA = {"relevant": {"yes", "no"}, "first_time": {"yes", "no", "unknown"}}


def main():
    sample = {}
    # sample A (representative) + B (regex stories, retired) + S (AI-detected stories)
    # + Q (question-targeted items, 23 Oct: posts that answer the brief's thin questions without being stories)
    for name in ("tagging_sample.jsonl", "stories_sample.jsonl", "stories_ai.jsonl", "questions_sample.jsonl"):
        path = ROOT / "data" / "samples" / name
        if path.exists():
            sample.update({x["id"]: x for x in map(json.loads, open(path, encoding="utf-8"))})
    # recode pass (recode.py): newer codes applied to older tags, field by field
    overrides = {}
    for p in sorted((ROOT / "data" / "recode" / "out").glob("recode_*.jsonl")):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                o = json.loads(line)
                # later recode files add to earlier ones; v1.7 (recode_04) re-codes root_cause
                overrides.setdefault(o["id"], {}).update(
                    {k: o[k] for k in ("action", "stay_reason", "stop_trigger", "root_cause", "rationale",
                                        "behaviour_change", "check_frequency")
                     # v1.8 recode (recode_v18.py) fills empty fields: its "unknown" must not wipe a value.
                     # Earlier recodes may set unknown on purpose (Correction 3 removed borrowed_conviction).
                     if o.get(k) and not (k in ("behaviour_change", "check_frequency")
                                          and o[k] in ("unknown", ["unknown"]))})
    merged, all_issues = [], []
    for path in sorted((ROOT / "data" / "tags_deep").glob("chunk_*.jsonl")):
        chunk_ids = [json.loads(l)["id"] for l in open(ROOT / "data" / "samples" / "chunks" / path.name, encoding="utf-8")]
        rows = {}
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                t = json.loads(line)
                rows[t.get("id")] = t
        counts = Counter()
        for i in chunk_ids:
            if i not in rows:
                all_issues.append({"id": i, "chunk": path.name, "issue": "missing_item"})
                counts["missing"] += 1
                continue
            raw = rows[i]
            # tags before codebook v1.4 carry first_time yes/no instead of investor_experience
            if "investor_experience" not in raw:
                raw["investor_experience"] = {"yes": "first_time", "no": "experienced"}.get(raw.get("first_time"), "unknown")
            raw.setdefault("stay_reason", ["unknown"])  # field added in v1.6; filled later by the recode pass
            raw.setdefault("behaviour_change", ["unknown"])  # field added in v1.8; same
            raw.update(overrides.get(i, {}))
            clean, issues = validate(raw, sample[i]["text"], FIELDS)
            for k, allowed in EXTRA.items():
                clean[k] = raw.get(k) if raw.get(k) in allowed else "unknown"
            clean.update(stratum=sample[i]["stratum"], weight=sample[i]["weight"], source=sample[i]["source"])
            for iss in issues:
                iss["chunk"] = path.name
                counts[iss["issue"]] += 1
            all_issues += issues
            counts["coded"] += 1
            counts["quote_ok"] += clean.get("quote_verified", False)
            counts["irrelevant"] += clean["relevant"] == "no"
            merged.append(clean)
        print(f"{path.name}: coded {counts['coded']}/{len(chunk_ids)}, irrelevant {counts['irrelevant']}, "
              f"verified quotes {counts['quote_ok']}, invalid codes {counts['invalid_code']}, "
              f"quotes not found {counts['quote_not_found']}, missing {counts['missing']}")
    with open(ROOT / "data" / "tags_deep.jsonl", "w", encoding="utf-8") as f:
        for t in merged:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    with open(ROOT / "data" / "tags_deep_issues.jsonl", "w", encoding="utf-8") as f:
        for i in all_issues:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")
    print(f"TOTAL merged {len(merged)}; issues {Counter(i['issue'] for i in all_issues)}")


if __name__ == "__main__":
    main()
