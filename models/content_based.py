"""
models/content_based.py
------------------------
Content-Based Filtering using cosine similarity on normalised audio features.

Usage
-----
    from models.content_based import ContentBasedRecommender
    cbr = ContentBasedRecommender()
    cbr.fit()                              # loads pre-processed data
    recs = cbr.recommend(track_id, top_n=10)
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models", "saved")
os.makedirs(MODELS_DIR, exist_ok=True)

AUDIO_FEATURES = [
    "tempo", "energy", "danceability", "loudness",
    "valence", "acousticness", "instrumentalness",
    "speechiness", "liveness",
]


class ContentBasedRecommender:
    """
    Recommends songs whose audio features are most similar to a given track.

    Attributes
    ----------
    songs_df   : pd.DataFrame  – full song catalogue (with metadata)
    feature_df : pd.DataFrame  – normalised audio features indexed by track_id
    sim_matrix : np.ndarray    – N × N cosine-similarity matrix
    track_ids  : list          – ordered list of track IDs (index into sim_matrix)
    """

    def __init__(self):
        self.songs_df   = None
        self.feature_df = None
        self.sim_matrix = None
        self.track_ids  = []

    # ──────────────────────────────────────────────────────────────────────────
    def fit(self) -> "ContentBasedRecommender":
        """Load data, compute cosine-similarity matrix, and persist it."""
        self._load_data()
        print("Computing cosine similarity matrix …", end=" ", flush=True)
        feat_matrix     = self.feature_df.values          # shape (N, F)
        self.sim_matrix = cosine_similarity(feat_matrix)  # (N, N)
        print("done.")
        self._save()
        return self

    def _load_data(self):
        songs_path = os.path.join(DATA_DIR, "songs_clean.csv")
        feat_path  = os.path.join(DATA_DIR, "audio_features.csv")
        if not os.path.exists(songs_path) or not os.path.exists(feat_path):
            raise FileNotFoundError(
                "Preprocessed data not found. Run preprocessing/clean_data.py first."
            )
        self.songs_df   = pd.read_csv(songs_path)
        self.feature_df = pd.read_csv(feat_path, index_col="track_id")
        self.track_ids  = list(self.feature_df.index)

    # ──────────────────────────────────────────────────────────────────────────
    def recommend(self, track_id: str, top_n: int = 10,
                  filter_genre: bool = False) -> pd.DataFrame:
        """
        Return the top-N most similar songs to *track_id*.

        Parameters
        ----------
        track_id     : str  – source track to find neighbours for
        top_n        : int  – how many results to return
        filter_genre : bool – if True, restrict results to the same genre

        Returns
        -------
        pd.DataFrame with columns: track_id, track_name, artist, genre,
                                   similarity_score
        """
        if track_id not in self.track_ids:
            raise ValueError(f"track_id '{track_id}' not found in the catalogue.")

        idx      = self.track_ids.index(track_id)
        scores   = self.sim_matrix[idx]                # shape (N,)
        sim_ser  = pd.Series(scores, index=self.track_ids).drop(track_id)

        # Optional same-genre filter
        if filter_genre:
            genre   = self.songs_df.loc[
                self.songs_df["track_id"] == track_id, "genre"
            ].iloc[0]
            same_genre_ids = self.songs_df.loc[
                self.songs_df["genre"] == genre, "track_id"
            ].tolist()
            sim_ser = sim_ser[sim_ser.index.isin(same_genre_ids)]

        top_ids   = sim_ser.nlargest(top_n).reset_index()
        top_ids.columns = ["track_id", "similarity_score"]

        result = top_ids.merge(
            self.songs_df[["track_id", "track_name", "artist", "genre",
                           "release_year", "popularity"]],
            on="track_id", how="left"
        )
        result["similarity_score"] = result["similarity_score"].round(4)
        return result.reset_index(drop=True)

    # ──────────────────────────────────────────────────────────────────────────
    def get_audio_features(self, track_id: str) -> dict:
        """Return the (normalised) audio feature vector for a single track."""
        if track_id not in self.track_ids:
            return {}
        return self.feature_df.loc[track_id].to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    def _save(self):
        path = os.path.join(MODELS_DIR, "content_based.pkl")
        with open(path, "wb") as f:
            pickle.dump({
                "sim_matrix" : self.sim_matrix,
                "track_ids"  : self.track_ids,
            }, f)
        print(f"  Model saved → {path}")

    @classmethod
    def load(cls) -> "ContentBasedRecommender":
        """Load a previously fitted model from disk."""
        path = os.path.join(MODELS_DIR, "content_based.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError("No saved content-based model. Run fit() first.")
        obj = cls()
        obj._load_data()
        with open(path, "rb") as f:
            data            = pickle.load(f)
        obj.sim_matrix  = data["sim_matrix"]
        obj.track_ids   = data["track_ids"]
        return obj


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cbr = ContentBasedRecommender()
    cbr.fit()
    sample_track = cbr.track_ids[0]
    print(f"\nContent-based recs for: {sample_track}")
    print(cbr.recommend(sample_track, top_n=5).to_string(index=False))
