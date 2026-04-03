"""
api/routes.py
--------------
Flask Blueprint defining all REST API endpoints.

Endpoints
---------
  GET /api/recommend/user/<user_id>        – hybrid personalised recommendations
  GET /api/recommend/song/<track_id>       – content-based similar songs
  GET /api/trending                        – globally trending tracks
  GET /api/users                           – list all user IDs
  GET /api/songs                           – list all songs (paginated)
  GET /api/songs/<track_id>                – single song detail + audio features
  GET /api/evaluate                        – Precision@K, Recall@K, NDCG@K
  GET /api/health                          – health check
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request, current_app

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ── Helper: safe JSON serialisation (converts numpy types) ────────────────────
def to_json_safe(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    return obj


def df_to_records(df: pd.DataFrame) -> list:
    """Convert DataFrame to list of JSON-safe dicts."""
    records = df.to_dict(orient="records")
    return [
        {k: (int(v) if isinstance(v, np.integer) else
             float(v) if isinstance(v, (np.floating, float)) and not np.isnan(v) else
             None if isinstance(v, float) and np.isnan(v) else v)
         for k, v in row.items()}
        for row in records
    ]


# ── Accessor: pull hybrid recommender from app context ───────────────────────
def get_engine():
    return current_app.config["ENGINE"]


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Spotify Recommender API is running"})


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/recommend/user/<user_id>")
def recommend_user(user_id: str):
    """
    GET /api/recommend/user/<user_id>
    Returns top-N personalised (hybrid) recommendations for the user.

    Query params:
      top_n      (int, default=10)
      cf_weight  (float, 0-1, default=0.6)
    """
    top_n     = int(request.args.get("top_n", 10))
    cf_weight = float(request.args.get("cf_weight", 0.6))
    top_n     = max(1, min(top_n, 50))
    cf_weight = max(0.0, min(cf_weight, 1.0))

    engine = get_engine()
    engine.cf_weight = cf_weight
    engine.cb_weight = 1.0 - cf_weight

    try:
        recs = engine.recommend(user_id, top_n=top_n)
        return jsonify({
            "user_id"      : user_id,
            "top_n"        : top_n,
            "cf_weight"    : cf_weight,
            "recommendations": df_to_records(recs),
            "count"        : len(recs),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 404


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/recommend/song/<track_id>")
def recommend_song(track_id: str):
    """
    GET /api/recommend/song/<track_id>
    Returns content-based similar songs.

    Query params:
      top_n        (int, default=10)
      filter_genre (bool, default=false)
    """
    top_n        = int(request.args.get("top_n", 10))
    filter_genre = request.args.get("filter_genre", "false").lower() == "true"
    top_n        = max(1, min(top_n, 50))

    engine = get_engine()
    try:
        recs = engine.cb_model.recommend(track_id, top_n=top_n,
                                          filter_genre=filter_genre)
        return jsonify({
            "seed_track_id"  : track_id,
            "filter_genre"   : filter_genre,
            "similar_songs"  : df_to_records(recs),
            "count"          : len(recs),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 404


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/trending")
def trending():
    """
    GET /api/trending
    Returns globally trending tracks.

    Query params:
      top_n (int, default=10)
    """
    top_n = int(request.args.get("top_n", 10))
    top_n = max(1, min(top_n, 50))

    engine = get_engine()
    tracks = engine.trending(top_n=top_n)
    return jsonify({
        "trending_tracks": df_to_records(tracks),
        "count"          : len(tracks),
    })


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/users")
def list_users():
    """GET /api/users – return all user IDs."""
    engine  = get_engine()
    user_ids = engine.svd_model.user_ids
    return jsonify({"users": user_ids, "count": len(user_ids)})


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/songs")
def list_songs():
    """
    GET /api/songs
    Returns paginated song list.

    Query params:
      page     (int, default=1)
      per_page (int, default=20, max=100)
      genre    (str, optional filter)
    """
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 100)
    genre    = request.args.get("genre", "").strip().lower()

    engine   = get_engine()
    songs_df = engine.songs_df.copy()

    if genre:
        songs_df = songs_df[songs_df["genre"].str.lower() == genre]

    total   = len(songs_df)
    start   = (page - 1) * per_page
    end     = start + per_page
    page_df = songs_df.iloc[start:end]

    return jsonify({
        "page"      : page,
        "per_page"  : per_page,
        "total"     : total,
        "songs"     : df_to_records(page_df[["track_id", "track_name", "artist",
                                             "genre", "release_year", "popularity"]]),
    })


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/songs/<track_id>")
def song_detail(track_id: str):
    """GET /api/songs/<track_id> – full song detail including audio features."""
    engine   = get_engine()
    songs_df = engine.songs_df
    row      = songs_df[songs_df["track_id"] == track_id]

    if row.empty:
        return jsonify({"error": f"track_id '{track_id}' not found"}), 404

    data = df_to_records(row)[0]

    # Attach audio features from CB model
    af = engine.cb_model.get_audio_features(track_id)
    data["audio_features"] = {k: round(float(v), 4) for k, v in af.items()}

    return jsonify(data)


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/evaluate")
def evaluate():
    """
    GET /api/evaluate
    Returns Precision@K, Recall@K, NDCG@K for the hybrid model
    on a random sample of users.

    Query params:
      k              (int, default=10)
      sample_users   (int, default=50)
    """
    k            = int(request.args.get("k", 10))
    sample_users = int(request.args.get("sample_users", 50))

    from recommender.evaluate import evaluate_model
    engine     = get_engine()
    history_df = engine.history_df

    # Use a random sample of users for speed
    user_sample = history_df["user_id"].drop_duplicates().sample(
        min(sample_users, history_df["user_id"].nunique()), random_state=42
    )
    hist_sample = history_df[history_df["user_id"].isin(user_sample)]

    metrics = evaluate_model(engine, hist_sample, k=k)
    return jsonify(metrics)


# ──────────────────────────────────────────────────────────────────────────────
@api_bp.route("/genres")
def list_genres():
    """GET /api/genres – return distinct genres in the catalogue."""
    engine = get_engine()
    genres = sorted(engine.songs_df["genre"].dropna().unique().tolist())
    return jsonify({"genres": genres})
