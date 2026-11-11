# How accurate are the keyword rules?

Measured on 11 November 2026 against reference labels for recent App Store reviews of all four games.

**Who labeled:** the reference labels were set by an AI assistant (Claude) reading each review for meaning, not by a person. The same assistant wrote the rules, so the numbers may be somewhat optimistic. A human-labeled check is the next step.

## Method

1. **Tuning set:** 100 reviews (25 per game; US and UK; a mix of 1–2★, 3★ and 4–5★). Labeled first, then the rules were measured and improved on these.
2. **Hold-out set:** 40 different reviews (Canada and Australia), labeled *before* the improved rules were run on them. This is the honest number, because the rules never saw these reviews.

Precision = of the reviews the rules tagged with a theme, the share that really had it.
Recall = of the reviews that really had a theme, the share the rules caught.

## Results on the hold-out set (40 reviews)

| | Precision | Recall |
|---|---|---|
| Old rules (v1) | 78% | 65% |
| **New rules (v2)** | **87%** | **69%** |

By theme (v2, hold-out): "Ad is not the game" 100% precision but only 44% recall; "Bugs / crashes" 50% precision, 20% recall; "Money" 88% / 88%; "Fun" 100% / 77%.

On the tuning set v2 reaches 95%+ on most themes, but that is not a fair score: the rules were fitted to those reviews.

## What this means

- **Shares of "Ad is not the game" are an undercount.** The rules almost never tag it by mistake, but they miss many ways of saying it ("doesn't look like the ads", "the levels advertised don't occur"). Real shares are likely well above what the dashboard shows. Read them as a lower bound and watch the trend, not the level.
- **What changed in v2:** curly apostrophes (’) are normalized (they silently broke patterns like "doesn't"); "not fun" / "can't enjoy" no longer count as praise; ad complaints are matched in both word orders; more ways to say money, difficulty and bugs.
- **Keyword rules hit a ceiling.** Paraphrases, sarcasm and other languages need the AI classifier (`GEMINI_API_KEY`). The same hold-out set can then compare AI vs. rules.
