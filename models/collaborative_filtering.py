"""
models/collaborative_filtering.py
-----------------------------------
Collaborative Filtering using matrix factorisation (SVD) and k-NN.

Because scikit-surprise often fails to build on Windows without a C compiler,
we implement SVD via numpy (Truncated SVD / NMF) and cosine k-NN on the
user-item matrix — giving equivalent recommendations without Cython.

Classes
-------
  SVDCollaborativeFilter     – latent-factor model (numpy TruncatedSVD)
  KNNCollaborativeFilter     – item-based k-NN cosine similarity
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import mean_squared_error

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models", "saved")
os.makedirs(MODELS_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
class SVDCollaborativeFilter:
    """
    Truncated-SVD (matrix factorisation) collaborative filter.

    Fills NaN ratings with zeros before decomposition (implicit feedback style).
    Scores for a user are the dot product of that user's latent vector
    and all item latent vectors.
    """

    def __init__(self, n_components: int = 50, random_state: int = 42):
        self.n_components = n_components
        self.random_state = random_state
        self.svd          = None
        self.ui_matrix    = None   # filled (no NaN)
        self.user_ids     = []
        self.track_ids    = []
        self.user_factors = None   # (n_users, n_components)
        self.item_factors = None   # (n_items, n_components)

    # ── fit ──────────────────────────────────────────────────────────────────
    def fit(self, ui_matrix: pd.DataFrame) -> "SVDCollaborativeFilter":
        """
        Parameters
        ----------
        ui_matrix : pd.DataFrame – shape (n_users, n_tracks), values = rating or NaN
        """
        self.user_ids  = list(ui_matrix.index)
        self.track_ids = list(ui_matrix.columns)

        filled = ui_matrix.fillna(0).values        # (n_users, n_items)
        self.ui_matrix = filled

        n_comp = min(self.n_components, min(filled.shape) - 1)
        self.svd = TruncatedSVD(n_components=n_comp,
                                random_state=self.random_state)
        # U Σ  →  user_factors  (n_users, n_comp)
        self.user_factors = self.svd.fit_transform(filled)
        # V^T  →  item_factors  (n_comp, n_items)  ⇒ transpose → (n_items, n_comp)
        self.item_factors = self.svd.components_.T

        print(f"  SVD fitted: {n_comp} components. "
              f"Explained variance: {self.svd.explained_variance_ratio_.sum():.2%}")
        return self

    # ── predict ───────────────────────────────────────────────────────────────
    def predict(self, user_id: str, track_id: str) -> float:
        """Predict the rating a user would give a specific track."""
        if user_id not in self.user_ids or track_id not in self.track_ids:
            return 0.0
        u_idx = self.user_ids.index(user_id)
        i_idx = self.track_ids.index(track_id)
        return float(np.dot(self.user_factors[u_idx], self.item_factors[i_idx]))

    # ── recommend ─────────────────────────────────────────────────────────────
    def recommend(self, user_id: str, top_n: int = 10,
                  exclude_seen: bool = True) -> pd.DataFrame:
        """
        Return top-N track recommendations for *user_id*.

        Parameters
        ----------
        user_id      : str  – target user
        top_n        : int  – number of recommendations
        exclude_seen : bool – exclude tracks the user already listened to
        """
        if user_id not in self.user_ids:
            raise ValueError(f"user_id '{user_id}' not found in training data.")

        u_idx  = self.user_ids.index(user_id)
        scores = self.user_factors[u_idx] @ self.item_factors.T  # (n_items,)
        scores_ser = pd.Series(scores, index=self.track_ids)

        if exclude_seen:
            seen_mask = self.ui_matrix[u_idx] > 0
            seen_ids  = [t for t, m in zip(self.track_ids, seen_mask) if m]
            scores_ser = scores_ser.drop(seen_ids, errors="ignore")

        top = scores_ser.nlargest(top_n).reset_index()
        top.columns = ["track_id", "cf_score"]
        top["cf_score"] = top["cf_score"].round(4)
        return top

    # ── evaluation ────────────────────────────────────────────────────────────
    def rmse(self, history_df: pd.DataFrame) -> float:
        """Compute RMSE on the observed (user, track, rating) triplets."""
        preds, actuals = [], []
        for _, row in history_df.iterrows():
            p = self.predict(row["user_id"], row["track_id"])
            preds.append(p)
            actuals.append(row["rating"])
        return float(np.sqrt(mean_squared_error(actuals, preds)))

    # ── persistence ───────────────────────────────────────────────────────────
    def save(self):
        path = os.path.join(MODELS_DIR, "svd_cf.pkl")
        with open(path, "wb") as f:
            pickle.dump(self.__dict__, f)
        print(f"  SVD model saved → {path}")

    @classmethod
    def load(cls) -> "SVDCollaborativeFilter":
        path = os.path.join(MODELS_DIR, "svd_cf.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError("No saved SVD model. Run fit() first.")
        obj = cls()
        with open(path, "rb") as f:
            obj.__dict__.update(pickle.load(f))
        return obj


# ──────────────────────────────────────────────────────────────────────────────
class KNNCollaborativeFilter:
    """
    Item-based collaborative filter using cosine similarity on the user-item matrix.

    For a given user, score unheard items by the weighted similarity of
    heard items (weighted by the user's rating of those items).
    """

    def __init__(self, k: int = 20):
        self.k          = k
        self.ui_matrix  = None   # filled
        self.item_sim   = None   # (n_items, n_items) cosine similarity
        self.user_ids   = []
        self.track_ids  = []

    # ── fit ──────────────────────────────────────────────────────────────────
    def fit(self, ui_matrix: pd.DataFrame) -> "KNNCollaborativeFilter":
        self.user_ids  = list(ui_matrix.index)
        self.track_ids = list(ui_matrix.columns)

        filled = ui_matrix.fillna(0).values          # (n_users, n_items)
        self.ui_matrix = filled

        # Item similarities: transpose so items are rows
        print("  Computing item-item cosine similarity …", end=" ", flush=True)
        self.item_sim = cosine_similarity(filled.T)  # (n_items, n_items)
        print("done.")
        return self

    # ── recommend ─────────────────────────────────────────────────────────────
    def recommend(self, user_id: str, top_n: int = 10,
                  exclude_seen: bool = True) -> pd.DataFrame:
        if user_id not in self.user_ids:
            raise ValueError(f"user_id '{user_id}' not found.")

        u_idx      = self.user_ids.index(user_id)
        user_row   = self.ui_matrix[u_idx]           # (n_items,)
        rated_mask = user_row > 0

        # For each unseen item, score = Σ sim(item_i, rated_j) × rating_j
        scores = np.zeros(len(self.track_ids))
        for j, is_rated in enumerate(rated_mask):
            if is_rated:
                scores += self.item_sim[:, j] * user_row[j]

        scores_ser = pd.Series(scores, index=self.track_ids)

        if exclude_seen:
            seen_ids = [t for t, m in zip(self.track_ids, rated_mask) if m]
            scores_ser = scores_ser.drop(seen_ids, errors="ignore")

        top = scores_ser.nlargest(top_n).reset_index()
        top.columns = ["track_id", "knn_score"]
        top["knn_score"] = top["knn_score"].round(4)
        return top

    # ── persistence ───────────────────────────────────────────────────────────
    def save(self):
        path = os.path.join(MODELS_DIR, "knn_cf.pkl")
        with open(path, "wb") as f:
            pickle.dump(self.__dict__, f)
        print(f"  KNN model saved → {path}")

    @classmethod
    def load(cls) -> "KNNCollaborativeFilter":
        path = os.path.join(MODELS_DIR, "knn_cf.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError("No saved KNN model. Run fit() first.")
        obj = cls()
        with open(path, "rb") as f:
            obj.__dict__.update(pickle.load(f))
        return obj


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ui_path = os.path.join(DATA_DIR, "user_item_matrix.csv")
    ui_df   = pd.read_csv(ui_path, index_col="user_id")

    # SVD
    svd = SVDCollaborativeFilter(n_components=30)
    svd.fit(ui_df)
    sample_user = svd.user_ids[0]
    print(f"\nSVD recommendations for {sample_user}:")
    print(svd.recommend(sample_user, top_n=5))

    # KNN
    knn = KNNCollaborativeFilter(k=15)
    knn.fit(ui_df)
    print(f"\nKNN recommendations for {sample_user}:")
    print(knn.recommend(sample_user, top_n=5))

    svd.save()
    knn.save()
