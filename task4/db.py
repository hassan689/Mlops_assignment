"""SQLite persistence for prediction history."""

import os
import sqlite3
from pathlib import Path


def database_url() -> str:
    return os.getenv("DATABASE_URL", "")


def database_path() -> str:
    return os.getenv("DATABASE_PATH", str(Path(__file__).with_name("history.db")))


def _connection():
    url = database_url()
    if url:
        import psycopg
        return psycopg.connect(url)
    return sqlite3.connect(database_path())


def initialise() -> None:
    with _connection() as connection:
        table_sql = (
            """CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                verdict TEXT NOT NULL,
                confidence DOUBLE PRECISION NOT NULL,
                model TEXT NOT NULL DEFAULT 'models:/VisionGuard@champion',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
            if database_url()
            else
            """CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                verdict TEXT NOT NULL,
                confidence REAL NOT NULL,
                model TEXT NOT NULL DEFAULT 'models:/VisionGuard@champion',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            table_sql
        )
        if not database_url():
            columns = {row[1] for row in connection.execute("PRAGMA table_info(predictions)")}
        else:
            columns = {row[0] for row in connection.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'predictions'"
            )}
        if "model" not in columns:
            connection.execute(
                "ALTER TABLE predictions ADD COLUMN model TEXT NOT NULL "
                "DEFAULT 'models:/VisionGuard@champion'"
            )


def add_prediction(filename: str, verdict: str, confidence: float, model: str) -> None:
    with _connection() as connection:
        connection.execute(
            "INSERT INTO predictions (filename, verdict, confidence, model) VALUES (%s, %s, %s, %s)"
            if database_url()
            else "INSERT INTO predictions (filename, verdict, confidence, model) VALUES (?, ?, ?, ?)",
            (filename, verdict, confidence, model),
        )


def recent_predictions(limit: int = 50) -> list[tuple]:
    with _connection() as connection:
        query = (
            "SELECT filename, verdict, confidence, model, created_at "
            "FROM predictions ORDER BY id DESC LIMIT %s"
            if database_url()
            else
            "SELECT filename, verdict, confidence, model, created_at "
            "FROM predictions ORDER BY id DESC LIMIT ?"
        )
        return connection.execute(
            query,
            (limit,),
        ).fetchall()
