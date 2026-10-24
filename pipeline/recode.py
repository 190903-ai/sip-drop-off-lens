"""Recode pass: when the codebook gains codes mid-run (v1.5 app_malfunction, v1.6 debit_after_cancel,
support_failure, stay_reason), revisit ONLY the tags that need them instead of re-tagging everything:
  - stayers (action continued / nearly_stopped / increased) -> fill stay_reason
  - stop_trigger containing "other" -> recheck against the new trigger codes

Usage: python pipeline/recode.py [chunk_size=60]
Writes data/recode/in/recode_NN.jsonl for subagents (they write data/recode/out/recode_NN.jsonl with
id, stay_reason, stop_trigger, rationale). validate_deep.py applies data/recode/out/* as overrides.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAYED = {"continued", "nearly_stopped", "increased"}


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    tags = [json.loads(l) for l in open(ROOT / "data" / "tags_deep.jsonl", encoding="utf-8")]
    texts = {r["id"]: r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))}
    d_in = ROOT / "data" / "recode" / "in"
    d_in.mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "recode" / "out").mkdir(exist_ok=True)
    done = {json.loads(l)["id"] for p in d_in.glob("recode_*.jsonl") for l in open(p, encoding="utf-8")}
    todo = [t for t in tags if t["id"] not in done and t.get("relevant") == "yes"
            and (t.get("action") in STAYED or "other" in (t.get("stop_trigger") or []))]
    n = len(list(d_in.glob("recode_*.jsonl")))
    for i in range(0, len(todo), size):
        n += 1
        with open(d_in / f"recode_{n:02d}.jsonl", "w", encoding="utf-8") as f:
            for t in todo[i:i + size]:
                r = texts[t["id"]]
                f.write(json.dumps({"id": t["id"], "source": r["source"], "app": r.get("app"), "text": r["text"][:1500],
                                    "action": t.get("action"), "stop_trigger": t.get("stop_trigger"),
                                    "rationale": t.get("rationale", "")}, ensure_ascii=False) + "\n")
        print(f"recode_{n:02d}.jsonl: {len(todo[i:i + size])} items")
    print(f"{len(todo)} items to recode "
          f"({sum(t.get('action') in STAYED for t in todo)} stayers, "
          f"{sum('other' in (t.get('stop_trigger') or []) for t in todo)} with stop_trigger other)")


if __name__ == "__main__":
    main()
