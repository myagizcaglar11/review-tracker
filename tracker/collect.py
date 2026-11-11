"""Collect recent store reviews for each game and market.

App Store: Apple's public customer-review RSS feed (up to 50 reviews per page,
10 pages per country).
Google Play: the open-source google-play-scraper package.

Each review comes back as a dict with the same fields, whatever the store.
"""
import time
import logging

import requests

log = logging.getLogger(__name__)

APPSTORE_URL = "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"


def appstore_reviews(app_id: str, country: str, pages: int = 10) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        url = APPSTORE_URL.format(country=country, page=page, app_id=app_id)
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            entries = r.json().get("feed", {}).get("entry", [])
        except Exception as e:  # network error, bad JSON, empty feed
            log.warning("App Store %s %s page %s failed: %s", app_id, country, page, e)
            break
        if isinstance(entries, dict):
            entries = [entries]
        reviews = [e for e in entries if "im:rating" in e]
        for e in reviews:
            out.append({
                "id": "ios-" + e["id"]["label"],
                "store": "app_store",
                "country": country,
                "date": e["updated"]["label"][:10],
                "rating": int(e["im:rating"]["label"]),
                "version": e.get("im:version", {}).get("label", ""),
                "text": (e["title"]["label"] + ". " + e["content"]["label"]).strip(),
            })
        if len(reviews) < 50:
            break
        time.sleep(0.5)
    return out


def googleplay_reviews(package: str, country: str, count: int = 500) -> list[dict]:
    try:
        from google_play_scraper import Sort, reviews
        result, _ = reviews(package, lang="en", country=country, sort=Sort.NEWEST, count=count)
    except Exception as e:
        log.warning("Google Play %s %s failed: %s", package, country, e)
        return []
    out = []
    for r in result:
        out.append({
            "id": "gp-" + r["reviewId"],
            "store": "google_play",
            "country": country,
            "date": r["at"].strftime("%Y-%m-%d"),
            "rating": int(r["score"]),
            "version": r.get("reviewCreatedVersion") or "",
            "text": (r.get("content") or "").strip(),
        })
    return out


def collect_all(config: dict) -> list[dict]:
    """Collect reviews for every game, store and market in the config."""
    rows = []
    for game in config["games"]:
        for country in config["markets"]:
            ios = appstore_reviews(game["ios_id"], country, config["appstore_pages"])
            gp = googleplay_reviews(game["android_id"], country, config["googleplay_reviews_per_market"])
            for r in ios + gp:
                r["game"] = game["key"]
            rows += ios + gp
            log.info("%s %s: %d App Store, %d Google Play", game["name"], country, len(ios), len(gp))
    return rows
