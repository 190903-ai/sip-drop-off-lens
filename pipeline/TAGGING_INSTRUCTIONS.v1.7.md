# Deep tagging instructions (for Claude subagents)

You are coding public posts for a Product Management research project: why do FIRST-TIME mutual
fund investors in India continue or stop their SIPs? (Business goal: % of first-time investors on
Groww with an active SIP, i.e. ≥1 successful instalment in the last 30 days, 12 months after
starting.) Your codes feed the quantitative analysis, so consistency matters more than eloquence.

## Inputs
- The codebook: `pipeline/codebook.json` (version v1.6). Read it fully first: every field,
  every code's definition, include example and exclude rule.
- Your chunk: `data/samples/chunks/chunk_NN.jsonl` (50 items; fields id, source, kind, subreddit,
  date, video_title, text). Read every item in full. Hindi/Hinglish: read it yourself, don't skip.

## Output
Write `data/tags_deep/chunk_NN.jsonl`: exactly one JSON object per input item, same order, with:
- `id`
- `relevant`: "yes" if the item says anything about how retail investors start, run, check,
  change, pause, stop or feel about SIPs / mutual fund investing; "no" for stock trading, F&O,
  IPOs, KYC/demat-only issues, spam, pure fund-name lists. If "no", set every other field to
  "unknown" (["unknown"] for multi fields) and evidence_quote/rationale to "".
- every field in the codebook, using ONLY codes listed there (investor_experience replaces the
  old first_time flag; it matters most, because the study is about FIRST-TIME investors):
  single fields → one code string; multi fields → list of codes; text fields → string.

## Rules
1. Code only what the text shows. Never infer age, income, platform or motives that are not
   written. "unknown" is a correct, common answer.
2. Follow exclude rules literally. Pay special attention to:
   - action: `restructured` (stopped one fund, still investing) vs `stopped` (left MFs entirely).
   - stop_trigger = the EVENT; root_cause = the MECHANISM. Only code root_cause when the text
     shows the mechanism, not just the event.
   - `return_misreading` (wrong frame) vs `expectation_violation` (right frame, unmet prior
     expectation): both can apply.
   - `borrowed_conviction` only when the continue/stop decision is handed to someone else.
   - Stayed stories matter as much as drop-offs: `continued` (kept going through a loss or
     doubt), `nearly_stopped` (wobbled, then stayed: code what made them stay in root_cause /
     influencer_source / unmet_need), `increased`.
3. `evidence_quote`: an EXACT, verbatim span from the text (same script, no translation, no
   fixing typos, ≤200 chars) supporting root_cause or stop_trigger; "" if both are unknown.
   It will be machine-checked against the source; a non-verbatim quote is discarded.
4. `rationale`: one short sentence on the root_cause/stop_trigger choice; required whenever a
   field uses "other" (say what the other thing is).
5. Reddit comments and TradingQ&A replies are replies in a thread about SIPs/mutual funds; code
   what the reply says.
6. YouTube comments: the video title is context, not the commenter's words.
7. Play Store items carry an `app` field (groww, etmoney, paytmmoney, indmoney, coin): set
   platform = groww only when app is groww; competitor reviews are platform = other.
   Blog items (Jagoinvestor, Freefincal) are reader comments on personal-finance articles.

## Efficiency
Do not echo item texts back in your reply. Write the output file, then reply with only:
count of items coded, count relevant="no", the 3 most common root_cause codes in the chunk, and
anything in the codebook that did not fit (with item ids). Do not edit any other file.
