"""
recommender/hybrid.py
----------------------
Hybrid Recommendation System
==============================
Combines collaborative filtering (SVD) scores with content-based similarity
scores using a weighted linear blend.

                hybrid_score = α × cf_score + (1-α) × cb_score

The weights (α) can be tuned at query time to shift between personalisation
(high α) and audio-feature discovery (low α).

Pipeline
--------
1. Load pre-trained SVD and content-based models (must call train_all.py first).
2. For a given user:
   a. Get SVD recommendations (collaborative score).
   b. Merge with content-based similarity relative to user's most-played track.
   c. Compute weighted hybrid score.
   d. Return top-N ranked results.
"""

import os
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from models.content_based         import ContentBasedRecommender
from models.collaborative_filtering import SVDCollaborativeFilter

DATA_DIR = os.path.join(BASE_DIR, "data")


# ──────────────────────────────────────────────────────────────────────────────
class HybridRecommender:
    """
    Weighted hybrid of SVD collaborative filtering + content-based similarity.

    Parameters
    ----------
    cf_weight  : float (0-1) – weight given to collaborative filtering score.
                               (1 - cf_weight) goes to content similarity.
    """

    def __init__(self, cf_weight: float = 0.6):
        self.cf_weight  = cf_weight
        self.cb_weight  = 1.0 - cf_weight
        self.svd_model  = None
        self.cb_model   = None
        self.songs_df   = None
        self.history_df = None

    # ── load ──────────────────────────────────────────────────────────────────
    def load_models(self) -> "HybridRecommender":
        """Load pre-trained SVD and content-based models from disk."""
        print("Loading content-based model …")
        self.cb_model = ContentBasedRecommender.load()

        print("Loading SVD collaborative filter …")
        self.svd_model = SVDCollaborativeFilter.load()

        self.songs_df   = pd.read_csv(os.path.join(DATA_DIR, "songs_clean.csv"))
        self.history_df = pd.read_csv(os.path.join(DATA_DIR, "history_clean.csv"))
        return self

    # ── helpers ───────────────────────────────────────────────────────────────
    def _get_user_seed_track(self, user_id: str) -> str | None:
        """Return the user's most-played track (seed for content-based component)."""
        user_hist = self.history_df[self.history_df["user_id"] == user_id]
        if user_hist.empty:
            return None
        return user_hist.sort_values("play_count", ascending=False).iloc[0]["track_id"]

    @staticmethod
    def _minmax_norm(series: pd.Series) -> pd.Series:
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series(np.ones(len(series)), index=series.index)
        return (series - mn) / (mx - mn)

    # ── recommend ─────────────────────────────────────────────────────────────
    def recommend(self, user_id: str, top_n: int = 10,
                  exclude_seen: bool = True) -> pd.DataFrame:
        """
        Generate top-N hybrid recommendations for *user_id*.

        Parameters
        ----------
        exclude_seen : bool – if False, include items the user already interacted
                              with. Set to False during hold-out evaluation so
                              the held-out test tracks can appear in results.

        Returns
        -------
        pd.DataFrame with columns:
            track_id, track_name, artist, genre, release_year, popularity,
            cf_score, cb_score, hybrid_score
        """
        if self.svd_model is None:
            raise RuntimeError("Call load_models() before recommend().")

        # ── Step 1: Collaborative filtering candidates ──────────────────────
        try:
            cf_recs = self.svd_model.recommend(user_id, top_n=top_n * 3,
                                               exclude_seen=exclude_seen)
        except ValueError:
            # New user — fall back to popular tracks
            return self._cold_start(top_n)

        # ── Step 2: Content-based scores via seed track ────────────────────
        seed_track = self._get_user_seed_track(user_id)
        cb_scores  = pd.DataFrame(columns=["track_id", "cb_raw"])

        if seed_track and seed_track in self.cb_model.track_ids:
            try:
                cb_recs = self.cb_model.recommend(seed_track, top_n=top_n * 5)
                cb_scores = cb_recs[["track_id", "similarity_score"]].rename(
                    columns={"similarity_score": "cb_raw"}
                )
            except ValueError:
                pass

        # ── Step 3: Merge & normalise ───────────────────────────────────────
        merged = cf_recs.merge(cb_scores, on="track_id", how="left")
        merged["cb_raw"] = merged["cb_raw"].fillna(merged["cb_raw"].mean()
                                                    if not merged["cb_raw"].isna().all()
                                                    else 0.0)

        merged["cf_norm"] = self._minmax_norm(merged["cf_score"])
        merged["cb_norm"] = self._minmax_norm(merged["cb_raw"])

        # ── Step 4: Weighted hybrid score ──────────────────────────────────
        merged["hybrid_score"] = (
            self.cf_weight  * merged["cf_norm"] +
            self.cb_weight  * merged["cb_norm"]
        ).round(4)

        # ── Step 5: Attach metadata & trim ─────────────────────────────────
        result = merged.merge(
            self.songs_df[["track_id", "track_name", "artist", "genre",
                           "release_year", "popularity"]],
            on="track_id", how="left"
        )
        result = result.sort_values("hybrid_score", ascending=False).head(top_n)
        result = result[[
            "track_id", "track_name", "artist", "genre",
            "release_year", "popularity",
            "cf_norm", "cb_norm", "hybrid_score"
        ]].rename(columns={"cf_norm": "cf_score", "cb_norm": "cb_score"})

        return result.reset_index(drop=True)

    # ── cold start ────────────────────────────────────────────────────────────
    def _cold_start(self, top_n: int) -> pd.DataFrame:
        """Fallback for unknown users: return most popular tracks."""
        popular = (
            self.songs_df
            .sort_values("popularity", ascending=False)
            .head(top_n)[["track_id", "track_name", "artist", "genre",
                          "release_year", "popularity"]]
        )
        popular["cf_score"]     = 0.0
        popular["cb_score"]     = 0.0
        popular["hybrid_score"] = (popular["popularity"] / 100).round(4)
        return popular.reset_index(drop=True)

    # ── trending ──────────────────────────────────────────────────────────────
    def trending(self, top_n: int = 10) -> pd.DataFrame:
        """Return globally trending tracks weighted by play_count + popularity."""
        play_counts = (
            self.history_df.groupby("track_id")["play_count"]
            .sum()
            .reset_index()
            .rename(columns={"play_count": "total_plays"})
        )
        result = play_counts.merge(
            self.songs_df[["track_id", "track_name", "artist", "genre",
                           "release_year", "popularity"]],
            on="track_id", how="left"
        )
        result["trend_score"] = (
            0.7 * self._minmax_norm(result["total_plays"]) +
            0.3 * self._minmax_norm(result["popularity"])
        ).round(4)
        return (
            result.sort_values("trend_score", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    h = HybridRecommender(cf_weight=0.6)
    h.load_models()

    sample_user = h.svd_model.user_ids[0]
    print(f"\nHybrid recommendations for {sample_user}:")
    print(h.recommend(sample_user, top_n=5).to_string(index=False))

    print("\nTrending tracks:")
    print(h.trending(top_n=5).to_string(index=False))
