"""Keyword pre-filter: pick ~2,000 story candidates from the clean corpus before any AI sees them.

The Gemma detector spent its budget on all 53k items, most of them advice posts, at ~50 items/hour.
This filter is built for RECALL, not precision: an item passes when the writer speaks in the first
person AND mentions an SIP action (stop, pause, continue, step up...) or a loss/worry. Advice posts
may pass; the detector removes them. Candidates are then ranked, with first-time-investor signals
weighted highest (the brief is about first-time investors), and capped per source so no single
source (Reddit by volume, ET Money by one pricing event) dominates.

Usage: python pipeline/prefilter.py
Writes data/candidates.jsonl and prints recall on the stories the old Gemma detector already found.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIRST_PERSON = re.compile(
    r"\b(i|i'm|im|i've|ive|i'd|my|me|mine|myself|maine|meine|mera|meri|mere|mujhe|mujhko|humne|hamara|"
    r"karu|karun|kiya|kar diya|kar di|kar deta|kar raha|rakha|liya)\b|^\W*(stopped|paused|cancell?ed|redeemed)", re.I)
ACTION = re.compile(
    r"\bstop|\bpaus|\bskip|cancel|discontinu|\bredeem|withdr[ae]w|\bexit|\bquit|band kar|band kr|band ho|"
    r"\brok |\bruk|bounce|fail|not deducted|missed|\bcontinu|kept (going|investing|my)|still investing|"
    r"didn'?t stop|did not stop|step[- ]?up|increased? my|\bhold(ing)?\b|sell(ing)? (all|my)|\bsold\b|"
    r"not working|unable|not able|deducted|\bswitch|migrat|charges?\b", re.I)
WORRY = re.compile(
    r"\bloss|negative|in (the )?red|\bminus|\bdown\b|fall(en|ing)?\b|crash|correction|worr|scar|panic|"
    r"regret|frustrat|confus|doubt|nervous|stress|ghata|nuksan|nuksaan|dar lag", re.I)
FIRST_TIME = re.compile(
    r"first (ever )?sip|my first (mutual|mf|investment)|first time invest|new to (investing|mutual|mf|sip|the market)|"
    r"\bbeginner|\bnewbie|\bnoob\b|just started|recently started|started (investing |my sips? |a sip )?"
    r"(\d+|a few|few|six|three|two|last) (month|months|year)|started (in|last) (20(24|25|26)|year|month)|"
    r"pehli baar|abhi shuru|naya (hu|hoon)|naye investor|fresher|first job|first salary", re.I)
ADVICE = re.compile(
    r"\byou should|\bi('d| would) suggest|\bi suggest|i recommend|my advice|\bop should|\bdon'?t stop\b|"
    r"\bkeep investing\b|check out|\bdm me|join (my|our)|telegram", re.I)

# Target candidates per source group (~2,000 in total). ET Money is capped low: one pricing event
# already supplied half the stories found so far.
CAPS = {
    "reddit/post": 450, "reddit/comment": 300, "tradingqna/post": 120, "tradingqna/comment": 280,
    "youtube": 300, "blog": 150, "playstore/groww": 400, "playstore/etmoney": 40,
    "playstore/paytmmoney": 80, "playstore/indmoney": 80, "playstore/coin": 80,
}
# Second track for STAYED stories (the control group): the main ranking favours stop words, and the
# first 400 labels held only 10 stayed stories (2.5%). Extra candidates per group, not in the main pick.
STAYED = re.compile(
    r"continu(e|ed|ing) (my|the|with|to invest|investing|sip)|still (investing|continuing|running|doing)|"
    r"didn'?t stop|did not stop|not stopp(ed|ing)|won'?t stop|never stopped|kept (investing|going|my|the sip)|"
    r"stay(ed|ing) invested|held on|holding on|step(ped)?[- ]?up|increas(ed|ing) (my|the) sip|doubled my sip|"
    r"restart(ed)?|resum(ed|ing)|bought (the|more|on) dips?|chalu rakh|band nahi|jaari rakh", re.I)
# Third track: forum / YouTube voices that name Groww (the product we design for). Play Store reviews
# are almost all complaints and rarely say whether the writer is new; Reddit/forum Groww users are
# often beginners and tell fuller stories.
GROWW = re.compile(r"\bgroww\b", re.I)
GROWW_CAPS = {"reddit/post": 100, "reddit/comment": 60, "tradingqna/post": 15, "tradingqna/comment": 15,
              "youtube": 30}
STAYED_CAPS = {"reddit/post": 120, "reddit/comment": 120, "tradingqna/post": 20, "tradingqna/comment": 60,
               "youtube": 60, "blog": 40, "playstore/groww": 30}


def group(r):
    if r["source"] == "playstore":
        return f"playstore/{r.get('app', 'groww')}"
    if r["source"] in ("reddit", "tradingqna"):
        return f"{r['source']}/{r.get('kind', 'post')}"
    return r["source"]


def score(text, source=""):
    """(passes, score, first_time_signal). Recall-first: pass = first person + action or worry.
    Play Store reviews are first-person by nature, so they skip the pronoun check."""
    fp, act, wor = FIRST_PERSON.search(text), len(ACTION.findall(text)), len(WORRY.findall(text))
    first = bool(FIRST_TIME.search(text))
    passes = (bool(fp) or source == "playstore") and (act > 0 or wor > 0)
    s = 2 * min(act, 3) + min(wor, 2) + 4 * first - 2 * min(len(ADVICE.findall(text)), 2)
    s += 1 if 120 <= len(text) <= 2000 else 0  # long enough to explain why, short enough to be one story
    return passes, s, first


def ids(path):
    return {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()


def main():
    data = ROOT / "data"
    tagged = {x for p in (data / "tags_deep").glob("chunk_*.jsonl") for x in ids(p)}
    old = {}
    if (data / "stories_detect.jsonl").exists():
        old = {x["id"]: x for x in map(json.loads, open(data / "stories_detect.jsonl", encoding="utf-8"))}
    known = {i for i, x in old.items() if x.get("story") == "yes"}

    pools, stayed_pools, groww_pools, recall = {}, {}, {}, Counter()
    for r in map(json.loads, open(data / "clean.jsonl", encoding="utf-8")):
        passes, s, first = score(r["text"], r["source"])
        if r["id"] in known:
            recall["known"] += 1
            recall["known_pass"] += passes
            continue  # already found as drop-off stories: they go straight to tagging
        if r["id"] in tagged:
            continue
        g = group(r)
        if passes:
            pools.setdefault(g, []).append((s, first, r))
        hits = len(STAYED.findall(r["text"]))
        if hits and (FIRST_PERSON.search(r["text"]) or r["source"] == "playstore"):
            stayed_pools.setdefault(g, []).append((2 * min(hits, 3) + 4 * first + min(len(WORRY.findall(r["text"])), 2), first, r))
        if r["source"] != "playstore" and GROWW.search(r["text"]) and (passes or hits):
            groww_pools.setdefault(g, []).append((s + 2 * min(hits, 2), first, r))

    out, report = [], []
    for g, items in sorted(pools.items()):
        items.sort(key=lambda x: -x[0])
        keep = items[:CAPS.get(g, 100)]
        out += [dict(id=r["id"], source=r["source"], group=g, score=s, first_time_signal=first) for s, first, r in keep]
        report.append(f"{g:22} passed {len(items):>6}  kept {len(keep):>4}  "
                      f"first-time signal {sum(f for _, f, _ in keep):>4}  min score {keep[-1][0] if keep else '-'}")
    picked = {c["id"] for c in out}
    for g, items in sorted(stayed_pools.items()):
        items = sorted((x for x in items if x[2]["id"] not in picked), key=lambda x: -x[0])
        keep = items[:STAYED_CAPS.get(g, 0)]
        out += [dict(id=r["id"], source=r["source"], group=g, score=s, first_time_signal=first, track="stayed")
                for s, first, r in keep]
        if keep:
            report.append(f"{'stayed ' + g:22} matched {len(items):>5}  kept {len(keep):>4}")
    picked = {c["id"] for c in out}
    for g, items in sorted(groww_pools.items()):
        items = sorted((x for x in items if x[2]["id"] not in picked), key=lambda x: -x[0])
        keep = items[:GROWW_CAPS.get(g, 0)]
        out += [dict(id=r["id"], source=r["source"], group=g, score=s, first_time_signal=first, track="groww")
                for s, first, r in keep]
        if keep:
            report.append(f"{'groww ' + g:22} matched {len(items):>5}  kept {len(keep):>4}  "
                          f"first-time signal {sum(f for _, f, _ in keep):>4}")
    with open(data / "candidates.jsonl", "w", encoding="utf-8") as f:
        for c in out:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print("\n".join(report))
    print(f"TOTAL candidates {len(out)}, with first-time signal {sum(c['first_time_signal'] for c in out)}")
    if recall["known"]:
        print(f"recall on {recall['known']} known drop-off stories: {recall['known_pass']} pass "
              f"({recall['known_pass'] / recall['known']:.0%})")


if __name__ == "__main__":
    main()
