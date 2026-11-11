"""Generate made-up sample reviews for offline testing (not real player reviews)."""
import json
import random
from datetime import date, timedelta

SNIPPETS = {
    "neg": [
        "The game is nothing like the ads, totally misleading.",
        "Where are the save the king levels from the ad?",
        "You have to pay money to pass anything, pay to win.",
        "Level 300 is impossible, I'm stuck for weeks.",
        "Boring and repetitive after a while.",
        "Keeps crashing after the update, lost my progress.",
    ],
    "pos": [
        "So much fun, I love this game!",
        "Very relaxing, good for my brain before bed.",
        "No ads and works offline, perfect.",
        "Love decorating the castle and the story.",
        "Great game, my favourite puzzle.",
    ],
}


def main(path="tests/sample.json", n=8000, seed=1):
    rnd = random.Random(seed)
    games = ["royal_match", "royal_kingdom", "candy_crush", "homescapes"]
    start = date.today() - timedelta(days=330)
    rows = []
    for i in range(n):
        g = rnd.choice(games)
        d = start + timedelta(days=rnd.randint(0, 330))
        rating = rnd.choice([1, 1, 2, 3, 4, 5, 5])
        bank = SNIPPETS["neg"] if rating <= 2 else SNIPPETS["pos"]
        # make the ad complaint grow for one game in the last complete month, to test alerts
        last_month = (date.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        if g == "royal_kingdom" and rating <= 2 and d.strftime("%Y-%m") == last_month:
            text = SNIPPETS["neg"][0] if rnd.random() < 0.6 else rnd.choice(bank)
        else:
            text = " ".join(rnd.sample(bank, rnd.randint(1, 2)))
        rows.append({"id": f"sample-{i}", "game": g, "store": rnd.choice(["app_store", "google_play"]),
                     "country": rnd.choice(["us", "gb", "ca", "au"]), "date": d.isoformat(),
                     "rating": rating, "version": "1.0", "text": text})
    json.dump(rows, open(path, "w"), indent=0)
    print(f"wrote {len(rows)} sample reviews to {path}")


if __name__ == "__main__":
    main()
