"""Step 2: merge raw sources, dedupe, drop junk, apply strict SIP filter, tag language.

Usage: python pipeline/clean.py
Reads data/raw/*.jsonl, writes data/clean.jsonl and data/funnel.json (volume per stage).
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

SOURCES = {  # file -> source label
    "playstore.jsonl": "playstore",
    "playstore_groww_sip_deep.jsonl": "playstore",  # older Groww SIP reviews, walked by star rating
    "reddit_y1_posts.jsonl": "reddit",
    "reddit_y1_comments.jsonl": "reddit",
    "reddit_y2_posts.jsonl": "reddit",
    "reddit_y2_comments.jsonl": "reddit",
    "youtube.jsonl": "youtube",
    # competitor apps' Play Store reviews (only SIP-relevant ones are saved), field "app" names the app
    "playstore_etmoney.jsonl": "playstore",
    "playstore_paytmmoney.jsonl": "playstore",
    "playstore_indmoney.jsonl": "playstore",
    "playstore_coin.jsonl": "playstore",
    "tradingqna.jsonl": "tradingqna",
    "blogs.jsonl": "blog",
    # 23 Oct pull for the brief's thin questions (posts before comments, so threads inherit relevance)
    "reddit_y0_posts.jsonl": "reddit",  # Oct 2022 - Sep 2024, same four subreddits
    "reddit_y0_comments.jsonl": "reddit",
    "reddit_wide_posts.jsonl": "reddit",  # developersIndia, IndianStreetBets, StockMarketIndia
    "reddit_wide_comments.jsonl": "reddit",
    "reddit_habits_posts.jsonl": "reddit",  # investing-habit posts (checking, first salary); no SIP words by design
    "reddit_threads_comments.jsonl": "reddit",  # full threads for checking / expectation / who-I-am questions
    "appstore_sip.jsonl": "appstore",  # iOS reviews, six apps (feed worked again on 23 Oct)
}
# Stricter than the collectors' filter: must actually be about SIPs / mutual funds
STRICT_SIP = re.compile(
    r"\bsips?\b|mutual ?funds?|\bmfs?\b|mandate|auto ?pay|e-?nach|instal+ments?|"
    r"\bnav\b|step[- ]?up|lump ?sum|elss|index fund|flexi ?cap|small ?cap fund|"
    r"म्यूचुअल|एसआईपी",
    re.IGNORECASE,
)
JUNK = {"[removed]", "[deleted]"}
# Files whose collector already applied its own topic filter (HABIT_PATTERN in reddit.py); skip STRICT_SIP
TOPIC_FILTERED = {"reddit_habits_posts.jsonl"}
HINGLISH = re.compile(r"\b(hai|nahi|kya|kaise|karu|kar|paisa|mera|mere|kyu|bhai|hoga|tha|raha|chahiye)\b", re.I)
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def language(text: str) -> str:
    if len(DEVANAGARI.findall(text)) > 10:
        return "hindi"
    if len(HINGLISH.findall(text)) >= 2:
        return "hinglish"
    return "english"


def fingerprint(text: str) -> str:
    norm = re.sub(r"[^a-z0-9ऀ-ॿ]+", "", text.lower())[:400]
    return hashlib.md5(norm.encode()).hexdigest()


def main():
    funnel = Counter()
    seen_ids, seen_fp, out = set(), set(), []
    sip_posts = set()  # Reddit comments inherit relevance from their parent post
    for fname, src in SOURCES.items():
        path = RAW / fname
        if not path.exists():
            print(f"missing {fname}, skipping")
            continue
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            funnel[f"{src}:raw"] += 1
            text = (r.get("text") or "").strip()
            if text in JUNK or len(text) < 50:
                continue
            funnel[f"{src}:not_junk"] += 1
            if not (fname in TOPIC_FILTERED or STRICT_SIP.search(text) or r.get("parent") in sip_posts):
                continue
            if r.get("kind") == "post":
                sip_posts.add(r["id"])
            funnel[f"{src}:sip_filter"] += 1
            fp = fingerprint(text)
            if r["id"] in seen_ids or fp in seen_fp:
                continue
            seen_ids.add(r["id"])
            seen_fp.add(fp)
            funnel[f"{src}:deduped"] += 1
            r["source"] = src
            if src == "playstore":
                r.setdefault("app", "groww")
            r["lang"] = language(text)
            r["text"] = text[:3000]  # cap very long posts; long-tail rarely changes tags
            out.append(r)

    with open(ROOT / "data" / "clean.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(ROOT / "data" / "funnel.json", "w") as f:
        json.dump(dict(funnel), f, indent=2)
    for k in sorted(funnel):
        print(f"{k:28} {funnel[k]:>7}")
    print("languages:", Counter(r["lang"] for r in out))
    print("kinds:", Counter(f"{r['source']}/{r.get('kind', '-')}" for r in out))
    print(f"TOTAL clean = {len(out)}")


if __name__ == "__main__":
    main()
