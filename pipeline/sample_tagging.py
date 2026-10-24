"""Draw the stratified sample for deep tagging (Claude subagents), with sampling weights.

Strata = source x drop_signal. Drop-signal items (stop/pause/skip/negative/bounce/...) are
over-sampled because they carry the "why people stop" evidence; each item gets a weight
(stratum population / stratum sample size) so prevalence can be re-weighted to the population.

Eligible = relevance score >= 1 (final Gemma score, else flash-lite screen) or not yet screened
(the tagger also judges relevance). Items used for open coding / the Reddit codebook check are
excluded so they stay independent.

Usage: python pipeline/sample_tagging.py
Writes data/samples/tagging_sample.jsonl, data/samples/tagging_strata.json and
data/samples/chunks/chunk_NN.jsonl (50 items each).
"""
import json
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
CHUNK = 50
# (source, kind) -> (drop-signal quota, other quota); None = take everything eligible
QUOTAS = {
    ("playstore", "-"): None,
    ("youtube", "-"): (150, 150),
    ("reddit", "post"): (200, 150),
    ("reddit", "comment"): (150, 76),
}
DROP = re.compile(
    r"\bstop|pause|skip|cancel|discontinu|reduc|redeem|withdr|exit|quit|band kar|ruk|"
    r"should i continue|continue or|negative|minus|loss|bounce|missed|failed|not deducted",
    re.IGNORECASE,
)


def load(path):
    return {x["id"]: x for x in map(json.loads, open(path, encoding="utf-8"))} if path.exists() else {}


def main():
    rng = random.Random(2026)
    rows = list(map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8")))
    final, screen = load(ROOT / "data" / "relevance.jsonl"), load(ROOT / "data" / "relevance_screen.jsonl")
    exclude = set(load(SAMPLES / "open_coding_r1.jsonl")) | set(load(SAMPLES / "reddit_check.jsonl"))

    strata = defaultdict(list)
    for r in rows:
        if r["id"] in exclude:
            continue
        score = final.get(r["id"], screen.get(r["id"], {})).get("score")
        if score == 0:
            continue
        key = (r["source"], r.get("kind", "-"))
        if key not in QUOTAS:
            continue
        strata[(*key, "drop" if DROP.search(r["text"]) else "other")].append(r)

    sample, meta = [], {}
    for (src, kind, sig), items in sorted(strata.items()):
        quota = QUOTAS[(src, kind)]
        n = len(items) if quota is None else min(len(items), quota[0] if sig == "drop" else quota[1])
        rng.shuffle(items)
        picked = items[:n]
        weight = len(items) / n if n else 0
        meta[f"{src}/{kind}/{sig}"] = {"population": len(items), "sampled": n, "weight": round(weight, 3)}
        for r in picked:
            sample.append({**r, "stratum": f"{src}/{kind}/{sig}", "weight": round(weight, 3)})
    rng.shuffle(sample)

    with open(SAMPLES / "tagging_sample.jsonl", "w", encoding="utf-8") as f:
        for r in sample:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (SAMPLES / "tagging_strata.json").write_text(json.dumps(meta, indent=2))
    chunk_dir = SAMPLES / "chunks"
    chunk_dir.mkdir(exist_ok=True)
    for i in range(0, len(sample), CHUNK):
        with open(chunk_dir / f"chunk_{i // CHUNK + 1:02d}.jsonl", "w", encoding="utf-8") as f:
            for r in sample[i:i + CHUNK]:
                keep = {k: r[k] for k in ("id", "source", "kind", "subreddit", "date", "video_title", "text") if k in r}
                f.write(json.dumps(keep, ensure_ascii=False) + "\n")
    for k, v in meta.items():
        print(f"{k:28} population {v['population']:>6}  sampled {v['sampled']:>4}  weight {v['weight']}")
    print(f"TOTAL sampled {len(sample)} in {(len(sample) + CHUNK - 1) // CHUNK} chunks")


if __name__ == "__main__":
    main()
