"""Turn stored reviews into the numbers the dashboard shows (docs/data.json)."""
import json
from collections import defaultdict
from datetime import date, timedelta

from .themes import NEGATIVE_THEMES, POSITIVE_THEMES, THEMES


def _std_shares(recent, before, theme, min_per_stratum=5):
    """Theme share now and before with the same mix of store and country on both sides.

    Recent months hold more Google Play and US reviews than older ones, and those write
    differently (shorter, other words). Comparing raw shares would show a change in the
    mix as a change in opinion. So each (store, country) group is compared with itself and
    the groups are weighted by their size in the recent window. Groups too small on either
    side are left out. Returns (share_now, share_before, n_now, n_before) or None."""
    def groups(rs):
        g = defaultdict(list)
        for r in rs:
            g[(r.get("store"), r.get("country"))].append(r)
        return g
    gn, gb = groups(recent), groups(before)
    keys = [k for k in gn if len(gn[k]) >= min_per_stratum and len(gb.get(k, [])) >= min_per_stratum]
    if not keys:
        return None
    w = {k: len(gn[k]) for k in keys}
    tot = sum(w.values())
    now = sum(w[k] * _share(gn[k], theme) for k in keys) / tot
    then = sum(w[k] * _share(gb[k], theme) for k in keys) / tot
    return round(now, 1), round(then, 1), sum(len(gn[k]) for k in keys), sum(len(gb[k]) for k in keys)


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
        last_complete = (date.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        prev_months = sorted({r["date"][:7] for r in neg if r["date"][:7] < last_complete})[-3:]
        last_neg = [r for r in neg if r["date"].startswith(last_complete)]
        prev_neg = [r for r in neg if r["date"][:7] in prev_months]
        if len(last_neg) >= config["alert_min_reviews"] and prev_neg:
            for t in NEGATIVE_THEMES:
                res = _std_shares(last_neg, prev_neg, t)
                if not res or res[2] < config["alert_min_reviews"]:
                    continue
                now, base, n_now, _ = res
                diff = now - base
                # Ignore changes that random noise could explain (z < 2 on a binomial share).
                p = max(min(base / 100, 0.99), 0.01)
                z = (diff / 100) / ((p * (1 - p) / n_now) ** 0.5)
                if diff >= config["alert_threshold_points"] and z >= 2:
                    alerts.append({"game": g["key"], "game_name": g["name"], "theme": t,
                                   "label": THEMES[t]["label"], "month": last_complete,
                                   "share": now, "baseline": base, "change": round(diff, 1)})

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

    changes = recent_changes(rows, config)

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
        "changes": changes,
    }


def recent_changes(rows: list[dict], config: dict, recent_days: int = 30, before_days: int = 90,
                   min_reviews: int = 30, min_points: float = 3.0) -> list[dict]:
    """Theme shares in the last 30 days vs. the 90 days before, per game, with the same
    store and country mix on both sides (see _std_shares).
    Complaint themes are shares of 1-2 star reviews, praise themes of 4-5 star reviews.
    Kept: changes of 3+ points, 30+ reviews on both sides, beyond random noise."""
    if not rows:
        return []
    end = date.fromisoformat(max(r["date"] for r in rows))
    cut = (end - timedelta(days=recent_days)).isoformat()
    start = (end - timedelta(days=recent_days + before_days)).isoformat()
    out = []
    for g in config["games"]:
        grows = [r for r in rows if r["game"] == g["key"]]
        for kind, themes, keep in (("complaint", NEGATIVE_THEMES, lambda r: r["rating"] <= 2),
                                   ("praise", POSITIVE_THEMES, lambda r: r["rating"] >= 4)):
            recent = [r for r in grows if keep(r) and r["date"] > cut]
            before = [r for r in grows if keep(r) and start < r["date"] <= cut]
            if len(recent) < min_reviews or len(before) < min_reviews:
                continue
            for t in themes:
                res = _std_shares(recent, before, t)
                if not res or res[2] < min_reviews or res[3] < min_reviews:
                    continue
                now, then, n_now, n_before = res
                # keep only changes beyond what random noise could explain (z >= 2)
                p = max(min(then / 100, 0.99), 0.01)
                z = abs(now - then) / 100 / ((p * (1 - p) * (1 / n_now + 1 / n_before)) ** 0.5)
                if abs(now - then) >= min_points and z >= 2:
                    out.append({"game": g["key"], "game_name": g["name"], "kind": kind, "theme": t,
                                "label": THEMES[t]["label"], "now": now, "before": then,
                                "change": round(now - then, 1), "n_now": n_now, "n_before": n_before})
    return sorted(out, key=lambda c: -abs(c["change"]))


def write_summary(data: dict, path: str) -> None:
    """A short Markdown report, committed with each weekly run."""
    lines = [f"# Weekly review summary ({data['updated']})", "",
             f"{data['n']:,} reviews tracked, {data['first_date']} to {data['last_date']}. "
             f"Live dashboard: https://myagizcaglar11.github.io/review-tracker/", ""]
    lines += ["## Alerts (last complete month vs. the three before, same store and country mix)", ""]
    lines += [f"- **{a['game_name']}**: \"{a['label']}\" in {a['share']}% of negative reviews in {a['month']} "
              f"(was {a['baseline']}%)" for a in data["alerts"]] or ["- None this month."]
    lines += ["", "## What moved in the last 30 days (vs. the 90 days before, same store and country mix)", ""]
    lines += [f"- **{c['game_name']}**: \"{c['label']}\" {c['before']}% → {c['now']}% of {c['kind']} reviews "
              f"({'+' if c['change'] > 0 else ''}{c['change']} pts; {c['n_now']} vs {c['n_before']} reviews)"
              for c in data["changes"][:8]] or ["- No change of 3 points or more."]
    lines += ["", "## Complaint themes now (share of 1–2★ reviews, all time)", "",
              "| Game | " + " | ".join(data["themes"][t]["label"] for t in data["negative_themes"]) + " |",
              "|---|" + "---|" * len(data["negative_themes"])]
    for g in data["games"]:
        lines.append(f"| {g['name']} | " + " | ".join(f"{g['neg'][t]}%" if g['neg'][t] is not None else "–"
                                                      for t in data["negative_themes"]) + " |")
    lines += ["", "Keyword rules undercount \"Ad is not the game\"; see EVALUATION.md and eval/results.md."]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
