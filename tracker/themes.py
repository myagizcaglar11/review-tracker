"""Review themes and the keyword rules used to tag them.

Each theme has a label for the dashboard and a regular expression.
The rules are the fallback classifier: they work for English reviews
with no API key. The AI classifier (classify.py) uses the same theme keys
and descriptions, so both methods produce comparable numbers.
"""
import re

AD_WORDS = r"(ads?|adds?|advert\w*|preview|commercials?)"

THEMES = {
    "ad_mismatch": {
        "label": "Ad is not the game",
        "description": "Says the ads are fake, misleading or show a different game.",
        "pattern": r"\b" + AD_WORDS + r"\b[^.!?]{0,60}\b(fake|misleading|false|lie|lying|scam|bait|nothing like|not like|not what|aren't (actually )?what|isn't what|different|no ?where close)\b"
                   r"|\b(fake|misleading|false|nothing like|not like|no ?where close|none of them (were|are) like|never played a level like)\b[^.!?]{0,60}\b" + AD_WORDS + r"\b"
                   r"|\bfalse advertis\w*|\bdoesn't match the game\b",
    },
    "save_king": {
        "label": "Where is 'save the king'?",
        "description": "Asks for or misses the rescue / 'save the king' style levels shown in ads.",
        "pattern": r"\b(save the king|saving the king|rescue|king'?s nightmare|nightmare levels?|save king)\b",
    },
    "money": {
        "label": "Money / pay to win",
        "description": "Complains about prices, needing to pay, or pay-to-win.",
        "pattern": r"\b(pay|paying|paid|money|expensive|spend|spent|cash ?grab|pay ?to ?win|greedy|purchas\w*|micro ?transactions?|stingy|rip ?off|\d[\d,]* coins|coins? out of you|coin packs?)\b|\$\d+",
    },
    "difficulty": {
        "label": "Too hard / stuck",
        "description": "Levels feel too hard, impossible, rigged, or the player is stuck.",
        "pattern": r"\b(too hard|so hard|very hard|super hard|insanely hard|really hard|hard levels?|harder|difficult|impossible|stuck|can'?t (pass|beat|win|get past|solve)|rigged|unbeatable|designed (for you )?to fail|works? against you|not enough moves|less moves)\b",
    },
    "boring": {
        "label": "Boring / repetitive",
        "description": "The game feels boring, repetitive or the same as other games.",
        "pattern": r"\b(boring|repetitive|bored|tedious|monotonous)\b",
    },
    "bugs": {
        "label": "Bugs / crashes",
        "description": "Crashes, bugs, freezing, lost progress, loading problems.",
        "pattern": r"\b(crash\w*|bug\w*|freez\w*|glitch\w*|lost (my )?progress|won'?t load|not loading|lock(s|ed)? me|can'?t exit|no way to exit|never received|did(n'?t| not) receive|can'?t receive|does(n'?t| not)( always)? (work|accept))\b",
    },
    "fun": {
        "label": "Fun / love it",
        "description": "Praises the game as fun, addictive, enjoyable or a favourite.",
        "pattern": r"\b(fun|love|loving|loved|enjoy\w*|addict\w*|favou?rite|a blast|brilliant|excellent|amazing|awesome|(great|best|good) game|so good|it'?s great|game is great)\b",
    },
    "relaxing": {
        "label": "Relaxing / brain break",
        "description": "Calming, relaxing, good for the brain, a short break.",
        "pattern": r"\b(relax\w*|calm\w*|unwind|stress[- ]?relie\w*|de-?stress|not stressful|brain|mental health|pass the time|kill time|waste a few minutes|short break|before (bed|sleep|going to sleep))\b",
    },
    "no_ads": {
        "label": "No ads in game",
        "description": "Praises that the game has no forced ads, or plays offline.",
        "pattern": r"(?<!advertised )\b(no ads|no adds|no adverts|without ads|ad[- ]free|wifi|wi-fi|offline|(doesn'?t|don'?t)( even)? (require|need|have)s? (ads|adds))\b",
    },
    "story_building": {
        "label": "Story / building",
        "description": "Mentions the story, characters, decorating or building areas.",
        "pattern": r"\b(story|storyline|decor\w*|renovat\w*|mansion|district|kingdom building|build(ing)? (the|my|your) (kingdom|castle|house))\b",
    },
}

NEGATIVE_THEMES = ["ad_mismatch", "save_king", "money", "difficulty", "boring", "bugs"]
POSITIVE_THEMES = ["fun", "relaxing", "no_ads", "story_building"]

_COMPILED = {k: re.compile(v["pattern"], re.IGNORECASE) for k, v in THEMES.items()}

# "not fun", "can't enjoy", "never boring" mean the opposite, so they are removed
# before the fun and boring rules run.
_NEGATED = re.compile(r"\b(not|no|never|isn'?t|can'?t|cannot|don'?t|won'?t)\s+(be\s+)?(fun|enjoy\w*|boring)\b|fun out of|taken the fun", re.IGNORECASE)
_USES_NEGATION_FILTER = {"fun", "boring"}


def _normalize(text: str) -> str:
    # Curly apostrophes (’) are common on phones and break patterns like "doesn't".
    return (text or "").replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'")


def rule_themes(text: str) -> list[str]:
    """Return the theme keys whose keyword rule matches the text."""
    text = _normalize(text)
    without_negations = _NEGATED.sub(" ", text)
    return [k for k, rx in _COMPILED.items()
            if rx.search(without_negations if k in _USES_NEGATION_FILTER else text)]
