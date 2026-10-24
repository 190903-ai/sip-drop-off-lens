"""Builds golden_labeller.html from template.html + the golden items and the review list."""
import json
from pathlib import Path

TMP = Path(__file__).parent  # golden_items.json, review_items.json
here = Path(__file__).parent


def js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", r"<\/")


t = (here / "template.html").read_text(encoding="utf-8")
t = t.replace("__ITEMS__", js(json.loads((TMP / "golden_items.json").read_text(encoding="utf-8"))))
t = t.replace("__REVIEW__", js(json.loads((TMP / "review_items.json").read_text(encoding="utf-8"))))
(here / "golden_labeller.html").write_text(t, encoding="utf-8")
print(len(t))
