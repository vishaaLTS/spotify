"""
generate_dataset.py
--------------------
Generates a realistic synthetic Spotify-style dataset including:
  - songs.csv          : 1000 songs with audio features
  - users.csv          : 200 simulated users
  - listening_history.csv : user-song interaction data (play counts, likes, skips)

Run this script once before training any models.
"""

import os
import random
import numpy as np
import pandas as pd

# ── Reproducibility ────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── Constants ──────────────────────────────────────────────────────────────────
NUM_SONGS   = 1000
NUM_USERS   = 200
NUM_HISTORY = 8000          # interaction rows

GENRES = [
    "pop", "rock", "hip-hop", "jazz", "classical",
    "electronic", "r&b", "country", "metal", "indie",
    "latin", "blues", "reggae", "folk", "soul"
]

ARTIST_POOL = [
    "The Weeknd", "Dua Lipa", "Ed Sheeran", "Billie Eilish", "Drake",
    "Ariana Grande", "Taylor Swift", "Post Malone", "Kendrick Lamar",
    "Olivia Rodrigo", "Bad Bunny", "Harry Styles", "SZA", "Tyler the Creator",
    "Doja Cat", "J. Cole", "Lizzo", "The 1975", "Lil Nas X", "Giveon",
    "Glass Animals", "Tame Impala", "Bon Iver", "Phoebe Bridgers", "Frank Ocean",
    "Lana Del Rey", "Arctic Monkeys", "Radiohead", "Fleetwood Mac", "Queen",
    "Michael Jackson", "Beyoncé", "Rihanna", "Bruno Mars", "Adele",
    "Coldplay", "Imagine Dragons", "Maroon 5", "OneRepublic", "Khalid",
]

TRACK_ADJECTIVES = [
    "Electric", "Neon", "Golden", "Midnight", "Crystal", "Dark", "Wild",
    "Broken", "Silent", "Fading", "Dancing", "Lost", "Burning", "Frozen",
    "Hidden", "Falling", "Rising", "Endless", "Sweet", "Hollow"
]

TRACK_NOUNS = [
    "Dreams", "Lights", "Nights", "Fire", "Rain", "Heart", "Soul", "Wave",
    "Storm", "Mirror", "Shadow", "Voice", "Road", "Sky", "Flame", "Echo",
    "Rhythm", "Pulse", "Vibe", "Moment"
]


# ── Helper: generate a unique track name ──────────────────────────────────────
def make_track_name(used: set) -> str:
    for _ in range(1000):
        name = f"{random.choice(TRACK_ADJECTIVES)} {random.choice(TRACK_NOUNS)}"
        if name not in used:
            used.add(name)
            return name
    return f"Track_{random.randint(10000, 99999)}"


# ── 1. Songs ───────────────────────────────────────────────────────────────────
def generate_songs() -> pd.DataFrame:
    """Create 1 000 songs with realistic audio-feature distributions."""
    used_names: set = set()
    rows = []
    for i in range(NUM_SONGS):
        genre = random.choice(GENRES)

        # genre-biased audio features (rough heuristics)
        if genre in ("rock", "metal"):
            energy       = np.clip(np.random.normal(0.80, 0.10), 0, 1)
            danceability = np.clip(np.random.normal(0.45, 0.15), 0, 1)
            acousticness = np.clip(np.random.normal(0.10, 0.10), 0, 1)
            valence      = np.clip(np.random.normal(0.45, 0.20), 0, 1)
        elif genre in ("classical", "jazz", "blues"):
            energy       = np.clip(np.random.normal(0.35, 0.15), 0, 1)
            danceability = np.clip(np.random.normal(0.38, 0.15), 0, 1)
            acousticness = np.clip(np.random.normal(0.75, 0.15), 0, 1)
            valence      = np.clip(np.random.normal(0.42, 0.20), 0, 1)
        elif genre in ("electronic", "pop"):
            energy       = np.clip(np.random.normal(0.72, 0.12), 0, 1)
            danceability = np.clip(np.random.normal(0.75, 0.12), 0, 1)
            acousticness = np.clip(np.random.normal(0.15, 0.12), 0, 1)
            valence      = np.clip(np.random.normal(0.65, 0.20), 0, 1)
        elif genre in ("hip-hop", "r&b"):
            energy       = np.clip(np.random.normal(0.65, 0.15), 0, 1)
            danceability = np.clip(np.random.normal(0.78, 0.10), 0, 1)
            acousticness = np.clip(np.random.normal(0.20, 0.15), 0, 1)
            valence      = np.clip(np.random.normal(0.55, 0.20), 0, 1)
        else:
            energy       = np.clip(np.random.uniform(0.2, 0.9),  0, 1)
            danceability = np.clip(np.random.uniform(0.3, 0.85), 0, 1)
            acousticness = np.clip(np.random.uniform(0.1, 0.8),  0, 1)
            valence      = np.clip(np.random.uniform(0.2, 0.9),  0, 1)

        rows.append({
            "track_id"         : f"TRACK_{i+1:04d}",
            "track_name"       : make_track_name(used_names),
            "artist"           : random.choice(ARTIST_POOL),
            "genre"            : genre,
            "release_year"     : random.randint(1990, 2024),
            "duration_ms"      : random.randint(120_000, 360_000),
            "popularity"       : random.randint(10, 100),
            # ── audio features (0-1 scale, Spotify convention) ──────────────
            "tempo"            : round(np.random.uniform(60, 200), 2),
            "energy"           : round(energy,           4),
            "danceability"     : round(danceability,     4),
            "loudness"         : round(np.random.uniform(-20, 0), 2),  # dB
            "valence"          : round(valence,          4),
            "acousticness"     : round(acousticness,     4),
            "instrumentalness" : round(np.clip(np.random.exponential(0.15), 0, 1), 4),
            "speechiness"      : round(np.clip(np.random.exponential(0.08), 0, 1), 4),
            "liveness"         : round(np.clip(np.random.exponential(0.18), 0, 1), 4),
            "key"              : random.randint(0, 11),
            "mode"             : random.randint(0, 1),   # 0=minor, 1=major
            "time_signature"   : random.choice([3, 4, 4, 4, 4]),
        })

    df = pd.DataFrame(rows)
    return df


# ── 2. Users ───────────────────────────────────────────────────────────────────
def generate_users() -> pd.DataFrame:
    """Create 200 simulated users with preferred genre and age."""
    ages = np.random.randint(16, 60, NUM_USERS)
    rows = [
        {
            "user_id"          : f"USER_{i+1:04d}",
            "age"              : int(ages[i]),
            "preferred_genre"  : random.choice(GENRES),
            "subscription_type": random.choice(["free", "premium", "premium"]),
        }
        for i in range(NUM_USERS)
    ]
    return pd.DataFrame(rows)


# ── 3. Listening history ───────────────────────────────────────────────────────
def generate_listening_history(songs_df: pd.DataFrame,
                                users_df: pd.DataFrame) -> pd.DataFrame:
    """
    Simulate user-song interactions.
    Users are slightly biased toward their preferred genre.
    """
    track_ids  = songs_df["track_id"].tolist()
    user_ids   = users_df["user_id"].tolist()
    genre_map  = songs_df.set_index("track_id")["genre"].to_dict()

    user_genre = users_df.set_index("user_id")["preferred_genre"].to_dict()

    rows = []
    seen = set()         # (user_id, track_id) pairs — no duplicates

    attempts = 0
    while len(rows) < NUM_HISTORY and attempts < NUM_HISTORY * 10:
        attempts += 1
        uid = random.choice(user_ids)
        # 60 % chance to pick from preferred genre
        if random.random() < 0.60:
            preferred = user_genre[uid]
            subset = songs_df[songs_df["genre"] == preferred]["track_id"].tolist()
            tid = random.choice(subset) if subset else random.choice(track_ids)
        else:
            tid = random.choice(track_ids)

        if (uid, tid) in seen:
            continue
        seen.add((uid, tid))

        play_count = int(np.random.negative_binomial(3, 0.3) + 1)  # heavy-tailed
        like       = 1 if play_count > 5 or random.random() < 0.35 else 0
        skip       = 1 if play_count == 1 and random.random() < 0.55 else 0

        rows.append({
            "user_id"    : uid,
            "track_id"   : tid,
            "play_count" : play_count,
            "likes"      : like,
            "skips"      : skip,
            "rating"     : _compute_rating(play_count, like, skip),
            "genre"      : genre_map[tid],
        })

    return pd.DataFrame(rows)


def _compute_rating(play_count: int, like: int, skip: int) -> float:
    """Derive an implicit 1-5 rating from interaction signals."""
    score = min(play_count / 3.0, 3.0)   # 0-3 from plays
    score += like * 1.5
    score -= skip * 1.0
    return round(np.clip(score, 1.0, 5.0), 1)


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating songs …")
    songs_df = generate_songs()
    songs_path = os.path.join(out_dir, "songs.csv")
    songs_df.to_csv(songs_path, index=False)
    print(f"  Saved {len(songs_df)} songs → {songs_path}")

    print("Generating users …")
    users_df = generate_users()
    users_path = os.path.join(out_dir, "users.csv")
    users_df.to_csv(users_path, index=False)
    print(f"  Saved {len(users_df)} users → {users_path}")

    print("Generating listening history …")
    history_df = generate_listening_history(songs_df, users_df)
    history_path = os.path.join(out_dir, "listening_history.csv")
    history_df.to_csv(history_path, index=False)
    print(f"  Saved {len(history_df)} interactions → {history_path}")

    print("\nDataset generation complete!")
    print(f"  Songs shape          : {songs_df.shape}")
    print(f"  Users shape          : {users_df.shape}")
    print(f"  Interactions shape   : {history_df.shape}")
    print(f"  Unique users in hist : {history_df['user_id'].nunique()}")
    print(f"  Unique tracks in hist: {history_df['track_id'].nunique()}")
