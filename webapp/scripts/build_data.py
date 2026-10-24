"""Build the web app's static data from the frozen analysis inputs.

Uses pipeline/analyze.py's own loaders, so every story, outcome and cut matches findings.json exactly.

Usage: python webapp/scripts/build_data.py
Writes webapp/site/data/: findings.json (copy), stories.json (explorer + Ask), search.json (server-only text
excerpts for retrieval), cuts.json (the two drop-off worlds for every dashboard cut).
"""
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
import analyze  # noqa: E402

FREEZE = ROOT / "data" / "freeze_2026-10-24"
OUT = ROOT / "webapp" / "site" / "data"

# tag fields shown in the explorer and used for retrieval; "unknown"/"none" values are dropped
FIELDS = ["action", "stage", "root_cause", "stop_trigger", "unmet_need", "emotion", "metric_branch",
          "in_app_confusion", "outside_app_workaround", "influencer_source", "stay_reason", "start_motivation",
          "expectation", "behaviour_change", "checking_behaviour", "check_frequency", "life_stage", "income_type",
          "source_of_money", "investor_experience", "platform"]
EMPTY = {"unknown", "none"}

STORE = {  # store pages: app reviews have no per-review permalink
    "playstore": {"groww": "com.nextbillion.groww", "etmoney": "com.smartspends", "paytmmoney": "com.paytmmoney",
                  "indmoney": "in.indwealth", "coin": "com.zerodha.coin", "kuvera": "com.kuvera.android"},
    "appstore": {"groww": "1404871703", "etmoney": "1212752482", "paytmmoney": "1344431352",
                 "indmoney": "1450178837", "coin": "1392892554", "kuvera": "1329701793"},
}


def sha16(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def link(r):
    if r.get("url"):
        return r["url"], True
    app = r.get("app")
    if r["source"] == "playstore" and app in STORE["playstore"]:
        return f"https://play.google.com/store/apps/details?id={STORE['playstore'][app]}", False
    if r["source"] == "appstore" and app in STORE["appstore"]:
        return f"https://apps.apple.com/in/app/id{STORE['appstore'][app]}", False
    return None, False


def scrub(text):
    """No usernames: drop Reddit/YouTube handles and @mentions from any text we publish."""
    text = re.sub(r"(?<![\w/])/?u/[\w-]+", "[user]", text)
    text = re.sub(r"@[\w.-]{2,}", "[user]", text)
    return text


def excerpt(text, n=220):
    """Stories whose evidence quote was cleared by validation still need a verbatim line to show."""
    text = scrub(re.sub(r"\s+", " ", text)).strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut + "…"


def main():
    # inputs must be the frozen ones
    for name in ["tags_deep.jsonl", "findings.json"]:
        live = ROOT / ("data" if name.endswith("jsonl") else "analysis") / name
        assert sha16(live) == sha16(FREEZE / name), f"{name} differs from the freeze"
    assert sha16(ROOT / "data" / "clean.jsonl") == "b32e3c05c8f9429c", "clean.jsonl differs from the freeze"

    stories = analyze.load_stories()
    items = analyze.load_question_items(stories)
    F = json.loads((FREEZE / "findings.json").read_text(encoding="utf-8"))
    n_drop = sum(s["story_class"] == "dropoff_story" for s in stories)
    assert len(stories) == F["corpus"]["stories"] and n_drop == F["corpus"]["dropoff"], (len(stories), n_drop)
    assert len(items) == F["corpus"]["question_items"], len(items)

    clean, by_source = {}, Counter()
    for line in open(ROOT / "data" / "clean.jsonl", encoding="utf-8"):
        r = json.loads(line)
        clean[r["id"]] = r
        by_source[r["source"] if r["source"] not in ("playstore", "appstore") else f"{r['source']}/{r.get('app')}"] += 1
    qmeta = {x["id"]: x for x in map(json.loads, open(ROOT / "data" / "samples" / "questions_sample.jsonl",
                                                       encoding="utf-8"))}

    # Correction 6 (24 Oct): weak quotes widened to verbatim spans that show the SIP context (refine_quotes.py)
    fixes = {r["id"]: r["new"] for r in map(json.loads, open(ROOT / "data" / "quote_fixes_v1.jsonl", encoding="utf-8"))}
    out, search = [], {}
    for kind, rows in (("story", stories), ("item", items)):
        for t in rows:
            r = clean.get(t["id"]) or qmeta[t["id"]]
            url, exact = link(r)
            tags = {}
            for f in FIELDS:
                v = [x for x in analyze.as_list(t.get(f)) if x not in EMPTY]
                if v:
                    tags[f] = v
            out.append({
                "id": t["id"], "kind": kind,
                "cls": {"dropoff_story": "dropoff", "stayed_story": "stayed"}.get(t["story_class"], "item"),
                "outcome": analyze.outcome(t), "src": t["source"], "app": t.get("app"),
                "sub": r.get("subreddit"), "st": t["source_type"], "grp": t["group"],
                "date": (t.get("date") or r.get("date_relative") or "")[:10],
                "quote": scrub(fixes.get(t["id"]) or t.get("evidence_quote") or "") or excerpt(t.get("text") or ""),
                "refined": t["id"] in fixes,
                "excerpt": not t.get("evidence_quote"), "why": scrub(t.get("rationale") or ""),
                "url": url, "exact": exact, "tags": tags,
                "len": len(t.get("text") or ""),
            })
            search[t["id"]] = scrub(re.sub(r"\s+", " ", t.get("text") or ""))[:900]

    # the two drop-off worlds for each dashboard cut (computed with analyze.py's shares())
    drop = [s for s in stories if s["story_class"] == "dropoff_story"]
    cuts_def = {
        "all": lambda s: True,
        "first_time": lambda s: s["group"] == "first_time",
        "groww": lambda s: s.get("app") == "groww" or s.get("platform") == "groww",
        "without_etmoney": lambda s: s.get("app") != "etmoney",
    }
    cuts = {}
    for cut, keep in cuts_def.items():
        rows = [s for s in drop if keep(s)]
        cuts[cut] = {"n": len(rows), "first_time": sum(s["group"] == "first_time" for s in rows)}
        for st in ("app_review", "community"):
            sub = [s for s in rows if s["source_type"] == st]
            cuts[cut][st] = {"n": len(sub), **{f: analyze.shares(sub, f, analyze.EMPTY)
                                                 for f in ("root_cause", "stop_trigger", "unmet_need")}}
        ft = [s for s in rows if s["group"] == "first_time"]
        cuts[cut]["first_time_root"] = analyze.shares(ft, "root_cause", analyze.EMPTY)
    # cross-check: the "all" and "groww" / "without_etmoney" sizes must match findings.json
    assert cuts["all"]["n"] == F["dropoff"]["all"]["n"]
    assert cuts["without_etmoney"]["n"] == F["dropoff"]["without_etmoney"]["n"], cuts["without_etmoney"]["n"]
    assert cuts["first_time"]["n"] == F["dropoff"]["first_time"]["n"]
    print("groww cut", cuts["groww"]["n"], "findings", F["dropoff"]["groww"]["n"])
    # opportunity areas compared on the business metric's terms: for each unmet need, how many drop-off stories are
    # first-time investors and how many state they were in their first 12 months. Descriptive comparison only:
    # no score and no "act here" (user rule, 22 Oct)
    n_ft = sum(s["group"] == "first_time" for s in drop)
    opps = []
    for u in F["unmet_needs"]:
        rows = [s for s in drop if u["need"] in analyze.as_list(s.get("unmet_need"))]
        assert len(rows) == u["stories"], (u["need"], len(rows))
        stage = Counter(analyze.as_list(s.get("stage"))[0] if analyze.as_list(s.get("stage")) else "unknown" for s in rows)
        opps.append({"need": u["need"], "stories": u["stories"], "share": u["share"], "exit_rate": u["exit_rate"],
                     "first_time": u["first_time"], "first_time_share": round(u["first_time"] / n_ft, 3),
                     "first_year": stage["early_0_3m"] + stage["3_12m"], "stage_known": len(rows) - stage["unknown"]})
    cuts["_opportunities"] = {"n_dropoff": len(drop), "n_first_time": n_ft, "rows": opps}
    cuts["_corpus"] = {
        "clean": sum(by_source.values()), "by_source": dict(by_source.most_common()),
        "story_candidates": sum(1 for _ in open(FREEZE / "stories_v2.jsonl", encoding="utf-8")),
        "question_candidates": len(qmeta),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy(FREEZE / "findings.json", OUT / "findings.json")
    dump = lambda name, obj: (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")),
                                                     encoding="utf-8")
    dump("stories.json", out)
    (ROOT / "webapp" / "site" / "public" / "data").mkdir(parents=True, exist_ok=True)
    shutil.copy(OUT / "stories.json", ROOT / "webapp" / "site" / "public" / "data" / "stories.json")  # explorer fetch
    dump("search.json", search)
    dump("cuts.json", cuts)
    c = Counter((s["kind"], s["cls"]) for s in out)
    print(f"stories.json {len(out)} rows {dict(c)}; no-url {sum(not s['url'] for s in out)}; "
          f"store-page links {sum(bool(s['url']) and not s['exact'] for s in out)}")


if __name__ == "__main__":
    main()
