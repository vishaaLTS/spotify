# 🎵 Spotify Music Personalization Recommendation Engine

A complete, end-to-end **AI-powered music recommendation system** built with Python,
Flask, and modern ML techniques. The engine combines **collaborative filtering**
(SVD matrix factorisation + k-NN) with **content-based audio-feature similarity**
into a **weighted hybrid model** served through a beautiful dark-themed web interface.

---

## 📸 Screenshots

| Dashboard | Personalised Recommendations |
|-----------|-------------------------------|
| Stats, trending tracks, genre doughnut chart | User-specific hybrid recs with score bars |

| Similar Songs | Trending Tracks |
|---------------|-----------------|
| Cosine-similarity ranked list | Global popularity-weighted grid |

---

## 🏗️ Project Structure

```
spotify-recommendation-engine/
│
├── data/
│   ├── generate_dataset.py      # Synthetic Spotify dataset generator
│   ├── songs.csv                # 1 000 songs with audio features
│   ├── users.csv                # 200 simulated users
│   ├── listening_history.csv    # 8 000 user–song interactions
│   ├── songs_clean.csv          # Cleaned song catalogue
│   ├── history_clean.csv        # Cleaned interaction log
│   ├── user_item_matrix.csv     # User × Track rating pivot
│   ├── audio_features.csv       # Normalised audio-feature vectors
│   └── spotify.db               # SQLite database
│
├── preprocessing/
│   └── clean_data.py            # Cleaning, normalisation, matrix builder
│
├── models/
│   ├── content_based.py         # Cosine-similarity content-based model
│   ├── collaborative_filtering.py  # SVD + KNN collaborative filter
│   ├── database.py              # SQLite ORM layer
│   └── saved/                   # Persisted model files (.pkl)
│
├── recommender/
│   ├── hybrid.py                # Weighted hybrid recommender + trending
│   └── evaluate.py              # Precision@K, Recall@K, NDCG@K, RMSE
│
├── api/
│   ├── __init__.py
│   └── routes.py                # Flask Blueprint REST API
│
├── notebooks/
│   ├── visualizations.py        # 7 analysis plots (Matplotlib/Seaborn)
│   └── plots/                   # Generated PNG plots
│
├── static/
│   ├── css/style.css            # Dark glassmorphism UI
│   └── js/app.js                # Frontend logic + Chart.js
│
├── templates/
│   └── index.html               # Single-page application
│
├── app.py                       # Flask application entry point
├── train_all.py                 # Full pipeline runner
├── requirements.txt
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Data | Pandas, NumPy |
| ML | Scikit-learn (TruncatedSVD, cosine similarity, MinMaxScaler) |
| Backend | Flask 3, Flask-CORS |
| Database | SQLite (via Python `sqlite3`) |
| Visualisation | Matplotlib, Seaborn, Chart.js |
| Frontend | Vanilla HTML/CSS/JS, dark glassmorphism design |

---

## 🚀 Quick Start

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### 2 — Train the models (one-time setup)

This single command runs the entire pipeline:

```bash
python train_all.py
```

It will:
1. Generate 1 000 synthetic songs, 200 users, and 8 000 listening interactions
2. Clean and normalise the data
3. Build the user–item rating matrix
4. Train the Content-Based model (cosine similarity)
5. Train the SVD Collaborative Filter (Truncated SVD, 50 components)
6. Train the KNN Collaborative Filter (item-based cosine k-NN)
7. Save all models to `models/saved/`

### 3 — (Optional) Seed the SQLite database

```bash
python models/database.py
```

### 4 — (Optional) Generate visualisation plots

```bash
python notebooks/visualizations.py
# Plots saved to notebooks/plots/
```

### 5 — Start the web server

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🧠 Machine Learning Architecture

### A. Content-Based Filtering

**File:** `models/content_based.py`

- Extracts 9 audio feature dimensions per song:
  `tempo, energy, danceability, loudness, valence, acousticness, instrumentalness, speechiness, liveness`
- Normalises with MinMaxScaler → unit-hypercube
- Constructs an **N×N cosine-similarity matrix** (1 000 × 1 000)
- `recommend(track_id)` returns the K most similar tracks by cosine score
- Optional `filter_genre=True` restricts results to the same genre

### B. Collaborative Filtering

**File:** `models/collaborative_filtering.py`

**SVDCollaborativeFilter**
- Builds a User × Track rating matrix (implicit ratings from play count + likes + skips)
- Applies `sklearn.decomposition.TruncatedSVD` with 50 latent components
- Predicts ratings as U Σ Vᵀ dot products
- Evaluates with RMSE on held-out ratings

**KNNCollaborativeFilter**
- Item-based cosine similarity on the user–item matrix
- Scores unheard items via weighted k-NN sum over heard items

### C. Hybrid Recommendation System

**File:** `recommender/hybrid.py`

```
hybrid_score = α × cf_norm + (1−α) × cb_norm
```

- Default `α = 0.6` (adjustable at query-time via slider or API param)
- Both scores are min-max normalised before blending
- Seed track for the content component = user's most-played track
- Cold-start fallback: return globally popular tracks for unknown users

---

## 🌐 REST API Reference

The API is available at `http://localhost:5000/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/recommend/user/{user_id}` | Personalised hybrid recommendations |
| GET | `/api/recommend/song/{track_id}` | Content-based similar songs |
| GET | `/api/trending` | Globally trending tracks |
| GET | `/api/users` | All user IDs |
| GET | `/api/songs` | Paginated song catalogue |
| GET | `/api/songs/{track_id}` | Song detail + audio features |
| GET | `/api/genres` | Distinct genres |
| GET | `/api/evaluate` | Precision@K, Recall@K, NDCG@K |

### Query Parameters

**GET /api/recommend/user/{user_id}**
- `top_n` (int, default 10) — number of results
- `cf_weight` (float 0–1, default 0.6) — hybrid blend weight

**GET /api/trending**
- `top_n` (int, default 10)

**GET /api/songs**
- `page`, `per_page`, `genre`

**GET /api/evaluate**
- `k` (default 10), `sample_users` (default 50)

---

## 📊 Dataset Schema

### songs.csv

| Column | Type | Description |
|--------|------|-------------|
| track_id | str | Unique track identifier |
| track_name | str | Song title |
| artist | str | Artist name |
| genre | str | Music genre (15 genres) |
| release_year | int | Year of release |
| popularity | int | 0–100 Spotify-style score |
| tempo | float | BPM |
| energy | float | 0–1 (intensity) |
| danceability | float | 0–1 |
| loudness | float | dB |
| valence | float | 0–1 (musical positivity) |
| acousticness | float | 0–1 |
| instrumentalness | float | 0–1 |
| speechiness | float | 0–1 |
| liveness | float | 0–1 |

### listening_history.csv

| Column | Type | Description |
|--------|------|-------------|
| user_id | str | User identifier |
| track_id | str | Track identifier |
| play_count | int | How many times played |
| likes | int | 0/1 flag |
| skips | int | 0/1 flag |
| rating | float | Implicit 1–5 rating |

---

## 📈 Evaluation Metrics

Run from the UI (Metrics tab) or CLI:

```bash
python recommender/evaluate.py
```

| Metric | Description |
|--------|-------------|
| **Precision@K** | Fraction of top-K recs that are actually relevant |
| **Recall@K** | Fraction of relevant items captured in top-K |
| **NDCG@K** | Ranking quality accounting for position |
| **RMSE** | Predicted vs actual rating error (SVD) |

A "relevant" item is defined as one the user rated ≥ 3.5.

---

## 🎨 UI Features

| Feature | Details |
|---------|---------|
| Dark glassmorphism design | Spotify-green accent, subtle gradients |
| Dashboard | Live stats, trending preview, genre doughnut chart |
| For You tab | User ID input, CF-weight slider, recommendation cards with score bars |
| Similar Songs tab | Track ID search, seed song detail card, cosine-similarity bar list |
| Trending tab | Card grid with rank numbers, coloured genre tags, trend score badges |
| Metrics tab | Run evaluation on demand, animated metric cards + Chart.js bar chart |
| Responsive | Mobile-friendly sidebar collapse |

---

## 🔧 Configuration

All key parameters live in the relevant source file and are easily tunable:

| Parameter | File | Default | Effect |
|-----------|------|---------|--------|
| `NUM_SONGS` | `data/generate_dataset.py` | 1000 | Size of catalogue |
| `NUM_USERS` | `data/generate_dataset.py` | 200 | Number of users |
| `NUM_HISTORY` | `data/generate_dataset.py` | 8000 | Interaction rows |
| `n_components` | `train_all.py` | 50 | SVD latent dims |
| `cf_weight` | `recommender/hybrid.py` | 0.6 | Hybrid blend (0=pure CB, 1=pure CF) |
| `PORT` | `app.py` | 5000 | Flask server port |

---

## 🧪 Running Individual Components

```bash
# Generate dataset only
python data/generate_dataset.py

# Clean and preprocess data
python preprocessing/clean_data.py

# Train content-based model
python models/content_based.py

# Train collaborative filters
python models/collaborative_filtering.py

# Test hybrid recommender
python recommender/hybrid.py

# Run evaluation
python recommender/evaluate.py

# Generate visualisation plots
python notebooks/visualizations.py

# Seed SQLite database
python models/database.py
```

---

## 💡 How It Works — Step by Step

```
User enters user_id
        │
        ▼
SVD model scores all unheard tracks        (collaborative signal)
        │
        ▼
Content-based model scores all tracks      (audio similarity to
   relative to user's most-played song      most-played track)
        │
        ▼
Merge, min-max normalise both score lists
        │
        ▼
hybrid_score = 0.6 × cf_norm + 0.4 × cb_norm
        │
        ▼
Return top-10 highest hybrid-score tracks
```

---

## 📝 License

MIT License — free to use and modify for educational purposes.
"# spotify-recommentation-system" 
"# spotify" 
