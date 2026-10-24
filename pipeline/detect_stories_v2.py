"""Three-way story detection on the pre-filtered candidates (v1, detect_stories.py, left untouched).

Every candidate is labelled dropoff_story / stayed_story / not_a_story. Stayed stories (kept going
through a loss, nearly stopped, stepped up) are the control group: without them we can only say
why people leave, not what separates them from people who stay.

Claude subagents label the bulk (Gemma's free tier returned empty answers / 503s at ~50 items/hour);
Gemma labels a small slice so the two can be compared on the golden set.

Usage:
  python pipeline/detect_stories_v2.py export [chunk_size]   new candidates -> data/detect_v2/in/chunk_dNN.jsonl
  python pipeline/detect_stories_v2.py export_targeted        data/candidates_targeted.jsonl -> chunk_tNN.jsonl
  python pipeline/detect_stories_v2.py ingest                data/detect_v2/out/*.jsonl -> data/stories_v2.jsonl (+ checks)
  python pipeline/detect_stories_v2.py gemma [n]              Gemma labels n candidates -> data/stories_v2_gemma.jsonl
  python pipeline/detect_stories_v2.py report                 counts by class, source, first-time
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IN, OUT = DATA / "detect_v2" / "in", DATA / "detect_v2" / "out"
MERGED, GEMMA_OUT = DATA / "stories_v2.jsonl", DATA / "stories_v2_gemma.jsonl"
MAX_CHARS = 1500

CLASSES = {"dropoff_story", "stayed_story", "not_a_story"}
TYPES = {
    "dropoff_story": {"stopped", "paused_or_skipped", "reduced", "redeemed", "instalment_failed",
                      "attempted_blocked", "considering_stop", "restructured", "switched_platform"},
    "stayed_story": {"continued_through_loss", "nearly_stopped", "increased", "restarted"},
    "not_a_story": {"none"},
}
EXPERIENCE = {"first_time", "experienced", "unknown"}
KEEP = ("id", "source", "app", "kind", "subreddit", "site", "date", "video_title")


def norm(s):
    return " ".join(s.lower().split())


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()] if path.exists() else []


def corpus():
    return {r["id"]: r for r in map(json.loads, open(DATA / "clean.jsonl", encoding="utf-8"))}


def export(size=100, cands_file="candidates.jsonl", prefix="d"):
    IN.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    done = {x["id"] for p in IN.glob(f"chunk_{prefix}*.jsonl") for x in load(p)}
    cands = [c for c in load(DATA / cands_file) if c["id"] not in done]
    # interleave groups so every chunk mixes sources (a stalled run still covers every voice)
    groups = {}
    for c in cands:
        groups.setdefault(c["group"], []).append(c)
    order = []
    while any(groups.values()):
        for g in groups.values():
            if g:
                order.append(g.pop(0))
    texts, n = corpus(), len(list(IN.glob(f"chunk_{prefix}*.jsonl")))
    for i in range(0, len(order), size):
        n += 1
        with open(IN / f"chunk_{prefix}{n:02d}.jsonl", "w", encoding="utf-8") as f:
            for c in order[i:i + size]:
                r = texts[c["id"]]
                row = {k: r[k] for k in KEEP if r.get(k)}
                row["text"] = r["text"][:MAX_CHARS]
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"wrote chunk_{prefix}{n:02d}.jsonl ({len(order[i:i + size])} items)")
    print(f"exported {len(order)} new candidates")


def check(label, text):
    """Clean one label; return (row, issues)."""
    issues, row = [], {"id": label.get("id")}
    cls = label.get("story_class")
    if cls not in CLASSES:
        issues.append("bad_class")
        cls = "not_a_story"
    typ = label.get("story_type")
    if typ not in TYPES[cls]:
        issues.append("bad_type")
        typ = "none" if cls == "not_a_story" else "unknown"
    exp = label.get("investor_experience")
    if exp not in EXPERIENCE:
        issues.append("bad_experience")
        exp = "unknown"
    quote = (label.get("evidence_quote") or "").strip()
    ok = bool(quote) and norm(quote) in norm(text)
    if quote and not ok:
        issues.append("quote_not_found")
        quote = ""
    row.update(story_class=cls, story_type=typ, investor_experience=exp, evidence_quote=quote, quote_verified=ok)
    return row, issues


def ingest():
    texts, merged, issues = corpus(), {}, Counter()
    for path in sorted(OUT.glob("chunk_[dt]*.jsonl")):  # d = main pre-filter, t = targeted pull
        expected = [x["id"] for x in load(IN / path.name)]
        labels = {x.get("id"): x for x in load(path)}
        c = Counter()
        for i in expected:
            if i not in labels:
                c["missing"] += 1
                continue
            row, iss = check(labels[i], texts[i]["text"][:MAX_CHARS])
            row.update(source=texts[i]["source"], app=texts[i].get("app"), chunk=path.stem, labeller="claude")
            merged[i] = row
            c[row["story_class"]] += 1
            c.update(iss)
        issues.update(c)
        print(f"{path.name}: drop-off {c['dropoff_story']}, stayed {c['stayed_story']}, not {c['not_a_story']}, "
              f"missing {c['missing']}, quotes not found {c['quote_not_found']}, bad codes "
              f"{c['bad_class'] + c['bad_type'] + c['bad_experience']}")
    with open(MERGED, "w", encoding="utf-8") as f:
        for row in merged.values():
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"TOTAL {len(merged)} labelled; {dict(issues)}")


SYSTEM = (Path(__file__).resolve().parent / "DETECT_INSTRUCTIONS.md").read_text(encoding="utf-8")


def gemma(n=100, batch=10):
    from llm import generate_json
    texts, done = corpus(), {x["id"] for x in load(GEMMA_OUT)}
    # the slice Gemma labels = candidates Claude already labelled, so the two can be compared
    pool = [x["id"] for x in load(MERGED) if x["id"] not in done][:n]
    with open(GEMMA_OUT, "a", encoding="utf-8") as f:
        for i in range(0, len(pool), batch):
            items = "\n\n".join(f"[id={j}] ({texts[j]['source']})\n{texts[j]['text'][:MAX_CHARS]}" for j in pool[i:i + batch])
            try:
                res = generate_json(f"Label these items. Return JSON {{\"results\": [...]}}.\n\n{items}",
                                    model="gemma-4-26b-a4b-it", system=SYSTEM)
            except Exception as e:
                print(f"  batch failed: {str(e)[:120]}", flush=True)
                continue
            for x in res.get("results", []):
                if x.get("id") in texts:
                    row, _ = check(x, texts[x["id"]]["text"][:MAX_CHARS])
                    f.write(json.dumps({**row, "labeller": "gemma"}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  {min(i + batch, len(pool))}/{len(pool)}", flush=True)


def report():
    rows = load(MERGED)
    print("class:", Counter(r["story_class"] for r in rows))
    stories = [r for r in rows if r["story_class"] != "not_a_story"]
    print("type:", Counter(r["story_type"] for r in stories).most_common())
    print("experience:", Counter(f"{r['story_class']}/{r['investor_experience']}" for r in stories))
    print("source:", Counter(f"{r['source']}/{r.get('app') or '-'}" for r in stories).most_common())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    arg = int(sys.argv[2]) if len(sys.argv) > 2 else None
    {"export": lambda: export(arg or 100),
     "export_targeted": lambda: export(arg or 100, "candidates_targeted.jsonl", "t"), "ingest": ingest, "gemma": lambda: gemma(arg or 100),
     "report": report}[cmd]()
