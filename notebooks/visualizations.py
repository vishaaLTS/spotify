"""
notebooks/visualizations.py
----------------------------
Stand-alone visualisation script. Generates 6 analysis plots and saves them
to notebooks/plots/.

Run:
    python notebooks/visualizations.py

Plots
-----
  1. Genre distribution in the catalogue
  2. Audio feature distributions (box plots)
  3. Play-count distribution (histogram)
  4. User-genre preference heat-map
  5. Song popularity distribution
  6. Top 15 most-played tracks
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")
PLOTS_DIR = os.path.join(BASE_DIR, "notebooks", "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

sns.set_theme(style="darkgrid", palette="muted")
PALETTE = "husl"

# ── Load data ──────────────────────────────────────────────────────────────────
def load_data():
    songs   = pd.read_csv(os.path.join(DATA_DIR, "songs_clean.csv"))
    history = pd.read_csv(os.path.join(DATA_DIR, "history_clean.csv"))
    users   = pd.read_csv(os.path.join(DATA_DIR, "users.csv"))
    return songs, history, users


# ── Plot 1: Genre distribution ─────────────────────────────────────────────────
def plot_genre_distribution(songs: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 6))
    genre_counts = songs["genre"].value_counts()
    colors = sns.color_palette(PALETTE, len(genre_counts))
    bars = ax.barh(genre_counts.index, genre_counts.values, color=colors)
    ax.bar_label(bars, padding=3, fontsize=10)
    ax.set_xlabel("Number of Songs", fontsize=12)
    ax.set_title("Genre Distribution in the Catalogue", fontsize=15, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "01_genre_distribution.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Plot 2: Audio feature box plots ───────────────────────────────────────────
def plot_audio_features(songs: pd.DataFrame):
    features = ["energy", "danceability", "valence",
                "acousticness", "instrumentalness", "speechiness", "liveness"]
    feat_df  = songs[features]
    fig, ax  = plt.subplots(figsize=(14, 7))
    feat_df.boxplot(ax=ax, patch_artist=True,
                    boxprops=dict(facecolor="#4e9af1", alpha=0.6),
                    medianprops=dict(color="red", linewidth=2))
    ax.set_title("Audio Feature Distributions", fontsize=15, fontweight="bold")
    ax.set_ylabel("Normalised Value (0–1)", fontsize=12)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "02_audio_features.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Plot 3: Play-count histogram ───────────────────────────────────────────────
def plot_play_count(history: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5))
    clipped = history["play_count"].clip(upper=30)
    ax.hist(clipped, bins=30, color="#6c63ff", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Play Count (clipped at 30)", fontsize=12)
    ax.set_ylabel("Number of Interactions", fontsize=12)
    ax.set_title("Play-Count Distribution", fontsize=15, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "03_play_count_dist.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Plot 4: User-genre heat-map ────────────────────────────────────────────────
def plot_user_genre_heatmap(history: pd.DataFrame):
    pivot = (
        history.groupby(["user_id", "genre"])["play_count"]
        .sum()
        .unstack(fill_value=0)
    )
    # Keep top-20 users and top-10 genres for readability
    top_users  = pivot.sum(axis=1).nlargest(20).index
    top_genres = pivot.sum(axis=0).nlargest(10).index
    sub = pivot.loc[top_users, top_genres]

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(sub, ax=ax, cmap="YlOrRd", linewidths=0.5,
                cbar_kws={"label": "Total Plays"}, fmt="d", annot=True,
                annot_kws={"size": 8})
    ax.set_title("User–Genre Play-Count Heatmap (Top 20 users × Top 10 genres)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Genre", fontsize=11)
    ax.set_ylabel("User ID", fontsize=11)
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "04_user_genre_heatmap.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Plot 5: Song popularity distribution ──────────────────────────────────────
def plot_popularity(songs: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(songs["popularity"], bins=20, kde=True, ax=ax,
                 color="#f7b731", edgecolor="white")
    ax.set_xlabel("Popularity Score (0–100)", fontsize=12)
    ax.set_ylabel("Count", fontsize=12)
    ax.set_title("Song Popularity Distribution", fontsize=15, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "05_popularity_dist.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Plot 6: Top 15 most-played tracks ─────────────────────────────────────────
def plot_top_tracks(history: pd.DataFrame, songs: pd.DataFrame):
    top = (
        history.groupby("track_id")["play_count"]
        .sum()
        .nlargest(15)
        .reset_index()
        .merge(songs[["track_id", "track_name", "artist"]], on="track_id")
    )
    top["label"] = top["track_name"] + "\n(" + top["artist"] + ")"
    fig, ax = plt.subplots(figsize=(14, 7))
    colors = sns.color_palette("cool", len(top))
    bars = ax.barh(top["label"], top["play_count"], color=colors)
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_xlabel("Total Play Count", fontsize=12)
    ax.set_title("Top 15 Most-Played Tracks", fontsize=15, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "06_top_tracks.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Plot 7: Correlation heatmap of audio features ─────────────────────────────
def plot_feature_correlation(songs: pd.DataFrame):
    features = ["tempo", "energy", "danceability", "valence",
                "acousticness", "instrumentalness", "speechiness", "liveness"]
    corr = songs[features].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, ax=ax, cmap="coolwarm", annot=True, fmt=".2f",
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
    ax.set_title("Audio Feature Correlation Matrix", fontsize=15, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "07_feature_correlation.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading data …")
    songs, history, users = load_data()
    print(f"  Songs: {songs.shape}  History: {history.shape}  Users: {users.shape}")

    print("\nGenerating plots …")
    plot_genre_distribution(songs)
    plot_audio_features(songs)
    plot_play_count(history)
    plot_user_genre_heatmap(history)
    plot_popularity(songs)
    plot_top_tracks(history, songs)
    plot_feature_correlation(songs)

    print(f"\nAll plots saved to: {PLOTS_DIR}")
