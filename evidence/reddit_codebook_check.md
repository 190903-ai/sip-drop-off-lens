# Reddit stress test of codebook v1

## Method
One coder (an AI) read all 60 posts in `data/samples/reddit_check.jsonl` in full and applied `pipeline/codebook.json` v1 field by field, following its exclude rules. A script then checked that every code is valid and every evidence_quote is an exact substring of its post. The codes are in `evidence/reddit_check_coded.jsonl`.
**Sample caveat:** all 60 posts come from **r/mutualfunds**. None are from r/IndiaInvestments, r/personalfinanceindia or r/FIREIndia, so this tests one subreddit, not "Reddit". Most posts (57/60) are "review my portfolio / which funds" requests.

## Coverage

| Field | Items with a code other than unknown/other | Notes |
|---|---|---|
| root_cause | **9 / 60 (15%)** | 8 more items carry `other`, and 43 are unknown. Of the 20 items with a stop-type action, only 7 (35%) get a listed root cause. |
| stop_trigger | **9 / 60 (15%)** | 6 `other`. Of the 20 stop-type items, 9 (45%) get a listed trigger. |
| metric_branch | **60 / 60 (100%)** not unknown, but only **33 / 60 (55%)** map to a real branch (A–D) | 27 are `none`, mostly fund-selection posts from people who haven't started or just started. Branch use: intent 32, recovery 3, activation 1, **reliability 0**. |

For comparison, Play Store/YouTube coverage is not in this file, so read these as absolute levels. The low root_cause rate is mostly correct behaviour, because most posts contain no doubt and no stop. The `other` share is the real gap: of the 17 items with any root-cause signal, 8 (47%) needed `other`.

## Missing codes

| Field | Proposed code | Definition | Include example (verbatim) | Count | Item ids |
|---|---|---|---|---|---|
| action | `restructured` | Stops, switches or plans to stop the SIP in one or more funds **while continuing or redirecting investing** (to other funds or a direct plan). Total investing does not end. | "I’ve stopped SIPs in my old funds but not selling them to avoid taxes and let them compound" | **16** of the 20 stop-type items | 1sqjh5f, 1ta7nbz, 1sc324r, 1oi9ryt, 1ssv7s0, 1odi1fa, 1uatq0n, 1rann30, 1o8wyft, 1rd2gcn, 1qd7mtv, 1u9tzm2, 1qufhmp, 1o9s3v1, 1uwbpzm, 1tzvsvc |
| root_cause | `portfolio_rationalisation` | Stops or switches a SIP to fix their own portfolio design: overlap, too many funds, category concentration, regular→direct, or picks they made before they understood funds. | "started putting some amount in SIP a few years ago and selected random funds" | **6** (coded `other`); a 7th (1rann30, concentration) was forced into volatility_mismatch | 1uatq0n, 1sc324r, 1u9tzm2, 1odi1fa, 1uwbpzm, 1rd2gcn |
| stop_trigger | `self_review` | No outside event. A deliberate portfolio review, new knowledge, or an income change prompts the stop or switch. | "I am thinking of cancelling Nifty 50 index fund as i’ve heard it has like 50% overlap with PPFCF" | **5** (coded `other`); 2 more (1qd7mtv, 1tzvsvc "revamp") were left unknown | 1uatq0n, 1sc324r, 1rd2gcn, 1u9tzm2, 1odi1fa |
| unmet_need | `portfolio_construction_help` | Wants help with allocation, overlap, number of funds, or category mix. | "Does this allocation look over-diversified or reasonably balanced?" | **~46**, forced into independent_reassurance | Every independent_reassurance item except 1rgv53r, 1pixwfq and 1t93mbj |

Below threshold (one or two items each; note them but don't add codes):
- **Break-even exit:** sold as soon as a loss recovered to a small profit (1szvb7a).
- **Forward-return pessimism:** "golden days over" (1rd2gcn).
- **An LLM used as an adviser** (1rd2gcn; 1qxoexd used GPT to make a chart).
- **The fund itself closed to fresh SIPs**, e.g. Nasdaq FoFs (1wql6dc, 1sc324r).
- **Reddit itself as the influencer** (1qxoexd).
- **Age 19, not a student:** no life_stage value fits (1plcozb).

## Ambiguous boundaries (with proposed rules)

| # | Pair I hesitated between | Count | Proposed rule |
|---|---|---|---|
| 1 | action `stopped` / `considering_stop` vs `increased` (single-select, but one fund stopped while another is raised) | 16 | Add `restructured` (above). Keep `stopped` only when the user stops all MF SIPs or says they've stopped investing. |
| 2 | action `increased` vs `considering_start` (has a running SIP and plans to add a fund or amount) | ~11 (1oj5cp6, 1opp1pv, 1r1uai8, 1t3pojl, 1pkqmkp, 1wql6dc, 1plcozb, 1p8sspk, 1ojl7zh, 1tb5gvc, 1t60lwl) | If any SIP is already running, a planned addition is `increased`. Use `considering_start` only at stage pre_start. |
| 3 | metric_branch `intent` vs `none` for step-ups | 12 | The metric tree's C1 already lists step-up. Add "increase/step-up" to the `intent` definition. |
| 4 | `volatility_mismatch` requires distress, but Reddit users stop small caps calmly as a "risk-profile fit" decision | 3 (1oi9ryt, 1rann30, 1rgv53r) | Change the definition to "holds high-volatility funds and judges their swings as unsuitable for themselves, **with or without distress**". |
| 5 | `borrowed_conviction` vs a plain "is this normal?" benchmarking question | 4 (1qufhmp, 1rgv53r, 1q6jdbx, 1sx9p8p) | Code borrowed_conviction only when the **hold/stop decision** is handed to others or the writer says they have no reasoning of their own. "Is X normal?" → unmet `understand_my_returns`, root unknown. (Under this rule, 1qufhmp would move to unknown.) |
| 6 | `cashflow_rigidity` defined only for stopping or skipping, but people also avoid a fixed SIP up front, or plan a gap | 3 (1pixwfq, 1wqsurn, 1oc93em) | Extend it to cover "avoids a fixed SIP or plans a hiatus because income or surplus is irregular or will stop". |
| 7 | `own_returns_negative_flat` vs a fund that is positive but **lags a peer** | 2 (1o9s3v1, 1ta7nbz) | Add "or lagging a peer fund/benchmark" to the definition. (The safe_asset_benchmark exclude rule already routes "another fund" comparisons to return_misreading, which is wrong for a correct peer comparison.) |
| 8 | `platform_trust_erosion` (the app only) vs feeling misled by an advisor or distributor | 1 clear (1vav9s6); 2 regular-plan cases (1odi1fa, 1uwbpzm) went to rationalisation instead | Rename the scope to "platform **or intermediary** (app, distributor, advisor)". |
| 9 | stage: "stated duration" vs a stated **calendar start date** ("June 2024", "since 2018") | 6 (1oz9uzv, 1sqjh5f, 1o5t3zu, 1oc93em, 1p8sspk, 1ouc9dz) | Compute stage from the start date to the post date. |
| 10 | `outside_app_workaround = reddit_forum` and `in_app_confusion` "inside the app" | 59 of 60 got reddit_forum | On Reddit, reddit_forum is constant for the source, so ignore it in analysis. Code in_app_confusion for MF mechanics questions even when no app is named. |

## Dead codes on Reddit
- **Platform and operations codes are completely absent.** This is expected for literate forum posters, but notable:
  - stop_trigger: payment_failure, platform_change, order_redemption_delay, data_discrepancy, advice_received
  - root_cause: payment_plumbing, product_distrust
  - metric_branch: **reliability**
  - unmet_need: reliable_payment_recovery, accurate_timely_portfolio, responsive_support
  - emotion: angry_frustrated
- **Return-frame codes:**
  - root_cause: expectation_violation, safe_asset_benchmark
  - expectation: beat_safe_asset, steady_growth, savings_not_returns
- **Checking codes:**
  - checking_behaviour: daily_pnl, nav, fund_level_returns, transaction_status, avoids_checking
  - check_frequency: all values dead (60/60 unknown)
- **Other dead codes:**
  - start_motivation: creator_push, saving_discipline, app_ease
  - action: continued, reduced, switched_platform
  - income_type: self_employed_business, irregular_gig, homemaker (still no evidence for these segments)
  - influencer_source: app_platform

## Do metric_branch and root_cause map cleanly?
- **metric_branch:** this field works for stops, but the branch values (A–D) don't fit pre-start or just-started fund selection. These 27 posts all fall to `none`. Treating step-ups as `intent` needs the rule fix in #3. Fund-level restructuring codes as `intent`, but it **isn't a continuation risk at the user level**, because the user stays active. If the cancelled SIP is analysed as churn, `intent` will overstate the risk. Use `restructured` to separate the two.
- **root_cause:** this field maps poorly on Reddit. Nearly half of the root-cause signals needed `other`, because the codebook models *doubt-driven* stopping, while Reddit shows *design-driven* stopping (rationalisation).
- **Hypothesis H1 (return-interpretation gap):** two literate posters (1o5t3zu, 1rd2gcn) read XIRR correctly (11.77%, 14.5%) and still feel the returns are "below par" or consider pausing. That is a weak sign against H1 and in favour of forward-looking expectation effects.

## First-time investors on Reddit

| Status | Items |
|---|---|
| First-time, pre-start | 5 |
| First-time, invested ≤12 months (the target cohort) | **18 (30%)** |
| First-time cohort, now past 12 months | 5 |
| Experienced (multi-year or prior exits) | 9 |
| Unknown | 23 |

- **In-window first-timers almost never talk about stopping.** Only **2 of 18** do:
  - 1qufhmp: folio negative at month 12, "is it normal?"
  - 1oc93em: a planned 2-year hiatus for an MBA

  The other 16 post pre-emptive "review my new portfolio" requests. Most of the stop and restructure reasoning comes from people more than 12 months in, or of unknown tenure.
- **These first-timers are a different segment from Play Store/YouTube.** They are salaried, in their 20s, and invest ₹5k–₹1L/month. Many start heavy in small or mid caps on day one (1sx9p8p 60% mid/small, 1tev4v6, 1sqjh5f "haven’t experienced a real crash yet"). That is a latent volatility_mismatch that hasn't been tested yet.

## New themes Reddit adds versus Play Store/YouTube
1. **"Stopping" usually means reallocating, not quitting.** 16 of the 20 stop-type items cancel one fund's SIP while continuing or increasing total investing. If cancellations are read as SIP-level churn, they overcount drop-off. They still matter to Groww, because the switch is a moment where a gap or a platform move (to a direct plan, to Zerodha) can happen.
2. **Selection debt.** The first SIP is often picked without much thought: "random funds" (1u9tzm2), YouTube reels (1q6jdbx), a friend (1odi1fa), an advisor's regular plans (1rah287, 1p8sspk, 1uwbpzm), "didn’t do much analysis" (1rgv53r). Those first picks are the SIPs later cancelled or doubted (5 stop-type items).
3. **Planned cash-flow gaps.** These are anticipated income breaks (an MBA, 1oc93em; a master's in 2–4 years, 1sqjh5f), not shocks, plus irregular surplus leading to ad-hoc lumpsums instead of a SIP (1wqsurn, 1pixwfq).
4. **Cost and plan-type awakening.** Users learn about regular vs direct plans and stop SIPs to switch, through intermediaries rather than through the app (1vav9s6, 1odi1fa, 1uwbpzm).
5. **Macro and performance-driven rotation:**
   - Trump uncertainty → metals (1o8wyft)
   - chasing metal returns (1oc93em)
   - a peer fund lagging (1o9s3v1, 1ta7nbz)
   - a break-even exit (1szvb7a)
6. **Literate return reading still produces doubt** (see the root_cause bullet above).

## Recommendation: minimal codebook changes for v1.1
Each change below has at least 3 supporting items or is a clear boundary fix.
1. **action:** add `restructured`. Support: 16.
2. **root_cause:** add `portfolio_rationalisation`. Support: 6, or 7 including 1rann30.
3. **stop_trigger:** add `self_review`. Support: 5.
4. **unmet_need:** add `portfolio_construction_help`. Support: ~46.
5. **Boundary fixes:**
   - `increased` vs `considering_start` (#2, ~11)
   - step-up counts as `intent` (#3, 12)
   - volatility_mismatch "with or without distress" (#4, 3)
   - cashflow_rigidity covers avoidance and planned gaps (#6, 3)
   - borrowed_conviction only for a delegated hold/stop decision (#5, 4)
   - stage from calendar date (#9, 6)
6. **Smaller fixes:**
   - own_returns_negative_flat covers "lagging a peer" (#7, 2)
   - platform_trust_erosion covers intermediaries (#8)
   - mark reddit_forum as source-constant (#10)

**Do not** add codes yet for break-even exits, forward-return pessimism, LLM advice or fund closures (one or two items each). Re-test on the other three subreddits before freezing v1.1, because this sample is r/mutualfunds only.
