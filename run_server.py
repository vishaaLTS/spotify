"""
run_server.py
-------------
Starts the Spotify Recommendation Flask app and creates a public URL via pyngrok.

Usage:
    python run_server.py
    python run_server.py --token YOUR_NGROK_AUTHTOKEN

Get a free token at: https://dashboard.ngrok.com/signup
"""

import sys
import os
import threading
import time
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── Parse optional --token argument ──────────────────────────────────────────
ngrok_token = None
if "--token" in sys.argv:
    idx = sys.argv.index("--token")
    if idx + 1 < len(sys.argv):
        ngrok_token = sys.argv[idx + 1]

PORT = 5000

# ── Start ngrok tunnel ────────────────────────────────────────────────────────
def start_ngrok(port):
    try:
        from pyngrok import ngrok, conf

        if ngrok_token:
            conf.get_default().auth_token = ngrok_token

        tunnel = ngrok.connect(port, "http")
        public_url = tunnel.public_url
        print("\n" + "=" * 60)
        print("  🎵  Spotify Recommendation Engine is LIVE!")
        print("=" * 60)
        print(f"\n  ✅  Public URL  : {public_url}")
        print(f"  🏠  Local URL   : http://localhost:{port}")
        print("\n  Share the Public URL with anyone to access your app.")
        print("  Press CTRL+C to stop the server.")
        print("=" * 60 + "\n")
        # Auto-open in browser
        webbrowser.open(public_url)
        return public_url
    except Exception as e:
        print(f"\n[WARNING] Could not create public ngrok tunnel: {e}")
        print(f"          App is still running at http://localhost:{port}\n")
        webbrowser.open(f"http://localhost:{port}")
        return None


# ── Create and run app ────────────────────────────────────────────────────────
if __name__ == "__main__":
    from app import create_app

    flask_app = create_app()

    # Start ngrok in a background thread after a brief delay
    def delayed_tunnel():
        time.sleep(1.5)  # let Flask start first
        start_ngrok(PORT)

    t = threading.Thread(target=delayed_tunnel, daemon=True)
    t.start()

    print(f"\nStarting Flask server on port {PORT} …")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
