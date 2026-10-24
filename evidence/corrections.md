# AI corrections log (feeds the AI Evidence Log)

## Correction 1: relevance filter was too lenient (2026-10-21)

**Where:** Step 3, relevance scoring (Gemini 3.5 flash-lite), first 100-item test run.

**What the AI did wrong**
- Generic praise with no behavioural detail scored as most relevant (2):
  - "it's a very good app for SIP... I really appreciate it" → score 2
  - "easy login and faster to create sip in less than 1 minute" → score 2
- `first_time = yes` was assigned when the review said the *app* is good for beginners,
  not that the *writer* is a beginner ("Best app for beginners in mutual funds").

**Test-run distribution:** score 2 = 57, 1 = 33, 0 = 10. Far too many 2s for app-store text.

**Why it matters:** inflated relevance would flood theme counts with content-free praise
and inflate the "first-time investor" segment, making every downstream percentage wrong.

**Fix:** rewrote the rubric. Generic praise/abuse is now explicitly 0, the AI must pick the
lower score when unsure, and `first_time = yes` requires the writer to say *they* are new.
Re-ran the same 100 items to compare (see below).

**Result after fix (flash-lite, v2 rubric):** score 0 = 41, 1 = 25, 2 = 34; first_time = yes fell
from 20 to 4. Generic praise now correctly scored 0.

## Model selection log (relevance step)

| Model | Keep/drop agreement with flash | Exact 0/1/2 agreement | Free-tier limit hit | Decision |
|---|---|---|---|---|
| gemini-3.5-flash | reference | reference | 20 requests/day | Reference only |
| gemini-3.5-flash-lite (v2 rubric) | not measured directly | 82/100 | none observed | High-recall screen only |
| gemma-4-26b-a4b-it | 103/111 (93%) | 93/111 (84%) | none in a 20-call burst | **Final relevance scorer** |
| gemma-4-31b-it | n/a | n/a | errors + slow (18 s/call) | Rejected |

Free-tier limits measured from 429 errors: gemini-3.5-flash 5 requests/min and 20/day;
gemini-3.5-flash-lite 500 requests/day; gemma-4-26b 16,000 input tokens/min (no daily cap hit).
Gemma's token-per-minute cap, not request count, sets pipeline speed (~25-45 items/min).

Gemma errs mostly toward leniency (6 items flash=0 → Gemma=1). It missed 2 of 62 flash-relevant
items (MF Prime complaint, MF dashboard outage), i.e. ~97% recall. Flash is a reference model, not
ground truth; the human-labelled golden set is the final check.

## Correction 2: flash-lite ignored rubric exclusions → switched model for final scoring (2026-10-21)

**Where:** Step 3, same 100 items, v2 rubric.

**What the AI did wrong:** even with the explicit rule, flash-lite still scored off-topic items
as highly relevant (2):
- "I need customer support I have ipo autopay issue" (IPO, not SIP)
- "Is it mandatory to register for a demat account???" (account setup, not SIP)
- "my money has blocked to incorrect kyc information" (KYC)
- "place sell order of stocks at market price" (stock trading)

It also *under*-rated a genuine continuation need: "Allow us to pause SIPs indefinitely…
I just want to pause for a few months" got score 1.

**Check:** re-scored the same 100 items with gemini-3.5-flash. 18 disagreements; flash was right
in all 18 on manual review (IPO/KYC/demat/stock items → 0, "pause for a few months" → 2).
No item that lite scored 0 was scored >0 by flash.

**Fix:** two-pass design. flash-lite is kept only as a high-recall screen (its 0s are dropped);
gemini-3.5-flash makes the final relevance call. Trade-off: flash is limited to 5 requests/min on
the free tier, so it runs with 50-item batches and pacing.

## Correction 3: "borrowed conviction" was coded too broadly (codebook v1.7, 22 Oct 2026)

**What went wrong:** after the targeted first-timer/stayer pull, `borrowed_conviction` appeared on
26 of 193 new stories (13%, vs 4% before). The subagents had followed the codebook literally: v1.6
defined it as "asks others to decide continue/stop". So most tagged posts were simply people asking
Reddit "should I continue?". The finding's name ("started because someone told them to, so they
hand over the decision") claimed more than the tags showed, and the earlier "borrowed conviction
12% of community drop-offs" headline rested on the same broad definition.

**Check:** all 52 tagged stories (26 earlier, 26 new) re-read by hand. Only 8 show a specific
person steering the decision (a brother who opened the account and set the autopay; a friend who
recommended the first SIP; an agent who misled; a father following his son; a creator asked to
decide "mujhe itna knowledge hai nahi").

**Fix:** codebook v1.7 narrows the code to a SPECIFIC person steering the hold/stop decision; asking a
forum is coded by its mechanism instead. 44 tags re-coded (`data/recode/out/recode_04.jsonl`, each
with a note): volatility_mismatch, expectation_violation, portfolio_rationalisation, timing_mindset,
cashflow_rigidity, or unknown when the text shows no mechanism. `validate_deep.py` now applies
root_cause overrides and merges recode files instead of overwriting them.

**Effect:** borrowed conviction drops from a headline theme (12% of community drop-offs) to 8
stories (~1%). It is now an anecdote for interviews, not a finding. Also removed 2 cross-posted
duplicate stories in `analyze.py`.

## Correction 4: golden set showed the AI missing drop-offs and two rules that didn't match the metric (24 Oct 2026)

**Check:** 25 posts labelled blind by the user (plain-English labelling page, AI answers hidden), then
every disagreement reviewed with both answers visible (`evidence/golden_review.md`). Blind agreement on
story-or-not was 72% (below the 80% bar); against the reviewed final answers the AI reaches 80%.

**What the AI got wrong:**
- Missed drop-offs that never say "SIP": a user blocked from switching out of regular-plan funds
  (#2, tq_163724) and a user leaving Coin to redeem elsewhere (#12, ps_a27b9cbd) were labelled
  "not a story".
- Read a hypothetical ("Say I believe there is a better fund… what if I cancel?", #13) as the
  writer's own plan.

**Where the rules, not the AI, were wrong (user's call in review):**
- A SIP cut from ₹4,000 to ₹500 a month (#4) was a drop-off under our rules. The brief defines an
  active SIP as at least one successful instalment in the last 30 days, so a reduced, running SIP has
  stayed.
- A restart after a multi-year stop (#3) was "stayed" under our rules. The stop is the drop-off we
  study, so it now counts as a drop-off.

**Fix:** DETECT_INSTRUCTIONS gained rule notes (exits without the word "SIP" count; hypotheticals are
not stories); `analyze.py` counts reduced-but-running as stayed (5 stories) and restarts as drop-offs
(12 stories). Backups: `pipeline/DETECT_INSTRUCTIONS.before_golden.md`.

**Human error is reported too:** against the reviewed answers the user's own blind labels scored 92%
(story-or-not) and 75% (tags). In review the user took the AI's answer 18 times and kept their own 18
times.

## Correction 5: "thinking about stopping" was over-used, and app-switchers were mixed in (24 Oct 2026)

**Found by:** the golden-set review. The AI coded people asking for portfolio advice while their SIPs keep
running as `considering_stop` (#11, #15, #21). The user then pointed out that wanting to move to another
app is not doubting investing either.

**Check:** all 295 `considering_stop` tags re-read by Sonnet subagents with a sharpened rule (it needs a
stated or asked stop, pause, reduce, sell, redeem or switch out of their own SIP / fund):
247 kept, 22 → continued, 16 → unknown, 6 → increased, 3 → attempted_blocked, 1 → considering_start
(`data/recode/out/recode_09..13.jsonl`). Three hand fixes where a subagent missed pause/reduce questions.
Then 65 posts mentioning an app and a move were re-read: 29 → new code `considering_switch_platform`,
5 → unknown (`recode_14.jsonl`).

**Fix:** codebook v1.10 adds `considering_switch_platform`; the analysis puts it and `switched_platform`
in their own outcome group ("changed the app"): still investing, but a loss for Groww. The rule text is in
TAGGING_INSTRUCTIONS.md.

**Caveat:** three golden-set posts were in this re-check, so the golden-set scores are kept as measured
before the fix and are not re-scored on the posts that shaped the rule.

## Correction 6: evidence quotes that hid the SIP context (24 Oct 2026, after the data freeze)

**Found by:** the user, reading the Story Explorer. A story tagged as a stayer who stopped on retiring showed only
"Took early retirement last year after 21 years in the IT industry." The post is about a 19-year SIP (₹5K/month in
2005, raised to ₹2.5L/month, stopped in 2024), but the quote never says so.

**What the AI did wrong:** the tagging instructions asked for one exact line as evidence, and the AI often picked the
line that shows the *reason* (a support complaint, a fee, a life event) rather than the one that shows it is about a
SIP. 513 of the 1,848 quotes (129 of the 720 stories) contain no SIP or investing words at all.

**Fix:** `webapp/scripts/refine_quotes.py` widens each such quote to a continuous, word-for-word stretch of the same
post that keeps the original line and reaches the nearest sentence about the SIP or investment (max 420 characters).
479 widened, 34 left unchanged (the SIP sentence was too far away to stay contiguous). A first version also *replaced*
28 quotes with a different SIP sentence; that was dropped because it lost the reason the story was tagged for
(e.g. "hidden charges" became "constantly force you to buy sip").

**Effect:** quotes only; no tag, count or finding changes. The freeze is untouched; fixes live in
`data/quote_fixes_v1.jsonl` (id, old, new) and are applied by `webapp/scripts/build_data.py`. Every new quote is
asserted to be an exact substring of its post.
