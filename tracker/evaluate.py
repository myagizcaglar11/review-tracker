"""Measure how well each classifier matches the reference labels in eval/labels.json.

    python -m tracker.evaluate

The labels file holds review ids and themes only. Review text is fetched again
from the App Store feed at run time (reviews that have dropped out of the feed
are skipped and counted), so no review text is stored in the repository.

Writes eval/results.md: precision and recall per theme for the keyword rules,
and for the AI classifier when GEMINI_API_KEY is set.
"""
import json
import logging
import os
from collections import defaultdict
from datetime import date

from . import classify, collect
from .themes import THEMES, rule_themes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = os.path.join(ROOT, "eval", "labels.json")
RESULTS = os.path.join(ROOT, "eval", "results.md")
log = logging.getLogger("evaluate")


def fetch_texts(items: list[dict], config: dict) -> dict[str, str]:
    """Find each labeled review in the current App Store feeds by its id."""
    wanted = {i["id"] for i in items}
    found, ios_ids = {}, {g["key"]: g["ios_id"] for g in config["games"]}
    pairs = {(i["game"], c) for i in items for c in i["countries"]}
    for game, country in sorted(pairs):
        for r in collect.appstore_reviews(ios_ids[game], country, pages=10):
            if r["id"] in wanted:
                found[r["id"]] = r["text"]
    return found


def scores(items: list[dict], predicted: dict[str, list[str]]) -> dict:
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    for it in items:
        gold, pred = set(it["themes"]), set(predicted[it["id"]])
        for t in THEMES:
            if t in pred and t in gold:
                tp[t] += 1
            elif t in pred:
                fp[t] += 1
            elif t in gold:
                fn[t] += 1
    out = {}
    for t in list(THEMES) + ["ALL"]:
        a = sum(tp.values()) if t == "ALL" else tp[t]
        b = sum(fp.values()) if t == "ALL" else fp[t]
        c = sum(fn.values()) if t == "ALL" else fn[t]
        out[t] = {"n": a + c, "precision": a / (a + b) if a + b else None, "recall": a / (a + c) if a + c else None}
    return out


def _pct(v):
    return "–" if v is None else f"{v:.0%}"


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    labels = json.load(open(LABELS, encoding="utf-8"))
    texts = fetch_texts(labels, config)
    items = [dict(i, text=texts[i["id"]]) for i in labels if i["id"] in texts]
    log.info("Found %d of %d labeled reviews in the current feeds", len(items), len(labels))

    methods = {"Keyword rules": {i["id"]: rule_themes(i["text"]) for i in items}}
    if os.environ.get("GEMINI_API_KEY", "").strip():
        rows = [{"text": i["text"], "rating": i["rating"], "id": i["id"]} for i in items]
        cfg = dict(config, llm_max_reviews_per_run=len(rows))
        classify.classify(rows, cfg)
        if any(r["method"] == "ai" for r in rows):
            methods["AI (" + os.environ.get("GEMINI_MODEL", classify.DEFAULT_MODEL) + ")"] = {r["id"]: r["themes"] for r in rows}
            n_rules = sum(r["method"] == "rules" for r in rows)
            if n_rules:
                log.warning("%d reviews fell back to rules during the AI run", n_rules)

    lines = [f"# Classifier accuracy", "", f"Run on {date.today().isoformat()} against `eval/labels.json` "
             f"({len(items)} of {len(labels)} labeled reviews still in the App Store feeds).", ""]
    for set_name in ("holdout", "tuning"):
        subset = [i for i in items if i["set"] == set_name]
        if not subset:
            continue
        title = "Hold-out set (the fair test: the rules were not tuned on these)" if set_name == "holdout" else "Tuning set (the rules were adjusted on these, so scores are optimistic)"
        lines += [f"## {title}", "", f"{len(subset)} reviews.", "",
                  "| Theme | Reviews with it | " + " | ".join(f"{m} precision | {m} recall" for m in methods) + " |",
                  "|---|---|" + "---|---|" * len(methods)]
        results = {m: scores(subset, p) for m, p in methods.items()}
        for t in list(THEMES) + ["ALL"]:
            label = "**All themes**" if t == "ALL" else THEMES[t]["label"]
            n = next(iter(results.values()))[t]["n"]
            cells = " | ".join(f"{_pct(results[m][t]['precision'])} | {_pct(results[m][t]['recall'])}" for m in methods)
            lines.append(f"| {label} | {n} | {cells} |")
        lines.append("")
    lines += ["Reference labels were set by an AI assistant reading each review for meaning, not by a person; "
              "see EVALUATION.md."]
    open(RESULTS, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
