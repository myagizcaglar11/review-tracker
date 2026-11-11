"""Save classified reviews without their text.

data/reviews.csv keeps one row per review: id, game, store, country, date,
rating, version, themes, method. Review text and usernames are never stored,
so the public repository holds counts, not people's words.

data/quotes.json keeps at most a few short, recent excerpts per game and theme,
shown on the dashboard as examples.
"""
import csv
import json
import os

FIELDS = ["id", "game", "store", "country", "date", "rating", "version", "themes", "method"]


def load(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["rating"] = int(r["rating"])
        r["themes"] = [t for t in r["themes"].split("|") if t]
    return rows


def save(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["game"], r["date"], r["id"]))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "themes": "|".join(r["themes"])})


def new_only(collected: list[dict], existing: list[dict]) -> list[dict]:
    seen = {r["id"] for r in existing}
    out, batch_seen = [], set()
    for r in collected:
        if r["id"] not in seen and r["id"] not in batch_seen:
            out.append(r)
            batch_seen.add(r["id"])
    return out


def _excerpt(text: str, max_chars: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + "…"


def update_quotes(path: str, new_rows: list[dict], max_chars: int, per_theme: int = 3) -> None:
    quotes = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    for r in sorted(new_rows, key=lambda r: r["date"]):
        if len(r.get("text", "")) < 25:
            continue
        for t in r["themes"]:
            bucket = quotes.setdefault(r["game"], {}).setdefault(t, [])
            bucket.append({"date": r["date"], "rating": r["rating"], "store": r["store"],
                           "text": _excerpt(r["text"], max_chars)})
            bucket.sort(key=lambda q: q["date"], reverse=True)
            del bucket[per_theme:]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(quotes, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
