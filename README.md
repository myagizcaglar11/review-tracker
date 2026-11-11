# Match-3 Review Tracker

A small tool that listens to what players say about **Royal Match** and **Royal Kingdom** (Dream Games), compared with **Candy Crush Saga** (King) and **Homescapes** (Playrix).

Every week it collects new public reviews from the App Store and Google Play, tags each one with themes such as *"the ad is not the game"*, *pay to win* or *relaxing*, and updates a public dashboard with trends and alerts.

**Live dashboard:** https://myagizcaglar11.github.io/review-tracker/ (live after the first weekly run)

## Why

Ads win the install, but reviews show what happens after it. In a one-off analysis of 4,000 reviews I found that about 1 in 4 negative Royal Kingdom reviews say the game is not what the ad showed. A one-off analysis gets old fast; a weekly tracker can show whether a new creative or update moves these numbers.

Possible uses for a marketing team:
- **Creative check:** did "the ad is not the game" complaints rise after a new campaign?
- **Early warning:** spot difficulty or pricing frustration before it shows in retention.
- **Message ideas:** find hooks in players' own words, market by market.

## How it works

```
App Store RSS ─┐
               ├─> collect ─> keep new reviews ─> classify (AI or keyword rules) ─> save counts ─> dashboard data
Google Play  ──┘
```

| Step | File | What it does |
|---|---|---|
| Collect | `tracker/collect.py` | Up to 500 newest reviews per game, store and market (US, GB, CA, AU) |
| Classify | `tracker/classify.py` | Tags themes with Google Gemini if `GEMINI_API_KEY` is set (any language, batches of 50); otherwise keyword rules from `tracker/themes.py` |
| Store | `tracker/store.py` | Saves one row per review **without the review text or username**, plus a few short example excerpts |
| Aggregate | `tracker/aggregate.py` | Theme shares per game and month; flags a theme whose share of negative reviews jumped in the last complete month (≥ 5 points and beyond random noise) |
| Dashboard | `docs/index.html` | Static page on GitHub Pages: tiles, alerts, heatmaps, monthly trend, example quotes |
| Schedule | `.github/workflows/update.yml` | Runs every Monday and commits the new data |

Change games, markets or limits in `config.json`. Change themes in `tracker/themes.py`.

## Run it locally

```bash
pip install -r requirements.txt pytest
python -m pytest -q tests                      # unit tests
python tests/make_sample.py                    # made-up sample reviews
python -m tracker.run --fixtures tests/sample.json   # offline run
python -m tracker.run                          # live run
cd docs && python -m http.server               # open http://localhost:8000
```

## Limits

- Written reviews lean negative compared with star ratings, so the numbers show what drives praise and complaints, not overall satisfaction.
- The stores only expose recent reviews, so history builds up week by week from the first run.
- Keyword rules only understand English and miss sarcasm; the AI classifier is better but limited by free-tier quotas.
- This is an independent project using public data. It is not affiliated with Dream Games, King or Playrix.

## About

Built by Mehmet Yağız Çağlar (ITU Industrial Engineering) with the help of AI tools, as a follow-up to my Dream Games marketing intern case study.
