"""Step 5: tag relevant items with the codebook, with automatic quality checks.

Two modes:
  --mode light : 9 core fields, compact prompt (codes + one-line definitions). Built for
                 gemma-4-26b on the free tier, whose server drops the full 21k-char prompt.
                 Run on ALL relevant items -> volume for the numbers.
  --mode deep  : every codebook field incl. root cause, expectation, workaround, unmet need
                 and evidence quote, with examples and exclude rules. Run on a stratified
                 sample with a stronger model -> the "why".

Checks on every tagged item (logged next to the output as <out>_issues.jsonl):
  - invalid_code:    a code not in the codebook -> replaced with "unknown"
  - quote_not_found: evidence_quote is not an exact substring of the text (hallucination) -> blanked
  - missing_item:    the model skipped an item in the batch (retried on the next run)

Usage: python pipeline/tag.py [limit] [--mode light|deep] [--ids-file path] [--out path]
                              [--model name] [--batch n] [--workers n] [--min-score n]
"""
import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from llm import generate_json

ROOT = Path(__file__).resolve().parent.parent
CODEBOOK = json.loads((ROOT / "pipeline" / "codebook.json").read_text(encoding="utf-8"))
LIGHT_FIELDS = ["voice", "platform", "stage", "action", "stop_trigger", "metric_branch",
                "income_type", "life_stage", "influencer_source"]
MODES = {
    # mode: (fields, compact prompt, default model, batch, workers)
    "light": (LIGHT_FIELDS, True, "gemma-4-26b-a4b-it", 10, 2),
    "deep": ([f["name"] for f in CODEBOOK["fields"]], False, "gemini-3.5-flash", 15, 4),
}

RULES = """Rules:
- Code only what the text shows. Never infer age, income, platform or motives that are not written.
  Use "unknown" whenever the text gives no signal. Unknown is a good answer, not a failure.
- single fields: exactly one code string. multi fields: a list of codes (["unknown"] if none).
- Use "other" only if no listed code fits{rationale_rule}.
- Play Store items are reviews of the Groww app (platform = groww).
- Text may be English, Hindi or Hinglish."""


def render_codebook(fields: list[dict], compact: bool) -> str:
    lines = []
    for f in fields:
        lines.append(f"\n## {f['name']} ({f['type']}): {f['question']}")
        for v in f.get("values", []):
            if v["code"] == "unknown":
                continue
            definition = v["definition"].split(". ")[0].rstrip(".") if compact else v["definition"]
            line = f"- {v['code']}: {definition}"
            if not compact:
                if v.get("include_example"):
                    line += f' e.g. "{v["include_example"]}"'
                if v.get("exclude_rule"):
                    line += f" NOT: {v['exclude_rule']}"
            lines.append(line)
    return "\n".join(lines)


def build_system(field_names: list[str], compact: bool) -> str:
    fields = [f for f in CODEBOOK["fields"] if f["name"] in field_names]
    has_quote = "evidence_quote" in field_names
    rules = RULES.format(rationale_rule=", and then explain it in rationale" if "rationale" in field_names else "")
    if has_quote:
        rules += ("\n- evidence_quote: copy an EXACT span (same language/script, max 200 chars) from the item "
                  "that supports root_cause or stop_trigger; \"\" if both are unknown. Do not translate.")
    return (
        "You are a careful qualitative researcher coding public posts by Indian retail investors for a "
        "study on why FIRST-TIME mutual fund investors continue or stop their SIPs.\n\n"
        f"Apply this codebook to EACH item.\n{rules}\n{render_codebook(fields, compact)}\n\n"
        'Return JSON: {"results": [{"id": "...", <every field name above>: ...}]}'
    )


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def validate(tag: dict, text: str, field_names: list[str]) -> tuple[dict, list[dict]]:
    fields = {f["name"]: f for f in CODEBOOK["fields"] if f["name"] in field_names}
    issues, clean = [], {"id": tag["id"]}
    for name, f in fields.items():
        val = tag.get(name)
        if f["type"] == "text":
            clean[name] = val if isinstance(val, str) else ""
            continue
        allowed = {v["code"] for v in f["values"]} | {"unknown"}
        vals = val if isinstance(val, list) else [val]
        good = [x for x in vals if x in allowed]
        for bad in (x for x in vals if x not in allowed):
            issues.append({"id": tag["id"], "issue": "invalid_code", "field": name, "value": bad})
        if f["type"] == "single":
            clean[name] = good[0] if good else "unknown"
        else:
            clean[name] = sorted(set(x for x in good if x != "unknown")) or ["unknown"]
    if "evidence_quote" in fields:
        quote = clean.get("evidence_quote", "")
        if quote and norm(quote) not in norm(text):
            issues.append({"id": tag["id"], "issue": "quote_not_found", "value": quote[:200]})
            clean["evidence_quote"] = ""
        clean["quote_verified"] = bool(clean["evidence_quote"])
    return clean, issues


def tag_batch(batch: list[dict], model: str, system: str, field_names: list[str]):
    items = "\n\n".join(
        f"[id={r['id']}] (source={r['source']}"
        + (f", posted={r['date'][:10]}" if r.get("date") else "")
        + (f", video=\"{r['video_title'][:80]}\"" if r.get("video_title") else "")
        + f")\n{r['text'][:2500]}" for r in batch)
    result = generate_json(f"Items:\n\n{items}", model=model, system=system)
    by_id = {r["id"]: r for r in batch}
    tags, issues = [], []
    for t in result.get("results", []):
        if t.get("id") in by_id:
            clean, iss = validate(t, by_id[t["id"]]["text"], field_names)
            tags.append(clean)
            issues += iss
    returned = {t["id"] for t in tags}
    issues += [{"id": i, "issue": "missing_item"} for i in by_id if i not in returned]
    return tags, issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("limit", nargs="?", type=int)
    ap.add_argument("--mode", choices=MODES, default="light")
    ap.add_argument("--ids-file", help="jsonl with an 'id' per line: tag exactly these items")
    ap.add_argument("--out")
    ap.add_argument("--min-score", type=int, default=1)
    ap.add_argument("--model")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--batch", type=int)
    args = ap.parse_args()
    field_names, compact, model, batch_size, workers = MODES[args.mode]
    model, batch_size, workers = args.model or model, args.batch or batch_size, args.workers or workers
    out = Path(args.out or ROOT / "data" / f"tags_{args.mode}.jsonl")
    system = build_system(field_names, compact)

    rows = {r["id"]: r for r in map(json.loads, open(ROOT / "data" / "clean.jsonl", encoding="utf-8"))}
    if args.ids_file:
        ids = [json.loads(l)["id"] for l in open(args.ids_file, encoding="utf-8")]
        todo = [rows[i] for i in ids if i in rows]
    else:
        scores = {x["id"]: x for x in map(json.loads, open(ROOT / "data" / "relevance.jsonl", encoding="utf-8"))}
        todo = [rows[i] for i, s in scores.items() if s["score"] >= args.min_score and i in rows]
    done = {json.loads(l)["id"] for l in open(out, encoding="utf-8")} if out.exists() else set()
    todo = [r for r in todo if r["id"] not in done][: args.limit]
    batches = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]
    print(f"[tag {args.mode}/{model}] prompt {len(system)} chars; {len(done)} done, "
          f"{len(todo)} to go in {len(batches)} batches", flush=True)

    n_issues = 0
    issues_path = out.with_name(out.stem + "_issues.jsonl")
    with open(out, "a", encoding="utf-8") as f, open(issues_path, "a", encoding="utf-8") as fi, \
            ThreadPoolExecutor(workers) as pool:
        futures = [pool.submit(tag_batch, b, model, system, field_names) for b in batches]
        for n, fut in enumerate(as_completed(futures), 1):
            try:
                tags, issues = fut.result()
            except Exception as e:
                print(f"  batch failed: {str(e)[:200]}", flush=True)
                continue
            for t in tags:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
            for i in issues:
                fi.write(json.dumps(i, ensure_ascii=False) + "\n")
            n_issues += len(issues)
            f.flush()
            fi.flush()
            if n % 10 == 0:
                print(f"  {n}/{len(batches)} batches, {n_issues} issues so far", flush=True)
    print(f"done ({n_issues} issues logged)", flush=True)


if __name__ == "__main__":
    main()
