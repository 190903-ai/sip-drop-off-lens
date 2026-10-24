"""Turn the open-coding draft into codebook v1 (edits are listed in CHANGES).

Usage: python pipeline/build_codebook.py
Reads pipeline/codebook_draft.json, writes pipeline/codebook.json.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

CHANGES = [
    "Sharpened return_misreading (wrong frame) vs expectation_violation (right frame, unmet prior); both may co-occur.",
    "Added metric_branch to map every item onto the metric tree (analysis/metric_tree_v1.md).",
    "Added platform (groww / other / unknown) because the business metric is measured on Groww.",
    "Added rationale (required when any field uses 'other').",
    # v1.1: from the 60-item Reddit check (evidence/reddit_codebook_check.md)
    "v1.1 action: added restructured (16/60 Reddit): stopping one fund's SIP while still investing.",
    "v1.1 root_cause: added portfolio_rationalisation (6/60).",
    "v1.1 stop_trigger: added self_review (5/60).",
    "v1.1 unmet_need: added portfolio_construction_help (~46/60, previously forced into independent_reassurance).",
    "v1.1 boundaries: planned addition to a running SIP = increased; step-ups = intent branch; stage computed "
    "from stated start vs post date; borrowed_conviction only when the hold/stop decision is handed to others; "
    "cashflow_rigidity includes avoiding or planning gaps in a SIP because of cash flow.",
    # v1.2: from deep-tagging chunks 02, b02, b03 (4 items coded 'other' with the same rationale)
    "v1.2 stop_trigger: added tax_rule_change (new tax regime / 80C / tax rules make the SIP pointless).",
    # v1.3: from AI-detected story chunk s01 (ET Money reviews)
    "v1.3 action: added attempted_blocked (~8 items: tried to cancel/skip/pause/redeem, app did not allow it).",
    "v1.3 stop_trigger: added missing_notification (not told about a failed/missed instalment or SIP change).",
    # v1.4: from the plan review (first-time focus + a stayed control group)
    "v1.4 added investor_experience (first_time / experienced / unknown): the brief is about first-time "
    "investors and r/FIREIndia / TradingQ&A lean experienced. Replaces the loose first_time flag.",
    "v1.4 action: added nearly_stopped (seriously considered stopping, then decided to continue) and widened "
    "continued to 'kept the SIP running through a loss, doubt or pressure to stop' so stayed stories can be "
    "compared with drop-offs.",
    # v1.5: from deep-tagging chunks s02-s03 (12 stop_trigger 'other' codes, mostly app bugs)
    "v1.5 stop_trigger: added app_malfunction (app crash, login failure, blank screen, a feature not "
    "working) when it is not a payment, modify or redemption problem.",
    # v1.6: from deep-tagging chunks s04-s10 (recurring 'other' codes + no field for why stayers stay)
    "v1.6 stop_trigger: added debit_after_cancel (5+ items: money still debited after cancelling) and "
    "support_failure (5+ items: support unreachable or unhelpful was the push).",
    "v1.6 added stay_reason (multi): what kept a stayer going. Stayed stories are the control group, "
    "and root_cause only explains doubt/stopping, so their reasons had nowhere to go.",
    # v1.7: targeted pull (s14-s17) put borrowed_conviction on 13% of stories vs 4% before: most were
    # people asking a forum "should I continue?", which is not what the finding's name claims
    "v1.7 root_cause: borrowed_conviction narrowed to a SPECIFIC person steering the hold/stop decision "
    "(started on their advice, or hands the decision to a named person/creator they follow). Asking a "
    "forum whether to continue is not enough: code the mechanism instead. 52 tags re-checked by hand "
    "(data/recode/out/recode_04.jsonl): 8 kept, 44 re-coded.",
    # v1.8: coverage check (23 Oct) showed the brief's Q2 (what changes in the months after starting)
    # had no field, and Q4 (how often they check) had 4/720 values
    "v1.8 added behaviour_change (multi): how the writer's behaviour changed since they started "
    "(checking habits, amount, number of funds, attention). Brief Q2 had no field; action only says "
    "where they ended up. check_frequency + event_driven (checks only when news / a fall / an SMS "
    "prompts it), the commonest answer in 'how often do you check' threads. start_motivation + tax_saving, "
    "influencer_source + online_community (both flagged by the wave-1 taggers).",
    # v1.9: across waves 2-3 and the story recode, behaviour_change "other" was mostly one thing
    "v1.9 behaviour_change + mode_switched (SIP <-> lump sum, regular -> direct, FD -> MF, MF -> stocks): the "
    "commonest 'other' in waves 2-3 and the v1.8 story recode. Existing 'other' tags re-mapped by hand "
    "(data/recode/out/recode_07.jsonl).",
]


def add_value(fields, field, value, before="other"):
    vals = fields[field]["values"]
    idx = next((i for i, x in enumerate(vals) if x["code"] in (before, "unknown")), len(vals))
    vals.insert(idx, value)


def patch(fields, field, code, **updates):
    for val in fields[field]["values"]:
        if val["code"] == code:
            val.update(updates)


def unknown():
    return {"code": "unknown", "definition": "Text gives no observable signal for this field.",
            "include_example": "", "exclude_rule": "Use only when no other value is supported by the text."}


def v(code, definition, include="", exclude=""):
    return {"code": code, "definition": definition, "include_example": include, "exclude_rule": exclude}


def main():
    cb = json.loads((HERE / "codebook_draft.json").read_text(encoding="utf-8"))
    fields = {f["name"]: f for f in cb["fields"]}

    for val in fields["root_cause"]["values"]:
        if val["code"] == "return_misreading":
            val["definition"] = (
                "Reads own performance through a WRONG or partial frame: point-to-point NAV, absolute "
                "rupees, the fund's headline return vs their own SIP return, a single day's P&L, or "
                "hindsight lumpsum comparison. The error is in HOW they read the number.")
            val["exclude_rule"] = ("Reads correctly but is unhappy because reality fell short of a stated "
                                   "expectation -> expectation_violation (both may apply).")
        if val["code"] == "expectation_violation":
            val["definition"] = (
                "Reads performance CORRECTLY, but a prior expectation they state (return rate, time to "
                "profit, no losses) was not met.")
            val["exclude_rule"] = ("Expectation not stated -> not this. If the reading itself is flawed, "
                                   "add return_misreading too.")

    # --- v1.1 changes from the Reddit check ---
    add_value(fields, "action", v(
        "restructured", "Stopped or switched one fund's SIP but keeps investing overall (consolidating, "
        "moving regular->direct, replacing a fund).",
        "stopped my small cap SIP and moved the amount to my index fund",
        "If they stop investing in MFs altogether -> stopped. Moving platform only -> switched_platform."),
        before="considering_stop")
    patch(fields, "action", "stopped",
          exclude_rule="If they still invest in other funds/SIPs -> restructured. "
                       "If they left Groww but invest elsewhere -> switched_platform.")
    patch(fields, "action", "increased",
          definition="Raised amount, stepped up, added SIPs or lump sums, or plans a specific addition "
                     "to an already-running SIP.")
    patch(fields, "action", "considering_start",
          exclude_rule="Already has a running SIP and plans to add to it -> increased.")
    add_value(fields, "root_cause", v(
        "portfolio_rationalisation", "Cancels or changes a SIP to fix the portfolio itself: fund overlap, "
        "too many funds, regular->direct, cleaning up hastily chosen first funds.",
        "too many funds with overlapping holdings so stopping two SIPs",
        "Stops because of returns disappointment -> expectation_violation / return_misreading."))
    add_value(fields, "stop_trigger", v(
        "self_review", "Their own periodic review of the portfolio (no external event).",
        "was reviewing my portfolio after a year and realised"))
    add_value(fields, "action", v(
        "attempted_blocked", "Tried to cancel, skip, pause, reduce or redeem, but the app did not let them "
        "or the request failed.",
        "trying to cancel my sip for weeks but the option is not working",
        "If the action eventually went through, code that action (stopped/paused/...)."),
        before="considering_stop")
    add_value(fields, "stop_trigger", v(
        "missing_notification", "Was not told about a failed or missed instalment, a mandate problem, or a "
        "change to their SIP, and found out late.",
        "no notification that my sip was not processed",
        "If they were told but the debit still failed -> payment_failure."))
    add_value(fields, "stop_trigger", v(
        "tax_rule_change", "A tax rule or the writer's tax regime changed so the SIP no longer serves its "
        "purpose (e.g. new tax regime makes an ELSS SIP pointless).",
        "moved to the new tax regime so stopped my ELSS SIP"))
    add_value(fields, "stop_trigger", v(
        "app_malfunction", "The app crashed, would not log in, showed a blank screen, or a feature did not "
        "work, and this pushed them towards stopping or leaving.",
        "app shows white screen for days, can't even see my SIPs, moving to another app",
        "Failed debit -> payment_failure. Could not skip/edit -> modify_blocked. Slow redemption -> "
        "order_redemption_delay. Wrong value shown -> data_discrepancy."))
    add_value(fields, "stop_trigger", v(
        "debit_after_cancel", "Money was still debited after they cancelled or paused the SIP.",
        "cancelled my SIP last month but amount still got deducted",
        "Could not cancel at all -> modify_blocked."))
    add_value(fields, "stop_trigger", v(
        "support_failure", "Customer support was unreachable, slow or unhelpful, and that pushed them "
        "towards stopping or leaving.",
        "raised 5 tickets, no one replied, so I am moving my SIPs out",
        "Support is mentioned but the push is a failed debit -> payment_failure (both may apply)."))
    add_value(fields, "unmet_need", v(
        "portfolio_construction_help", "Wants help deciding how many/which kinds of funds, allocation, or "
        "whether their mix makes sense (NOTE: the product may not recommend specific funds).",
        "is this portfolio okay or too many funds",
        "Wants to know if their own returns are normal -> understand_my_returns."))
    add_value(fields, "action", v(
        "nearly_stopped", "Seriously considered stopping, pausing or redeeming, then decided to keep the SIP "
        "running (says what made them stay).",
        "was about to stop my SIP when it went red but my friend explained rupee cost averaging, so I continued",
        "Still undecided -> considering_stop. No stated wobble -> continued."),
        before="considering_stop")
    patch(fields, "action", "continued",
          definition="Kept the SIP running, including through a loss, a doubt or outside pressure to stop.",
          exclude_rule="Says they nearly stopped and then decided to stay -> nearly_stopped.")
    patch(fields, "root_cause", "borrowed_conviction",
          definition="A SPECIFIC person steers the hold/stop decision for an EXISTING SIP: the writer started "
                     "on a family member's, friend's, advisor's or creator's say-so and defers to them, blames "
                     "them, or explicitly hands the decision to a named person/creator they follow.",
          include_example="mene apke bolne pr 2lamsum or sip kiya hu switch krdu batana",
          exclude_rule="Asking a forum or the public 'should I continue or stop?' -> not this; code the "
                       "mechanism (volatility_mismatch, expectation_violation, ...). Asking which fund to pick "
                       "-> not this.")
    patch(fields, "root_cause", "cashflow_rigidity",
          definition="A fixed SIP clashes with income shocks, irregular/low income or competing needs, so "
                     "stopping, skipping, avoiding or planning gaps in the SIP is seen as the only option.")
    patch(fields, "stage", "unknown",
          definition="No stated duration or start date. If a start date is stated, compute the stage "
                     "from it relative to the post date.")

    metric_branch = {
        "name": "metric_branch",
        "question": "Which branch of the 12-month continuation metric tree does this item speak to?",
        "type": "multi",
        "values": [
            v("activation", "Problems or experiences with setting up a SIP or the first instalment "
              "(mandate registration, first debit, choosing the SIP date).",
              exclude="Problems with later, recurring instalments -> reliability."),
            v("reliability", "A recurring instalment failed or was blocked without the user choosing it "
              "(bounce, mandate expiry, no retry, skip/edit not working).",
              exclude="User chose to skip/stop -> intent."),
            v("intent", "The user chose, or is weighing, to skip, pause, reduce, stop, restructure, "
              "continue or step up, and why (returns, cash flow, trust, advice, goals)."),
            v("recovery", "Restarting after a pause, lapse or failure (or barriers to restarting)."),
            v("none", "Relevant context (e.g. motivation, education need) but no continuation branch."),
            unknown(),
        ],
        "unknown_allowed": True,
    }
    platform = {
        "name": "platform",
        "question": "Which platform is the writer's SIP on, if stated or clear from the source?",
        "type": "single",
        "values": [
            v("groww", "Groww (all Play Store items are Groww reviews).", "Groww makes investing easy"),
            v("other", "Another app, AMC, bank or distributor.", "I use Zerodha Coin for my SIPs"),
            unknown(),
        ],
        "unknown_allowed": True,
    }
    rationale = {
        "name": "rationale",
        "question": "One short sentence explaining the root_cause / stop_trigger choice; REQUIRED if any "
                    "field uses 'other' (say what the 'other' is).",
        "type": "text",
        "unknown_allowed": True,
    }

    investor_experience = {
        "name": "investor_experience",
        "question": "Is the writer a first-time mutual fund / SIP investor or an experienced one, as stated?",
        "type": "single",
        "values": [
            v("first_time", "Says they are new to mutual funds / SIPs, it is their first SIP, or they started "
              "investing within about the last year.",
              "this is my first SIP, started 4 months ago",
              "Only a new SIP added by someone who says they have invested for years -> experienced."),
            v("experienced", "Says they have invested in mutual funds for more than about a year, or describes "
              "a long-held, multi-fund portfolio.",
              "been doing SIPs since 2018"),
            unknown(),
        ],
        "unknown_allowed": True,
    }

    stay_reason = {
        "name": "stay_reason",
        "question": "If the writer kept, nearly stopped then kept, increased or restarted their SIP: what kept "
                    "them going (stated)? Use only for stayed stories; otherwise unknown.",
        "type": "multi",
        "values": [
            v("long_horizon_belief", "Believes in investing for the long term / that time in the market wins.",
              "it's for 15 years, a few red months don't matter"),
            v("averaging_understanding", "Understands that falls buy more units (rupee-cost averaging) or "
              "sees a fall as a discount.", "market down means I get more units for the same SIP"),
            v("past_recovery_seen", "Has seen or read about markets recovering after earlier falls.",
              "stayed through covid crash and it came back"),
            v("advice_reassurance", "Someone (friend, creator, forum, advisor) reassured them to continue.",
              "everyone here said don't stop, so I continued",
              "The decision itself handed over -> also code borrowed_conviction in root_cause."),
            v("goal_linked", "The SIP is tied to a named goal (house, retirement, child) that keeps it going."),
            v("automation_inertia", "Kept going because it is automatic / they don't look at it.",
              "I don't check the app, it just gets deducted"),
            v("affordable_amount", "The amount is small enough that stopping isn't worth it.",
              "it's just 1000 a month, not stopping"),
            v("other", "Signal present but fits no listed value; describe it in a rationale."),
            unknown(),
        ],
        "unknown_allowed": True,
    }

    add_value(fields, "check_frequency", v(
        "event_driven", "Checks when something prompts it: a market fall, news, an SMS / debit alert, a "
        "friend's comment. Not on a routine.", "I only open the app when I hear the market crashed",
        "Routine checking -> daily_or_more / weekly_monthly."), before="unknown")

    # flagged by 3 of 4 wave-1 taggers (23 Oct): tax saving and online communities had no code
    add_value(fields, "start_motivation", v(
        "tax_saving", "Started to save tax (ELSS / 80C).", "started ELSS SIP to save tax under 80C"))
    add_value(fields, "influencer_source", v(
        "online_community", "A forum, subreddit, blog author or online reviews (not a named creator / person).",
        "everyone on this sub said start an index fund SIP", "A YouTube creator -> youtube_creator."))

    behaviour_change = {
        "name": "behaviour_change",
        "question": "How has the writer's own SIP behaviour CHANGED since they started (stated change over "
                    "time, not a one-off action)? Unknown if no change over time is described.",
        "type": "multi",
        "values": [
            v("checking_faded", "Checked often at first, now checks less or not at all.",
              "first few months I checked daily, now I open it once in 3 months"),
            v("checking_rose", "Started checking more often, usually after a fall or worry.",
              "since the market fell I check every morning"),
            v("autopilot_forgot", "Stopped thinking about it; it runs on autopay unnoticed (good or bad).",
              "honestly forgot I even had a SIP running"),
            v("amount_increased", "Raised the SIP amount, added a SIP or used step-up since starting.",
              "started with 500, now 5000 after the hike", "One-time lump sum top-up only -> other."),
            v("amount_reduced", "Lowered the SIP amount (still running).", "cut my SIP from 10k to 3k"),
            v("paused_resumed", "Paused / skipped / stopped and later restarted.",
              "stopped in 2022, restarted last year"),
            v("funds_added", "Kept adding funds over time (portfolio sprawl).", "I now have 9 funds"),
            v("funds_consolidated", "Cut down the number of funds / restructured.",
              "merged my 7 funds into 3"),
            v("mode_switched", "Changed HOW they invest: SIP to lump sum or back, regular to direct plans, "
              "FD/RD to mutual funds, active to index funds, or mutual funds to direct stocks / other assets.",
              "moved from regular plans to direct", "Only cutting the number of funds -> funds_consolidated."),
            v("learned_more", "Became more informed: reads, learned XIRR, joined forums, changed how "
              "they judge returns.", "after a year I learned to look at XIRR not absolute"),
            v("confidence_fell", "Grew more doubtful or anxious about SIPs over time.",
              "initially excited, now I feel it was a mistake"),
            v("confidence_rose", "Grew calmer / more convinced over time.",
              "after seeing the 2024 fall recover I worry less"),
            v("other", "Change described but fits no listed value; describe it in a rationale."),
            unknown(),
        ],
        "unknown_allowed": True,
    }

    order = [f["name"] for f in cb["fields"]]
    order.insert(order.index("check_frequency") + 1, "behaviour_change")
    fields["behaviour_change"] = behaviour_change
    order.insert(order.index("stage"), "platform")
    order.insert(order.index("platform"), "investor_experience")
    order.insert(order.index("root_cause") + 1, "metric_branch")
    order.insert(order.index("root_cause") + 1, "stay_reason")
    fields.update({"metric_branch": metric_branch, "platform": platform, "rationale": rationale,
                   "investor_experience": investor_experience, "stay_reason": stay_reason})
    order.append("rationale")

    cb["version"] = "v1.9"
    cb["changes_from_draft"] = CHANGES
    cb["fields"] = [fields[n] for n in order]
    (HERE / "codebook.json").write_text(json.dumps(cb, ensure_ascii=False, indent=2), encoding="utf-8")
    print("fields:", ", ".join(order))


if __name__ == "__main__":
    main()
