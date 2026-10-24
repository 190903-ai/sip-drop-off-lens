# Web app build brief: "SIP Drop-off Lens" (AI Discovery Engine link)

Everything a fresh session needs to build and deploy the engine's web app. Decisions here are final
(agreed with the user 22–24 Oct); the design question phase is done and mockups v3 are approved.

## Inputs (frozen, do not edit)
- `data/freeze_2026-10-24/findings.json`: all numbers, per-question answers, quotes. Keys: `corpus`,
  `dropoff` (cuts incl. `without_etmoney`), `robustness` (app reviews vs community), `stayed`,
  `stayed_vs_dropoff`, `unmet_needs` (NOT "opportunities"; sorted by frequency, no score), `examples`,
  `questions` (q1–q9: n, strength, fields, by_outcome, quotes; q7 `differences`; q8 `segment_outcomes`).
  Outcome groups: stayed / wobbling / left / restructured / **changed_app** / unknown.
- `data/freeze_2026-10-24/tags_deep.jsonl` + `data/clean.jsonl`: build a static `stories.json` for the
  story explorer (verbatim quote, AI tags, AI rationale, source link; **no usernames**). Only relevant items.
- `data/freeze_2026-10-24/FREEZE.md`: corpus counts for the Sources / How it works pages.
- `evidence/golden_review.md`, `evidence/corrections.md`: Validation page content.
- Mockups (approved): `webapp/mockups/*.html` + `base.css` + PNGs (desktop / laptop / phone).

## Stack
- Next.js (App Router) on Vercel, deployed with the existing Vercel CLI login. Static JSON for everything
  except one API route for Ask the data.
- Ask the data: one server route calling **Gemma 4 26B** (`gemma-4-26b-a4b-it`) via the Gemini API, key from
  Vercel env var `GEMINI_API_KEY`, value taken from `.env` line `GEMINI_WEB_API_KEY` (never print it or put
  it in client code). Backup model `gemini-3.5-flash-lite` on the same key. Retrieval = tag filters +
  keyword search over tagged stories (no vector DB). Answers cite quotes.
- Fallbacks: the 9 brief questions pre-computed and cached (work with no AI); model failure / limit →
  keyword-search results + clear "AI limit reached" message; weak evidence → "not enough evidence".

## Pages (sidebar layout from mockups v3)
1. Findings dashboard: two drop-off worlds (app reviews = reliability; community = intent), first-time
   lens, stayers vs leavers, unmet needs by frequency (ET Money toggle removed by the user 24 Oct), the 9 questions with
   evidence strength (all strong except Q4 how-often = moderate).
2. Story explorer: grouped filters, quote left + AI tags right, AI reason + original link.
3. Ask the data: question card, 6 numbered starter prompts, recent questions, "Understood as" chips,
   cited answer, evidence panel (on phones directly under the answer).
4. How it works: 8-stage pipeline, sources and volumes, codebook history v1 → v1.10.
5. ~~Validation~~: removed by the user 24 Oct (content lives in the separate AI Evidence Log). Was: automatic checks (0 invalid codes / 0 quote errors), golden set blind 72% → 80% after
   review (tags 80%; action and root cause 69%), corrections 1–5.
6. Limitations: survivorship bias, public posts not a random sample, no social media (X/Instagram),
   Quora blocked, sources under 30 stories (blogs 24, INDmoney 16), Reddit collection stopped early
   (no r/IndianStreetBets, r/StockMarketIndia, Oct 2022–Sep 2024), Q4 how-often moderate.

## Hard rules (user)
- **No advice of any kind:** no investment advice, no fund picks, no product solutions. Personal
  "should I stop my SIP?" → describe what investors said + balanced stories + "talk to a SEBI-registered
  adviser" line. Visible "No advice" note on Ask.
- **Responsive at every size:** check 1440 / 1024 / 390, no horizontal scroll. Sidebar pinned (sticky,
  full height) down to 900px; below 900px a pinned top bar. Story cards stack below 1180px.
- Groww-inspired green look, no Groww logo. Name: "SIP Drop-off Lens".
- Graders are the audience; the app must keep working if the AI is down.

## Done when
Deployed Vercel URL works logged-out, all six pages render at the three widths, Ask answers a cached
brief question and a free-form one (and falls back cleanly with the key removed), PROGRESS.md gets a
"Day N" entry, and the checklist doc (https://claude.ai/artifact/3WSM87MTLtqJkEGsQJsXos) rows for the web
app are updated. Check /usage before any subagent wave (stop at ~70% weekly).
