"""Turn AI-detected stories into deep-tagging chunks for Claude subagents: drop-off stories from the
old Gemma run (data/stories_detect.jsonl, story == "yes") and drop-off + stayed stories from the
three-way detector (data/stories_v2.jsonl). Incremental: only stories not already in a chunk are added.

Usage: python pipeline/make_story_chunks.py [chunk_size=50]
Appends to data/samples/stories_ai.jsonl and writes data/samples/chunks/chunk_sNN.jsonl.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
KEEP = ("id", "source", "app", "kind", "subreddit", "site", "date", "video_title", "text")


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    detected = {x["id"]: {**x, "story_class": "dropoff_story"}
                for x in map(json.loads, open(ROOT / "data" / "stories_detect.jsonl", encoding="utf-8"))
                if x.get("story") == "yes"}
    v2 = ROOT / "data" / "stories_v2.jsonl"
    if v2.exists():
        detected.update({x["id"]: x for x in map(json.loads, open(v2, encoding="utf-8"))
                         if x["story_class"] != "not_a_story"})
    meta_path = SAMPLES / "stories_ai.jsonl"
    already = {json.loads(l)["id"] for l in open(meta_path, encoding="utf-8")} if meta_path.exists() else set()
    rows = [r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))
            if r["id"] in detected and r["id"] not in already]
    if not rows:
        print("no new stories")
        return
    existing = sorted((SAMPLES / "chunks").glob("chunk_s*.jsonl"))
    next_no = len(existing) + 1
    with open(meta_path, "a", encoding="utf-8") as meta:
        for i in range(0, len(rows), size):
            name = f"chunk_s{next_no:02d}.jsonl"
            with open(SAMPLES / "chunks" / name, "w", encoding="utf-8") as f:
                for r in rows[i:i + size]:
                    f.write(json.dumps({k: r[k] for k in KEEP if k in r}, ensure_ascii=False) + "\n")
                    d = detected[r["id"]]
                    meta.write(json.dumps({**r, "stratum": f"S/{r['source']}", "weight": None,
                                           "story_class": d["story_class"], "story_type": d.get("story_type"),
                                           "chunk": name},
                                          ensure_ascii=False) + "\n")
            print(f"{name}: {len(rows[i:i + size])} stories")
            next_no += 1


if __name__ == "__main__":
    main()
