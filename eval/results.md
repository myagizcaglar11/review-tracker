# Classifier accuracy

Run on 2026-11-12 against `eval/labels.json` (96 of 140 labeled reviews still in the App Store feeds).

## Hold-out set (the fair test: the rules were not tuned on these)

21 reviews.

| Theme | Reviews with it | Keyword rules precision | Keyword rules recall |
|---|---|---|---|
| Ad is not the game | 6 | 100% | 33% |
| Where is 'save the king'? | 3 | 100% | 67% |
| Money / pay to win | 5 | 80% | 80% |
| Too hard / stuck | 3 | 60% | 100% |
| Boring / repetitive | 1 | 100% | 100% |
| Bugs / crashes | 1 | – | 0% |
| Fun / love it | 4 | 100% | 50% |
| Relaxing / brain break | 1 | 100% | 100% |
| No ads in game | 0 | – | – |
| Story / building | 0 | – | – |
| **All themes** | 24 | 83% | 62% |

## Tuning set (the rules were adjusted on these, so scores are optimistic)

75 reviews.

| Theme | Reviews with it | Keyword rules precision | Keyword rules recall |
|---|---|---|---|
| Ad is not the game | 10 | 100% | 100% |
| Where is 'save the king'? | 3 | 100% | 100% |
| Money / pay to win | 18 | 95% | 100% |
| Too hard / stuck | 12 | 86% | 100% |
| Boring / repetitive | 6 | 75% | 100% |
| Bugs / crashes | 3 | 100% | 100% |
| Fun / love it | 33 | 100% | 100% |
| Relaxing / brain break | 4 | 100% | 100% |
| No ads in game | 1 | 100% | 100% |
| Story / building | 0 | – | – |
| **All themes** | 90 | 95% | 100% |

Reference labels were set by an AI assistant reading each review for meaning, not by a person; see EVALUATION.md.
