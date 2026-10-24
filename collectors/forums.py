"""Collect SIP discussions from TradingQ&A (Zerodha's Discourse forum) and comments on two
Indian personal-finance blogs (Jagoinvestor, Freefincal) via the WordPress REST API.
No account or key needed. Crash-safe: rows are appended as fetched, reruns skip done work.

Usage: python collectors/forums.py [blogs]
Writes data/raw/tradingqna.jsonl and data/raw/blogs.jsonl.
"""
import html
import json
import re
import time

import requests

from playstore import RAW

H = {"User-Agent": "Mozilla/5.0 (research; nextleap-sip-discovery/0.1)"}
QUERIES = [
    "stopped sip", "stop sip", "pause sip", "cancel sip", "skip sip", "sip mandate", "sip bounce",
    "sip failed", "first sip", "sip negative returns", "continue sip", "sip loss", "reduce sip",
    "beginner mutual fund", "sip not deducted", "redeem mutual fund", "sip autopay",
]
BLOGS = {"jagoinvestor": "https://www.jagoinvestor.com", "freefincal": "https://freefincal.com",
         # added 23 Oct: reader Q&A blogs where people describe themselves (age, salary, first SIP)
         "basunivesh": "https://www.basunivesh.com", "stableinvestor": "https://stableinvestor.com"}
BLOG_TERMS = ["sip", "stopped", "pause", "mutual fund", "redeem",
              # added 23 Oct for the thin brief questions: expectations, checking, first year, who I am
              "expected", "check", "first salary", "started investing", "my age", "years old"]
MAX_POSTS_PER_TOPIC = 20


def clean_html(s: str) -> str:
    s = re.sub(r"<blockquote.*?</blockquote>", " ", s, flags=re.S)  # drop quoted replies
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def get_json(url, params=None):
    for attempt in range(6):
        try:
            r = requests.get(url, params=params, headers=H, timeout=60)
            if r.status_code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            if r.status_code in (400, 404):
                return None
            r.raise_for_status()
            time.sleep(1)
            return r.json()
        except Exception:
            time.sleep(10 * (attempt + 1))
    return None


def tradingqna():
    out = RAW / "tradingqna.jsonl"
    done = {json.loads(l)["topic_id"] for l in open(out, encoding="utf-8")} if out.exists() else set()
    topics = set()
    for q in QUERIES:
        for page in (1, 2, 3):
            j = get_json("https://tradingqna.com/search.json", {"q": q, "page": page})
            if not j or not j.get("topics"):
                break
            topics |= {t["id"] for t in j["topics"]}
    todo = sorted(topics - done)
    print(f"tradingqna: {len(topics)} topics found, {len(todo)} to fetch", flush=True)
    with open(out, "a", encoding="utf-8") as f:
        for n, tid in enumerate(todo, 1):
            j = get_json(f"https://tradingqna.com/t/{tid}.json")
            if not j:
                continue
            posts = j.get("post_stream", {}).get("posts", [])[:MAX_POSTS_PER_TOPIC]
            first_id = f"tq_{posts[0]['id']}" if posts else None
            for i, p in enumerate(posts):
                text = clean_html(p.get("cooked", ""))
                if i == 0:
                    text = f"{j.get('title', '')}\n{text}"
                f.write(json.dumps({
                    "id": f"tq_{p['id']}", "source": "tradingqna", "kind": "post" if i == 0 else "comment",
                    "topic_id": tid, "parent": None if i == 0 else first_id, "text": text,
                    "date": p.get("created_at"), "likes": p.get("like_count", 0),
                    "url": f"https://tradingqna.com/t/{j.get('slug', '')}/{tid}/{p.get('post_number', 1)}",
                }, ensure_ascii=False) + "\n")
            f.flush()
            if n % 50 == 0:
                print(f"  tradingqna topics {n}/{len(todo)}", flush=True)


def blogs():
    out = RAW / "blogs.jsonl"
    seen = {json.loads(l)["id"] for l in open(out, encoding="utf-8")} if out.exists() else set()
    with open(out, "a", encoding="utf-8") as f:
        for site, base in BLOGS.items():
            kept = 0
            for term in BLOG_TERMS:
                for page in range(1, 21):  # up to 2,000 comments per term
                    j = get_json(f"{base}/wp-json/wp/v2/comments",
                                 {"search": term, "per_page": 100, "page": page})
                    if not j:
                        break
                    for c in j:
                        cid = f"bl_{site}_{c['id']}"
                        if cid in seen:
                            continue
                        seen.add(cid)
                        f.write(json.dumps({
                            "id": cid, "source": "blog", "site": site, "kind": "comment",
                            "text": clean_html(c.get("content", {}).get("rendered", "")),
                            "date": c.get("date"), "url": c.get("link"), "post_id": c.get("post"),
                        }, ensure_ascii=False) + "\n")
                        kept += 1
                    f.flush()
                    if len(j) < 100:
                        break
            print(f"blog {site}: {kept} new comments", flush=True)


if __name__ == "__main__":
    import sys
    if "blogs" not in sys.argv[1:]:  # `python collectors/forums.py blogs` runs the blogs only
        tradingqna()
    blogs()
    print("DONE", flush=True)
