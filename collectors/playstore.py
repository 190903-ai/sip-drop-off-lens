"""Collect Play Store reviews (Groww by default, or a competitor) and keep SIP / MF ones.

Usage: python collectors/playstore.py [max_reviews] [app_id app_name]
Groww writes data/raw/playstore.jsonl (all) and data/raw/playstore_sip.jsonl (SIP-relevant);
a competitor writes data/raw/playstore_<app_name>.jsonl with only SIP-relevant reviews.
"""
import json
import re
import sys
from pathlib import Path

from google_play_scraper import Sort, reviews

APP_ID = "com.nextbillion.groww"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# Keyword filter for SIP / first-time MF relevance (English + common Hinglish)
SIP_PATTERN = re.compile(
    r"\bsip\b|sips\b|mutual fund|\bmf\b|mandate|autopay|auto[- ]?pay|instal+ment|"
    r"nav\b|xirr|returns?\b|redeem|redemption|pause|step[- ]?up|lumpsum|"
    r"first time invest|beginner|new investor|portfolio",
    re.IGNORECASE,
)


def collect(max_reviews: int, app_id: str = APP_ID, app_name: str = "groww", score=None) -> list[dict]:
    out, token = [], None
    while len(out) < max_reviews:
        batch, token = reviews(
            app_id, lang="en", country="in", sort=Sort.NEWEST, filter_score_with=score,
            count=min(200, max_reviews - len(out)), continuation_token=token,
        )
        if not batch:
            break
        for r in batch:
            out.append({
                "id": f"ps_{r['reviewId']}",
                "source": "playstore",
                "app": app_name,
                "text": r["content"] or "",
                "rating": r["score"],
                "date": r["at"].isoformat() if r.get("at") else None,
                "thumbs_up": r.get("thumbsUpCount", 0),
                "app_version": r.get("reviewCreatedVersion"),
            })
        print(f"  fetched {len(out)}", flush=True)
        if token is None:
            break
    return out


def main():
    max_reviews = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    RAW.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 3:  # competitor app: keep only SIP-relevant reviews
        app_id, app_name = sys.argv[2], sys.argv[3]
        rows = collect(max_reviews, app_id, app_name)
        sip_rows = [r for r in rows if len(r["text"]) >= 25 and SIP_PATTERN.search(r["text"])]
        with open(RAW / f"playstore_{app_name}.jsonl", "w", encoding="utf-8") as f:
            for r in sip_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{app_name}: total={len(rows)} sip_relevant={len(sip_rows)}")
        return
    rows = collect(max_reviews)
    sip_rows = [r for r in rows if len(r["text"]) >= 25 and SIP_PATTERN.search(r["text"])]
    for name, data in (("playstore.jsonl", rows), ("playstore_sip.jsonl", sip_rows)):
        with open(RAW / name, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"total={len(rows)} sip_relevant={len(sip_rows)}")


if __name__ == "__main__":
    main()
