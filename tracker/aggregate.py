"""Turn stored reviews into the numbers the dashboard shows (docs/data.json)."""
import json
from collections import defaultdict
from datetime import date

from .themes import NEGATIVE_THEMES, POSITIVE_THEMES, THEMES


def _share(rows, theme):
    return round(100 * sum(theme in r["themes"] for r in rows) / len(rows), 1) if rows else None


def build(rows: list[dict], quotes: dict, config: dict, months: int = 12) -> dict:
    by_game = defaultdict(list)
    for r in rows:
        by_game[r["game"]].append(r)

    all_months = sorted({r["date"][:7] for r in rows})[-months:]
    games_out, alerts = [], []

    for g in config["games"]:
        grows = by_game.get(g["key"], [])
        neg = [r for r in grows if r["rating"] <= 2]
        pos = [r for r in grows if r["rating"] >= 4]

        monthly = []
        for m in all_months:
            mrows = [r for r in grows if r["date"].startswith(m)]
            mneg = [r for r in mrows if r["rating"] <= 2]
            mpos = [r for r in mrows if r["rating"] >= 4]
            monthly.append({
                "month": m, "n": len(mrows), "n_neg": len(mneg), "n_pos": len(mpos),
                "avg_rating": round(sum(r["rating"] for r in mrows) / len(mrows), 2) if mrows else None,
                "neg": {t: _share(mneg, t) for t in NEGATIVE_THEMES},
                "pos": {t: _share(mpos, t) for t in POSITIVE_THEMES},
            })

        # Alert: latest complete month vs. the average of the three months before it.
        this_month = date.today().strftime("%Y-%m")
        usable = [m for m in monthly if m["month"] < this_month and m["n_neg"] >= config["alert_min_reviews"]]
        if len(usable) >= 2:
            last, prev = usable[-1], usable[-4:-1]
            for t in NEGATIVE_THEMES:
                base = sum(p["neg"][t] for p in prev) / len(prev)
                diff = last["neg"][t] - base
                # Ignore changes that random noise could explain (z < 2 on a binomial share).
                p = max(min(base / 100, 0.99), 0.01)
                z = (diff / 100) / ((p * (1 - p) / last["n_neg"]) ** 0.5)
                if diff >= config["alert_threshold_points"] and z >= 2:
                    alerts.append({"game": g["key"], "game_name": g["name"], "theme": t,
                                   "label": THEMES[t]["label"], "month": last["month"],
                                   "share": last["neg"][t], "baseline": round(base, 1),
                                   "change": round(diff, 1)})

        games_out.append({
            "key": g["key"], "name": g["name"], "studio": g["studio"],
            "n": len(grows), "n_neg": len(neg), "n_pos": len(pos),
            "avg_rating": round(sum(r["rating"] for r in grows) / len(grows), 2) if grows else None,
            "by_store": {s: sum(r["store"] == s for r in grows) for s in ("app_store", "google_play")},
            "neg": {t: _share(neg, t) for t in NEGATIVE_THEMES},
            "pos": {t: _share(pos, t) for t in POSITIVE_THEMES},
            "monthly": monthly,
            "quotes": quotes.get(g["key"], {}),
        })

    methods = defaultdict(int)
    for r in rows:
        methods[r["method"]] += 1

    return {
        "updated": date.today().isoformat(),
        "n": len(rows),
        "methods": dict(methods),
        "markets": config["markets"],
        "first_date": min((r["date"] for r in rows), default=None),
        "last_date": max((r["date"] for r in rows), default=None),
        "themes": {k: {"label": v["label"], "description": v["description"]} for k, v in THEMES.items()},
        "negative_themes": NEGATIVE_THEMES,
        "positive_themes": POSITIVE_THEMES,
        "games": games_out,
        "alerts": sorted(alerts, key=lambda a: -a["change"]),
    }


def write(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
