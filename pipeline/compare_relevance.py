"""Model selection eval: score the items that gemini-3.5-flash already scored with another
model and report agreement (flash is the reference after Correction 2).

Usage: python pipeline/compare_relevance.py <model>
Writes data/model_eval/relevance_<model>.jsonl and prints agreement + disagreements.
"""
import json
import sys
from collections import Counter
from pathlib import Path

from relevance import score_batch

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_FILES = ["relevance_v3_flash_test.jsonl", "relevance_flash_partial.jsonl"]  # flash-scored runs


def main():
    model = sys.argv[1]
    ref = {}
    for name in REFERENCE_FILES:
        path = ROOT / "data" / name
        if path.exists():
            ref.update({x["id"]: x for x in map(json.loads, open(path, encoding="utf-8"))})
    rows = {r["id"]: r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))}
    items = [rows[i] for i in ref if i in rows]
    out_dir = ROOT / "data" / "model_eval"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"relevance_{model}.jsonl"

    got = {}
    for i in range(0, len(items), 25):
        try:
            for x in score_batch(items[i:i + 25], model, pace=2):
                got[x["id"]] = x
        except Exception as e:
            print(f"  batch failed: {str(e)[:150]}")
    with open(out, "w", encoding="utf-8") as f:
        for x in got.values():
            f.write(json.dumps(x, ensure_ascii=False) + "\n")

    both = [i for i in got if i in ref]
    exact = sum(got[i]["score"] == ref[i]["score"] for i in both)
    # what matters downstream: keep (>=1) vs drop (0)
    keep = sum((got[i]["score"] > 0) == (ref[i]["score"] > 0) for i in both)
    print(f"{model}: {len(both)}/{len(items)} items compared")
    print(f"  exact score agreement with flash: {exact}/{len(both)} = {exact / max(1, len(both)):.0%}")
    print(f"  keep/drop agreement with flash:   {keep}/{len(both)} = {keep / max(1, len(both)):.0%}")
    print("  confusion (flash -> model):", Counter(f"{ref[i]['score']}->{got[i]['score']}" for i in both))
    for i in both:
        if (got[i]["score"] > 0) != (ref[i]["score"] > 0):
            print(f"   flash {ref[i]['score']} vs {got[i]['score']} | {rows[i]['text'][:110]!r}")


if __name__ == "__main__":
    main()
