"""Targeted Groww pull: the default pull (20k newest) is mostly stock/F&O reviews and only reaches
back a few weeks, so it held no Groww SIP drop-off stories. This walks each star rating separately
(1-5), which reaches much further back, and keeps only SIP / mutual fund / mandate / autopay reviews.

Usage: python collectors/playstore_groww_deep.py [max_per_star]
Writes data/raw/playstore_groww_sip_deep.jsonl (deduplicated with the default pull in clean.py).
"""
import json
import re
import sys

from playstore import RAW, collect

GROWW_SIP = re.compile(
    r"\bsip\b|sips\b|mutual fund|\bmf\b|mandate|autopay|auto[- ]?pay|instal+ment|"
    r"redeem|redemption|step[- ]?up|lumpsum|nav\b|xirr",
    re.IGNORECASE,
)


def main():
    max_per_star = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
    out, seen = RAW / "playstore_groww_sip_deep.jsonl", set()
    with open(out, "w", encoding="utf-8") as f:
        for star in (1, 2, 3, 4, 5):
            rows = collect(max_per_star, score=star)
            kept = [r for r in rows if len(r["text"]) >= 25 and GROWW_SIP.search(r["text"]) and r["id"] not in seen]
            for r in kept:
                seen.add(r["id"])
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            dates = sorted(r["date"] for r in rows if r["date"])
            print(f"{star} star: fetched {len(rows)} ({dates[0][:10] if dates else '-'} to "
                  f"{dates[-1][:10] if dates else '-'}), SIP-relevant {len(kept)}", flush=True)
    print(f"total SIP-relevant Groww reviews: {len(seen)}")


if __name__ == "__main__":
    main()
