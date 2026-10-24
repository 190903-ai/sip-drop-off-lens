"""Refine weak evidence quotes (Correction 6, 24 Oct 2026): quotes that never mention a SIP or investing.

The tagging AI had to copy one exact line as evidence and sometimes picked one that hides the SIP context
(e.g. "Took early retirement last year after 21 years in the IT industry."). The fix widens the quote to a
continuous, verbatim stretch of the same post that keeps the original line and reaches the nearest sentence
about the SIP / investment. Nothing is paraphrased; tags, counts and the frozen files are untouched.

Usage: python webapp/scripts/refine_quotes.py
Writes data/quote_fixes_v1.jsonl ({id, old, new, how}); build_data.py applies it on top of the freeze.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
import analyze  # noqa: E402

KW = re.compile(r"\b(sips?|mutual funds?|mf|funds?|invest\w*|mandate|auto ?pay|instal?ments?|nav|xirr|redeem\w*|"
                r"redemption|portfolio|step.?up|nach|debit\w*|deduct\w*|elss|index|amc|folio|units?|returns?|"
                r"lump ?sum|equity|equities)\b", re.I)
MAX = 420  # widened quotes keep the original line, so they run longer than a single sentence


def sentences(text):
    """Sentence spans as (start, end) offsets into the original text, so every quote stays verbatim."""
    spans, start = [], 0
    for m in re.finditer(r"[.!?]+(?=\s)|\n+", text):
        end = m.end()
        if text[start:end].strip():
            spans.append((start, end))
        start = end
    if text[start:].strip():
        spans.append((start, len(text)))
    # trim surrounding whitespace inside each span
    out = []
    for s, e in spans:
        while s < e and text[s].isspace():
            s += 1
        while e > s and text[e - 1].isspace():
            e -= 1
        out.append((s, e))
    return out


def words(t):
    return set(re.findall(r"[a-z]{4,}", t.lower()))


def refine(t):
    text, old = t.get("text") or "", t.get("evidence_quote") or ""
    if not old or KW.search(old) or not KW.search(text):
        return None
    sp = sentences(text)
    at = text.find(old)
    if at < 0:
        return None
    i = next((k for k, (s, e) in enumerate(sp) if s <= at < e), None)
    j_end = next((k for k, (s, e) in enumerate(sp) if s < at + len(old) <= e), i)
    if i is None:
        return None
    # nearest sentence with SIP / investing words, preferring the one that shares words with the AI's reason
    cands = [k for k, (s, e) in enumerate(sp) if KW.search(text[s:e])]
    if not cands:
        return None
    why = words(t.get("rationale") or "")
    cands.sort(key=lambda k: (min(abs(k - i), abs(k - j_end)), -len(words(text[sp[k][0]:sp[k][1]]) & why)))
    for k in cands:
        lo, hi = min(i, k), max(j_end, k)
        new = text[sp[lo][0]:sp[hi][1]]
        if len(new) <= MAX:
            return new, "widened to include the SIP context"
    # too far apart to stay contiguous: keep the original quote rather than lose the reason it was tagged for
    return None


def main():
    stories = analyze.load_stories()
    items = analyze.load_question_items(stories)
    out, seen = [], 0
    for t in stories + items:
        if (t.get("evidence_quote") or "") and not KW.search(t["evidence_quote"]):
            seen += 1
        r = refine(t)
        if r:
            new, how = r
            assert new in t["text"], t["id"]  # verbatim
            out.append({"id": t["id"], "old": t["evidence_quote"], "new": new, "how": how})
    path = ROOT / "data" / "quote_fixes_v1.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"weak quotes {seen}; widened {len(out)}; left as is {seen - len(out)} -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
