"""Sample B: purposive sample of first-person drop-off stories, for root-cause analysis.

Sample A (sample_tagging.py) is representative and estimates how common behaviours are. In the
150-item pilot only 14% of A items showed a root cause, so B targets posts where the writer says
they stopped / paused / skipped / reduced / are considering stopping their own SIP, or describes a
cash-flow shock. B is NOT used for prevalence estimates, only for "why" and segment contrasts.

Usage: python pipeline/sample_stories.py [n=500]
Writes data/samples/stories_sample.jsonl and data/samples/chunks/chunk_bNN.jsonl (50 each).
"""
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
CHUNK = 50
STORY = re.compile(
    r"\bi (have |had |just |recently )?(stopped|paused|cancell?ed|skipped|discontinued|reduced|redeemed|withdrew|exited)\b"
    r"|(stopped|paused|cancell?ed|skipped|discontinued) (my|all my|the|both|one of my) (sips?|mfs?|mutual)"
    r"|should i (stop|pause|discontinue|exit|cancel|redeem)"
    r"|thinking (of|about) (stopping|pausing|exiting|cancell?ing)"
    r"|(stop|pause|exit) my sips?"
    r"|sip (band|bnd) (kar|kr)|band kar (du|doon|diya|di|dena)|sip (rok|ruk)"
    r"|continue (my |the )?sips? or|worth continuing"
    r"|not able to (pay|continue)|lost (my )?job|job loss|emergency fund",
    re.IGNORECASE,
)
# source quota (share of n); Play Store and YouTube are small pools, take what exists up to quota
SHARES = {"playstore": 0.1, "youtube": 0.3, "reddit": 0.6}


def ids(path):
    return {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    rng = random.Random(7)
    exclude = ids(SAMPLES / "tagging_sample.jsonl") | ids(SAMPLES / "open_coding_r1.jsonl") | ids(SAMPLES / "reddit_check.jsonl")
    screen = {x["id"]: x["score"] for x in map(json.loads, open(ROOT / "data" / "relevance_screen.jsonl", encoding="utf-8"))}
    pool = {}
    for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8")):
        if r["id"] in exclude or screen.get(r["id"], 1) == 0 or not STORY.search(r["text"]):
            continue
        pool.setdefault(r["source"], []).append(r)
    print("pool:", {k: len(v) for k, v in pool.items()})

    sample = []
    for src, items in pool.items():
        rng.shuffle(items)
        sample += items[: int(n * SHARES[src])]
    # top up from Reddit if the small pools could not fill their share
    leftover = [r for r in pool.get("reddit", []) if r not in sample]
    sample += leftover[: max(0, n - len(sample))]
    rng.shuffle(sample)

    with open(SAMPLES / "stories_sample.jsonl", "w", encoding="utf-8") as f:
        for r in sample:
            f.write(json.dumps({**r, "stratum": f"B/{r['source']}", "weight": None}, ensure_ascii=False) + "\n")
    for i in range(0, len(sample), CHUNK):
        with open(SAMPLES / "chunks" / f"chunk_b{i // CHUNK + 1:02d}.jsonl", "w", encoding="utf-8") as f:
            for r in sample[i:i + CHUNK]:
                keep = {k: r[k] for k in ("id", "source", "kind", "subreddit", "date", "video_title", "text") if k in r}
                f.write(json.dumps(keep, ensure_ascii=False) + "\n")
    print("sampled:", Counter(r["source"] for r in sample), f"total {len(sample)} in {(len(sample) + CHUNK - 1) // CHUNK} chunks")


if __name__ == "__main__":
    main()
