"""Question-targeted pre-filter: pick items that answer the brief's THIN questions directly, whether or
not they are drop-off / stayed stories.

Coverage check (23 Oct) on the 720 tagged stories: how often people check had 4 values, expectations 43,
segment fields 44-144 and stay reasons 46. Story detection threw these posts away, because "I check
once a month" or "I'm 24, started with my first salary" is not a stop/stay story. Each track below
targets one question; deep tagging then codes all fields, so action still tells who left and who stayed.

Tracks (an item is kept once, under its best-scoring track):
  checking      Q4  how often / what they check (direct replies in "how often do you check" threads count)
  start_expect  Q1  why they started, what they expected
  journey       Q2  what changed in the months after starting
  who_i_am      Q8  self-description (age, income, family money, who pushed them) + a SIP outcome
  stayed_why    Q7  kept going AND says why

Usage: python pipeline/prefilter_questions.py [chunk_size=60] [--dry] [--tracks=checking,journey]
Writes data/samples/questions_sample.jsonl (stratum Q/<track>) and data/samples/chunks/chunk_qNN.jsonl.
"""
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from prefilter import ACTION, ADVICE, FIRST_PERSON, FIRST_TIME, STAYED, WORRY

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SAMPLES = DATA / "samples"
KEEP = ("id", "source", "app", "kind", "subreddit", "site", "date", "video_title", "thread_title", "text")

TRACKS = {
    # a FREQUENCY phrase is required: plain "xirr" filled wave 1 (q01-q04) with "my XIRR is 8%" posts and
    # gave 4 check_frequency values in 240 items; what they check is already covered by the stories
    "checking": re.compile(
        r"\b(i|we|i'?ve|i used to|main)\b[^.?\n]{0,15}\b(check|checking|checked|look at|looking at|open|opening|refresh|track|monitor|dekh\w*)\b[^.\n]{0,50}"
        r"\b(daily|every ?day|every (single )?(morning|night|week|month|quarter|year|few (days|weeks|months))|weekly|"
        r"monthly|once (a|in a|every)|twice a|hourly|multiple times|many times|again and again|regularly|rarely|"
        r"never|hardly|only (when|on|once)|roz|har (din|hafte|mahine))\b|"
        r"\b(daily|every ?day|once a (week|month|year)|every (morning|month|few months)|rarely|never|hardly ever)\b"
        r"[^.\n]{0,30}\b(check|look at|open the app|track)|"
        r"\b(i|we)\b[^.?\n]{0,15}\b(stopped|don.?t|do not|never|rarely|avoid|quit|not) (checking|looking at|opening|tracking)\b|"
        r"deleted the app|uninstall(ed)? (the )?app|how often|dekhta nahi|dekhti nahi", re.I),
    "start_expect": re.compile(
        r"\b(i|we) (expected|was expecting|thought (i|it|that|sip|mf)|hoped|assumed)\b|expect(ed|ing)? \d+ ?%|"
        r"\b(i|we) (started|began|first invested|chose sip|opted for sip)[^.\n]{0,40}\b(because|so that|for my|to (build|save|create|beat|get)|"
        r"for (retirement|house|marriage|child|education|emergency))|why i (started|invest)|"
        r"(reason|motivation) (i|for|to) (start|invest)|(convinced|told|asked|pushed) me to (start|invest)|"
        r"thought (it|sip|mutual funds?) (would|will)|soch(a|ke) (tha|ki)|umeed", re.I),
    # wave 1 lesson: "initially" / "at first" alone hit unrelated text; a change needs a THEN and a NOW
    "journey": re.compile(
        r"(?s)\b(at first|initially|in the beginning|when i (first )?started|first few months|back then|"
        r"earlier i|i used to|pehle)\b.{0,400}\b(now|these days|nowadays|eventually|gradually|over time|"
        r"later|ab|today i|these months)\b", re.I),
    "who_i_am": re.compile(
        r"\b(1[89]|2\d|3\d|4\d) ?(m|f|yo|y/o|years? old)\b|\bi.?m (1[89]|2\d|3\d|4\d)\b|\bage (1[89]|2\d|3\d)\b|"
        r"first (salary|job|paycheck)|fresher|college student|\bstudent\b|salaried|freelanc|self.?employed|"
        r"business (owner|income)|irregular income|variable (pay|income)|lost my job|job loss|"
        r"(parents|dad|father|mom|mother|family|wife|husband)('s)? (money|savings|told|asked|pushed|started|suggested)|"
        r"(advisor|adviser|agent|relationship manager|\brm\b|distributor|bank (guy|person|manager)|"
        r"youtuber|finfluencer|colleague|friend|cousin|uncle) (told|asked|suggested|recommended|pushed|started|sold)", re.I),
    # wave 1 lesson: "should I continue ... because" is a question, not a stayer; require I + past tense
    "stayed_why": re.compile(
        r"\b(i|we)\b[^.?\n]{0,20}\b(continued|kept (investing|going|my sips?|the sips?)|didn'?t stop|did not stop|"
        r"never stopped|stayed invested|held on|didn'?t pause|didn'?t panic|did not panic|"
        r"(am|have been) still (investing|continuing)|(will|won'?t|am not|'m not) (stop|stopping|pause|pausing)|"
        r"(continue|keep) (my|the|with my) sips?)[^?\n]{0,120}\b(because|since|as|reason|kyunki|kyuki|goal|"
        r"long.?term|horizon|averag|more units|recover|discount|cheap)", re.I),
}
# a reply in a "how often do you check..." thread answers Q4 even without "I check" in it ("once a month")
HOW_OFTEN_THREAD = re.compile(r"how often|how frequently|(stop(ped)?|quit) (checking|looking)|"
                              r"check\w* (your |my )?(portfolio|mf|app|returns?) (daily|every ?day|regularly)", re.I)
TIME_WORD = re.compile(r"\b(daily|every ?day|weekly|monthly|once|twice|never|rarely|hardly|every|month|week|year|"
                       r"quarter|roz|mahine)\b", re.I)
# second cut (23 Oct) aims at what wave 1 left thin: check frequency, change over time, stay reasons
TARGET = {"checking": 300, "start_expect": 150, "journey": 250, "who_i_am": 150, "stayed_why": 200}
# share of each track one source group may take, so Reddit posts don't crowd out everyone else
GROUP_SHARE = {"reddit/post": 0.35, "reddit/comment": 0.35, "tradingqna/post": 0.08, "tradingqna/comment": 0.12,
               "youtube": 0.15, "blog": 0.10, "appstore": 0.08, "playstore": 0.08}


def group(r):
    if r["source"] in ("reddit", "tradingqna"):
        return f"{r['source']}/{r.get('kind', 'post')}"
    return r["source"]


def ids(path):
    return {json.loads(l)["id"] for l in open(path, encoding="utf-8") if l.strip()} if path.exists() else set()


def main():
    dry = "--dry" in sys.argv  # print pool sizes only
    only = {t for a in sys.argv[1:] if a.startswith("--tracks=") for t in a[9:].split(",")}  # e.g. --tracks=checking
    args = [a for a in sys.argv[1:] if a != "--dry" and not a.startswith("--tracks=")]
    size = int(args[0]) if args else 60
    taken = ids(DATA / "tags_deep.jsonl") | ids(SAMPLES / "questions_sample.jsonl")
    pools = defaultdict(list)
    rows = [json.loads(l) for l in open(DATA / "clean.jsonl", encoding="utf-8")]
    titles = {r["id"]: r["text"].split("\n", 1)[0][:200] for r in rows if r.get("kind") == "post"}
    for r in rows:
        if r.get("parent") in titles:  # a reply like "once a month" needs the thread's question
            r["thread_title"] = titles[r["parent"]]
        t = r["text"]
        if r["id"] in taken or not (40 <= len(t) <= 3000):
            continue
        reply_to_check_thread = bool(HOW_OFTEN_THREAD.search(r.get("thread_title", "")) and TIME_WORD.search(t))
        if not (FIRST_PERSON.search(t) or r["source"] in ("playstore", "appstore") or reply_to_check_thread):
            continue
        adv = min(len(ADVICE.findall(t)), 2)
        outcome = len(ACTION.findall(t)) + len(STAYED.findall(t)) + len(WORRY.findall(t))
        first = len(FIRST_TIME.findall(t))
        best = None
        for track, rx in TRACKS.items():
            hits = len(rx.findall(t)) + (2 if track == "checking" and reply_to_check_thread else 0)
            if not hits or (track == "who_i_am" and not outcome):  # segments only help if linked to an outcome
                continue
            s = 3 * min(hits, 3) + 2 * min(first, 2) + min(outcome, 3) - 2 * adv + (1 if 150 <= len(t) <= 1500 else 0)
            if best is None or s > best[1]:
                best = (track, s)
        if best:
            pools[best[0]].append((best[1], r))

    picked = []
    for track, pool in pools.items():
        if only and track not in only:
            continue
        pool.sort(key=lambda x: -x[0])
        per_group, chosen = Counter(), []
        for s, r in pool:
            g = group(r)
            if per_group[g] < TARGET[track] * GROUP_SHARE.get(g, 0.1) and len(chosen) < TARGET[track]:
                per_group[g] += 1
                chosen.append(r)
        for s, r in pool:  # fill the rest from any group, best score first
            if len(chosen) >= TARGET[track]:
                break
            if r not in chosen:
                chosen.append(r)
        print(f"{track:13} pool {len(pool):>6}  kept {len(chosen):>4}  {dict(Counter(group(r) for r in chosen))}")
        picked += [(track, r) for r in chosen]
    if dry:
        return
    random.Random(23).shuffle(picked)  # every chunk gets a mix of tracks and sources

    existing = sorted((SAMPLES / "chunks").glob("chunk_q*.jsonl"))
    next_no = len(existing) + 1
    with open(SAMPLES / "questions_sample.jsonl", "a", encoding="utf-8") as meta:
        for i in range(0, len(picked), size):
            name = f"chunk_q{next_no:02d}.jsonl"
            with open(SAMPLES / "chunks" / name, "w", encoding="utf-8") as f:
                for track, r in picked[i:i + size]:
                    f.write(json.dumps({k: r[k] for k in KEEP if k in r}, ensure_ascii=False) + "\n")
                    meta.write(json.dumps({**r, "stratum": f"Q/{track}", "weight": None, "chunk": name},
                                          ensure_ascii=False) + "\n")
            next_no += 1
    print(f"TOTAL {len(picked)} items in {next_no - 1 - len(existing)} chunks of {size}")


if __name__ == "__main__":
    main()
