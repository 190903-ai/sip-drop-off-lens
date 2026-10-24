"""Pull full comment threads for Reddit posts that ask the brief's thin questions directly.

The first Reddit pass only fetched the top 25 comments of stop/continue posts, so threads like
"How often do you check your portfolio?" or "What made you start your first SIP?" were missed, and
those threads are made of direct answers. Posts are picked from every data/raw/reddit_*_posts.jsonl
by question-shaped titles (checking habits, expectations and motivation, first-year journeys,
self-descriptions: age, first salary, family money, who influenced them).

Arctic Shift's full-text search times out, so threads are fetched by post id (reliable).
Crash-safe: a rerun skips threads already fetched.

Usage: python collectors/reddit_threads.py
Writes data/raw/reddit_threads_comments.jsonl.
"""
import json
import re

from playstore import RAW
from reddit import get, read_jsonl, ts

QUESTION_PATTERNS = {
    "checking": r"how often|check(ing|ed)? (my |your |the )?(portfolio|returns?|mf|funds?|sips?|app|nav|xirr)|"
                r"(stop(ped)?|quit|don.?t|avoid) (checking|looking)|xirr|returns? (showing|look|is showing)|"
                r"daily (check|look)|every ?day",
    "start_expect": r"why (did )?(you|u|people) (start|invest)|what made (you|u)|reason.{0,20}(start|invest)|"
                    r"motivat|expect(ed|ation|ing)?|what returns|realistic return|disappoint",
    "journey": r"\b(\d+|one|two|three|six|nine|few) (years?|months?) (of|into|since|after)|journey|"
               r"(sip|mf|investment|portfolio) (update|review|experience)|lessons|looking back|"
               r"still (continuing|investing)|(stopped|quit|gave up|continued|kept) (my )?(sip|investing)|"
               r"beginner|first (sip|investment|year|time)|newbie|new to",
    "who_i_am": r"\b\d\d ?(m|f|yo|y/?o|years? old)\b|\bi.?m \d\d\b|first (salary|job|paycheck)|fresher|"
                r"\bstudent|salaried|freelanc|self.?employed|business owner|(parents|dad|father|mom|mother|family)|"
                r"advisor|agent|relationship manager|distributor|youtube|finfluencer|colleague|friend",
}
PATTERNS = {k: re.compile(v, re.I) for k, v in QUESTION_PATTERNS.items()}
MIN_COMMENTS = 3
MAX_THREADS = 2400  # 1800 first pass + room for the habit posts found by `reddit.py habits`
COMMENTS_PER_THREAD = 100


def main():
    posts = [p for f in sorted(RAW.glob("reddit_*_posts.jsonl")) for p in read_jsonl(f)]
    picked = []
    for p in posts:
        title = p["text"].split("\n", 1)[0]
        hits = [k for k, rx in PATTERNS.items() if rx.search(title)]
        if hits and p.get("num_comments", 0) >= MIN_COMMENTS:
            picked.append((p, hits))
    # prefer the gap questions (checking, expectations) over the broad ones, then busier threads
    rank = {"checking": 0, "start_expect": 1, "who_i_am": 2, "journey": 3}
    picked.sort(key=lambda x: (min(rank[h] for h in x[1]), -x[0]["num_comments"]))
    picked = picked[:MAX_THREADS]
    print("picked by question:", {k: sum(k in h for _, h in picked) for k in PATTERNS}, flush=True)

    out = RAW / "reddit_threads_comments.jsonl"
    done_path = RAW / "reddit_threads_done.txt"
    done = set(done_path.read_text().split()) if done_path.exists() else set()
    todo = [(p, h) for p, h in picked if p["id"] not in done]
    print(f"threads: {len(picked)} picked, {len(todo)} remaining", flush=True)
    with open(out, "a", encoding="utf-8") as f, open(done_path, "a") as d:
        for i, (p, hits) in enumerate(todo, 1):
            pid = p["id"].removeprefix("rd_")
            try:
                comments = get("comments/search", {"link_id": pid, "limit": 100})
            except RuntimeError:
                continue
            comments = sorted(comments, key=lambda c: c.get("score", 0), reverse=True)
            for c in comments[:COMMENTS_PER_THREAD]:
                text = c.get("body", "")
                if len(text) < 40 or text in ("[removed]", "[deleted]"):
                    continue
                f.write(json.dumps({
                    "id": f"rd_{c['id']}", "source": "reddit", "subreddit": p["subreddit"],
                    "kind": "comment", "text": text, "score": c.get("score", 0),
                    "date": ts(c["created_utc"]), "parent": p["id"], "thread_question": hits,
                    "url": f"https://reddit.com/comments/{pid}/_/{c['id']}",
                }, ensure_ascii=False) + "\n")
            f.flush()
            d.write(p["id"] + "\n")
            d.flush()
            if i % 100 == 0:
                print(f"  threads: {i}/{len(todo)}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
