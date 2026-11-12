"""Tag each review with themes.

Two methods, same theme keys:
- "ai":    Google Gemini, if a GEMINI_API_KEY is set. Understands any language,
           sarcasm and context. Runs in batches to stay inside free-tier limits.
- "rules": keyword rules from themes.py. Free, instant, English only.

Reviews the AI does not get to (no key, quota reached, error) fall back to rules,
so a run never fails because of the AI step.
"""
import json
import logging
import os
import time

import requests

from .themes import THEMES, rule_themes

log = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3.8-flash"

PROMPT = """You label mobile game store reviews with themes.
Themes (key: meaning):
{themes}

For each review below, return the keys of every theme it clearly mentions (can be none).
Answer with JSON only: a list of objects {{"i": <review number>, "themes": [<keys>]}}.

Reviews:
{reviews}"""


def _gemini_batch(batch: list[dict], api_key: str, model: str) -> dict[int, list[str]]:
    themes = "\n".join(f"- {k}: {v['description']}" for k, v in THEMES.items())
    reviews = "\n".join(f"{i}. [{r['rating']} stars] {r['text'][:600]}" for i, r in enumerate(batch))
    body = {
        "contents": [{"parts": [{"text": PROMPT.format(themes=themes, reviews=reviews)}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }
    r = requests.post(GEMINI_URL.format(model=model), headers={"x-goog-api-key": api_key}, json=body, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini returned HTTP {r.status_code}: {r.text[:300]}")
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text)
    valid = set(THEMES)
    return {int(x["i"]): [t for t in x.get("themes", []) if t in valid] for x in parsed}


def classify(rows: list[dict], config: dict) -> list[dict]:
    """Add 'themes' (list of keys) and 'method' to each row, in place."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
    budget = config.get("llm_max_reviews_per_run", 0) if api_key else 0
    size = config.get("llm_batch_size", 20)

    todo = [r for r in rows if r.get("text")]
    ai_rows, rule_rows = todo[:budget], todo[budget:]

    for start in range(0, len(ai_rows), size):
        batch = ai_rows[start:start + size]
        labels = None
        for attempt in (1, 2):  # one retry: a slow or dropped answer is often a one-off
            try:
                labels = _gemini_batch(batch, api_key, model)
                break
            except Exception as e:
                log.warning("AI batch failed, attempt %d of 2 (%s)", attempt, e)
                time.sleep(20)
        if labels is None:
            log.warning("Using keyword rules for the rest of this run")
            rule_rows = ai_rows[start:] + rule_rows
            break
        for i, r in enumerate(batch):
            r["themes"], r["method"] = labels.get(i, []), "ai"
        time.sleep(13)  # stay under a ~5 requests/minute free-tier limit

    for r in rule_rows:
        r["themes"], r["method"] = rule_themes(r["text"]), "rules"
    for r in rows:
        r.setdefault("themes", [])
        r.setdefault("method", "rules")
    return rows
