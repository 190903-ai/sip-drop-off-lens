"""Find first-person SIP discontinuation stories with an LLM (Gemma), so deep tagging is spent on
items that can explain WHY people stop. Regex selection failed: in chunks b01-b03 most regex hits
were portfolio-review or planning posts (b03: zero clear stop stories in 50).

Candidate pool: any clean item with a broad stop/pause/skip/fail/negative keyword, not yet deep-
tagged or used for codebook work. Gemma answers one short question per item.

Usage: python pipeline/detect_stories.py [limit]
Writes data/stories_detect.jsonl (id, story, story_type, first_time). Resumable.
"""
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from llm import generate_json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "stories_detect.jsonl"
MODEL = "gemma-4-26b-a4b-it"
BATCH, WORKERS, PACE = 25, 2, 2
BROAD = re.compile(
    r"\bstop|pause|skip|cancel|discontinu|reduc|redeem|withdr|exit|quit|band kar|band kr|ruk|rok|"
    r"negative|minus|loss|bounce|missed|fail|not deducted|mandate|autopay|salary|job|emergency|"
    r"continue|worth it",
    re.IGNORECASE,
)

SYSTEM = """You screen posts for a study on why first-time Indian investors stop their SIPs.

For EACH item decide whether the writer describes THEIR OWN SIP / mutual fund investing being
interrupted, or seriously considering it:
- story: "yes" only if the writer says THEY stopped, cancelled, paused, skipped, reduced,
  redeemed early, or had an instalment fail/bounce, OR says they are seriously considering
  stopping/pausing their own SIP. Advice to others, portfolio reviews, "which fund to pick",
  planning a new SIP, or general market talk = "no".
- story_type: one of stopped, paused_or_skipped, reduced, redeemed, instalment_failed,
  considering_stop, restructured (stopped one fund but still investing), none.
- first_time: "yes" only if the writer says they are new / started recently; "no" if they say
  they have invested for years; else "unknown".
Text may be English, Hindi or Hinglish. When unsure, answer "no".
Return JSON: {"results": [{"id": ..., "story": "yes"|"no", "story_type": ..., "first_time": ...}]}"""


def detect(batch):
    started = time.time()
    items = "\n\n".join(f"[id={r['id']}] ({r['source']})\n{r['text'][:1200]}" for r in batch)
    result = generate_json(f"Items:\n\n{items}", model=MODEL, system=SYSTEM)
    time.sleep(max(0, PACE - (time.time() - started)))
    valid = {r["id"] for r in batch}
    return [x for x in result.get("results", []) if x.get("id") in valid]


def ids(path):
    return {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    s = ROOT / "data" / "samples"
    exclude = (ids(s / "tagging_sample.jsonl") | ids(s / "open_coding_r1.jsonl") | ids(s / "reddit_check.jsonl")
               | {x for p in (ROOT / "data" / "tags_deep").glob("chunk_b*.jsonl") for x in ids(p)})
    screen = {x["id"]: x["score"] for x in map(json.loads, open(ROOT / "data" / "relevance_screen.jsonl", encoding="utf-8"))}
    rows = [r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))
            if r["id"] not in exclude and screen.get(r["id"], 1) > 0 and BROAD.search(r["text"])]
    # round-robin across source/app so every stretch of the run covers all voices
    # (Groww, each competitor app, TradingQ&A, blogs, YouTube, Reddit posts/comments)
    done = ids(OUT)
    groups = {}
    for r in rows:
        if r["id"] not in done:
            groups.setdefault((r["source"], r.get("app") or r.get("kind", "-")), []).append(r)
    todo = []
    while any(groups.values()):
        for g in groups.values():
            if g:
                todo.append(g.pop(0))
    todo = todo[:limit]
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    print(f"[detect/{MODEL}] pool {len(rows)}, {len(done)} done, {len(todo)} to go in {len(batches)} batches", flush=True)
    with open(OUT, "a", encoding="utf-8") as f, ThreadPoolExecutor(WORKERS) as pool:
        futures = [pool.submit(detect, b) for b in batches]
        stories = 0
        for n, fut in enumerate(as_completed(futures), 1):
            try:
                res = fut.result()
            except Exception as e:
                print(f"  batch failed: {str(e)[:150]}", flush=True)
                continue
            for x in res:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
                stories += x.get("story") == "yes"
            f.flush()
            if n % 10 == 0:
                print(f"  {n}/{len(batches)} batches, {stories} stories so far", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
