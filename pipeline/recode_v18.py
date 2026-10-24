"""Recode pass for codebook v1.8: the 720 stories were tagged before behaviour_change and
check_frequency `event_driven` existed. Revisit only stories whose text shows a change over time or a
checking habit (cheap regex screen), and fill those two fields.

Usage: python pipeline/recode_v18.py [chunk_size=130]
Writes data/recode/in/recode_NN.jsonl. Subagents write data/recode/out/recode_NN.jsonl with
id, behaviour_change, check_frequency, rationale; validate_deep.py applies them as overrides.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIGNAL = re.compile(
    r"\b(at first|initially|in the beginning|when i (first )?started|back then|earlier i|i used to|pehle|"
    r"now i|these days|nowadays|eventually|gradually|over time|since then|from then)\b|"
    r"\b(started|began) (with|at) (₹|rs\.?|inr)? ?\d|increased (my|the) sip|step(ped)?[- ]?up|"
    r"\b(check|checking|checked|look at|open|opening|track)\w*\b[^.\n]{0,50}\b(daily|every ?day|every (morning|week|month)|"
    r"weekly|monthly|once a|rarely|never|only when|roz)\b|stop(ped)? (checking|looking)|deleted the app", re.I)


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 130
    texts = {r["id"]: r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))}
    d_in = ROOT / "data" / "recode" / "in"
    done = {json.loads(l)["id"] for p in d_in.glob("recode_*.jsonl") for l in open(p, encoding="utf-8")
            if "behaviour_change" in json.loads(l).get("fill", [])}
    todo = []
    for t in map(json.loads, open(ROOT / "data" / "tags_deep.jsonl", encoding="utf-8")):
        if not t["stratum"].startswith("S/") or t.get("relevant") != "yes" or t["id"] in done:
            continue
        r = texts.get(t["id"])
        if r and SIGNAL.search(r["text"]):
            todo.append((t, r))
    # numbering follows out/ too: recode_04 exists only there (hand recode, Correction 3)
    n = max(len(list(d_in.glob("recode_*.jsonl"))), len(list((d_in.parent / "out").glob("recode_*.jsonl"))))
    for i in range(0, len(todo), size):
        n += 1
        with open(d_in / f"recode_{n:02d}.jsonl", "w", encoding="utf-8") as f:
            for t, r in todo[i:i + size]:
                f.write(json.dumps({"id": t["id"], "source": r["source"], "app": r.get("app"),
                                    "text": r["text"][:2000], "fill": ["behaviour_change", "check_frequency"],
                                    "stage": t.get("stage"), "action": t.get("action"),
                                    "check_frequency_now": t.get("check_frequency")}, ensure_ascii=False) + "\n")
        print(f"recode_{n:02d}.jsonl: {len(todo[i:i + size])} items")
    print(f"{len(todo)} stories to recode for v1.8")


if __name__ == "__main__":
    main()
