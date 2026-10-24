"""Step 3: AI relevance scoring in two passes, batched and resumable.

Score 2 = the person's own SIP / first-time MF journey or decision
Score 1 = general SIP talk that still reveals retail investor beliefs/behaviour
Score 0 = not useful (stocks/F&O/IPO, unrelated app bugs, spam, fund-pick lists)

Pass "screen": gemini-3.5-flash-lite over everything (fast, lenient: high recall).
Pass "score":  gemma-4-26b-a4b-it over items the screen did not reject. Chosen by measurement
               (pipeline/compare_relevance.py): 93% keep/drop agreement with gemini-3.5-flash on
               111 items. Flash itself is capped at 20 requests/day on the free tier.
In a 100-item test no item screened 0 by lite was scored >0 by flash.

Usage: python pipeline/relevance.py screen|score [limit]
Writes data/relevance_screen.jsonl / data/relevance.jsonl (id, score, first_time, reason).
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from llm import generate_json

ROOT = Path(__file__).resolve().parent.parent
PASSES = {
    # pass: (model, output file, items per call, parallel workers, min seconds between calls)
    "screen": ("gemini-3.5-flash-lite", ROOT / "data" / "relevance_screen.jsonl", 40, 3, 0),
    "score": ("gemma-4-26b-a4b-it", ROOT / "data" / "relevance.jsonl", 25, 8, 2),
}

SYSTEM = """You screen public posts for a research study on why first-time Indian
mutual fund investors continue or stop their SIPs (systematic investment plans).

For EACH item return:
- score:
  2 = the writer describes their OWN specific experience, decision, feeling or question
      about starting, continuing, increasing, pausing, reducing, stopping, or tracking
      a SIP / mutual fund (e.g. returns disappointed them, a mandate failed, money got
      tight, they don't understand what they see, they are unsure whether to continue).
  1 = general SIP/MF discussion, advice or a SPECIFIC feature request/complaint about
      SIP/MF tracking that reveals how retail investors think, behave or what they need.
  0 = generic praise or abuse with no detail ("very good app for SIP", "worst app"),
      stock trading, F&O, IPOs, KYC/demat issues, app bugs unrelated to SIPs/MFs,
      spam, promotions, or bare lists of fund names.
  When in doubt between two scores, choose the LOWER one.
- first_time: "yes" ONLY if the writer says they THEMSELVES are new or recently
  started (e.g. "my first SIP", "started 6 months ago", "I'm a beginner").
  An app being "good for beginners" is NOT evidence. "no" if they say they have
  invested for years. Otherwise "unknown".
- reason: at most 8 words.

Text may be English, Hindi or Hinglish. Judge only what is written; do not guess.
Return JSON: {"results": [{"id": ..., "score": 0|1|2, "first_time": ..., "reason": ...}]}"""


def score_batch(batch: list[dict], model: str, pace: float) -> list[dict]:
    started = time.time()
    items = "\n\n".join(f"[id={r['id']}] ({r['source']})\n{r['text'][:1200]}" for r in batch)
    result = generate_json(f"Items:\n\n{items}", model=model, system=SYSTEM)
    valid = {r["id"] for r in batch}
    time.sleep(max(0, pace - (time.time() - started)))  # stay under the per-minute quota
    return [x for x in result.get("results", []) if x.get("id") in valid]


def load_ids(path: Path) -> dict:
    if not path.exists():
        return {}
    return {x["id"]: x for x in map(json.loads, open(path, encoding="utf-8"))}


def main():
    pass_name = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    model, out, batch_size, workers, pace = PASSES[pass_name]
    rows = [json.loads(l) for l in open(ROOT / "data" / "clean.jsonl", encoding="utf-8")]
    if pass_name == "score":
        # Drop only what the screen rejected; unscreened items (flash-lite hits a 500/day
        # free cap) go straight to the scorer.
        screened = load_ids(PASSES["screen"][1])
        rows = [r for r in rows if screened.get(r["id"], {}).get("score", 1) > 0]
    done = load_ids(out)
    todo = [r for r in rows if r["id"] not in done][:limit]
    batches = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]
    print(f"[{pass_name}/{model}] {len(done)} done, {len(todo)} to go in {len(batches)} batches", flush=True)

    failed = 0
    with open(out, "a", encoding="utf-8") as f, ThreadPoolExecutor(workers) as pool:
        futures = [pool.submit(score_batch, b, model, pace) for b in batches]
        for n, fut in enumerate(as_completed(futures), 1):
            try:
                for x in fut.result():
                    f.write(json.dumps(x, ensure_ascii=False) + "\n")
                f.flush()
            except Exception as e:
                failed += 1
                print(f"  batch failed: {str(e)[:200]}", flush=True)
            if n % 10 == 0:
                print(f"  {n}/{len(batches)} batches", flush=True)
    print(f"done ({failed} failed batches; rerun to retry them)", flush=True)


if __name__ == "__main__":
    main()
