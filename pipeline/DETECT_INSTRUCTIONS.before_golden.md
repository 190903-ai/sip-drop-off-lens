# Story detection instructions (three-way)

You screen public posts for a Product Management study: why do FIRST-TIME mutual fund investors in
India keep or stop their SIPs? For each item, decide whether the writer tells a story about THEIR
OWN SIP / mutual fund investing, and which kind.

## Labels (one per item)
- `story_class`:
  - `dropoff_story`: the writer says THEY stopped, cancelled, paused, skipped, reduced, redeemed
    early, switched platform, had an instalment fail or bounce, tried to stop but the app blocked
    it, or are seriously considering stopping their own SIP.
  - `stayed_story`: the writer says THEY kept their own SIP going through a loss, a doubt, a
    failure or pressure to stop; nearly stopped and then stayed; stepped up; or restarted after a
    gap. Say-so is enough: "my SIP is down 12% but I'm continuing" counts.
  - `not_a_story`: advice to others ("you should keep investing"), questions with no personal
    situation, fund-picking, planning a first SIP, market talk, stocks / F&O / IPO, KYC-only issues,
    spam. When unsure, choose `not_a_story`.
- `story_type`:
  - dropoff_story: stopped, paused_or_skipped, reduced, redeemed, instalment_failed,
    attempted_blocked, considering_stop, restructured (stopped one fund but still investing),
    switched_platform
  - stayed_story: continued_through_loss, nearly_stopped, increased, restarted
  - not_a_story: none
- `investor_experience`: `first_time` if the writer says they are new, it is their first SIP, or
  they started within about the last year; `experienced` if they say they have invested for more
  than about a year or describe a long-held multi-fund portfolio; else `unknown`.
- `evidence_quote`: an EXACT span copied from the text (same script, no translation, no fixing
  typos, at most 150 characters) showing the story; "" for not_a_story. It is machine-checked.

Consistency rules (from the first 800 labels):
- A failed or blocked redemption/withdrawal counts only if the item mentions a SIP or ongoing
  mutual fund investing; a one-off withdrawal bug with no SIP context = `not_a_story`.
- A SIP amount debited from the bank but not invested = `instalment_failed`.
- Asking "should I stop?" with the writer's own SIP situation described = `considering_stop`;
  a generic question with no personal situation = `not_a_story`.
- `investor_experience` is coded for stories only; use `unknown` for `not_a_story`.

Play Store reviews are written by users about their own account. YouTube comments: the video
title is context, not the commenter's words. Text may be English, Hindi or Hinglish: read it.

Output one JSON object per item:
{"id": "...", "story_class": "...", "story_type": "...", "investor_experience": "...", "evidence_quote": "..."}
