# Classifier accuracy

Run on 2026-11-12 against `eval/labels.json` (104 of 140 labeled reviews still in the App Store feeds).

## Hold-out set (the fair test: the rules were not tuned on these)

40 reviews.

| Theme | Reviews with it | Keyword rules precision | Keyword rules recall |
|---|---|---|---|
| Ad is not the game | 9 | 100% | 44% |
| Where is 'save the king'? | 4 | 100% | 50% |
| Money / pay to win | 8 | 88% | 88% |
| Too hard / stuck | 6 | 75% | 100% |
| Boring / repetitive | 2 | 100% | 100% |
| Bugs / crashes | 5 | 50% | 20% |
| Fun / love it | 13 | 100% | 77% |
| Relaxing / brain break | 1 | 100% | 100% |
| No ads in game | 0 | – | – |
| Story / building | 0 | 0% | – |
| **All themes** | 48 | 87% | 69% |

## Tuning set (the rules were adjusted on these, so scores are optimistic)

64 reviews.

| Theme | Reviews with it | Keyword rules precision | Keyword rules recall |
|---|---|---|---|
| Ad is not the game | 10 | 100% | 100% |
| Where is 'save the king'? | 2 | 100% | 100% |
| Money / pay to win | 16 | 89% | 100% |
| Too hard / stuck | 9 | 75% | 100% |
| Boring / repetitive | 3 | 75% | 100% |
| Bugs / crashes | 3 | 100% | 100% |
| Fun / love it | 32 | 100% | 100% |
| Relaxing / brain break | 5 | 100% | 100% |
| No ads in game | 1 | 100% | 100% |
| Story / building | 0 | – | – |
| **All themes** | 81 | 93% | 100% |

Reference labels were set by an AI assistant reading each review for meaning, not by a person; see EVALUATION.md.
