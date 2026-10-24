"""Analysis of the tagged story corpus (Sample S): what drives drop-off, for whom, and what keeps
stayers going. Every cut the plan promised:
  - app reviews vs community posts (Play Store reviews are complaints by design, so a pattern only
    counts when it also shows up in Reddit / TradingQ&A / YouTube / blogs)
  - first-time vs experienced (first-time = says so, OR SIP under 12 months old)
  - drop-off vs stayed (the control group)
  - with and without ET Money (one pricing event dominated the early corpus)
  - unmet needs ranked by how often they come with an actual exit (stopped / redeemed / switched)

Usage: python pipeline/analyze.py
Writes analysis/findings.json (feeds the web app) and analysis/findings_v1.md (readable summary).
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXITS = {"stopped", "redeemed", "switched_platform"}
FIRST_STAGES = {"early_0_3m", "3_12m"}
FIELDS = ["root_cause", "stop_trigger", "unmet_need", "metric_branch", "emotion", "action",
          "in_app_confusion", "outside_app_workaround", "influencer_source", "stay_reason", "stage"]


def as_list(v):
    return v if isinstance(v, list) else [v]


def load_stories():
    meta = {x["id"]: x for x in map(json.loads, open(ROOT / "data" / "samples" / "stories_ai.jsonl", encoding="utf-8"))}
    texts = {r["id"]: r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))}
    out, seen = [], set()
    for t in map(json.loads, open(ROOT / "data" / "tags_deep.jsonl", encoding="utf-8")):
        if not t["stratum"].startswith("S/") or t.get("relevant") != "yes":
            continue
        m, r = meta.get(t["id"], {}), texts[t["id"]]
        key = re.sub(r"\W+", "", r["text"].lower())[:300]  # the same post cross-posted to two subreddits
        if key in seen:
            continue
        seen.add(key)
        t["story_class"] = m.get("story_class", "dropoff_story")
        # rule change 24 Oct (golden-set review): the metric counts a SIP as active if an instalment went through
        # in the last 30 days, so a reduced-but-running SIP stayed (#4), and a restart still means it lapsed (#3)
        if m.get("story_type") == "reduced":
            t["story_class"] = "stayed_story"
        elif m.get("story_type") == "restarted":
            t["story_class"] = "dropoff_story"
        t["app"] = r.get("app")
        t["source_type"] = "app_review" if r["source"] in ("playstore", "appstore") else "community"
        t["group"] = ("first_time" if t.get("investor_experience") == "first_time" or t.get("stage") in FIRST_STAGES
                      else "experienced" if t.get("investor_experience") == "experienced" else "unknown")
        t["text"], t["date"] = r["text"], r.get("date")
        out.append(t)
    return out


def load_question_items(stories):
    """Q items (prefilter_questions.py): posts that answer a brief question without being a story.
    Pooled with the stories for the per-question answers; never mixed into the drop-off cuts."""
    meta = ROOT / "data" / "samples" / "questions_sample.jsonl"
    if not meta.exists():
        return []
    meta = {x["id"]: x for x in map(json.loads, open(meta, encoding="utf-8"))}
    seen = {s["id"] for s in stories}
    out = []
    for t in map(json.loads, open(ROOT / "data" / "tags_deep.jsonl", encoding="utf-8")):
        if not t["stratum"].startswith("Q/") or t.get("relevant") != "yes" or t["id"] in seen:
            continue
        r = meta[t["id"]]
        t["story_class"] = "question_item"
        t["app"] = r.get("app")
        t["source_type"] = "app_review" if r["source"] in ("playstore", "appstore") else "community"
        t["group"] = ("first_time" if t.get("investor_experience") == "first_time" or t.get("stage") in FIRST_STAGES
                      else "experienced" if t.get("investor_experience") == "experienced" else "unknown")
        t["text"], t["date"] = r["text"], r.get("date")
        out.append(t)
    return out


# the brief's nine questions -> the codebook fields that answer them
QUESTIONS = {
    "q1_start_expect": ("Why do people start a SIP, and what do they expect to happen?",
                        ["start_motivation", "expectation"]),
    "q2_change_over_time": ("What changes in their behaviour in the months after starting?",
                            ["behaviour_change"]),
    "q3_stop_drivers": ("What leads investors to pause, reduce or stop a SIP?", ["stop_trigger", "root_cause"]),
    "q4_checking": ("What do investors check, and how often, once they have started?",
                    ["checking_behaviour", "check_frequency"]),
    "q5_in_app_confusion": ("What confuses or worries them inside the app?", ["in_app_confusion"]),
    "q6_outside_app": ("What do they do outside the app when they feel unsure?", ["outside_app_workaround"]),
    "q7_continue_vs_drop": ("What separates investors who continue from those who quietly drop off?",
                            ["stay_reason"]),
    "q8_segments": ("How do these patterns differ across user segments?",
                    ["income_type", "life_stage", "source_of_money", "influencer_source"]),
    "q9_unmet_needs": ("What unmet needs emerge consistently across conversations?", ["unmet_need"]),
}
OUTCOME = {"continued": "stayed", "increased": "stayed", "reduced": "stayed",  # reduced: still active (24 Oct rule)
           "stopped": "left", "paused": "left", "redeemed": "left",
           # app switchers still invest: their own group, a loss for Groww but not a loss of intent (24 Oct)
           "switched_platform": "changed_app", "considering_switch_platform": "changed_app",
           "considering_stop": "wobbling", "nearly_stopped": "wobbling", "attempted_blocked": "wobbling",
           "restructured": "restructured"}
EMPTY = ("unknown", "none", "other")


def outcome(r):
    return OUTCOME.get(r.get("action"), "unknown")


def strength(n):
    return "strong" if n >= 100 else "moderate" if n >= 30 else "thin"


def known(r, f):
    return [v for v in as_list(r.get(f)) if v not in EMPTY]


def answer(rows, fields):
    """Per question: items with a signal, code shares among them, and splits by outcome / first-time."""
    have = [r for r in rows if any(known(r, f) for f in fields)]
    A = {"n": len(have), "strength": strength(len(have)),
         "by_source_type": dict(Counter(r["source_type"] for r in have)),
         "by_outcome": dict(Counter(outcome(r) for r in have)), "fields": {}}
    for f in fields:
        hf = [r for r in have if known(r, f)]
        A["fields"][f] = {
            "n": len(hf), "strength": strength(len(hf)), "all": shares(hf, f, EMPTY),
            "stayed": shares([r for r in hf if outcome(r) == "stayed"], f, EMPTY),
            "left_or_wobbling": shares([r for r in hf if outcome(r) in ("left", "wobbling")], f, EMPTY),
            "first_time": shares([r for r in hf if r["group"] == "first_time"], f, EMPTY),
            "quotes": {code: quotes(hf, f, code) for code in list(shares(hf, f, EMPTY))[:6]},
        }
    A["strength"] = strength(min(v["n"] for v in A["fields"].values()))  # a question is as strong as its weakest part
    return A


def segment_outcomes(rows):
    """Q8: for each segment value, how its people split between stayed and left / wobbling."""
    out = {}
    for f in QUESTIONS["q8_segments"][1]:
        out[f] = {}
        for code in shares(rows, f, EMPTY):
            rs = [r for r in rows if code in known(r, f) and outcome(r) != "unknown"]
            c = Counter(outcome(r) for r in rs)
            out[f][code] = {"n_with_outcome": len(rs), **c,
                            "stayed_share": round(c["stayed"] / len(rs), 2) if rs else None,
                            "evidence": strength(len(rs))}
    return out


def shares(rows, field, drop=("unknown",)):
    """{code: (count, share)} — each item counted once per code; share over all rows."""
    c = Counter(v for r in rows for v in set(as_list(r.get(field))) if v not in drop)
    n = len(rows) or 1
    return {k: {"n": v, "share": round(v / n, 3)} for k, v in c.most_common()}


def quotes(rows, field, code, k=3):
    hits = [r for r in rows if code in as_list(r.get(field)) and r.get("evidence_quote")]
    hits.sort(key=lambda r: (r["source_type"] != "community", r["group"] != "first_time"))  # community + first-time first
    return [{"id": r["id"], "source": r["source"], "app": r.get("app"), "group": r["group"],
             "quote": r["evidence_quote"]} for r in hits[:k]]


def main():
    rows = load_stories()
    drop = [r for r in rows if r["story_class"] == "dropoff_story"]
    stay = [r for r in rows if r["story_class"] == "stayed_story"]
    F = {}
    F["corpus"] = {
        "stories": len(rows), "dropoff": len(drop), "stayed": len(stay),
        "by_source": dict(Counter(f"{r['source']}" + (f"/{r['app']}" if r.get("app") else "") for r in rows).most_common()),
        "by_group": dict(Counter(f"{r['story_class']}/{r['group']}" for r in rows)),
        "by_source_type": dict(Counter(f"{r['story_class']}/{r['source_type']}" for r in rows)),
    }
    cuts = {
        "all": drop,
        "app_review": [r for r in drop if r["source_type"] == "app_review"],
        "community": [r for r in drop if r["source_type"] == "community"],
        "first_time": [r for r in drop if r["group"] == "first_time"],
        "experienced": [r for r in drop if r["group"] == "experienced"],
        "groww": [r for r in drop if r.get("app") == "groww" or r.get("platform") == "groww"],
        "without_etmoney": [r for r in drop if r.get("app") != "etmoney"],
    }
    F["dropoff"] = {name: {"n": len(rs), **{f: shares(rs, f) for f in FIELDS}} for name, rs in cuts.items()}

    # robustness: a root cause / trigger counts as a cross-source pattern if >= 8% of BOTH source types
    robust = {}
    for f in ("root_cause", "stop_trigger", "unmet_need"):
        a, c = F["dropoff"]["app_review"][f], F["dropoff"]["community"][f]
        robust[f] = [{"code": k, "app_review": a.get(k, {}).get("share", 0), "community": c.get(k, {}).get("share", 0),
                      "cross_source": a.get(k, {}).get("share", 0) >= 0.08 and c.get(k, {}).get("share", 0) >= 0.08}
                     for k in sorted(set(a) | set(c), key=lambda k: -(a.get(k, {}).get("n", 0) + c.get(k, {}).get("n", 0)))
                     if k != "other"][:12]
    F["robustness"] = robust

    # control group: how stayers differ from leavers
    F["stayed"] = {"n": len(stay), **{f: shares(stay, f) for f in FIELDS}}
    diffs = {}
    for f in ("emotion", "influencer_source", "stage", "metric_branch", "checking_behaviour", "expectation"):
        d, s = shares(drop, f), shares(stay, f)
        diffs[f] = sorted(({"code": k, "dropoff": d.get(k, {}).get("share", 0), "stayed": s.get(k, {}).get("share", 0),
                            "diff": round(s.get(k, {}).get("share", 0) - d.get(k, {}).get("share", 0), 3)}
                           for k in set(d) | set(s)), key=lambda x: -abs(x["diff"]))[:6]
    F["stayed_vs_dropoff"] = diffs

    # unmet needs by frequency, plus how often each comes with an ACTUAL exit. Descriptive only: no score or
    # ranking of where to act (user rule, 22 Oct: the engine gives no advice and no product solutions)
    needs = []
    for need, v in shares(drop, "unmet_need", drop=("unknown", "other")).items():
        with_need = [r for r in drop if need in as_list(r.get("unmet_need"))]
        exit_rate = sum(r.get("action") in EXITS for r in with_need) / len(with_need)
        ft = sum(r["group"] == "first_time" for r in with_need)
        comm = sum(r["source_type"] == "community" for r in with_need)
        needs.append({"need": need, "stories": v["n"], "share": v["share"], "exit_rate": round(exit_rate, 2),
                      "first_time": ft, "community": comm, "quotes": quotes(with_need, "unmet_need", need)})
    F["unmet_needs"] = sorted(needs, key=lambda x: -x["stories"])

    F["examples"] = {f: {code: quotes(drop, f, code) for code in list(shares(drop, f, ("unknown", "other")))[:8]}
                     for f in ("root_cause", "stop_trigger")}
    F["examples"]["stay_reason"] = {code: quotes(stay, "stay_reason", code)
                                    for code in list(shares(stay, "stay_reason", ("unknown", "other")))[:8]}

    # per-question answers (brief Part 1): stories + question-targeted items
    pool = rows + load_question_items(rows)
    F["questions"] = {k: {"question": q, "fields": fs, **answer(pool, fs)} for k, (q, fs) in QUESTIONS.items()}
    # Q2 also reads the cross-section: what people at each stage are doing
    F["questions"]["q2_change_over_time"]["action_by_stage"] = {
        st: shares([r for r in pool if r.get("stage") == st], "action", EMPTY)
        for st in ("early_0_3m", "3_12m", "12m_plus")}
    # Q7 compares stayers with leavers on every field, not only stated stay reasons
    st = [r for r in pool if outcome(r) == "stayed"]
    lw = [r for r in pool if outcome(r) in ("left", "wobbling")]
    q7 = F["questions"]["q7_continue_vs_drop"]
    q7["n_stayed"], q7["n_left_or_wobbling"] = len(st), len(lw)
    q7["differences"] = {}
    for f in ("emotion", "checking_behaviour", "check_frequency", "behaviour_change", "expectation",
              "start_motivation", "stage", "influencer_source", "outside_app_workaround"):
        a, b = shares(st, f, EMPTY), shares(lw, f, EMPTY)
        q7["differences"][f] = sorted(
            ({"code": k, "stayed": a.get(k, {}).get("share", 0), "left_or_wobbling": b.get(k, {}).get("share", 0)}
             for k in set(a) | set(b)), key=lambda x: -abs(x["stayed"] - x["left_or_wobbling"]))[:5]
    F["questions"]["q8_segments"]["segment_outcomes"] = segment_outcomes(pool)
    F["corpus"]["question_items"] = len(pool) - len(rows)

    out = ROOT / "analysis"
    (out / "findings.json").write_text(json.dumps(F, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(F, out / "findings_v1.md")
    print(f"stories {len(rows)} (drop-off {len(drop)}, stayed {len(stay)}); groups {F['corpus']['by_group']}")


def top(d, k=5):
    return ", ".join(f"{c} {v['share']:.0%}" for c, v in list(d.items())[:k]) or "-"


def write_md(F, path):
    D = F["dropoff"]
    L = ["# Findings v1 (auto-generated by pipeline/analyze.py)", "",
         f"Corpus: {F['corpus']['stories']} tagged stories — {F['corpus']['dropoff']} drop-off, "
         f"{F['corpus']['stayed']} stayed. Shares are of drop-off stories in each cut.", "",
         "## Root cause by cut", "", "| Cut | n | Top root causes |", "| --- | --- | --- |"]
    L += [f"| {k} | {v['n']} | {top(v['root_cause'])} |" for k, v in D.items()]
    L += ["", "## Stop trigger by cut", "", "| Cut | n | Top triggers |", "| --- | --- | --- |"]
    L += [f"| {k} | {v['n']} | {top(v['stop_trigger'])} |" for k, v in D.items()]
    L += ["", "## Cross-source check (app reviews vs community)", "",
          "| Field | Code | App reviews | Community | Both ≥8% |", "| --- | --- | --- | --- | --- |"]
    for f, items in F["robustness"].items():
        L += [f"| {f} | {x['code']} | {x['app_review']:.0%} | {x['community']:.0%} | {'yes' if x['cross_source'] else ''} |"
              for x in items[:6]]
    L += ["", "## What keeps stayers going", "", f"n = {F['stayed']['n']}: {top(F['stayed']['stay_reason'], 7)}", "",
          "## Stayers vs leavers (biggest differences)", "", "| Field | Code | Drop-off | Stayed | Diff |",
          "| --- | --- | --- | --- | --- |"]
    for f, items in F["stayed_vs_dropoff"].items():
        L += [f"| {f} | {x['code']} | {x['dropoff']:.0%} | {x['stayed']:.0%} | {x['diff']:+.0%} |" for x in items[:3]]
    L += ["", "## Unmet needs by frequency", "",
          "| Need | Stories | Share | Exit rate | First-time | Community |", "| --- | --- | --- | --- | --- | --- |"]
    L += [f"| {o['need']} | {o['stories']} | {o['share']:.0%} | {o['exit_rate']:.0%} | {o['first_time']} | {o['community']} |"
          for o in F["unmet_needs"][:10]]
    L += ["", "## The brief's nine questions (stories + question-targeted items)", "",
          f"Question items added: {F['corpus'].get('question_items', 0)}. "
          "Evidence: strong = 100+ items, moderate = 30-99, thin = under 30.", ""]
    for k, Q in F.get("questions", {}).items():
        L += [f"### {Q['question']}", "", f"{Q['n']} items with a signal ({Q['strength']}); outcomes {Q['by_outcome']}", ""]
        for f, A in Q["fields"].items():
            L.append(f"- **{f}** (n={A['n']}, {A['strength']}): {top(A['all'], 6)}")
            if A["stayed"] or A["left_or_wobbling"]:
                L.append(f"  - stayed: {top(A['stayed'], 4)} · left/wobbling: {top(A['left_or_wobbling'], 4)}")
        for f, codes in Q.get("segment_outcomes", {}).items():
            L.append(f"- {f}, share who stayed: " + ", ".join(
                f"{c} {v['stayed_share']:.0%} (n={v['n_with_outcome']})" for c, v in codes.items()
                if v["stayed_share"] is not None))
        L.append("")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
