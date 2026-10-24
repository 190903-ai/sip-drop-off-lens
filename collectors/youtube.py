"""Collect comments from Indian personal-finance YouTube videos about SIPs.

No API key needed: scrapetube finds videos, youtube-comment-downloader pulls comments.
Usage: python collectors/youtube.py
Writes data/raw/youtube.jsonl (only SIP-relevant comments).
"""
import json
import time

import scrapetube
from youtube_comment_downloader import SORT_BY_POPULAR, YoutubeCommentDownloader

from playstore import RAW, SIP_PATTERN

QUERIES = [
    "SIP for beginners india", "should I stop my SIP", "SIP negative returns what to do",
    "why people stop SIP", "my first SIP experience", "SIP in falling market",
    "groww SIP tutorial", "mutual fund SIP mistakes", "SIP kab band kare",
    "SIP loss kyu ho raha hai",
    # round 2: life events, checking behaviour, motivation, first-year experience
    "1 year SIP returns honest review", "SIP pause kaise kare", "SIP band karu ya nahi",
    "mutual fund returns kam kyu hai", "how to read mutual fund returns xirr",
    "SIP me paisa doob gaya", "salary late SIP bounce", "SIP step up kya hai",
    "first salary investment plan", "SIP for students", "mutual funds for beginners hindi",
    "SIP 6 months negative", "should beginners invest in mutual funds now",
    "SIP vs FD which is better",
    # round 3 (23 Oct): the brief's thin questions: expectations, checking habits, first-year
    # journeys, who people are (age, first salary, family money, who pushed them to start)
    "my SIP journey 1 year", "2 years of SIP results", "SIP portfolio review after 1 year",
    "how often should you check mutual fund portfolio", "stop checking your portfolio daily",
    "what returns to expect from SIP", "SIP returns reality", "why I started SIP at 22",
    "investing my first salary in mutual funds", "SIP for freshers", "mutual fund for college students",
    "SIP kaise shuru kare first salary", "SIP kitna return deta hai", "mutual fund portfolio roz check",
    "parents ke liye SIP", "SIP for housewife", "SIP for self employed irregular income",
    "my mutual fund mistakes as a beginner",
]
VIDEOS_PER_QUERY = 6
COMMENTS_PER_VIDEO = 300


def main():
    dl = YoutubeCommentDownloader()
    out_path = RAW / "youtube.jsonl"
    # Incremental: keep earlier comments, skip videos already collected, append per video
    rows = [json.loads(l) for l in open(out_path, encoding="utf-8")] if out_path.exists() else []
    seen_videos = {r["video_id"] for r in rows}
    out = open(out_path, "a", encoding="utf-8")
    for q in QUERIES:
        try:
            videos = list(scrapetube.get_search(q, limit=VIDEOS_PER_QUERY, sort_by="relevance"))
        except Exception as e:
            print(f"  search failed for {q!r}: {e}", flush=True)
            continue
        for v in videos:
            vid = v["videoId"]
            if vid in seen_videos:
                continue
            seen_videos.add(vid)
            video_rows = []
            title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))
            kept = 0
            try:
                for i, c in enumerate(dl.get_comments_from_url(
                        f"https://www.youtube.com/watch?v={vid}", sort_by=SORT_BY_POPULAR)):
                    if i >= COMMENTS_PER_VIDEO:
                        break
                    text = c.get("text", "")
                    if len(text) < 40 or not SIP_PATTERN.search(text):
                        continue
                    video_rows.append({
                        "id": f"yt_{c['cid']}", "source": "youtube", "video_id": vid,
                        "video_title": title, "text": text, "likes": c.get("votes"),
                        "date_relative": c.get("time"),
                        "url": f"https://www.youtube.com/watch?v={vid}&lc={c['cid']}",
                    })
            except Exception as e:
                print(f"  skip {vid}: {e}", flush=True)
                seen_videos.discard(vid)  # not saved, so a rerun retries it
                continue
            for r in video_rows:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
            out.flush()
            rows.extend(video_rows)
            print(f"  [{q}] {title[:60]!r}: kept {len(video_rows)} (total {len(rows)})", flush=True)
            time.sleep(1)
    out.close()
    print(f"videos={len(seen_videos)} comments={len(rows)}")


if __name__ == "__main__":
    main()
