"""Per-field agreement between two tag files (e.g. a model vs a reference coder).

single fields: exact match. multi fields: exact set match, plus "overlap" (share at least one
code, or both unknown). Codes added in v1.1 are mapped back to their v1 fallback so a v1-coded
reference is compared fairly.

Usage: python pipeline/compare_tags.py <candidate.jsonl> <reference.jsonl>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODEBOOK = json.loads((ROOT / "pipeline" / "codebook.json").read_text(encoding="utf-8"))
SKIP = {"evidence_quote", "rationale"}
# v1.1 additions -> what a v1 coder would have had to use
V11_FALLBACK = {"restructured": "other", "portfolio_rationalisation": "other",
                "self_review": "other", "portfolio_construction_help": "independent_reassurance"}


def as_set(x) -> set:
    vals = x if isinstance(x, list) else [x]
    vals = {V11_FALLBACK.get(v, v) for v in vals if v}
    return vals - {"unknown"} or {"unknown"}


def main():
    cand = {x["id"]: x for x in map(json.loads, open(sys.argv[1], encoding="utf-8"))}
    ref = {x["id"]: x for x in map(json.loads, open(sys.argv[2], encoding="utf-8"))}
    ids = [i for i in ref if i in cand]
    print(f"{len(ids)} items in both files\n")
    print(f"{'field':24} {'exact':>7} {'overlap':>8}  {'ref non-unknown':>15}")
    rows = []
    for f in CODEBOOK["fields"]:
        name = f["name"]
        if name in SKIP or f["type"] == "text":
            continue
        exact = overlap = informative = 0
        for i in ids:
            a, b = as_set(cand[i].get(name)), as_set(ref[i].get(name))
            exact += a == b
            overlap += a == b or bool((a & b) - {"unknown"})
            informative += b != {"unknown"}
        rows.append((name, exact / len(ids), overlap / len(ids), informative))
        print(f"{name:24} {exact / len(ids):>7.0%} {overlap / len(ids):>8.0%}  {informative:>15}")
    verified = sum(bool(cand[i].get("quote_verified")) for i in ids)
    print(f"\nevidence quotes present and verified verbatim: {verified}/{len(ids)}")


if __name__ == "__main__":
    main()
