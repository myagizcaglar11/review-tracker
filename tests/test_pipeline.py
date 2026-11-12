import json

from tracker import aggregate, classify, collect, store
from tracker.themes import rule_themes

CONFIG = json.load(open("config.json"))


def test_rules_tag_known_phrases():
    assert "ad_mismatch" in rule_themes("Fake ads, the game is nothing like the ad")
    assert "money" in rule_themes("Pay to win, I spent so much money")
    assert "fun" in rule_themes("I love it")
    assert rule_themes("") == []


def test_appstore_parser(monkeypatch):
    entry = {"id": {"label": "123"}, "updated": {"label": "2026-11-01T10:00:00-07:00"},
             "im:rating": {"label": "2"}, "im:version": {"label": "1.0"},
             "title": {"label": "Meh"}, "content": {"label": "Too hard"}}

    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"feed": {"entry": [entry]}}

    monkeypatch.setattr(collect.requests, "get", lambda *a, **k: Resp())
    rows = collect.appstore_reviews("1", "us", pages=3)
    assert rows == [{"id": "ios-123", "store": "app_store", "country": "us", "date": "2026-11-01",
                     "rating": 2, "version": "1.0", "text": "Meh. Too hard"}]


def test_ai_failure_falls_back_to_rules(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    def boom(*a, **k): raise RuntimeError("quota")
    monkeypatch.setattr(classify, "_gemini_batch", boom)
    monkeypatch.setattr(classify.time, "sleep", lambda s: None)  # skip the retry wait in tests
    rows = [{"text": "fake ads", "rating": 1}]
    classify.classify(rows, CONFIG)
    assert rows[0]["method"] == "rules" and "ad_mismatch" in rows[0]["themes"]


def test_text_is_never_saved(tmp_path):
    rows = [{"id": "a", "game": "royal_match", "store": "app_store", "country": "us", "date": "2026-11-01",
             "rating": 1, "version": "", "themes": ["money"], "method": "rules", "text": "secret words"}]
    p = tmp_path / "r.csv"
    store.save(str(p), rows)
    assert "secret" not in p.read_text()
    assert store.load(str(p))[0]["themes"] == ["money"]


def test_alert_fires_on_spike():
    from datetime import date, timedelta
    def month(back):
        d = date.today().replace(day=1)
        for _ in range(back):
            d = (d - timedelta(days=1)).replace(day=1)
        return d.strftime("%Y-%m")
    rows = []
    for m, share in [(month(4), 0.1), (month(3), 0.1), (month(2), 0.1), (month(1), 0.4)]:
        for i in range(100):
            rows.append({"game": "royal_match", "date": f"{m}-05", "rating": 1, "method": "rules",
                         "store": "app_store", "themes": ["ad_mismatch"] if i < share * 100 else []})
    data = aggregate.build(rows, {}, CONFIG)
    assert data["alerts"] and data["alerts"][0]["theme"] == "ad_mismatch" and data["alerts"][0]["change"] == 30.0


def test_curly_apostrophes_and_negations():
    assert "ad_mismatch" in rule_themes("The ads for it aren’t actually what the game is")
    assert "fun" not in rule_themes("Can’t enjoy it anymore, it’s not fun anymore")
    assert "boring" not in rule_themes("You can’t be boring with this game")
    assert "money" in rule_themes("900 coins for 5 more moves")


def test_a_change_in_market_mix_is_not_reported_as_a_change_in_opinion():
    """Same share within each store, but the recent window has far more Google Play reviews,
    which mention the theme less. Raw shares would drop; like-for-like shares must not."""
    from tracker.aggregate import _std_shares
    def make(store, n, k):
        return [{"store": store, "country": "us", "themes": ["fun"] if i < k else []} for i in range(n)]
    before = make("app_store", 100, 60) + make("google_play", 10, 2)    # 60% and 20%
    recent = make("app_store", 20, 12) + make("google_play", 100, 20)   # same 60% and 20%
    now, then, _, _ = _std_shares(recent, before, "fun")
    assert now == then


def test_evaluation_scores():
    from tracker.evaluate import scores
    items = [{"id": "a", "themes": ["money"]}, {"id": "b", "themes": []}]
    s = scores(items, {"a": ["money"], "b": ["money"]})
    assert s["money"]["precision"] == 0.5 and s["money"]["recall"] == 1.0
