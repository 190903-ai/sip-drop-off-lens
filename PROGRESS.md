# NextLeap Grad Project: progress log

Product: **Groww** · Goal: raise % of first-time MF investors with an active SIP at month 12
Deadline: **7 Nov 2026, 3:59 PM IST**
Plan & architecture doc (Claude Docs, private): https://claude.ai/artifact/EyY3tZ51EYWgiKBJMtuR1B

---

## Day 1: 21 Oct 2026

### Decisions made
- Product = Groww. Discovery engine = Python + AI, web app (Vercel) later. Claude builds, user reviews.
- **No paid APIs.** Free stack:
  - Gemma 4 26B (via the free Gemini key in `.env`) for bulk relevance / story detection
  - Claude subagents (Sonnet) for deep tagging, on the user's Pro plan
- Metric breakdown comes *before* the problem (brief's flow: Metric → Outcomes → AI discovery →
  Research → Problem). v1 is structural; v2 will attach evidence.

### Data collected (all without accounts/keys)
| Source | How | Clean SIP-related items |
|---|---|---|
| Reddit (r/mutualfunds, r/IndiaInvestments, r/personalfinanceindia, r/FIREIndia), Oct 2024 – Oct 2026 | Arctic Shift archive | 41,887 (29,648 posts + 12,239 comments) |
| Play Store: Groww + ET Money, Paytm Money, INDmoney, Zerodha Coin | google-play-scraper | 4,704 |
| TradingQ&A (Zerodha forum, named in brief) | Discourse JSON | 4,338 (849 threads) |
| YouTube comments (69 videos, EN + Hindi) | scrapetube + comment downloader | 2,278 |
| Blog comments (Jagoinvestor, Freefincal) | WordPress REST | 437 |
| **Total after cleaning/dedupe** | `pipeline/clean.py` | **53,644** |
App Store: Apple's feed returned nothing (log as a gap). Quora blocked (403).

### Pipeline built (`pipeline/`)
- `clean.py`: merge, dedupe, strict SIP filter, language tag; Reddit/TradingQ&A replies inherit
  relevance from their parent post
- `relevance.py`: flash-lite screen → Gemma final score (paused at ~350 items; lower priority now)
- `detect_stories.py`: Gemma finds first-person "I stopped / paused / skipped / my SIP failed /
  thinking of stopping" stories. Running via `run_until_done.sh` (auto-retry loop)
- `codebook.json` (built by `build_codebook.py`): **tag set v1.3**, 21 fields incl. root_cause,
  stop_trigger, metric_branch, segment signals, evidence_quote. Version history:
  v1 draft from open coding → v1.1 Reddit check (restructured, portfolio_rationalisation,
  self_review, portfolio_construction_help) → v1.2 tax_rule_change → v1.3 attempted_blocked
  (action) + missing_notification (trigger)
- `make_story_chunks.py`: turns newly detected stories into `chunk_sNN.jsonl` for tagging
  (incremental). Detector now round-robins across sources/apps so each batch is a mix.
- `TAGGING_INSTRUCTIONS.md` + `validate_deep.py`: Claude subagent tagging + automatic checks
  (valid codes, verbatim quote check, missing items)
- `sample_tagging.py` (Sample A, representative, with weights), `sample_stories.py` (regex story
  sample, now retired in favour of the AI detector)

### Results so far
- **393 items deep-tagged** by Claude subagents, all validated: 0 invalid codes, 0 hallucinated
  quotes (121/121 verified), 0 missing
  - chunks 01–03 = Sample A (representative, 150)
  - b01–b04 = regex "stories" (200, mostly advice posts → method retired)
  - s01 = **43 AI-detected drop-off stories** (all ET Money Play Store reviews; see below)
- Story detector: ~124 scanned, **45 stories found** (~40% hit rate) as of 17:40

### s01 findings: 43 ET Money drop-off stories
- Action: stopped 16, switched app 9, considering stopping 8
- Trigger: **platform change 18** (ET Money pricing/plan change), modify blocked 4, charges 3
- Root cause: **platform trust erosion 26/43**, payment plumbing 5
- Metric branch: intent 34, reliability 15 · Emotion: angry/frustrated 36/43
- Unmet needs: responsive support 12, flexible pause/modify 7, transparent costs 7, reliable payments 6
- Caveat: one app's event (ET Money monetisation) dominates; it is consistent with the Groww
  Play Store pattern (7/9 exits after app events) but NOT evidence about quiet first-time drop-off

### Early findings (hypotheses, not final)
- Exits in Play Store reviews are mostly triggered by **app events** (bounce charges, plan
  changes, redemption delays), not returns
- Same negative returns → some double their SIP, others quit; difference seems to be **how they
  read the number**
- **"Borrowed conviction"**: people who started on someone's advice outsource the continue/stop
  decision too
- On Reddit, "stopping" a SIP is usually **restructuring** (16/20), not quitting → measure churn at
  user level, not SIP level (noted in metric tree)
- **Survivorship bias**: quiet drop-offs rarely post; forums are dominated by engaged investors.
  This is why the interviews matter.

### Evidence Log material (`evidence/`)
- `corrections.md`: Correction 1 (relevance too lenient), Correction 2 (flash-lite ignored
  exclusions → model switch), model-selection table (flash vs lite vs Gemma: 93% keep/drop agreement)
- `open_coding_r1.md`, `reddit_codebook_check.md`: how the tag set was built and stress-tested

### Other deliverables ready
- `analysis/metric_tree_v1.md`: Activation / Reliability / Intent / Recovery
- `research/interview_kit.md`: screener, consent, 40-min guide, modules, synthesis plan

### Problems hit (and fixes)
- Gemini flash free tier = 20 requests/day; flash-lite = 500/day → switched bulk work to Gemma
- Gemma: 16k input tokens/min, slow on long prompts, frequent 503s → short prompts only,
  retry loop, Claude does the heavy tagging
- Low RAM: background jobs got killed → run 1–2 jobs at a time
- Regex "story" selection mostly caught advice posts → AI story detector instead

### Running overnight (independent of Claude Code)
- Story detector launched detached via WMI (hidden, no window):
  `pipeline/run_until_done.ps1 -Script pipeline/detect_stories.py -Log data/detect_log.txt`
  Loops passes, waits 5 min between passes during Gemma 503 outages, stops when "0 to go".
- Check progress: last lines of `data/detect_log.txt`; count `"story": "yes"` in
  `data/stories_detect.jsonl`.
- Stop it: Task Manager → end the hidden `powershell` + `python` processes (nothing is lost).
- Paused (resumable, lower priority): Gemma relevance scorer (~350 scored), Reddit comment
  collection (~16k comments collected).

### Status check 21:13
- Detector: 298 scanned, **79 stories** (~27% hit rate). Only ~50 items/hour: Gemma often returns
  empty responses (free-tier overload), failed batches retry next pass. Full 20k pool is not
  feasible → target ~300–400 stories total.
- Plan for Day 2: after ~12:30 PM IST (Google free quota reset), validate **flash-lite as a second
  story detector** against Gemma's 298 labels; if recall is good, run it in parallel.
- User chose to tag the 36 untagged stories in the morning together with the overnight batch.

### Status check 22:48
- Detector alive (charger was briefly off, laptop back on charge) but stuck: no new results since
  21:13, log shows only Gemma "empty response" / "failed after retries".
- **84 stories** found, heavily skewed: ET Money 53, Paytm Money 10, YouTube 6, Reddit 6,
  TradingQ&A 3, INDmoney 3, Coin 2, blog 1, **Groww 0**. Types: considering_stop 29, stopped 21,
  redeemed 14, instalment_failed 12, paused/skipped 6, restructured 2.

### Story-corpus plan (agreed 22:50)
84 stories are enough to *generate* hypotheses (themes usually saturate at 50–100 rich stories, and
the brief treats AI insights as a starting point validated by interviews), but the **skew** is the
problem: two-thirds come from one ET Money pricing event. Target: **~300 stories, ≥30 per source**.
1. After ~12:30 PM IST (free quota reset): flash-lite as a second detector, **only on
   under-represented sources** (TradingQ&A, YouTube, Reddit, blogs); no more ET Money.
2. Groww: run detection on remaining Groww Play Store reviews, and count drop-off stories already
   tagged in Sample A / open coding.
3. Fallback if Gemma and flash-lite both stay unreliable: Claude (Sonnet) subagents do story
   detection on the richest pool (~4k TradingQ&A + YouTube items).
4. In the deck, report the corpus honestly: "X stories across N sources (n per source)", and only
   treat a pattern as a hypothesis when it appears across sources (Play Store + forums + YouTube).

## Day 2: 22 Oct 2026 — plan reset: AI engine complete by 25 Oct

Plan doc (Claude Docs) was reviewed and rewritten (see link at top). Agreed changes:
- **Keyword pre-filter** (`pipeline/prefilter.py`) → ~2,000 candidates, capped per source,
  ranked towards first-time signals (+4). Recall on the 139 known stories: **97%** (fixed: Play
  Store reviews skip the pronoun check; Hinglish verb forms count as first person).
  First run: 1,964 candidates, 497 with a first-time signal.
- **Three-way detection** (`pipeline/detect_stories_v2.py` + `DETECT_INSTRUCTIONS.md`):
  dropoff_story / stayed_story / not_a_story (stayed = control group). Claude Sonnet subagents
  do the bulk in waves of 3–4 (chunks of 100 in `data/detect_v2/in` → `out`), `ingest` checks
  codes + verbatim quotes → `data/stories_v2.jsonl`. Gemma labels a comparison slice only.
- **Codebook v1.4** (22 fields): `investor_experience` (first_time / experienced / unknown;
  replaces the first_time flag, old tags mapped in validate_deep.py) and action `nearly_stopped`;
  `continued` widened to "kept going through a loss/doubt".
- First-time lens: first_time stated OR stage under 12 months = primary analysis group.
- Cut: relevance scoring, Flash-Lite test, live tagger in the web app. Golden set 20–25 items.
- Old Gemma detector **stopped** (final: 622 checked, 139 drop-off stories). The 96 untagged ones
  are in `chunk_s02`, `chunk_s03` for deep tagging.
- Targeted Groww pull: `collectors/playstore_groww_deep.py` (walks 1–5 stars separately, keeps
  SIP/MF/mandate/autopay reviews) → `playstore_groww_sip_deep.jsonl`, added to clean.py SOURCES.
  After it finishes: rerun clean.py → prefilter.py → `detect_stories_v2.py export` (incremental).
- Usage-limit rule: check `/usage` before each wave; stop at ~70% weekly.

### Status end of Day 2 build (22 Oct)
- Groww deep pull: ~120k reviews walked → 5,207 SIP-relevant → 4,378 clean (corpus now 57,757).
- Pre-filter has 3 tracks: main (stop/worry words, first-time +4), **stayed** (still investing,
  didn't stop, doubled my SIP…) and **Groww mentions** on Reddit/TQnA/YouTube. 2,672 candidates.
- Detection (Claude subagents, 30 chunks of ≤100; d09–d20 = lowest-ranked main track, SKIPPED to
  save usage): 1,664 labelled → 323 drop-off, 72 stayed. 0 invalid codes, 0 quote errors.
- Codebook **v1.6** (23 fields): + app_malfunction (v1.5), debit_after_cancel, support_failure,
  stay_reason (v1.6). `pipeline/recode.py` revisits only tags needing new codes (156 done);
  validate_deep.py applies `data/recode/out/*` as overrides.
- Deep tags: **884 items, 529 stories** (457 drop-off, 72 stayed; first-time drop-off 59).
- `pipeline/analyze.py` → `analysis/findings.json` (for the web app) + `analysis/findings_v1.md`.
  Headline: **two drop-off worlds** — app reviews = reliability (trust erosion 52%, payment
  plumbing 38%); community = intent (portfolio clean-up 27%, borrowed conviction 12%, cash-flow
  11%). Only flexible pause/modify crosses both. Stayers: 12m+ (59% vs 16%), accept volatility,
  read XIRR, calm. Most stayers don't state why (interviews must fill this).
- Golden set: `evidence/golden_set.xlsx` (25 items, blind, dropdowns) → user labels; key in
  `data/golden_key.jsonl`. Scoring script still to write.
- Gemma comparison slice (`detect_stories_v2.py gemma`) stuck at 10/100 (empty responses).
- Doc updated with results, chart redrawn (529 stories by source).

Schedule: 22 build + detection starts · 23 detection + golden-set file · 24 deep tag, validate,
**data freeze**, analysis · 25 web app (Next.js on Vercel) deployed.

### Next steps (Day 1 list, superseded by the Day 2 plan above)
1. Run `python pipeline/make_story_chunks.py` → deep-tag new `chunk_sNN` with Claude subagents
   (Sonnet, per TAGGING_INSTRUCTIONS.md) → `python pipeline/validate_deep.py`
2. Finish Sample A (150 more representative items)
3. Golden set: 20 items for the user to label by hand (Excel with dropdowns) → agreement score
4. Analysis: theme frequencies, segment cross-tabs, continuers vs leavers, opportunity scoring,
   metric tree v2
5. Discovery engine web app (dashboard + "ask the data" with citations) → deploy on Vercel
6. **User:** send interview screener; aim for 10–15 responses, then 5–6 interviews

### Day 2 evening (22 Oct)
- `pipeline/score_golden.py` written: reads `evidence/golden_set.xlsx`, skips unlabelled rows,
  reports story_class agreement + Cohen's kappa + confusion table, per-field tag agreement
  (human's one main code must be among the AI's codes), and a disagreement list →
  `evidence/golden_scores.md` + `data/golden_scored.jsonl`. Pass bar 80%.
- Golden set: user has labelled 1/25 so far (#1: human `increased` vs AI `continued` — first
  disagreement to discuss). Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -W ignore pipeline/score_golden.py`
- Status check: no detector processes running (old Gemma detector stopped, last log lines =
  empty responses). All 395 v2 stories + 139 old Gemma stories are deep-tagged (0 untagged).
  Chunks d09–d20 (lowest-ranked main track, ~1,200 items) were never run, by choice.
- Web app decisions (22 Oct): audience = graders; sections = findings dashboard, story explorer
  (verbatim quotes + source link, no usernames), Ask the data (free Gemini flash-lite/Gemma key,
  keyword-search fallback when the model fails); Groww-inspired look (green, no logo);
  **mockups first** for approval; deploy via existing Vercel CLI login.
- **Mockups for approval** (no image generator available, so HTML mockups with real numbers,
  screenshotted): `webapp/mockups/01_findings_top.png`, `02_findings_lower.png`,
  `03_stories.png`, `04_ask.png` (+ the .html sources and base.css). Name used: "SIP Drop-off
  Lens". Reference checked: myntra-wishlist-discovery-engine-weld.vercel.app has the same
  3-section layout (dashboard / evidence explorer / query), but its backend was down ("Failed to
  fetch" on every page) → our app ships findings + stories as static JSON; only Q&A calls an API.
- Waiting on: user approval of mockups; user's golden-set labels.
- Mockups v2 (user asked for the reference engine's layout): left sidebar (logo, Workspace nav
  with subtitles, theme toggle, "data frozen" note), page header = eyebrow + big title + one-line
  description; Story Explorer = Filters panel (grouped dropdowns) + stories panel (quote left,
  AI tags right, AI's reason + original link); Ask = question card + 6 numbered starter prompts +
  "Recent questions" panel; new `05_ask_answer.png` shows "Understood as" chips, cited answer,
  evidence panel and the AI-unavailable fallback. Groww green kept.
- Golden set role agreed: built in parallel; it gates the DATA (score ≥80% before freeze, else
  fix instructions → re-tag → re-run analyze.py), the app just reads findings.json.
- **Targeted pull started** (user asked: corpus thin for first-timers and stayers).
  `pipeline/prefilter_targeted.py` re-searches the whole corpus with a wider first-timer vocabulary
  (age, student, first salary, "started N months ago", Hinglish) + stayed vocabulary, skipping
  anything already labelled (d09–d20 items eligible). Matches: first_time 3,344, stayed 910, almost
  all Reddit posts. Kept 809 (639 first-time track, 170 stayed track) → `data/candidates_targeted.jsonl`
  → `detect_stories_v2.py export_targeted` → `data/detect_v2/in/chunk_t01..t09`. ingest now reads
  chunk_d* and chunk_t*. Wave 1 (t01–t04) running on Sonnet subagents; then t05–t09, then
  `detect_stories_v2.py ingest` → make_story_chunks / deep tagging of new stories → analyze.py.
- Targeted pull detected (4 Sonnet subagents, 22 Oct): 809 labelled → **193 new stories**
  (111 drop-off incl. 37 first-time; 75 stayed... see counts below), 0 bad codes, 193/193 quotes
  verified, 0 missing. stories_v2 now 2,473 labelled (441 drop-off, 147 stayed). Spot check of
  t07/t08 OK (one borderline: "need another fund / increase SIP" labelled considering_stop).
  Backup of pre-pull labels: data/stories_v2.before_targeted.jsonl.
  Counts of new stories: drop-off first_time 37 / experienced 44 / unknown 37; stayed first_time 21 /
  experienced 48 / unknown 6. Next: deep-tag the 193 (make_story_chunks → subagents → validate_deep)
  → analyze.py.
- Targeted stories deep-tagged (s14–s17, 4 Sonnet subagents): 193/193 valid, 0 quote errors.
- **Codebook v1.7 / Correction 3** (user chose "narrow it"): borrowed_conviction only when a specific
  person steers the decision; 52 tags re-checked by hand → 8 kept, 44 re-coded (recode_04.jsonl).
  validate_deep.py: overrides now include root_cause and merge across recode files.
  analyze.py: drops cross-posted duplicates (2). Backups: tags_deep.before_targeted.jsonl,
  findings.before_targeted.json / findings_v1.before_targeted.md.
- **Analysis re-run: 720 stories (573 drop-off, 147 stayed); first-time drop-off 102, first-time
  stayed 35.** Changes: borrowed conviction gone as a theme; community root causes = portfolio
  clean-up 30%, cash-flow 11%; community trigger own returns flat/negative 23%; community needs =
  portfolio construction help 48%, independent reassurance 29%; flexible pause/modify now 14% app vs
  7% community (no longer "in both worlds" at the 8% bar); stayers: long-horizon belief 22%,
  12m+ 62% vs 21%, XIRR 22% vs 3%.
- User rule (22 Oct): **the engine gives no advice of its own**: no investment advice in Ask the
  Data (personal "should I stop?" → describe what investors said + stories), and no product
  solutions (rename "Where to act" → neutral "unmet needs by frequency"). Mockups still to update.
- **Mockups v3** (22 Oct): numbers from the 720-story analysis; card tags now the AI's real tags
  (earlier cards had invented tags); borrowed conviction removed; community world retitled "They
  second-guess their own portfolio"; bridge = first-timers span both worlds; needs table is neutral
  (sorted by frequency, no opportunity score / "where to act"); Ask page has a "No advice" note and a
  personal-question state (no advice + SEBI-registered adviser line + balanced story links).
  **Responsive** (user rule: must fit every screen): sidebar → sticky top bar ≤1180px, columns stack
  ≤900/760px, checked at 1440 / 1024 / 390 with no horizontal scroll. PNGs: `*.png`, `*_laptop.png`,
  `*_phone.png`. In the real app, on phones put "Evidence behind the answer" directly under the answer.
- User: **keep the side panel fixed**. Sidebar is now pinned (sticky, full height, scrolls itself if
  needed) and stays a sidebar down to 900px (laptops/tablets landscape); only below 900px (phones /
  portrait tablets) it becomes a pinned top bar. Story cards stack quote-over-tags below 1180px.
  Verified scrolled at 1440 / 1024 / 390 (nav top stays 0): `03_stories_scrolled*.png`.

## Day 3: 23 Oct 2026

### Coverage check: can the engine answer the brief's 9 questions?
Known-value counts across the 720 stories (unknown/none/other excluded):
- **Strong:** Q3 stop drivers (stop_trigger 486, root_cause 447), Q5 in-app confusion (370, but 361 are
  drop-off and 274 are app reviews), Q6 outside-app workarounds (330), Q9 unmet needs (598).
- **Thin:** Q1 why start / expect (start_motivation 94, expectation 43, zero from app reviews),
  Q7 continue vs drop off (stay_reason 46 of 147 stayers; the comparison has to lean on other fields),
  Q2 change over months (stage 304, but one snapshot per person, so no real timeline).
- **Not answerable yet:** Q4 checking frequency (check_frequency 4/720; checking_behaviour 200, mostly
  transaction_status), Q8 segments (income 101, life stage 144, source of money 44, influencer 86;
  first-time drop vs stay cross-tabs are in single digits).
- Cause: the corpus is drop-off/stayed *stories* only. General discussions about checking habits,
  expectations and who people are were filtered out by story detection.
- Raw material in the full 57,757 corpus (rough regex): checking-frequency 110, expectations 86,
  "first months / after N months" 315, segment self-descriptions 2,086.

### Goal set by the user (23 Oct): the engine must answer ALL nine brief questions
Collect more data where needed. Work done:
- **New data** (no accounts/keys):
  - App Store feed works again: `collectors/appstore.py` now reads 6 apps (Groww, ET Money, Paytm Money,
    INDmoney, Coin, Kuvera) in two sort orders → 4,725 reviews, 1,431 SIP-related (1,031 after cleaning).
  - Blogs: + Basunivesh, Stableinvestor, and new search terms (expected, check, first salary, years old...)
    → 6,609 raw blog comments (4,496 clean).
  - YouTube round 3: 18 new queries (SIP journeys, checking, expectations, first salary, students, Hindi)
    → 207 videos, 4,989 comments.
  - Reddit (`collectors/run_reddit_more.ps1`, detached via WMI, log `data/reddit_more_log.txt`):
    `collectors/reddit_threads.py` pulls FULL threads (≤100 comments) of question-shaped posts (checking,
    expectations, journeys, who-I-am), then r/developersIndia + r/IndianStreetBets + r/StockMarketIndia
    (Oct 2024–Oct 2026), then the four core subs back to Oct 2022, then threads again. ~12 threads/min,
    expected to run overnight. Arctic Shift full-text search proved too flaky (1 of 4 calls worked).
- **Codebook v1.8** (24 fields): + `behaviour_change` (Q2 had no field) and check_frequency `event_driven`.
  Backup `pipeline/codebook.v1.7.json`. TAGGING_INSTRUCTIONS gained a "Question chunks" section
  (thread_title context, evidence_quote fallback order). Backup `TAGGING_INSTRUCTIONS.v1.7.md`.
- **`pipeline/prefilter_questions.py`**: 5 tracks (checking, start_expect, journey, who_i_am, stayed_why)
  over the whole corpus, not just stories; per-source caps; stratum `Q/<track>` in
  `data/samples/questions_sample.jsonl`; chunks `chunk_qNN`. First run (corpus 65,550): 1,030 items,
  q01–q18.
- **`analyze.py`**: new `questions` section in findings.json / findings_v1.md: per brief question, items
  with a signal, strength per field (strong ≥100 / moderate 30–99 / thin <30; question = weakest field),
  splits stayed vs left/wobbling and first-time, quotes; Q2 action-by-stage, Q7 stayer-vs-leaver diffs,
  Q8 stayed share per segment value. Backup `pipeline/analyze.before_questions.py`.
- Tagging wave 1 (q01–q04, Sonnet subagents) started 23 Oct ~22:40.
- Next: waves q05–q18 → validate_deep.py → analyze.py; when the Reddit chain finishes: clean.py →
  prefilter_questions.py (second run, picks only untagged items) → tag → analyze. Then golden set, freeze.
- **Wave 1 (q01–q04) result + fixes (23 Oct ~22:45):** validated clean (0 issues), but yield was low:
  4 check_frequency values in 240 items. Cause: the checking pattern matched any "XIRR" mention. Also
  "should I continue… because" questions passed as stayers, and a bare "initially" passed as a journey.
  Fixes: first-person + frequency phrase required for checking; THEN…NOW pair required for journey;
  I + past-tense stayed verb for stayed_why. Codebook v1.8 + start_motivation `tax_saving`,
  influencer_source `online_community` (flagged by 3 of 4 taggers). Untagged q05–q18 were deleted and
  re-cut: second batch = 730 items, q05–q17.
- **Collector gap found:** reddit.py kept only posts that say SIP/MF, so "How often do you check your
  portfolio?" threads were dropped at collection (only 15 survived). reddit.py now also keeps
  HABIT_PATTERN posts; new chain step 1 `reddit.py habits 2024-10-01 2026-10-22` re-lists the four subs
  for them (no comments; reddit_threads.py, MAX_THREADS 2400, fetches their threads with checking first).
- Wave 2 (q05–q08) started ~22:55.
- **Wave 2 (q05–q08) validated** (0 issues). Per question after waves 1–2 (stories + 480 question items):
  Q1 motivation 207 / expectation 75 · Q2 behaviour_change 77 · Q4 check_frequency 20 (thin) ·
  Q7 stay_reason 67 · Q8 income 183, life stage 257, source of money 106, influencer 167 (all strong).
- **`pipeline/recode_v18.py`**: the 720 stories predate v1.8; 207 with time / checking signals →
  `data/recode/in/recode_05.jsonl` (130) + `recode_06.jsonl` (77) to fill behaviour_change +
  check_frequency. (in/ had no recode_04: that number exists only in out/ for Correction 3, so the
  script now numbers after max(in, out).) validate_deep.py: a v1.8 recode answering "unknown" never
  wipes a value; earlier recodes still can (Correction 3 set 6 root_causes to unknown on purpose;
  borrowed_conviction count checked: 13, unchanged).
- Wave 3 started ~23:20: recode_05, recode_06, q09, q10.
- **Wave 3 validated** (recode_05/06: 118 of 207 stories got behaviour_change; q09/q10 clean).
  Codebook **v1.9**: behaviour_change + `mode_switched` (SIP↔lump sum, regular→direct, FD→MF, MF→stocks),
  the commonest "other". 18 "other" tags re-mapped by hand → `data/recode/out/recode_07.jsonl`
  (plain stops / fund swaps stay "other"; action covers them).
- After wave 3: Q2 behaviour_change **222 (strong)**, Q1 motivation 207+ / expectation 86, Q7 stay_reason 71,
  Q4 check_frequency **26 (thin)**. Reddit habits listing: 14k r/mutualfunds posts scanned, 1,322 kept,
  but only ~15 "how often do you check" threads → Q4 likely ends moderate; frequency is rarely stated
  publicly (say so in the deck; interviews cover it).
- Wave 4 (q11–q14) started ~23:05. Left after it: q15–q17, then the post-Reddit round.
- **Wave 4 (q11–q14) validated** (0 issues). 617 relevant question items + 720 stories. **No question is
  thin any more:** Q1 motivation 284 / expectation 106, Q2 263, Q3 736, Q4 what 334 / how often 48
  (moderate), Q5 468, Q6 520, Q7 stay_reason 83 (moderate), Q8 income 259 / life stage 349 / money 152 /
  influencer 225, Q9 1,039.
- Q8 segment → share who stayed (items with a known outcome; directional, public posts are not a random
  sample): salaried 42% (n=118) vs student 25% (20); 30s–40s 48% (52) vs 20s 35% (136); own earnings 49%
  (65) vs family money 20% (10, thin); advisor/distributor-led 23% (48) vs self-directed 42% (43), family 46% (26).
- Candidate code for later: stop_trigger "learned direct plans are cheaper" (3 taggers used other).
- **Paused here (23 Oct ~23:30)** for the user's /usage check. ~24 Sonnet subagent runs so far today.
  Left: q15–q17 (3 chunks), then after the overnight Reddit chain: clean.py → prefilter_questions.py →
  tag the new chunks → validate_deep.py → analyze.py.
- User: /usage = **47% weekly** at ~23:35 → ran q15–q17 (3 runs). The post-Reddit round waits for a
  fresh /usage check tomorrow (stop at ~70%).
- **q15–q17 validated** (0 issues; 2,047 tag rows in total). Final for tonight, 720 stories + 712 relevant
  question items: Q1 motivation 307 / expectation 112 · Q2 286 · Q3 768 · Q4 what 358 / how often 58
  (moderate) · Q5 485 · Q6 532 · Q7 stay_reason 91 (moderate) · Q8 580 (all four fields strong) · Q9 1,104.
  rd_1n0d3sr (manual buys → autopay) added to recode_07 as mode_switched.
- Reddit chain at 23:50: habits listing finished r/mutualfunds (30,072 scanned), now on the next subreddit.
- **Tomorrow (24 Oct):** check /usage → if under ~70%: when `data/reddit_more_log.txt` says "chain done"
  (or at least the habits + threads steps are done), run clean.py → prefilter_questions.py → tag new
  chunk_qNN (Sonnet subagents, same prompt as q11–q16) → validate_deep.py → analyze.py. Then golden set
  scoring, data freeze, web app numbers.
- Stopped 23 Oct ~23:55: user's /usage = **89% current session, 49% weekly**. No subagents running.
  Reddit chain keeps running detached (uses no Claude usage).

## Day 4: 24 Oct 2026

- Reddit chain had died at ~23:19 on 23 Oct (laptop slept): habits listing finished r/mutualfunds (1,322 kept),
  stopped inside r/IndiaInvestments; the threads step for the habit posts never ran. **Relaunched detached via
  WMI at 12:51** (resumes; same log `data/reddit_more_log.txt`).
- **Gap fixed in clean.py:** `reddit_habits_posts.jsonl` was never read, and its posts would fail STRICT_SIP by
  design. Added to SOURCES + `TOPIC_FILTERED` (skips STRICT_SIP). Corpus 67,698 → **70,957**.
  Backup `data/clean.before_round2.jsonl`.
- prefilter_questions.py round 2 (backup `data/samples/questions_sample.before_round2.jsonl`): journey 194,
  start_expect 141, who_i_am 150, checking 3, stayed_why 0 → **488 items, chunks q18–q26 (55 each)**.
  Checking stays thin until the habit threads are fetched.
- User /usage: under ~60% weekly → run all 9. Wave 1 (q18–q20) started.
- **Requirements checklist** (Claude Docs): https://claude.ai/artifact/3WSM87MTLtqJkEGsQJsXos — brief Part 1 +
  Evidence Log (19 rows: 9 ready / 7 partial / 3 not started) and plan-doc commitments (20 rows), plus gaps.
- Golden set still 1/25 labelled.
- Round 2 waves 1–2 (q18–q23) validated: 0 invalid codes, 0 quote errors (2,377 rows). Hand fix
  `data/recode/out/recode_08.jsonl` (2 specific planned step-ups → action increased; validate_deep.py overrides
  now accept `action`). TAGGING_INSTRUCTIONS now says codebook v1.9. Wave 3 (q24–q26) running.
- Candidate codes for v2.0 (repeated "other"): risk appetite rose (behaviour_change), ChatGPT/AI as influencer,
  advisor/broker-led start (start_motivation), "increases SIP with each raise" (stay_reason).
- **User decisions (24 Oct):** Gemma vs human golden-set comparison DROPPED; **mockups v3 approved**;
  analyze.py "Opportunities" → `unmet_needs` / "Unmet needs by frequency": score removed, sorted by story count
  (exit rate, first-time, community counts kept as description). Web app must read `F["unmet_needs"]`.
- **Round 2 complete (24 Oct afternoon):** q18–q26 all validated (2,535 tag rows, 0 issues). 488 tagged → 363
  relevant. analyze.py re-run (backups `analysis/findings.before_round2.*`). 720 stories + 1,075 question items:
  Q1 motivation 420 / expectation 151 · Q2 385 · Q3 862 · Q4 what 413 / how often **60 (moderate)** · Q5 524 ·
  Q6 676 · Q7 stay_reason **109 (now strong)** · Q8 817 · Q9 1,398. Q4 how-often is the only moderate field left.
- Q7 headline diffs (stayed vs left/wobbling): amount_increased 42% vs 3%, calm 30% vs 1%, angry 2% vs 34%,
  XIRR checking 17% vs 8%, specific goal 15% vs 5%.
- Next: when the Reddit chain reaches the threads step and finishes, clean.py → prefilter_questions.py (checking
  track) → tag → validate → analyze (lifts Q4). Then golden set (user: 24 labels left) → data freeze → web app.
- **Golden set made easier (user is not from finance):** guided labelling page
  https://claude.ai/artifact/BXYZ9EpuPxztvxuJc4ybZv (source `evidence/labeller/template.html` + build →
  `golden_labeller.html`). One post at a time, plain-English questions with tap options mapped 1:1 to codebook
  codes, "Can't tell" = unknown, glossary, blind (no AI answers). Fields: story_class, investor_experience,
  action, stop_trigger, root_cause (**metric_branch dropped**, user choice; scorer skips blank fields). Item #1
  to be redone. Answers save to the artifact db, collection `labels`, doc id = item id (owner-only rules).
  When done: read `labels` with ArtifactData → write into evidence/golden_set.xlsx "Label these" → score_golden.py.
- **Golden set labelled (25/25) and scored, raw blind result BELOW BAR:** story_class 72% (18/25, kappa 0.56);
  investor_experience 82% (n17), action 38%, stop_trigger 56%, root_cause 44% (n16). Labels imported into
  evidence/golden_set.xlsx (backup golden_set.before_labeller.xlsx); ps_523c96c6 had only a note → not_a_story;
  yt_UgzJz has only Q1–2.
- My read of the 7 story_class misses: AI clearly wrong #2 tq_163724 (blocked switch out of regular plans),
  #12 ps_a27b9cbd (leaving Coin, redeeming elsewhere); human slip per rules #4 (SIP cut 4000→500 = reduced = drop-off),
  #5 (step-up + lump sums = stayed); rule-boundary #3 (stopped 2010, restarted 2015), #9 ("continuing a few more
  months, will see"), #13 (hypothetical "say I…" cancel after exit load). Tag patterns: AI infers
  platform_trust_erosion where human says can't tell (4×); action boundary considering_stop vs continued /
  attempted_blocked. Next: adjudication pass with the user (unblinded), report raw + adjudicated agreement.
- **Review step added** to the labeller (tab 2, v3): 19 posts / 36 disagreements, both answers shown, choose
  mine / AI's / something else + reason; Claude's reading shown only on the 7 story_class ones. Saves to db
  collection `review` (doc = item id, {field: {choice, final, reason}}); blind `labels` untouched.
  Build: `evidence/labeller/build.py` (template.html + golden_items.json + review_items.json).
  When done: report raw blind agreement AND agreement vs final answers; AI-wrong cases → instruction fixes =
  Evidence Log corrections.
- **Golden-set review done (19 posts, 36 disagreements: 18 kept human, 18 took AI).** Report:
  `evidence/golden_review.md`; finals `data/golden_review.json`. AI vs final: story_class **80% (20/25, at bar)**,
  experience 94%, action **69%**, trigger 88%, root cause **69%**; all tag fields 80% (52/65). Human blind vs final:
  story 92%, tags 75%. Raw blind numbers stay reported (72% / 55%).
- AI error patterns: (A) missed drop-offs that don't say "SIP" (#2 blocked switch out of regular plans, #12 redeem +
  leave Coin); (B) action considering_stop over-used when the writer asks for advice while still investing
  (#11, #15, #21; 295 considering_stop tags in total); (C) rule disputes: user calls a restart-after-stop a
  drop-off (#3; 12 "restarted" stories) and a reduced SIP stayed/still active (#4; 5 "reduced" stories).
  #9 is inconsistent (final story = stayed, final action = considering_stop). Fixes await user decision.
- **User decisions after golden review (24 Oct):** (1) both rule changes adopted in analyze.py: story_type
  reduced → stayed_story, restarted → dropoff_story; OUTCOME reduced → stayed. (2) considering_stop re-check:
  295 → recode_09..13 (Sonnet, sharpened rule incl. pause/reduce asks); 247 kept, 48 changed; 3 hand fixes
  (rd_1s6nr6b, rd_1tshecp, rd_1o1xn2h → considering_stop). validate_deep 0 issues. Stories now 580 drop-off /
  140 stayed. Backups analysis/findings.before_recheck.*. Note: golden items rd_1kr7wvi, tq_491514, rd_1p69v0f
  were in this re-check, so golden scores stay the pre-fix numbers (no re-scoring on the items that shaped the rule).
  (3) **User: wanting to switch apps = "changing the app", not thinking of stopping** → codebook **v1.10** adds
  action `considering_switch_platform` (backup pipeline/codebook.v1.9.json); analyze.py OUTCOME
  switched_platform + considering_switch_platform → new outcome `changed_app` (EXITS unchanged: still a loss for
  Groww). 65 candidates (app + move words among considering_stop/unknown re-check items) → recode_14 running.
- Corrections log: Correction 4 written (golden set: AI misses + two rules that didn't match the metric).
- recode_14 done: 29 → considering_switch_platform, 31 kept considering_stop, 5 unknown. validate 0 issues;
  analyze re-run. Q3 pool outcomes now: changed_app 68, wobbling 232, left 121, restructured 153, stayed 85,
  unknown 203. Q7 (stayed 326 vs left/wobbling 413, app-changers excluded): angry 2% vs 30%, calm 27% vs 1%,
  amount increased 39% vs 2%. Correction 5 logged.
- **Collector stopped by user decision (24 Oct ~17:30).** Done before stopping: habits listing (r/mutualfunds,
  r/IndiaInvestments, part of r/personalfinanceindia), threads step 2 (2,043 threads; thread replies 11k → 39.6k),
  wide step partial (r/developersIndia only, 2,956 posts kept). Not collected: r/IndianStreetBets,
  r/StockMarketIndia, Oct 2022–Sep 2024 history → Limitations page.
- clean.py → corpus **91,150** (backup data/clean.before_q4.jsonl). prefilter_questions.py gained
  `--tracks=`; Q4 round = checking 70 + start_expect 60 + journey 53 + stayed_why 1 = 184 items, chunks q27–q29
  (who_i_am skipped: Q8 already strong). Tagging (Sonnet, codebook v1.10) running.
- Q4 round validated (q27–q29: 184 coded, 53 relevant — generic thread replies, low yield; 0 issues; 2,719 rows).
  check_frequency 60 → **73 (moderate, final)**: rarely by choice 51%, weekly/monthly 26%, daily+ 21%, event-driven 3%.
  Q7 stay_reason 116.
- **DATA FROZEN 24 Oct** → `data/freeze_2026-10-24/` (findings, tags, stories, codebook v1.10, golden review,
  FREEZE.md with counts + sha256 fingerprints). 720 stories (580/140) + 1,128 question items; all 9 questions
  strong except Q4 how-often (moderate; stated rarely in public — interviews cover it).
- **Next session: build the web app** (Next.js on Vercel) from approved mockups v3, reading the frozen
  findings.json (`unmet_needs` key, outcome group `changed_app`). Pages: findings, story explorer, Ask the data
  (Gemma, cached 9 questions, no-advice + fallbacks), How it works, Validation, Limitations.
- **Web app key:** user created a separate free Gemini key for the website → `.env` as `GEMINI_WEB_API_KEY`
  (gitignored; never printed). Tested 24 Oct: gemma-4-26b-a4b-it OK (2.6 s), gemini-3.5-flash-lite OK (1.6 s).
  At deploy: `vercel env add GEMINI_API_KEY` for the web project, fed from this line, not typed in chat.
  Pipeline keeps `GEMINI_API_KEY`.

## Day 4 (evening): web app built, 24 Oct 2026

- **"build sip lens"**: Next.js 15 app in `webapp/site` built from WEBAPP_BRIEF.md + mockups v3 (styles ported from
  `webapp/mockups/base.css`). Six pages: Findings (cut toggle All / First-time / Groww / Without ET Money, two worlds,
  stayers vs leavers, unmet needs by frequency, 9 questions with strength), Story Explorer (URL-driven filters, quote
  left + AI tags right, AI reason + original / store-page link), Ask the Data, How it works, Validation, Limitations.
- Data: `webapp/scripts/build_data.py` reuses analyze.py's loaders (asserts the frozen hashes and counts 720 / 580 /
  1,128). Writes `webapp/site/data/` (findings.json copy, stories.json 1,848 rows, search.json server-only excerpts,
  cuts.json) + `public/data/stories.json`. Usernames scrubbed (u/…, @…). 172 items had no evidence quote → a verbatim
  opening excerpt, labelled as such. App-store reviews link to the store page (no per-review permalink).
- Ask: `/api/ask` = keyword "understanding" (chips) → topic-scoped pool → tag + keyword retrieval (12 items, ≤4 per
  source) → Gemma 4 26B, backup Gemini Flash-Lite (Gemma returned some 500s; backup covered) → checks: every sentence
  needs a story citation unless it only reports counts; every % must exist in the counts; quotes verbatim; advice /
  "should" / "to prevent" sentences removed. Personal "should I" → no-advice + SEBI line + stopped & stayed stories.
  Weak evidence → "Not enough evidence". AI down / 429 → matched stories + clear message.
- Saved answers (`webapp/site/data/cached.json`, via `scripts/precompute.mjs`): 9 brief questions + 6 starters,
  each reviewed; Q7 uses stayed-vs-left differences, Q8 per-segment stay shares (thin segments excluded).
- Checked: `next build` passes; no horizontal overflow on all 6 pages at 1440 / 1024 / 390; production server with
  the key removed → saved answers still work, free-form falls back cleanly.
- Key: local `webapp/site/.env.local` (gitignored, from `.env` GEMINI_WEB_API_KEY, never printed).
- **Blocked: Vercel CLI token expired** → user to run `vercel login`; then deploy from webapp/site, add
  GEMINI_API_KEY (production) from the .env line, verify logged-out, update the checklist doc rows.
- **User review round (24 Oct night):** sidebar fixed (overflow-x clip), Findings filter moved into Headline finding,
  funnel panel → link in intro, golden-set line removed, text ~10% smaller, strength chips removed, "Without ET Money"
  toggle removed (brief updated), Story Explorer cards scroll separately (>900px), store-page links removed (source
  name only), filters trimmed to Outcome / Experience / Source / Root cause / Trigger / Unmet need / Stay reason.
- **Correction 6:** 513 weak quotes (no SIP / investing words) → 479 widened to verbatim spans with SIP context
  (`webapp/scripts/refine_quotes.py` → `data/quote_fixes_v1.jsonl`, applied in build_data.py; freeze untouched).
  Card chip now follows story class (Kept going / Stopped or wavering), not the action outcome (56 stories disagreed).
- Open: Validation tab → replace with an "AI Evidence Log ↗" link? (awaiting user). Deploy still blocked on `vercel login`.
- Validation tab removed from the engine (user, 24 Oct): the golden set and corrections live in the separate AI Evidence Log (Google Doc). Limitations page now points there.
- 24 Oct: sidebar footer "Data frozen 24 Oct 2026" replaced by an "AI Evidence Log ↗" link (user's Google Doc).
- 24 Oct (grader review fixes): Findings "Unmet needs" table became "Opportunity areas: what investors lacked, compared" (rank by all drop-offs or first-time investors; adds first-12-months and full-exit columns; built in build_data.py as cuts.json `_opportunities`; descriptive, no score). Ask the Data: nonsense/off-topic questions get "didn't understand"; questions naming a source (YouTube, Reddit, Play Store, App Store, TradingQ&A, blogs) or app (ET Money, Coin, Paytm Money, INDmoney, Kuvera) are filtered to it; app crashes/bugs no longer read as market crashes; "crashes/falling" now match market-fall questions; opportunity questions answered from the comparison; Flash-Lite gets a JSON schema + one retry; mixed curly/straight quotes no longer leave broken fragments. Metric tree draft (analysis/metric_tree_v1.md, written by Claude) deliberately NOT used in the engine: the user hasn't made their own Part 2 decomposition yet.
- 24 Oct: pushed to private GitHub repo https://github.com/190903-ai/sip-drop-off-lens (code + docs; raw /data/ and .env excluded).
- 24 Oct: deployed to Vercel production: https://sip-drop-off-lens.vercel.app (GEMINI_API_KEY set as a Production secret; tested logged-out). Answer checks now also drop lowercase-start fragments and first-person text outside quotes.
