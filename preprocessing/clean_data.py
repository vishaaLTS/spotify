"""
preprocessing/clean_data.py
----------------------------
Cleans raw CSVs, normalises audio features, and saves processed files.

Outputs
-------
  data/songs_clean.csv      - cleaned song catalogue
  data/history_clean.csv    - cleaned interaction log
  data/user_item_matrix.csv - pivot: user × track → rating
  data/audio_features.csv   - normalised audio-feature vectors (songs only)
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")


def load_raw(filename: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Raw data not found: {path}\n"
            "Run  python data/generate_dataset.py  first."
        )
    return pd.read_csv(path)


# ── Audio-feature columns used throughout the project ─────────────────────────
AUDIO_FEATURES = [
    "tempo", "energy", "danceability", "loudness",
    "valence", "acousticness", "instrumentalness",
    "speechiness", "liveness",
]


def clean_songs(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicates, fill/clip missing values, normalise loudness to [0,1]."""
    df = df.copy()

    # Drop exact duplicates
    df.drop_duplicates(subset=["track_id"], inplace=True)

    # Fill any NaN in audio features with column median
    for col in AUDIO_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    # Clip [0,1] features — loudness is dB so just clip to [−60, 0]
    unit_cols = [c for c in AUDIO_FEATURES if c != "loudness"]
    for col in unit_cols:
        df[col] = df[col].clip(0.0, 1.0)
    if "loudness" in df.columns:
        df["loudness"] = df["loudness"].clip(-60.0, 0.0)

    # release_year sanity check
    if "release_year" in df.columns:
        df["release_year"] = df["release_year"].clip(1900, 2025)

    # Normalise loudness to [0,1] for ML use (keep raw column too)
    if "loudness" in df.columns:
        df["loudness_norm"] = (df["loudness"] - df["loudness"].min()) / \
                              (df["loudness"].max() - df["loudness"].min() + 1e-9)

    df.reset_index(drop=True, inplace=True)
    return df


def clean_history(df: pd.DataFrame, valid_tracks: set, valid_users: set) -> pd.DataFrame:
    """
    Remove interactions referencing unknown users/tracks,
    clip play_count, and ensure rating in [1,5].
    """
    df = df.copy()
    df = df[df["track_id"].isin(valid_tracks) & df["user_id"].isin(valid_users)]
    df.drop_duplicates(subset=["user_id", "track_id"], inplace=True)
    df["play_count"] = df["play_count"].clip(1, 500)
    df["rating"]     = df["rating"].clip(1.0, 5.0)
    df.reset_index(drop=True, inplace=True)
    return df


def build_user_item_matrix(history_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot table: rows=users, cols=track_ids, values=rating (NaN if none)."""
    matrix = history_df.pivot_table(
        index="user_id", columns="track_id", values="rating", aggfunc="mean"
    )
    return matrix


def extract_audio_features(songs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame of MinMax-normalised audio features indexed by track_id.
    Tempo is scaled together with the other features.
    """
    feat_cols = [c for c in AUDIO_FEATURES if c in songs_df.columns]
    features  = songs_df[["track_id"] + feat_cols].set_index("track_id").copy()

    scaler = MinMaxScaler()
    features[feat_cols] = scaler.fit_transform(features[feat_cols])
    return features


# ── Main ───────────────────────────────────────────────────────────────────────
def run_preprocessing():
    print("Loading raw data …")
    songs_raw   = load_raw("songs.csv")
    history_raw = load_raw("listening_history.csv")

    print(f"  Raw songs      : {songs_raw.shape}")
    print(f"  Raw history    : {history_raw.shape}")

    print("\nCleaning songs …")
    songs_clean = clean_songs(songs_raw)
    valid_tracks = set(songs_clean["track_id"])
    valid_users  = set(history_raw["user_id"])      # users come from history

    print("Cleaning listening history …")
    history_clean = clean_history(history_raw, valid_tracks, valid_users)

    print("Building user-item matrix …")
    ui_matrix = build_user_item_matrix(history_clean)

    print("Extracting normalised audio features …")
    audio_feat = extract_audio_features(songs_clean)

    # ── Save ──────────────────────────────────────────────────────────────────
    songs_clean.to_csv(os.path.join(DATA_DIR, "songs_clean.csv"), index=False)
    history_clean.to_csv(os.path.join(DATA_DIR, "history_clean.csv"), index=False)
    ui_matrix.to_csv(os.path.join(DATA_DIR, "user_item_matrix.csv"))
    audio_feat.to_csv(os.path.join(DATA_DIR, "audio_features.csv"))

    print("\nPreprocessing complete!")
    print(f"  songs_clean.csv      : {songs_clean.shape}")
    print(f"  history_clean.csv    : {history_clean.shape}")
    print(f"  user_item_matrix.csv : {ui_matrix.shape}")
    print(f"  audio_features.csv   : {audio_feat.shape}")
    return songs_clean, history_clean, ui_matrix, audio_feat


if __name__ == "__main__":
    run_preprocessing()
