# AI Evidence Log: SIP Drop-off Lens (Groww)

24 Oct 2026

The discovery engine read 91,150 public SIP posts and kept 720 personal stories (580 drop-off, 140 stayed) plus 1,128 posts that answer the brief's nine questions. Against 25 hand-labelled posts, the AI agreed with the human 72% of the time blind and 80% after reviewing every disagreement. AI output was rejected or corrected six times; each correction is logged below with the reason.

This log covers the three things the brief asks for: the sources and volume analysed, a hand-labelled golden set with how often the engine agreed and where it failed, and the places where AI output was rejected or corrected. All figures come from the data frozen on 24 Oct 2026, the same data the engine's web app reads.

**Try the engine:** [sip-drop-off-lens.vercel.app](https://sip-drop-off-lens.vercel.app)

## Linked files

| File | What it holds | Link |
| --- | --- | --- |
| Golden set (spreadsheet) | All 25 hand-labelled posts: the post, its link, and for each field the human's blind label, the AI's label, the final answer after review, and whether the AI was right; a second sheet sums the agreement | [Open the golden set](https://docs.google.com/spreadsheets/d/1AdiBL__ZVJ5a-KALcKmU4BTd5_YHNaEZ/edit?usp=sharing) |
| Questions asked and answered | The engine's answers to the brief's nine questions and its six starter questions, each with how the question was understood, the cited answer, a "how sure is this" note and every quote it rests on | [Open the questions](https://docs.google.com/document/d/15B44vYAT8RaEvv96QSSxfNQ2LemW2qal/edit?usp=sharing) |

## Sources and volume

The engine analysed 91,150 clean SIP-related items from six kinds of public source, collected without accounts or paid APIs. Reddit is 75% of the corpus; Play Store reviews are 10% of the corpus but give 304 of the 720 stories (42%).

| Source | How it was collected | Clean items | Stories | Question posts |
| --- | --- | --- | --- | --- |
| Reddit: r/personalfinanceindia (37,118), r/mutualfunds (27,562), r/IndiaInvestments (3,171), r/FIREIndia (815), r/developersIndia (123) | Arctic Shift archive: posts, then comment threads | 68,789 | 319 | 879 |
| Play Store: Groww | google-play-scraper, newest first + a SIP-keyword deep pull | 4,378 | 131 | 27 |
| Play Store: ET Money | google-play-scraper | 1,975 | 83 | 38 |
| Play Store: Coin (Zerodha) | google-play-scraper | 1,404 | 35 | 6 |
| Play Store: Paytm Money | google-play-scraper | 748 | 39 | 5 |
| Play Store: INDmoney | google-play-scraper | 312 | 16 | 2 |
| App Store: 6 apps (Groww, ET Money, Paytm Money, Coin, INDmoney, Kuvera) | Apple RSS review feed, India storefront | 1,031 | 0 | 34 |
| TradingQ&A (Zerodha forum) | Forum API: topics and replies | 4,338 | 35 | 22 |
| YouTube comments on SIP videos | scrapetube + youtube-comment-downloader | 3,679 | 38 | 30 |
| Blogs: basunivesh (3,607), stableinvestor (337), jagoinvestor (290), freefincal (262) | Comment sections of SIP articles | 4,496 | 24 | 85 |
| **Total** | | **91,150** | **720** | **1,128** |

From corpus to stories, each step narrowed what the AI read:

1. **91,150** clean SIP-related items after removing duplicates, cross-posts and non-SIP text.
2. **4,115** candidates read by AI after keyword pre-filters: 2,473 checked for "is this a personal SIP story?" and 1,642 for "does this answer a brief question?" (Gemma 4 26B and Claude).
3. **1,848** relevant items deep-tagged on 23 fields by Claude (codebook v1.10): 720 stories + 1,128 question posts.
4. **720** personal stories: 580 stopped or wavering, 140 kept going; 137 from first-time investors.

**Why did the AI read 4,115 of 91,150 items?** All 91,150 were searched with code; a keyword filter chose which ones the AI read, for three reasons:

- **Most posts are not personal stories.** The corpus is everything that mentions SIPs: advice to others, fund-pick questions, generic app reviews, stock and IPO talk. When the AI read posts unfiltered on 21 Oct, about 27% were personal stories.
- **Reading everything was not feasible on a free model.** Gemma's free tier managed about 50 items an hour (frequent overload errors), so 91,150 items would have taken about 1,800 hours, or 76 days.
- **The filter was built to miss as little as possible.** An item passed when the writer spoke in the first person and mentioned a SIP action (stop, pause, continue, step up) or a loss or worry. It caught 97% of the 139 stories the AI had already found by reading unfiltered. Advice posts were allowed through for the AI to remove; first-time-investor signals were ranked highest; each source was capped so Reddit and ET Money's pricing event could not dominate. Later searches over the whole corpus again added first-time investors, stayers and posts answering each brief question.

Of the 4,115 items read, 1,848 (45%) were relevant. **Limitation:** a keyword filter can miss stories that avoid the expected words; the golden set found two exits that never said "SIP" (Correction 4).

**Not collected:** X (Twitter) and Instagram were out of scope; Quora blocked collection; Reddit collection was stopped on 24 Oct before r/IndianStreetBets, r/StockMarketIndia and the Oct 2022 to Sep 2024 history. Blogs (24 stories) and INDmoney (16) are under 30 stories each, so they are never reported on their own.

## Golden set: how often the engine agreed

On 25 posts labelled by hand, the AI agreed with the human on story-or-not 72% of the time blind, below the 80% bar, and 80% after every disagreement was reviewed. Its weakest fields are what the investor did and the real reason (69% each after review).

**How it was built.** 25 posts were drawn at random (seeded, reproducible), stratified by the AI's own call: 11 drop-off stories, 7 stayed stories and 7 not-a-story, round-robin across sources so every source appears. The human labelled them blind on a guided page: one post at a time, plain-English questions mapped one-to-one to codebook codes, "Can't tell" for unknown, and the AI's answers hidden. Then all 36 disagreements were reviewed with both answers visible, and the human chose a final answer: their own 18 times, the AI's 18 times.

| Field | Posts | Blind: AI vs human | AI vs final answer | Human blind vs final answer |
| --- | --- | --- | --- | --- |
| Story or not | 25 | 18/25 (72%) | 20/25 (80%) | 23/25 (92%) |
| New vs experienced investor | 17 | 14/17 (82%) | 16/17 (94%) | 15/17 (88%) |
| What they did (action) | 16 | 6/16 (38%) | 11/16 (69%) | 11/16 (69%) |
| The event (trigger) | 16 | 9/16 (56%) | 14/16 (88%) | 11/16 (69%) |
| The real reason (root cause) | 16 | 7/16 (44%) | 11/16 (69%) | 12/16 (75%) |
| All four tag fields | 65 | 36/65 (55%) | 52/65 (80%) | 49/65 (75%) |

Story-or-not agreement beyond chance (Cohen's kappa) was 0.56 blind. Tag fields are scored only on posts both sides call a story. The raw blind numbers are the honest measure; the reviewed numbers show how much of the gap was the human's own first read, which scored 92% and 75% against the final answers.

**Caveat:** three golden posts were later part of the "thinking of stopping" re-check (Correction 5), so the scores are kept as measured before that fix and are not re-scored on posts that shaped the rule.

## Where the engine failed

The AI got story-or-not wrong on 5 of 25 posts against the final answers: it missed two exits that never say "SIP", took one hypothetical as a plan, and followed two rules that did not match the business metric. On the other 2 of the 7 blind disagreements, the human changed their own label.

| Post | What the post says | Human (blind) | AI | Final | Who was wrong |
| --- | --- | --- | --- | --- | --- |
| #2 (TradingQ&A) | Blocked from switching out of regular-plan funds | Drop-off | Not a story | Drop-off | AI: missed an exit with no "SIP" in it |
| #12 (Play Store, Coin) | Leaving Coin and redeeming elsewhere | Drop-off | Not a story | Drop-off | AI: same pattern |
| #13 (TradingQ&A) | "Say I believe there is a better fund… what if I cancel?" | Not a story | Drop-off | Not a story | AI: read a hypothetical as the writer's plan |
| #3 (blog) | Stopped in 2010, restarted in 2015 | Drop-off | Stayed | Drop-off | AI, under our rule then: a restart counted as stayed |
| #4 (YouTube) | SIP cut from ₹4,000 to ₹500 a month, still running | Stayed | Drop-off | Stayed | AI, under our rule then: any reduction counted as drop-off |
| #5 (YouTube) | Step-ups plus lump sums | Drop-off | Stayed | Stayed | Human first read |
| #9 (Reddit) | "Continuing a few more months, will see" | Drop-off | Stayed | Stayed | Human first read |

Three patterns explain most tag disagreements:

1. **"Thinking of stopping" was over-used.** The AI coded people asking for portfolio advice while their SIPs kept running as thinking of stopping (#11, #15, #21). 295 tags in the full data carried this code, so the error was systematic.
2. **Trust erosion was inferred readily.** Blind, the AI gave "platform trust erosion" as the real reason four times where the human said the post doesn't show one. On review the human accepted it three times (#10, #18, #20) and rejected it once (#8, where the app fault came after the SIP was already cancelled).
3. **Blocked vs thinking of stopping.** Posts where the app refused a pause or cancel were split between "tried, was blocked" and "thinking of stopping" or "paused" (#17, #18); here the AI's "blocked" was right both times.

Each pattern led to a fix in the next section (Corrections 4 and 5).

## Where AI output was rejected or corrected, and why

Six times the AI's output was rejected or corrected; three of them (3, 5, 6) changed what the engine reports. Each row says what the AI did, how it was caught, and what changed.

| # | Date | What the AI did wrong | How it was caught | Fix and effect |
| --- | --- | --- | --- | --- |
| 6 | 24 Oct | Evidence quotes hid the SIP context: 513 of 1,848 quotes had no SIP or investing words (e.g. "Took early retirement last year after 21 years in the IT industry" for a 19-year SIP story) | Human read the Story Explorer | 479 quotes widened to a verbatim stretch of the same post that includes the SIP sentence; 34 left as they were. A version that swapped in a different sentence was rejected because it lost the tagged reason. No tag or count changed |
| 5 | 24 Oct | Coded people asking for portfolio advice while still investing as "thinking of stopping", and mixed app-switchers in with people doubting investing | Golden set (#11, #15, #21) + human's rule on switching apps | All 295 such tags re-read with a sharper rule: 247 kept, 48 changed. New code "thinking of switching app"; app-switchers became their own outcome group, still a loss for Groww |
| 4 | 24 Oct | Missed exits that never say "SIP" and read a hypothetical as a plan; two of our rules did not match the metric | Golden set review (#2, #3, #4, #12, #13) | Detection rules updated. A reduced but running SIP now counts as stayed (the brief's active-SIP definition), a restart after a stop as drop-off |
| 3 | 22 Oct | "Someone else's conviction" coded whenever a person asked Reddit "should I continue?", making it a headline theme (12% of community drop-offs) | The code jumped to 13% of new stories (from 4%) after a new data pull; all 52 tags re-read by hand | Code narrowed to a specific person steering the decision: 8 kept, 44 re-coded. Fell from 12% to about 1%, now an anecdote, not a finding |
| 2 | 21 Oct | Flash-Lite scored IPO, KYC, demat and stock-trading complaints as SIP-relevant and under-rated a real "let me pause for a few months" need | Same 100 items re-scored by a stronger model; it was right in all 18 disagreements | Flash-Lite kept only as a first screen; Gemma 4 26B became the final relevance scorer (93% keep/drop agreement with the stronger model) |
| 1 | 21 Oct | Relevance filter scored generic praise ("very good app for SIP") as most relevant and marked "best app for beginners" as a first-time investor | Manual check of the first 100-item run | Rubric rewritten: generic praise scores 0, first-time needs the writer to say they are new. First-time flags fell from 20 to 4 on the same items |

## Automatic checks

Every one of the 2,719 tag rows passed two automatic checks: 0 codes outside the codebook and 0 evidence quotes not found word for word in their source post. A failing code or quote is reset to "unknown" and logged, never kept.

The engine's "Ask the Data" feature applies the same idea to every answer before it is shown:

- **Citations:** a sentence about what people said must cite a numbered story, or it is removed.
- **Numbers:** every percentage must match the counts computed from the data, or the sentence is removed.
- **Quotes:** any quoted words must be found word for word in a cited post.
- **No advice:** sentences that recommend, prescribe or suggest product fixes are removed; personal "should I stop my SIP?" questions get no AI answer, only what investors on both sides said and a pointer to a SEBI-registered adviser.
- **Fallbacks:** the nine brief questions are saved answers that work without the AI; if the AI is down or out of quota, the best-matching stories are shown instead; if the stories say too little, the answer is "not enough evidence".
