import React, { useState, useEffect } from "react";
import { GENRE_EMOJI, getGradient } from "./utils";

export default function ForYouTab({ showToast }) {
  const [userId, setUserId] = useState("");
  const [cfWeight, setCfWeight] = useState(0.6);
  const [quickUsers, setQuickUsers] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await fetch("/api/users").then(r => r.json());
        if (res.users) {
          setQuickUsers(res.users.slice(0, 10));
        }
      } catch (err) {
        // ignore initially
      }
    };
    fetchUsers();
  }, []);

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value);
    setCfWeight(val);
    const pct = (val / 1) * 100;
    e.target.style.background = `linear-gradient(to right, var(--accent) ${pct}%, var(--bg-elevated) ${pct}%)`;
  };

  const fetchUserRecs = async () => {
    if (!userId.trim()) {
      showToast("Please enter a User ID");
      return;
    }
    setLoading(true);
    setHasSearched(true);
    try {
      const res = await fetch(`/api/recommend/user/${userId.trim()}?top_n=10&cf_weight=${cfWeight}`);
      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        throw new Error(json.error || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setRecommendations(data.recommendations || []);
    } catch (err) {
      showToast(`Error: ${err.message}`);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      fetchUserRecs();
    }
  };

  return (
    <section className="tab-pane active" id="tab-user-recs">
      <div className="search-bar-wrap">
        <label className="input-label" htmlFor="userIdInput">Enter User ID</label>
        <div className="input-row">
          <div className="input-group">
            <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <input
              type="text"
              id="userIdInput"
              className="text-input"
              placeholder="e.g. USER_0001"
              autoComplete="off"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>
          <div className="slider-wrap">
            <label>CF Weight: <strong>{cfWeight.toFixed(2)}</strong></label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={cfWeight}
              onChange={handleSliderChange}
            />
          </div>
          <button className="btn-primary" onClick={fetchUserRecs}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Get Recommendations
          </button>
        </div>
        <div className="quick-users">
          {quickUsers.map(uid => (
            <span
              key={uid}
              className="quick-user-chip"
              onClick={() => {
                setUserId(uid);
                // Can't auto fetch predictably with state update delay, wait...
                // actually we can trigger the fetch in useEffect, or simply:
                // but for now, the user can click the button. 
                // Let's implement an effect or pass it.
              }}
            >
              {uid}
            </span>
          ))}
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Generating recommendations…</p>
        </div>
      )}

      {!loading && hasSearched && recommendations.length > 0 && (
        <div className="results-section">
          <div className="results-header">
            <h3>Personalised playlist for <span className="highlight">{userId}</span></h3>
            <div className="score-legend">
              <span className="legend-dot" style={{ background: "#1DB954" }}></span>Hybrid
              <span className="legend-dot" style={{ background: "#A29BFE" }}></span>Collaborative
              <span className="legend-dot" style={{ background: "#FF6B6B" }}></span>Content
            </div>
          </div>
          <div className="track-cards">
            {recommendations.map((t, i) => {
              const [c1, c2] = getGradient(i);
              const hybrid = t.hybrid_score || 0;
              const cf = t.cf_score || 0;
              const cb = t.cb_score || 0;

              return (
                <div key={i} className="track-card" style={{ animationDelay: `${i * 0.04}s` }}>
                  <div className="card-top">
                    <div className="card-avatar" style={{ '--c1': c1, '--c2': c2 }}>
                      {GENRE_EMOJI[t.genre] || "🎵"}
                    </div>
                    <div className="card-info">
                      <div className="card-name">{t.track_name || t.track_id}</div>
                      <div className="card-artist">{t.artist || "—"}</div>
                      <span className="card-genre">{t.genre || ""}</span>
                    </div>
                  </div>
                  <div className="score-bars">
                    <ScoreBar label="Hybrid" value={hybrid} color="#1DB954" />
                    <ScoreBar label="Collab" value={cf} color="#A29BFE" />
                    <ScoreBar label="Content" value={cb} color="#FF6B6B" />
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

function ScoreBar({ label, value, color }) {
  const pct = Math.round(value * 100);
  return (
    <div className="score-bar-row">
      <span>{label}</span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%`, background: color }}></div>
      </div>
      <span className="score-val">{value.toFixed(2)}</span>
    </div>
  );
}
