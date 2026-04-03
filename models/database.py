"""
models/database.py
-------------------
SQLite database layer for persisting users, songs, listening history,
and cached recommendation results.

Tables
------
  users               – user profiles
  songs               – song catalogue with audio features
  listening_history   – user-song interactions
  recommendations     – cached recommendation results

Usage
-----
    from models.database import Database
    db = Database()
    db.init_db()
    db.seed_from_csv()      # load CSVs into SQLite
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH  = os.path.join(BASE_DIR, "data", "spotify.db")


# ── DDL Statements ─────────────────────────────────────────────────────────────
CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    user_id           TEXT PRIMARY KEY,
    age               INTEGER,
    preferred_genre   TEXT,
    subscription_type TEXT
);
"""

CREATE_SONGS = """
CREATE TABLE IF NOT EXISTS songs (
    track_id          TEXT PRIMARY KEY,
    track_name        TEXT,
    artist            TEXT,
    genre             TEXT,
    release_year      INTEGER,
    duration_ms       INTEGER,
    popularity        INTEGER,
    tempo             REAL,
    energy            REAL,
    danceability      REAL,
    loudness          REAL,
    valence           REAL,
    acousticness      REAL,
    instrumentalness  REAL,
    speechiness       REAL,
    liveness          REAL,
    key_              INTEGER,
    mode_             INTEGER,
    time_signature    INTEGER
);
"""

CREATE_LISTENING_HISTORY = """
CREATE TABLE IF NOT EXISTS listening_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,
    track_id   TEXT NOT NULL,
    play_count INTEGER DEFAULT 0,
    likes      INTEGER DEFAULT 0,
    skips      INTEGER DEFAULT 0,
    rating     REAL,
    genre      TEXT,
    UNIQUE(user_id, track_id),
    FOREIGN KEY(user_id)  REFERENCES users(user_id),
    FOREIGN KEY(track_id) REFERENCES songs(track_id)
);
"""

CREATE_RECOMMENDATIONS = """
CREATE TABLE IF NOT EXISTS recommendations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    track_id       TEXT NOT NULL,
    hybrid_score   REAL,
    cf_score       REAL,
    cb_score       REAL,
    model_type     TEXT DEFAULT 'hybrid',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id)  REFERENCES users(user_id),
    FOREIGN KEY(track_id) REFERENCES songs(track_id)
);
"""


# ──────────────────────────────────────────────────────────────────────────────
class Database:
    """Thin wrapper around SQLite for the recommendation engine."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row      # dict-like rows
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    # ── DDL ──────────────────────────────────────────────────────────────────
    def init_db(self):
        """Create all tables (idempotent)."""
        with self._connect() as conn:
            for ddl in [CREATE_USERS, CREATE_SONGS,
                        CREATE_LISTENING_HISTORY, CREATE_RECOMMENDATIONS]:
                conn.execute(ddl)
        print(f"  Database initialised at: {self.db_path}")

    # ── Seed ─────────────────────────────────────────────────────────────────
    def seed_from_csv(self):
        """Load preprocessed CSVs into the SQLite database."""
        users_path   = os.path.join(DATA_DIR, "users.csv")
        songs_path   = os.path.join(DATA_DIR, "songs_clean.csv")
        history_path = os.path.join(DATA_DIR, "history_clean.csv")

        with self._connect() as conn:
            # Users
            if os.path.exists(users_path):
                users_df = pd.read_csv(users_path)
                users_df.to_sql("users", conn, if_exists="replace", index=False)
                print(f"  Seeded {len(users_df)} users.")

            # Songs
            if os.path.exists(songs_path):
                songs_df = pd.read_csv(songs_path)
                # Rename Python-reserved or SQLite-reserved column names
                songs_df = songs_df.rename(columns={"key": "key_", "mode": "mode_"})
                songs_df.to_sql("songs", conn, if_exists="replace", index=False)
                print(f"  Seeded {len(songs_df)} songs.")

            # Listening history
            if os.path.exists(history_path):
                hist_df = pd.read_csv(history_path)
                hist_df.to_sql("listening_history", conn, if_exists="replace",
                                index=False)
                print(f"  Seeded {len(hist_df)} listening history rows.")

    # ── Read helpers ──────────────────────────────────────────────────────────
    def get_user(self, user_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_song(self, track_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM songs WHERE track_id = ?", (track_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_user_history(self, user_id: str) -> list:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM listening_history WHERE user_id = ? "
                "ORDER BY play_count DESC",
                (user_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Write helpers ─────────────────────────────────────────────────────────
    def save_recommendations(self, user_id: str,
                              recs_df: pd.DataFrame,
                              model_type: str = "hybrid"):
        """Persist a batch of recommendations for a user."""
        rows = [
            (user_id, row["track_id"],
             float(row.get("hybrid_score", 0)),
             float(row.get("cf_score", 0)),
             float(row.get("cb_score", 0)),
             model_type)
            for _, row in recs_df.iterrows()
        ]
        with self._connect() as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO recommendations
                   (user_id, track_id, hybrid_score, cf_score, cb_score, model_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                rows
            )

    def get_cached_recommendations(self, user_id: str,
                                    model_type: str = "hybrid") -> list:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT r.track_id, s.track_name, s.artist, s.genre,
                          r.hybrid_score, r.cf_score, r.cb_score
                   FROM recommendations r
                   JOIN songs s ON r.track_id = s.track_id
                   WHERE r.user_id = ? AND r.model_type = ?
                   ORDER BY r.hybrid_score DESC""",
                (user_id, model_type)
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Utility ───────────────────────────────────────────────────────────────
    def table_counts(self) -> dict:
        tables = ["users", "songs", "listening_history", "recommendations"]
        with self._connect() as conn:
            return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    for t in tables}


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db = Database()
    db.init_db()
    db.seed_from_csv()
    print("\nTable row counts:")
    for table, count in db.table_counts().items():
        print(f"  {table:<25}: {count}")
