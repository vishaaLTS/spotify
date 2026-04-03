import React, { useState } from "react";
import { GENRE_EMOJI, getGradient } from "./utils";

export default function SimilarSongsTab({ showToast }) {
  const [trackId, setTrackId] = useState("");
  const [genreFilter, setGenreFilter] = useState(false);
  const [seedSong, setSeedSong] = useState(null);
  const [similarSongs, setSimilarSongs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const fetchSimilarSongs = async () => {
    if (!trackId.trim()) {
      showToast("Please enter a Track ID");
      return;
    }
    setLoading(true);
    setHasSearched(true);

    try {
      const [simRes, detailRes] = await Promise.all([
        fetch(`/api/recommend/song/${trackId.trim()}?top_n=10&filter_genre=${genreFilter}`),
        fetch(`/api/songs/${trackId.trim()}`)
      ]);

      if (!simRes.ok) throw new Error(await simRes.json().then(d => d.error).catch(() => "HTTP Error"));
      
      const simData = await simRes.json();
      const detailData = detailRes.ok ? await detailRes.json() : null;

      setSeedSong(detailData);
      setSimilarSongs(simData.similar_songs || []);
    } catch (err) {
      showToast(`Error: ${err.message}`);
      setSeedSong(null);
      setSimilarSongs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") fetchSimilarSongs();
  };

  return (
    <section className="tab-pane active" id="tab-similar-songs">
      <div className="search-bar-wrap">
        <label className="input-label" htmlFor="trackIdInput">Enter Track ID</label>
        <div className="input-row">
          <div className="input-group">
            <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
            <input
              type="text"
              id="trackIdInput"
              className="text-input"
              placeholder="e.g. TRACK_0001"
              autoComplete="off"
              value={trackId}
              onChange={(e) => setTrackId(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={genreFilter}
              onChange={(e) => setGenreFilter(e.target.checked)}
            />
            Same genre only
          </label>
          <button className="btn-primary" onClick={fetchSimilarSongs}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Find Similar
          </button>
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Computing similarity…</p>
        </div>
      )}

      {!loading && hasSearched && (
        <div className="results-section">
          {seedSong && (
            <div className="seed-song-detail">
              <div className="seed-avatar">{GENRE_EMOJI[seedSong.genre] || "🎵"}</div>
              <div className="seed-info">
                <div className="seed-label">Seed Track</div>
                <h4>{seedSong.track_name || seedSong.track_id}</h4>
                <p>{seedSong.artist || "—"} · {seedSong.genre || ""} · {seedSong.release_year || ""}</p>
              </div>
            </div>
          )}

          <h3 style={{ marginBottom: "1rem" }}>Songs similar to <span className="highlight">{trackId}</span></h3>
          
          <div className="similarity-bars">
            {similarSongs.map((t, i) => {
              const [c1, c2] = getGradient(i);
              const pct = Math.round((t.similarity_score || 0) * 100);

              return (
                <div key={i} className="sim-row" style={{ animationDelay: `${i * 0.04}s` }}>
                  <span className="sim-rank">{i + 1}</span>
                  <div className="sim-avatar" style={{ background: `linear-gradient(135deg, ${c1}, ${c2})` }}>
                    {GENRE_EMOJI[t.genre] || "🎵"}
                  </div>
                  <div className="sim-info">
                    <div className="sim-name">{t.track_name || t.track_id}</div>
                    <div className="sim-sub">{t.artist || "—"} · {t.genre || ""}</div>
                  </div>
                  <div className="sim-bar-wrap">
                    <div className="sim-bar-bg">
                      <div className="sim-bar-fg" style={{ width: `${pct}%` }}></div>
                    </div>
                    <div className="sim-score">{(t.similarity_score || 0).toFixed(3)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
