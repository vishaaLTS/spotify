"""
app.py
-------
Flask application entry point for the Spotify Recommendation Engine.

Start the server:
    python app.py

The server runs on http://localhost:5000
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template
from flask_cors import CORS

from recommender.hybrid import HybridRecommender
from api.routes import api_bp


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    CORS(app)

    # ── Load and attach the recommendation engine ──────────────────────────
    print("\nLoading recommendation engine …")
    engine = HybridRecommender(cf_weight=0.6)
    try:
        engine.load_models()
        print("  Engine loaded successfully.\n")
    except FileNotFoundError as exc:
        print(f"\n[ERROR] {exc}")
        print("  Run  python train_all.py  first to train the models.\n")
        sys.exit(1)

    app.config["ENGINE"] = engine

    # ── Register blueprints ────────────────────────────────────────────────
    app.register_blueprint(api_bp)

    # ── Frontend route ────────────────────────────────────────────────────
    @app.route("/")
    def index():
        return render_template("index.html")

    return app


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
