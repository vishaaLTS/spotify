import React, { useState, useEffect } from "react";
import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { GENRE_EMOJI, getGradient } from "./utils";

ChartJS.register(ArcElement, Tooltip, Legend);

export default function DashboardTab({ showToast }) {
  const [stats, setStats] = useState({ songs: "-", users: "-", genres: 0 });
  const [trendingTracks, setTrendingTracks] = useState([]);
  const [genreData, setGenreData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [songsRes, usersRes, genresRes, trendingRes] = await Promise.all([
          fetch("/api/songs?per_page=1").then(res => res.json()),
          fetch("/api/users").then(res => res.json()),
          fetch("/api/genres").then(res => res.json()),
          fetch("/api/trending?top_n=8").then(res => res.json())
        ]);

        setStats({
          songs: songsRes.total?.toLocaleString() || "-",
          users: usersRes.count?.toLocaleString() || "-",
          genres: genresRes.genres?.length || 0
        });

        setTrendingTracks(trendingRes.trending_tracks || []);

        // fetch specific genre breakdown
        const allSongsRes = await fetch("/api/songs?per_page=1000").then(res => res.json());
        const counts = {};
        allSongsRes.songs?.forEach(s => {
          counts[s.genre] = (counts[s.genre] || 0) + 1;
        });

        const labels = Object.keys(counts);
        const vals = labels.map(g => counts[g]);
        const colors = [
          '#1DB954','#A29BFE','#FF6B6B','#FFEAA7','#4e9af1',
          '#fd79a8','#55efc4','#fdcb6e','#74b9ff','#a29bfe',
          '#e17055','#00b894','#e84393','#0984e3','#6c5ce7',
        ];

        setGenreData({
          labels,
          datasets: [
            {
              data: vals,
              backgroundColor: colors.slice(0, labels.length),
              borderColor: '#0d0d14',
              borderWidth: 2,
              hoverOffset: 6
            }
          ]
        });

      } catch (err) {
        showToast("Error loading dashboard data");
      }
    };

    fetchData();
  }, [showToast]);

  return (
    <section className="tab-pane active" id="tab-dashboard">
      <div className="hero-section">
        <div className="hero-text">
          <h2>Spotify Based Music Recommendations</h2>
          <p>Personalised recommendations using hybrid collaborative filtering + content-based audio-feature analysis.</p>
        </div>
        <div className="hero-graphic">
          <div className="vinyl-record" id="vinylRecord">
            <div className="vinyl-label"></div>
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ '--clr': '#1DB954' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
          </div>
          <div className="stat-body">
            <span className="stat-value">{stats.songs}</span>
            <span className="stat-label">Songs in Catalogue</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ '--clr': '#FF6B6B' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div className="stat-body">
            <span className="stat-value">{stats.users}</span>
            <span className="stat-label">Active Users</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ '--clr': '#A29BFE' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
          <div className="stat-body">
            <span className="stat-value">{stats.genres}</span>
            <span className="stat-label">Music Genres</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ '--clr': '#FFEAA7' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          </div>
          <div className="stat-body">
            <span className="stat-value">Hybrid</span>
            <span className="stat-label">AI Model Type</span>
          </div>
        </div>
      </div>

      <div className="section-row">
        <div className="card" style={{ flex: 1.3 }}>
          <h3 className="card-title">Trending Right Now</h3>
          <div className="track-list">
            {trendingTracks.map((t, i) => {
              const [c1, c2] = getGradient(i);
              return (
                <div key={i} className="track-row">
                  <span className="track-num">{i + 1}</span>
                  <div className="track-avatar" style={{ '--c1': c1, '--c2': c2 }}>{GENRE_EMOJI[t.genre] || '🎵'}</div>
                  <div className="track-info">
                    <div className="track-name">{t.track_name || t.track_id}</div>
                    <div className="track-sub">{t.artist || ''} · {t.genre || ''}</div>
                  </div>
                  <span className="track-badge">
                    {t.trend_score != null ? (t.trend_score * 100).toFixed(0) + '%' : t.popularity}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
        <div className="card" style={{ flex: 0.7 }}>
          <h3 className="card-title">Genre Breakdown</h3>
          <div className="genre-chart-wrap">
            {genreData ? (
              <Doughnut 
                data={genreData} 
                options={{
                  cutout: '68%',
                  plugins: { legend: { display: false } },
                  animation: { animateRotate: true, duration: 800 }
                }} 
              />
            ) : (
              <div style={{ color: '#55556a' }}>Loading...</div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
