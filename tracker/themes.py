"""Review themes and the keyword rules used to tag them.

Each theme has a label for the dashboard and a regular expression.
The rules are the fallback classifier: they work for English reviews
with no API key. The AI classifier (classify.py) uses the same theme keys
and descriptions, so both methods produce comparable numbers.
"""
import re

THEMES = {
    "ad_mismatch": {
        "label": "Ad is not the game",
        "description": "Says the ads are fake, misleading or show a different game.",
        "pattern": r"\b(ads?|adds|advert\w*|commercials?)\b[^.]{0,80}\b(fake|misleading|false|lie|lying|not (like|the same|in)|nothing like|different|never)\b"
                   r"|\b(fake|misleading|false)\b[^.]{0,30}\b(ads?|adds|advert\w*)\b",
    },
    "save_king": {
        "label": "Where is 'save the king'?",
        "description": "Asks for or misses the rescue / 'save the king' style levels shown in ads.",
        "pattern": r"\b(save the king|saving the king|rescue|king'?s nightmare|nightmare levels?|save king)\b",
    },
    "money": {
        "label": "Money / pay to win",
        "description": "Complains about prices, needing to pay, or pay-to-win.",
        "pattern": r"\b(pay|paying|paid|money|expensive|spend|spent|cash ?grab|pay ?to ?win|greedy|\$\d+)\b",
    },
    "difficulty": {
        "label": "Too hard / stuck",
        "description": "Levels feel too hard, impossible, rigged, or the player is stuck.",
        "pattern": r"\b(too hard|so hard|very hard|difficult|impossible|stuck|can'?t (pass|beat|win|get past)|rigged|unbeatable)\b",
    },
    "boring": {
        "label": "Boring / repetitive",
        "description": "The game feels boring, repetitive or the same as other games.",
        "pattern": r"\b(boring|repetitive|same thing|bored|tedious)\b",
    },
    "bugs": {
        "label": "Bugs / crashes",
        "description": "Crashes, bugs, freezing, lost progress, loading problems.",
        "pattern": r"\b(crash\w*|bug\w*|freez\w*|glitch\w*|lost (my )?progress|won'?t load|not loading)\b",
    },
    "fun": {
        "label": "Fun / love it",
        "description": "Praises the game as fun, addictive, enjoyable or a favourite.",
        "pattern": r"\b(fun|love|loving|enjoy\w*|addict\w*|great game|best game|favou?rite)\b",
    },
    "relaxing": {
        "label": "Relaxing / brain break",
        "description": "Calming, relaxing, good for the brain, a short break.",
        "pattern": r"\b(relax\w*|calm\w*|unwind|stress|brain|mind)\b",
    },
    "no_ads": {
        "label": "No ads in game",
        "description": "Praises that the game has no forced ads, or plays offline.",
        "pattern": r"\b(no ads|no adds|no adverts|without ads|ad[- ]free|no pop[- ]?ups|wifi|wi-fi|offline)\b",
    },
    "story_building": {
        "label": "Story / building",
        "description": "Mentions the story, characters, decorating or building areas.",
        "pattern": r"\b(story|castle|kingdom|decorat\w*|build\w*|renovat\w*|characters?|mansion|house)\b",
    },
}

NEGATIVE_THEMES = ["ad_mismatch", "save_king", "money", "difficulty", "boring", "bugs"]
POSITIVE_THEMES = ["fun", "relaxing", "no_ads", "story_building"]

_COMPILED = {k: re.compile(v["pattern"], re.IGNORECASE) for k, v in THEMES.items()}


def rule_themes(text: str) -> list[str]:
    """Return the theme keys whose keyword rule matches the text."""
    text = text or ""
    return [k for k, rx in _COMPILED.items() if rx.search(text)]
