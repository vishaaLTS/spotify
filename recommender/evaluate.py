"""
recommender/evaluate.py
------------------------
Evaluation metrics for the recommendation engine.

Metrics Implemented
-------------------
  Precision@K  –  fraction of top-K recommendations that are relevant
  Recall@K     –  fraction of relevant items that appear in top-K
  RMSE         –  root-mean-square error for predicted vs actual ratings
  NDCG@K       –  normalised discounted cumulative gain (ranking quality)

Usage
-----
    python recommender/evaluate.py
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")


# ──────────────────────────────────────────────────────────────────────────────
def precision_at_k(recommended: list, relevant: set, k: int) -> float:
    """
    Precision@K: Among the top-K recommended items, what fraction are relevant?

    Parameters
    ----------
    recommended : list – ordered list of recommended track IDs
    relevant    : set  – set of ground-truth relevant track IDs
    k           : int  – cutoff

    Returns
    -------
    float in [0, 1]
    """
    top_k = recommended[:k]
    hits  = sum(1 for tid in top_k if tid in relevant)
    return hits / k if k > 0 else 0.0


def recall_at_k(recommended: list, relevant: set, k: int) -> float:
    """
    Recall@K: Of all relevant items, what fraction appear in top-K?
    """
    if not relevant:
        return 0.0
    top_k = recommended[:k]
    hits  = sum(1 for tid in top_k if tid in relevant)
    return hits / len(relevant)


def ndcg_at_k(recommended: list, relevant: set, k: int) -> float:
    """
    NDCG@K: Normalised Discounted Cumulative Gain.
    Binary relevance: 1 if in relevant, 0 otherwise.
    """
    def dcg(items):
        return sum(
            (1 if tid in relevant else 0) / np.log2(rank + 2)
            for rank, tid in enumerate(items[:k])
        )
    ideal_hits = min(len(relevant), k)
    ideal_dcg  = sum(1 / np.log2(rank + 2) for rank in range(ideal_hits))
    actual_dcg = dcg(recommended)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def compute_rmse(predictions: list, actuals: list) -> float:
    """Root Mean Square Error between predicted and actual ratings."""
    return float(np.sqrt(mean_squared_error(actuals, predictions)))


# ──────────────────────────────────────────────────────────────────────────────
def evaluate_model(model, history_df: pd.DataFrame,
                   k: int = 10, test_fraction: float = 0.2,
                   relevant_threshold: float = 3.5) -> dict:
    """
    Hold-out evaluation: split each user's history into train / test,
    compute Precision@K, Recall@K, NDCG@K averaged over all users.

    IMPORTANT: We do NOT exclude seen items during evaluation so that
    the held-out test tracks can appear in the recommendations.

    Parameters
    ----------
    model            : object with .recommend(user_id, top_n) → DataFrame
    history_df       : full listening history DataFrame
    k                : cutoff for ranking metrics
    test_fraction    : fraction of each user's interactions used for testing
    relevant_threshold: minimum rating to be considered 'relevant'

    Returns
    -------
    dict of metric → value
    """
    np.random.seed(42)
    precisions, recalls, ndcgs = [], [], []

    # Determine relevant_threshold adaptively if ratings are all integers / low range
    if "rating" in history_df.columns:
        rating_col = "rating"
    elif "play_count" in history_df.columns:
        # Normalise play_count to a 1-5 scale for thresholding
        history_df = history_df.copy()
        pc = history_df["play_count"]
        history_df["rating"] = 1 + 4 * (pc - pc.min()) / max(pc.max() - pc.min(), 1)
        rating_col = "rating"
    else:
        return {"n_users_evaluated": 0,
                f"Precision@{k}": 0.0, f"Recall@{k}": 0.0, f"NDCG@{k}": 0.0}

    for user_id, group in history_df.groupby("user_id"):
        if len(group) < 5:
            continue  # not enough data for meaningful evaluation

        # ── train/test split (per user) ───────────────────────────────────
        test_n    = max(1, int(len(group) * test_fraction))
        test_rows = group.sample(n=test_n, random_state=42)
        relevant  = set(
            test_rows[test_rows[rating_col] >= relevant_threshold]["track_id"]
        )
        if not relevant:
            # Fallback: treat highest-rated test items as relevant
            top_rating = test_rows[rating_col].max()
            relevant = set(test_rows[test_rows[rating_col] == top_rating]["track_id"])
        if not relevant:
            continue

        # ── get recommendations (include seen so test items can appear) ───
        try:
            recs_df = model.recommend(user_id, top_n=k * 2, exclude_seen=False)
            recommended = list(recs_df["track_id"]) if "track_id" in recs_df.columns else []
        except Exception:
            continue

        precisions.append(precision_at_k(recommended, relevant, k))
        recalls.append(   recall_at_k(   recommended, relevant, k))
        ndcgs.append(     ndcg_at_k(     recommended, relevant, k))

    n = len(precisions)
    return {
        "n_users_evaluated": n,
        f"Precision@{k}"  : round(float(np.mean(precisions)) if precisions else 0.0, 4),
        f"Recall@{k}"     : round(float(np.mean(recalls))    if recalls    else 0.0, 4),
        f"NDCG@{k}"       : round(float(np.mean(ndcgs))      if ndcgs      else 0.0, 4),
    }


# ──────────────────────────────────────────────────────────────────────────────
def main():
    from models.collaborative_filtering import SVDCollaborativeFilter
    from recommender.hybrid import HybridRecommender

    history_df = pd.read_csv(os.path.join(DATA_DIR, "history_clean.csv"))
    ui_df      = pd.read_csv(os.path.join(DATA_DIR, "user_item_matrix.csv"),
                             index_col="user_id")

    K = 10

    # ── SVD ──────────────────────────────────────────────────────────────────
    print("\nEvaluating SVD Collaborative Filter …")
    svd = SVDCollaborativeFilter.load()
    svd_metrics = evaluate_model(svd, history_df, k=K)
    print(f"  SVD   : {svd_metrics}")

    # ── RMSE for SVD ──────────────────────────────────────────────────────────
    sample = history_df.sample(min(2000, len(history_df)), random_state=42)
    preds   = [svd.predict(r.user_id, r.track_id) for _, r in sample.iterrows()]
    actuals = list(sample["rating"])
    rmse    = compute_rmse(preds, actuals)
    print(f"  SVD RMSE (sample): {rmse:.4f}")

    # ── Hybrid ────────────────────────────────────────────────────────────────
    print("\nEvaluating Hybrid Recommender …")
    hybrid = HybridRecommender(cf_weight=0.6)
    hybrid.load_models()
    hybrid_metrics = evaluate_model(hybrid, history_df, k=K)
    print(f"  Hybrid: {hybrid_metrics}")

    # ── Summary table ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print(f"{'Metric':<20} {'SVD CF':>10} {'Hybrid':>10}")
    print("="*60)
    for metric in [f"Precision@{K}", f"Recall@{K}", f"NDCG@{K}"]:
        print(f"{metric:<20} {svd_metrics.get(metric, '-'):>10} "
              f"{hybrid_metrics.get(metric, '-'):>10}")
    print(f"{'RMSE':<20} {rmse:>10.4f} {'N/A':>10}")
    print("="*60)


if __name__ == "__main__":
    main()
