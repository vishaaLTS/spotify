"""
train_all.py
-------------
Master training script that runs the full ML pipeline end-to-end:

  1. Generate dataset (if not present)
  2. Preprocess and clean data
  3. Train Content-Based model
  4. Train SVD Collaborative Filter
  5. Train KNN Collaborative Filter
  6. Save all models to models/saved/

Run this once before starting the Flask API:
    python train_all.py
"""

import os
import sys
import time
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
sys.path.insert(0, BASE_DIR)


def banner(title: str):
    print("\n" + "═" * 60)
    print(f"  {title}")
    print("═" * 60)


# ── Step 1: Generate dataset ──────────────────────────────────────────────────
banner("STEP 1 — Generate Dataset")
songs_path   = os.path.join(DATA_DIR, "songs.csv")
history_path = os.path.join(DATA_DIR, "listening_history.csv")

if os.path.exists(songs_path) and os.path.exists(history_path):
    print("  Dataset already exists — skipping generation.")
else:
    t0 = time.time()
    from data.generate_dataset import generate_songs, generate_users, generate_listening_history
    songs_df   = generate_songs()
    users_df   = generate_users()
    history_df = generate_listening_history(songs_df, users_df)
    songs_df.to_csv(songs_path, index=False)
    users_df.to_csv(os.path.join(DATA_DIR, "users.csv"), index=False)
    history_df.to_csv(history_path, index=False)
    print(f"  Dataset generated in {time.time()-t0:.1f}s")


# ── Step 2: Preprocess ────────────────────────────────────────────────────────
banner("STEP 2 — Preprocess & Clean")
t0 = time.time()
from preprocessing.clean_data import run_preprocessing
songs_clean, history_clean, ui_matrix, audio_feat = run_preprocessing()
print(f"  Preprocessing done in {time.time()-t0:.1f}s")


# ── Step 3: Content-Based Model ───────────────────────────────────────────────
banner("STEP 3 — Content-Based Filtering (Cosine Similarity)")
t0 = time.time()
from models.content_based import ContentBasedRecommender
cbr = ContentBasedRecommender()
cbr.fit()
print(f"  Content-based model trained in {time.time()-t0:.1f}s")

# Smoke test
sample_track = cbr.track_ids[0]
recs = cbr.recommend(sample_track, top_n=3)
print(f"  Sample recs for {sample_track}:")
print(recs[["track_id", "track_name", "similarity_score"]].to_string(index=False))


# ── Step 4: SVD Collaborative Filter ─────────────────────────────────────────
banner("STEP 4 — SVD Collaborative Filtering")
t0 = time.time()
from models.collaborative_filtering import SVDCollaborativeFilter
svd = SVDCollaborativeFilter(n_components=50)
svd.fit(ui_matrix)
svd.save()
print(f"  SVD model trained in {time.time()-t0:.1f}s")

sample_user = svd.user_ids[0]
recs = svd.recommend(sample_user, top_n=3)
print(f"  Sample recs for {sample_user}:")
print(recs.to_string(index=False))


# ── Step 5: KNN Collaborative Filter ─────────────────────────────────────────
banner("STEP 5 — KNN (Item-Based) Collaborative Filtering")
t0 = time.time()
from models.collaborative_filtering import KNNCollaborativeFilter
knn = KNNCollaborativeFilter(k=20)
knn.fit(ui_matrix)
knn.save()
print(f"  KNN model trained in {time.time()-t0:.1f}s")

recs = knn.recommend(sample_user, top_n=3)
print(f"  Sample KNN recs for {sample_user}:")
print(recs.to_string(index=False))


# ── Step 6: RMSE evaluation (quick) ──────────────────────────────────────────
banner("STEP 6 — Quick RMSE Evaluation")
sample = history_clean.sample(min(2000, len(history_clean)), random_state=42)
preds   = [svd.predict(r.user_id, r.track_id) for _, r in sample.iterrows()]
actuals = list(sample["rating"])
import numpy as np
from sklearn.metrics import mean_squared_error
rmse = float(np.sqrt(mean_squared_error(actuals, preds)))
print(f"  SVD RMSE on {len(sample)} samples: {rmse:.4f}")


# ── Done ──────────────────────────────────────────────────────────────────────
banner("ALL TRAINING COMPLETE")
print("  You can now run the API:")
print("    python app.py")
print()
