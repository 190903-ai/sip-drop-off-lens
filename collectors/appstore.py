"""Collect iOS App Store reviews (India) for Groww and peer investing apps via Apple's public RSS feed.

The feed returned nothing on 21 Oct 2026 and works again on 23 Oct. Apple caps each feed at 10 pages
(~500 reviews), so both sort orders are read (most recent + most helpful) to widen the window.

Usage: python collectors/appstore.py
Writes data/raw/appstore.jsonl (all reviews) and data/raw/appstore_sip.jsonl (SIP-relevant only).
"""
import json
import time

import requests

from playstore import RAW, SIP_PATTERN

APPS = {  # App Store ids, India storefront
    "groww": "1404871703",
    "etmoney": "1212752482",
    "paytmmoney": "1344431352",
    "indmoney": "1450178837",
    "coin": "1392892554",
    "kuvera": "1329701793",
}
FEED = "https://itunes.apple.com/in/rss/customerreviews/page={page}/id={app}/sortby={sort}/json"


def collect() -> list[dict]:
    out, seen = [], set()
    for name, app_id in APPS.items():
        before = len(out)
        for sort in ("mostrecent", "mosthelpful"):
            for page in range(1, 11):
                try:
                    resp = requests.get(FEED.format(page=page, app=app_id, sort=sort), timeout=30)
                    entries = resp.json().get("feed", {}).get("entry", []) if resp.status_code == 200 else []
                except Exception:
                    entries = []
                if isinstance(entries, dict):
                    entries = [entries]
                for e in entries:
                    if "im:rating" not in e:  # first entry can be app metadata
                        continue
                    rid = f"as_{e['id']['label']}"
                    if rid in seen:
                        continue
                    seen.add(rid)
                    out.append({
                        "id": rid,
                        "source": "appstore",
                        "app": name,
                        "text": f"{e['title']['label']}. {e['content']['label']}",
                        "rating": int(e["im:rating"]["label"]),
                        "date": e.get("updated", {}).get("label"),
                        "app_version": e.get("im:version", {}).get("label"),
                    })
                if not entries:
                    break
                time.sleep(0.5)
        print(f"{name}: {len(out) - before} reviews", flush=True)
    return out


def main():
    rows = collect()
    sip_rows = [r for r in rows if SIP_PATTERN.search(r["text"])]
    for name, data in (("appstore.jsonl", rows), ("appstore_sip.jsonl", sip_rows)):
        with open(RAW / name, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"total={len(rows)} sip_relevant={len(sip_rows)}")


if __name__ == "__main__":
    main()
