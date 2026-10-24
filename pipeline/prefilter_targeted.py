"""Targeted pre-filter: find more FIRST-TIME and STAYED stories, the two thin groups after the first
detection pass (59 first-time drop-offs, 72 stayers of whom 12 first-time).

The first pre-filter ranked by stop/worry words, so it mostly surfaced app-failure complaints. This
one searches the whole clean corpus again with a wider first-timer vocabulary (age, student, first
salary, "started N months ago", Hinglish) and the stayed vocabulary, and keeps only items no detector
has labelled yet. Items sitting unread in the skipped chunks d09-d20 are eligible.

Tracks (an item can hit both; it is kept once, under its best track):
  first_time: first person + first-timer signal + some SIP action, worry or stayed signal
  stayed:     first person + stayed signal + a loss / doubt / first-timer context

Usage: python pipeline/prefilter_targeted.py
Writes data/candidates_targeted.jsonl; then `python pipeline/detect_stories_v2.py export_targeted`.
"""
import json
import re
from collections import Counter
from pathlib import Path

from prefilter import ACTION, ADVICE, FIRST_PERSON, FIRST_TIME, STAYED, WORRY, group

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

FIRST_TIME_WIDE = re.compile(
    r"started (my )?(first )?sips?\b|started investing (in|last|this|from|since|around)|"
    r"(been )?investing (for|since) (the )?(last |past )?(\d+|a|one|two|three|four|five|six|few|couple of) "
    r"(month|months|year)\b|new investor|first[- ]time investor|first year (of|in) (investing|mf|mutual)|"
    r"\b(1[89]|2[0-6]) ?(yo|y/o|years? old|m|f)\b|\bi'?m (1[89]|2[0-6])\b|college student|\bstudent\b|"
    r"\bintern(ship)?\b|first salary|first job|just got (a|my) job|started working|"
    r"shuru kiya|shuru ki|nayi sip|naya sip|pehli sip|abhi abhi", re.I)
CAPS = {
    "first_time": {"reddit/post": 520, "reddit/comment": 120, "tradingqna/post": 40, "tradingqna/comment": 60,
                   "youtube": 70, "blog": 30, "playstore/groww": 40, "playstore/etmoney": 5,
                   "playstore/paytmmoney": 10, "playstore/indmoney": 10, "playstore/coin": 10},
    "stayed": {"reddit/post": 160, "reddit/comment": 60, "tradingqna/post": 10, "tradingqna/comment": 20,
               "youtube": 25, "blog": 15, "playstore/groww": 10},
}


def ids(path):
    return {json.loads(l)["id"] for l in open(path, encoding="utf-8") if l.strip()} if path.exists() else set()


def main():
    labelled = ids(DATA / "stories_v2.jsonl") | ids(DATA / "stories_detect.jsonl") | ids(DATA / "tags_deep.jsonl")
    pools, seen = {"first_time": {}, "stayed": {}}, Counter()
    for r in map(json.loads, open(DATA / "clean.jsonl", encoding="utf-8")):
        if r["id"] in labelled:
            continue
        t, src = r["text"], r["source"]
        if not (FIRST_PERSON.search(t) or src == "playstore") or not (40 <= len(t) <= 3000):
            continue
        first = len(FIRST_TIME.findall(t)) + len(FIRST_TIME_WIDE.findall(t))
        act, wor, stay = len(ACTION.findall(t)), len(WORRY.findall(t)), len(STAYED.findall(t))
        adv = min(len(ADVICE.findall(t)), 2)
        g = group(r)
        if first and (act or wor or stay):
            s = 4 * min(first, 2) + 2 * min(stay, 2) + min(act, 3) + min(wor, 2) - 2 * adv
            pools["first_time"].setdefault(g, []).append((s, r["id"], first > 0))
            seen["first_time"] += 1
        if stay and (wor or first):
            s = 3 * min(stay, 3) + 2 * min(wor, 2) + 3 * (first > 0) - 2 * adv
            pools["stayed"].setdefault(g, []).append((s, r["id"], first > 0))
            seen["stayed"] += 1

    out, picked = [], set()
    for track in ("first_time", "stayed"):
        for g, items in sorted(pools[track].items()):
            items = sorted((x for x in items if x[1] not in picked), key=lambda x: -x[0])
            keep = items[:CAPS[track].get(g, 0)]
            picked |= {i for _, i, _ in keep}
            out += [dict(id=i, source=g.split("/")[0], group=g, score=s, first_time_signal=f, track=track)
                    for s, i, f in keep]
            if keep:
                print(f"{track:10} {g:22} matched {len(items):>5}  kept {len(keep):>4}  min score {keep[-1][0]}")
    with open(DATA / "candidates_targeted.jsonl", "w", encoding="utf-8") as f:
        for c in out:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"matched: {dict(seen)}; TOTAL kept {len(out)} "
          f"(first_time {sum(c['track'] == 'first_time' for c in out)}, stayed {sum(c['track'] == 'stayed' for c in out)})")


if __name__ == "__main__":
    main()
