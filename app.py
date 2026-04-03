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

from flask import Flask, render_template, send_from_directory  # type: ignore # pyre-ignore
from flask_cors import CORS  # type: ignore # pyre-ignore

from recommender.hybrid import HybridRecommender  # type: ignore # pyre-ignore
from api.routes import api_bp  # type: ignore # pyre-ignore


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "frontend", "dist"),
        static_folder=os.path.join(BASE_DIR, "frontend", "dist", "assets"),
        static_url_path="/assets"
    )
    CORS(app)

    # ── Load and attach the recommendation engine ──────────────────────────
    print("\nLoading recommendation engine …")
    engine = HybridRecommender(cf_weight=0.6)
    try:
        engine.load_models()
        print("  Engine loaded successfully.\n")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"\n[ERROR loading models] {exc}")
        print("  WARNING: Models not found or failed to load! Recommendations will fail.")
        print("  Run  python train_all.py  first to train the models locally.\n")
        # Do not exit so Vercel/Render can still boot up and show the UI!

    app.config["ENGINE"] = engine

    # ── Register blueprints ────────────────────────────────────────────────
    app.register_blueprint(api_bp)

    # ── Frontend routes ───────────────────────────────────────────────────
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/<path:filename>")
    def root_static(filename):
        return send_from_directory(app.template_folder, filename)

    return app


app = create_app()

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
