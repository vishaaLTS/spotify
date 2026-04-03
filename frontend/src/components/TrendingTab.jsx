import React, { useState, useEffect } from "react";
import { GENRE_EMOJI } from "./utils";

export default function TrendingTab({ showToast }) {
  const [trendingTracks, setTrendingTracks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const res = await fetch("/api/trending?top_n=20");
        if (!res.ok) throw new Error("HTTP Error");
        const data = await res.json();
        setTrendingTracks(data.trending_tracks || []);
      } catch (err) {
        showToast(`Failed to load trending: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };
    fetchTrending();
  }, [showToast]);

  return (
    <section className="tab-pane active" id="tab-trending">
      <div className="tab-header">
        <h2>🔥 Trending Tracks</h2>
        <p>Top songs ranked by play count and popularity right now.</p>
      </div>

      {loading ? (
        <div className="loading" id="trendingLoading">
          <div className="spinner"></div>
          <p>Loading trending tracks…</p>
        </div>
      ) : (
        <div className="trending-grid">
          {trendingTracks.map((t, i) => {
            const score = t.trend_score != null
              ? (t.trend_score * 100).toFixed(0) + '%'
              : (t.popularity || '—');

            return (
              <div key={i} className="trending-card" style={{ animationDelay: `${i * 0.05}s` }}>
                <div className="trending-rank">{String(i + 1).padStart(2, "0")}</div>
                <div className="trending-emoji">{GENRE_EMOJI[t.genre] || "🎵"}</div>
                <div className="trending-name">{t.track_name || t.track_id}</div>
                <div className="trending-artist">{t.artist || "—"}</div>
                <div className="trending-meta">
                  <span className="trend-score-badge">🔥 {score}</span>
                  <span className="genre-tag">{t.genre || ""}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
