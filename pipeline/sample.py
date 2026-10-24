"""Draw a fixed, stratified sample of high-relevance items (for open coding / golden set).

Usage: python pipeline/sample.py <out_name> <n> [seed]
Uses final flash scores when present, else the flash-lite screen. Stratifies by source
and keeps every language represented. Writes data/samples/<out_name>.jsonl.
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path) -> dict:
    return {x["id"]: x for x in map(json.loads, open(path, encoding="utf-8"))} if path.exists() else {}


def main():
    out_name, n = sys.argv[1], int(sys.argv[2])
    rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 42)
    scores = load(ROOT / "data" / "relevance.jsonl") or load(ROOT / "data" / "relevance_screen.jsonl")
    rows = [r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))
            if scores.get(r["id"], {}).get("score") == 2]
    by_source = defaultdict(list)
    for r in rows:
        r["first_time"] = scores[r["id"]].get("first_time")
        by_source[r["source"]].append(r)
    per_source = n // len(by_source)
    sample = []
    for src, items in by_source.items():
        rng.shuffle(items)
        # guarantee non-English voices are present, then fill
        non_en = [r for r in items if r["lang"] != "english"][: per_source // 3]
        rest = [r for r in items if r not in non_en][: per_source - len(non_en)]
        sample += non_en + rest
    rng.shuffle(sample)
    out_dir = ROOT / "data" / "samples"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / f"{out_name}.jsonl", "w", encoding="utf-8") as f:
        for r in sample:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(sample)} items from {dict((k, len(v)) for k, v in by_source.items())}")


if __name__ == "__main__":
    main()
