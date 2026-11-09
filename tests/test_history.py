import sqlite3

from task4 import db


def test_prediction_history_is_queryable(tmp_path, monkeypatch):
    path = tmp_path / "history.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    monkeypatch.delenv("DATABASE_URL", raising=False)

    db.initialise()
    db.add_prediction("example.png", "real", 0.75, "test-model")

    record = db.recent_predictions()[0]
    assert record[:4] == ("example.png", "real", 0.75, "test-model")
    assert sqlite3.connect(path).execute(
        "SELECT COUNT(*) FROM predictions"
    ).fetchone()[0] == 1
