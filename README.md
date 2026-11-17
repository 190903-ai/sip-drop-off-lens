# SIP Drop-off Lens

An AI discovery engine that reads public conversations about SIPs to find why first-time investors stop them. It is the research part of my NextLeap graduation project on Groww.

**Live engine:** https://sip-drop-off-lens.vercel.app
**The solution built from this research (live demo):** https://my-sip-explainer.vercel.app

## The question
Why do first-time mutual fund investors stop their SIP in the first year, and what could keep them investing for 12 months?

## How the engine works
1. **Collect:** public posts and reviews from Reddit, the Play Store, the App Store, TradingQ&A, YouTube and blogs.
2. **Clean:** remove duplicates and noise, and keep only SIP-related items.
3. **Detect:** AI finds personal stories and question posts.
4. **Tag:** each item is tagged on 23 fields, like trigger, cause, need and workaround.
5. **Verify:** quotes are checked, and my hand labels agreed with the AI 72% blind and 80% after review.
6. **Serve:** a web app with the findings, a story explorer, and an "ask the data" box.

## Scale
91,150 clean items, 4,115 read by AI, 1,848 tagged, and 720 stories (580 who stopped and 140 who stayed).

## What it found
- 78% of first-timer drop-off stories were about intent, meaning they chose to stop. 15% were payment or app failures.
- Flat or red returns were the top trigger for first-timers (18%).
- Stayers were calmer (34% vs 2%) and more likely to read XIRR (23% vs 3%).
- Public posts show correlation, not cause, and they lean towards people who post.

## What is in this repo
- `collectors/` scripts that gather the public data.
- `pipeline/` cleaning, story detection, tagging, the codebook and the analysis.
- `analysis/` the findings the engine produced.
- `evidence/` the AI Evidence Log, the hand-labelled golden set and its scores, and my corrections.
- `research/` the interview kit.
- `webapp/site/` the Next.js app behind the live engine.
- `webapp/mockups/` the screen designs.

The raw collected data is not included. The app ships with the processed stories only.

## Run the web app
```
cd webapp/site
npm install
npm run dev
```
The "ask the data" feature needs a `GEMINI_API_KEY` in your environment. Copy `.env.example` and add your own keys. Never commit a real key.

## Limits
- It only reads public posts, so people who never post are not in the data.
- Tags were made by AI and checked against my own labels, with one labeller.
- The engine gives no advice and no fund recommendations.
