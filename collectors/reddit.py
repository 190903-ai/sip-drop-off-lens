"""Collect SIP-related Reddit posts + comments from Indian investing subreddits.

Reddit blocks unauthenticated API access, so this uses the Arctic Shift public
Reddit archive (https://arctic-shift.photon-reddit.com). No account or key needed.

Strategy: list every post in each subreddit over the window (date-range listing is
fast; full-text search times out), keep SIP-relevant posts locally, then fetch
comments for the most-discussed posts about starting / stopping / continuing a SIP.

Crash-safe: every row is appended to disk as it is fetched, and a rerun resumes
where the last run stopped.

Usage: python collectors/reddit.py <tag> <after=YYYY-MM-DD> <before=YYYY-MM-DD> [sub1,sub2,...]
Writes data/raw/reddit_<tag>_posts.jsonl and data/raw/reddit_<tag>_comments.jsonl.
"""
import json
import re
import sys
import time
from datetime import datetime, timezone

import requests

from playstore import RAW, SIP_PATTERN

API = "https://arctic-shift.photon-reddit.com/api"
SUBREDDITS = ["mutualfunds", "IndiaInvestments", "personalfinanceindia", "FIREIndia"]
# Posts worth pulling comments for: the continuation / drop-off conversations
CONTINUATION_PATTERN = re.compile(
    r"stop|pause|cancel|discontinu|continue|negative|loss|red\b|first sip|started|"
    r"beginner|new to|worth it|should i|regret|bounce|missed|reduce|skip|"
    r"band kar|ruk|job|salary|emergency|withdraw|redeem",
    re.IGNORECASE,
)
# Investing-habit posts that never say "SIP" / "mutual fund" ("How often do you check your portfolio?",
# "Invested my first salary") were dropped by SIP_PATTERN; they answer the brief's checking, expectation
# and motivation questions (23 Oct). Their comment threads are pulled by reddit_threads.py.
HABIT_PATTERN = re.compile(
    r"how often|how frequently|(check|checking|checked|look at|looking at|track|tracking|open|opening)\w* "
    r"(my |your |the )?(portfolio|investments?|returns?|xirr|app|groww|coin|kite)|stop(ped)? (checking|looking)|"
    r"first (salary|paycheck|investment)|started investing|start(ed)? my investment journey|"
    r"why (did )?(you|u) (start|invest)|what made you (start|invest)|expected returns?|what returns|"
    r"(1|one|2|two|3|three|5|five) years? of investing|investing journey",
    re.IGNORECASE,
)
MIN_COMMENTS = 5
MAX_COMMENT_POSTS = 2500  # most-discussed first
COMMENTS_PER_POST = 25


def ts(utc: float) -> str:
    return datetime.fromtimestamp(utc, tz=timezone.utc).isoformat()


def get(path: str, params: dict) -> list[dict]:
    for attempt in range(10):
        try:
            body = requests.get(f"{API}/{path}", params=params, timeout=90).json()
            if not body.get("error"):
                time.sleep(0.5)
                return body["data"]
        except Exception:
            pass  # network blips / bad JSON: back off and retry
        time.sleep(min(120, 10 * (attempt + 1)))
    raise RuntimeError(f"failed: {path} {params}")


def read_jsonl(path) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8")] if path.exists() else []


def collect_posts(tag: str, after: str, before: str):
    out = RAW / f"reddit_{tag}_posts.jsonl"
    state_path = RAW / f"reddit_{tag}_state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    with open(out, "a", encoding="utf-8") as f:
        for sub in SUBREDDITS:
            if state.get(sub) == "done":
                continue
            cursor = state.get(sub, after)
            scanned = 0
            while True:
                batch = get("posts/search", {"subreddit": sub, "after": cursor, "before": before,
                                             "limit": 100, "sort": "asc"})
                for p in batch:
                    scanned += 1
                    body = f"{p.get('title', '')}\n{p.get('selftext') or ''}".strip()
                    if p.get("selftext") in ("[removed]", "[deleted]") and len(p.get("title", "")) < 40:
                        continue
                    keep = HABIT_PATTERN.search(body[:600]) if tag == "habits" else (
                        SIP_PATTERN.search(body) or HABIT_PATTERN.search(body[:600]))
                    if not keep:
                        continue
                    f.write(json.dumps({
                        "id": f"rd_{p['id']}", "source": "reddit", "subreddit": sub, "kind": "post",
                        "text": body, "score": p.get("score", 0), "date": ts(p["created_utc"]),
                        "num_comments": p.get("num_comments", 0),
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                    }, ensure_ascii=False) + "\n")
                f.flush()
                if len(batch) < 100:
                    state[sub] = "done"
                else:
                    cursor = state[sub] = str(int(batch[-1]["created_utc"]) + 1)
                state_path.write_text(json.dumps(state))
                if scanned % 2000 < 100:
                    print(f"  r/{sub}: scanned {scanned}", flush=True)
                if state[sub] == "done":
                    print(f"r/{sub}: done ({scanned} scanned this run)", flush=True)
                    break


def collect_comments(tag: str):
    posts = read_jsonl(RAW / f"reddit_{tag}_posts.jsonl")
    targets = [p for p in posts if p["num_comments"] >= MIN_COMMENTS and CONTINUATION_PATTERN.search(p["text"])]
    targets = sorted(targets, key=lambda p: p["num_comments"], reverse=True)[:MAX_COMMENT_POSTS]
    out = RAW / f"reddit_{tag}_comments.jsonl"
    done_path = RAW / f"reddit_{tag}_comments_done.txt"
    done = set(done_path.read_text().split()) if done_path.exists() else set()
    todo = [p for p in targets if p["id"] not in done]
    print(f"comments: {len(targets)} target posts, {len(todo)} remaining", flush=True)
    with open(out, "a", encoding="utf-8") as f, open(done_path, "a") as d:
        for i, p in enumerate(todo, 1):
            pid = p["id"].removeprefix("rd_")
            try:
                comments = get("comments/search", {"link_id": pid, "limit": 100})
            except RuntimeError:
                continue
            comments = sorted(comments, key=lambda c: c.get("score", 0), reverse=True)
            for c in comments[:COMMENTS_PER_POST]:
                text = c.get("body", "")
                if len(text) < 40 or text in ("[removed]", "[deleted]"):
                    continue
                f.write(json.dumps({
                    "id": f"rd_{c['id']}", "source": "reddit", "subreddit": p["subreddit"],
                    "kind": "comment", "text": text, "score": c.get("score", 0),
                    "date": ts(c["created_utc"]), "parent": p["id"],
                    "url": f"https://reddit.com/comments/{pid}/_/{c['id']}",
                }, ensure_ascii=False) + "\n")
            f.flush()
            d.write(p["id"] + "\n")
            d.flush()
            if i % 100 == 0:
                print(f"  comments: {i}/{len(todo)}", flush=True)


def main():
    global SUBREDDITS
    tag, after, before = sys.argv[1], sys.argv[2], sys.argv[3]
    if len(sys.argv) > 4:  # optional comma-separated subreddits, e.g. for the 23 Oct wider pull
        SUBREDDITS = sys.argv[4].split(",")
    collect_posts(tag, after, before)
    if tag != "habits":  # habit posts get full threads from reddit_threads.py instead
        collect_comments(tag)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
