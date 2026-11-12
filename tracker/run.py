"""Run the whole pipeline: collect -> keep new -> classify -> save -> build dashboard data.

    python -m tracker.run                              # live: fetch from the stores
    python -m tracker.run --fixtures tests/sample.json # offline test with sample reviews
"""
import argparse
import json
import logging
import os

from . import aggregate, classify, collect, store

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEWS = os.path.join(ROOT, "data", "reviews.csv")
QUOTES = os.path.join(ROOT, "data", "quotes.json")
DASHBOARD_DATA = os.path.join(ROOT, "docs", "data.json")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--fixtures", help="JSON file of sample reviews to use instead of the stores")
    p.add_argument("--config", default=os.path.join(ROOT, "config.json"))
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    log = logging.getLogger("tracker")
    config = json.load(open(args.config, encoding="utf-8"))

    collected = json.load(open(args.fixtures, encoding="utf-8")) if args.fixtures else collect.collect_all(config)
    existing = store.load(REVIEWS)
    new = store.new_only(collected, existing)
    log.info("Collected %d reviews, %d are new", len(collected), len(new))

    classify.classify(new, config)
    store.update_quotes(QUOTES, new, config["quote_max_chars"])
    for r in new:
        r.pop("text", None)  # never store review text
    all_rows = existing + new
    store.save(REVIEWS, all_rows)

    quotes = json.load(open(QUOTES, encoding="utf-8")) if os.path.exists(QUOTES) else {}
    data = aggregate.build(all_rows, quotes, config)
    aggregate.write(data, DASHBOARD_DATA)
    aggregate.write_summary(data, os.path.join(ROOT, "SUMMARY.md"))
    log.info("Saved %d reviews in total; %d alerts", len(all_rows), len(data["alerts"]))


if __name__ == "__main__":
    main()
