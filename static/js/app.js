/**
 * app.js — Spotify Recommendation Engine Frontend
 *
 * Handles:
 *  - Tab navigation
 *  - API calls to Flask backend
 *  - Dynamic rendering of recommendations, similar songs, trending tracks
 *  - Chart.js visualisations (genre doughnut, metrics bar chart)
 *  - Toast notifications
 */

'use strict';

// ── Constants ────────────────────────────────────────────────────────────────
const API = {
  health:     '/api/health',
  users:      '/api/users',
  songs:      '/api/songs',
  genres:     '/api/genres',
  trending:   '/api/trending',
  evaluate:   '/api/evaluate',
  recommend:  (uid)  => `/api/recommend/user/${uid}`,
  similar:    (tid)  => `/api/recommend/song/${tid}`,
  songDetail: (tid)  => `/api/songs/${tid}`,
};

// Genre emoji map
const GENRE_EMOJI = {
  pop:'🎤', rock:'🎸', 'hip-hop':'🎤', jazz:'🎷', classical:'🎻',
  electronic:'🎧', 'r&b':'🎙️', country:'🤠', metal:'🤘', indie:'🎸',
  latin:'💃', blues:'🎺', reggae:'🌴', folk:'🪕', soul:'❤️‍🔥',
};

// Gradient pairs for avatars
const GRADIENTS = [
  ['#1DB954','#0e4f25'], ['#A29BFE','#6c5ce7'], ['#FF6B6B','#c0392b'],
  ['#FFEAA7','#f39c12'], ['#4e9af1','#2980b9'], ['#fd79a8','#e84393'],
  ['#55efc4','#00b894'], ['#fdcb6e','#e17055'], ['#74b9ff','#0984e3'],
  ['#a29bfe','#6c5ce7'],
];
const gradient = (i) => GRADIENTS[i % GRADIENTS.length];

// ── Charts ───────────────────────────────────────────────────────────────────
let genreChartInstance   = null;
let metricsChartInstance = null;

// ── Utility ──────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const qs = (sel, root = document) => root.querySelector(sel);
const el = (tag, cls = '', inner = '') => {
  const e = document.createElement(tag);
  if (cls)   e.className   = cls;
  if (inner) e.innerHTML   = inner;
  return e;
};

function showToast(msg, duration = 3000) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}

function loading(id, show) {
  const el = $(id);
  if (el) el.style.display = show ? 'flex' : 'none';
}

async function apiFetch(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const json = await res.json().catch(() => ({}));
    throw new Error(json.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Tab navigation ────────────────────────────────────────────────────────────
const TAB_TITLES = {
  'dashboard'    : 'Dashboard',
  'user-recs'    : 'For You',
  'similar-songs': 'Similar Songs',
  'trending'     : 'Trending',
  'evaluate'     : 'Model Metrics',
};

function switchTab(tabId) {
  document.querySelectorAll('.nav-item').forEach(n => {
    n.classList.toggle('active', n.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });
  $('pageTitle').textContent = TAB_TITLES[tabId] || tabId;

  // Lazy-load tab content
  if (tabId === 'trending') loadTrending();
}

document.querySelectorAll('.nav-item').forEach(nav => {
  nav.addEventListener('click', e => {
    e.preventDefault();
    switchTab(nav.dataset.tab);
    // Close sidebar on mobile
    if (window.innerWidth <= 768) $('sidebar').classList.remove('open');
  });
});

// Mobile sidebar toggle
$('menuToggle').addEventListener('click', () => {
  $('sidebar').classList.toggle('open');
});

// ── API health check ──────────────────────────────────────────────────────────
async function checkHealth() {
  const pill = $('apiStatus');
  try {
    await apiFetch(API.health);
    pill.classList.add('online');
    $('statusText').textContent = 'Engine Online';
  } catch {
    $('statusText').textContent = 'Offline';
  }
}

// ── Dashboard: stats + trending preview ──────────────────────────────────────
async function loadDashboard() {
  // Songs count
  try {
    const data = await apiFetch(API.songs + '?per_page=1');
    $('stat-songs').textContent = data.total.toLocaleString();
  } catch {}

  // Users count
  try {
    const data = await apiFetch(API.users);
    $('stat-users').textContent = data.count.toLocaleString();
  } catch {}

  // Genres count + doughnut chart
  try {
    const data = await apiFetch(API.genres);
    $('stat-genres').textContent = data.genres.length;
    drawGenreChart(data.genres);
  } catch {}

  // Trending preview (top 8)
  try {
    const data = await apiFetch(API.trending + '?top_n=8');
    renderTrackList('dashboardTrending', data.trending_tracks);
  } catch {}
}

function renderTrackList(containerId, tracks) {
  const container = $(containerId);
  if (!container) return;
  container.innerHTML = '';
  tracks.forEach((t, i) => {
    const [c1, c2] = gradient(i);
    const row = el('div', 'track-row',
      `<span class="track-num">${i + 1}</span>
       <div class="track-avatar" style="--c1:${c1};--c2:${c2}">${GENRE_EMOJI[t.genre] || '🎵'}</div>
       <div class="track-info">
         <div class="track-name">${esc(t.track_name || t.track_id)}</div>
         <div class="track-sub">${esc(t.artist || '')} · ${esc(t.genre || '')}</div>
       </div>
       <span class="track-badge">${((t.trend_score || t.popularity || 0) * 100 / 100).toFixed ? (t.trend_score ? (t.trend_score * 100).toFixed(0) + '%' : t.popularity) : ''}</span>`
    );
    container.appendChild(row);
  });
}

function drawGenreChart(genres) {
  const canvas = $('genreChart');
  if (!canvas) return;
  if (genreChartInstance) { genreChartInstance.destroy(); genreChartInstance = null; }

  const colors = [
    '#1DB954','#A29BFE','#FF6B6B','#FFEAA7','#4e9af1',
    '#fd79a8','#55efc4','#fdcb6e','#74b9ff','#a29bfe',
    '#e17055','#00b894','#e84393','#0984e3','#6c5ce7',
  ];

  // Fetch per-genre counts
  apiFetch(API.songs + '?per_page=1000').then(data => {
    const counts = {};
    data.songs.forEach(s => { counts[s.genre] = (counts[s.genre] || 0) + 1; });
    const labels = Object.keys(counts);
    const vals   = labels.map(g => counts[g]);

    genreChartInstance = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data: vals, backgroundColor: colors.slice(0, labels.length),
                     borderColor: '#0d0d14', borderWidth: 2, hoverOffset: 6 }],
      },
      options: {
        cutout: '68%',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.parsed} songs`,
            },
          },
        },
        animation: { animateRotate: true, duration: 800 },
      },
    });
  }).catch(() => {
    // Fallback: show genres as doughnut with equal slices
    genreChartInstance = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: genres,
        datasets: [{
          data: Array(genres.length).fill(1),
          backgroundColor: colors.slice(0, genres.length),
          borderColor: '#0d0d14', borderWidth: 2,
        }],
      },
      options: { cutout:'68%', plugins:{ legend:{ display:false } } },
    });
  });
}

// ── For You Tab ────────────────────────────────────────────────────────────────
async function loadQuickUsers() {
  try {
    const data = await apiFetch(API.users);
    const container = $('quickUsers');
    data.users.slice(0, 10).forEach(uid => {
      const chip = el('span', 'quick-user-chip', uid);
      chip.addEventListener('click', () => {
        $('userIdInput').value = uid;
        fetchUserRecs();
      });
      container.appendChild(chip);
    });
  } catch {}
}

$('cfWeightSlider').addEventListener('input', function () {
  $('cfWeightVal').textContent = parseFloat(this.value).toFixed(2);
  // Update gradient fill on slider
  const pct = (this.value / this.max) * 100;
  this.style.background = `linear-gradient(to right, var(--accent) ${pct}%, var(--bg-elevated) ${pct}%)`;
});

$('getUserRecs').addEventListener('click', fetchUserRecs);
$('userIdInput').addEventListener('keydown', e => { if (e.key === 'Enter') fetchUserRecs(); });

async function fetchUserRecs() {
  const uid      = $('userIdInput').value.trim();
  const cfWeight = $('cfWeightSlider').value;
  if (!uid) { showToast('Please enter a User ID'); return; }

  $('userRecsResult').style.display = 'none';
  loading('userRecsLoading', true);
  try {
    const data = await apiFetch(`${API.recommend(uid)}?top_n=10&cf_weight=${cfWeight}`);
    loading('userRecsLoading', false);
    $('recUserLabel').textContent = uid;
    renderRecommendationCards('userRecsCards', data.recommendations);
    $('userRecsResult').style.display = 'block';
  } catch (err) {
    loading('userRecsLoading', false);
    showToast(`Error: ${err.message}`);
  }
}

function renderRecommendationCards(containerId, tracks) {
  const container = $(containerId);
  container.innerHTML = '';
  tracks.forEach((t, i) => {
    const [c1, c2] = gradient(i);
    const hybrid = (t.hybrid_score || 0);
    const cf     = (t.cf_score    || 0);
    const cb     = (t.cb_score    || 0);

    const card = el('div', 'track-card');
    card.style.animationDelay = `${i * 0.04}s`;
    card.innerHTML = `
      <div class="card-top">
        <div class="card-avatar" style="--c1:${c1};--c2:${c2}">${GENRE_EMOJI[t.genre] || '🎵'}</div>
        <div class="card-info">
          <div class="card-name">${esc(t.track_name || t.track_id)}</div>
          <div class="card-artist">${esc(t.artist || '—')}</div>
          <span class="card-genre">${esc(t.genre || '')}</span>
        </div>
      </div>
      <div class="score-bars">
        ${scoreBar('Hybrid',  hybrid, '#1DB954')}
        ${scoreBar('Collab',  cf,     '#A29BFE')}
        ${scoreBar('Content', cb,     '#FF6B6B')}
      </div>`;
    container.appendChild(card);
  });
}

function scoreBar(label, value, color) {
  const pct = Math.round(value * 100);
  return `<div class="score-bar-row">
    <span>${label}</span>
    <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
    <span class="score-val">${value.toFixed(2)}</span>
  </div>`;
}

// ── Similar Songs Tab ─────────────────────────────────────────────────────────
$('getSimilarSongs').addEventListener('click', fetchSimilarSongs);
$('trackIdInput').addEventListener('keydown', e => { if (e.key === 'Enter') fetchSimilarSongs(); });

async function fetchSimilarSongs() {
  const tid    = $('trackIdInput').value.trim();
  const genre  = $('genreFilterCheck').checked;
  if (!tid) { showToast('Please enter a Track ID'); return; }

  $('similarSongsResult').style.display = 'none';
  loading('similarLoading', true);
  try {
    const [simData, detailData] = await Promise.all([
      apiFetch(`${API.similar(tid)}?top_n=10&filter_genre=${genre}`),
      apiFetch(API.songDetail(tid)).catch(() => null),
    ]);
    loading('similarLoading', false);

    $('simTrackLabel').textContent = tid;
    renderSeedSong(detailData);
    renderSimilarityBars('similarityBars', simData.similar_songs);
    $('similarSongsResult').style.display = 'block';
  } catch (err) {
    loading('similarLoading', false);
    showToast(`Error: ${err.message}`);
  }
}

function renderSeedSong(song) {
  const wrap = $('seedSongDetail');
  if (!song) { wrap.style.display = 'none'; return; }
  wrap.style.display = 'flex';
  wrap.innerHTML = `
    <div class="seed-avatar">${GENRE_EMOJI[song.genre] || '🎵'}</div>
    <div class="seed-info">
      <div class="seed-label">Seed Track</div>
      <h4>${esc(song.track_name || song.track_id)}</h4>
      <p>${esc(song.artist || '—')} · ${esc(song.genre || '')} · ${song.release_year || ''}</p>
    </div>`;
}

function renderSimilarityBars(containerId, tracks) {
  const container = $(containerId);
  container.innerHTML = '';
  tracks.forEach((t, i) => {
    const [c1] = gradient(i);
    const pct  = Math.round((t.similarity_score || 0) * 100);
    const row  = el('div', 'sim-row');
    row.style.animationDelay = `${i * 0.04}s`;
    row.innerHTML = `
      <span class="sim-rank">${i + 1}</span>
      <div class="sim-avatar" style="background:linear-gradient(135deg,${gradient(i).join(',')})">${GENRE_EMOJI[t.genre] || '🎵'}</div>
      <div class="sim-info">
        <div class="sim-name">${esc(t.track_name || t.track_id)}</div>
        <div class="sim-sub">${esc(t.artist || '—')} · ${esc(t.genre || '')}</div>
      </div>
      <div class="sim-bar-wrap">
        <div class="sim-bar-bg"><div class="sim-bar-fg" style="width:${pct}%"></div></div>
        <div class="sim-score">${(t.similarity_score || 0).toFixed(3)}</div>
      </div>`;
    container.appendChild(row);
  });
}

// ── Trending Tab ──────────────────────────────────────────────────────────────
let trendingLoaded = false;
async function loadTrending() {
  if (trendingLoaded) return;
  loading('trendingLoading', true);
  try {
    const data = await apiFetch(API.trending + '?top_n=20');
    loading('trendingLoading', false);
    renderTrendingGrid(data.trending_tracks);
    $('trendingGrid').style.display = 'grid';
    trendingLoaded = true;
  } catch (err) {
    loading('trendingLoading', false);
    showToast(`Failed to load trending: ${err.message}`);
  }
}

function renderTrendingGrid(tracks) {
  const grid = $('trendingGrid');
  grid.innerHTML = '';
  tracks.forEach((t, i) => {
    const card = el('div', 'trending-card');
    card.style.animationDelay = `${i * 0.05}s`;
    const score = t.trend_score != null
      ? (t.trend_score * 100).toFixed(0) + '%'
      : (t.popularity || '—');
    card.innerHTML = `
      <div class="trending-rank">${String(i + 1).padStart(2,'0')}</div>
      <div class="trending-emoji">${GENRE_EMOJI[t.genre] || '🎵'}</div>
      <div class="trending-name">${esc(t.track_name || t.track_id)}</div>
      <div class="trending-artist">${esc(t.artist || '—')}</div>
      <div class="trending-meta">
        <span class="trend-score-badge">🔥 ${score}</span>
        <span class="genre-tag">${esc(t.genre || '')}</span>
      </div>`;
    grid.appendChild(card);
  });
}

// ── Evaluate Tab ──────────────────────────────────────────────────────────────
$('runEvalBtn').addEventListener('click', runEvaluation);

async function runEvaluation() {
  const k    = $('evalK').value           || 10;
  const su   = $('evalSampleUsers').value || 50;
  $('evalResults').style.display = 'none';
  loading('evalLoading', true);
  try {
    const data = await apiFetch(`${API.evaluate}?k=${k}&sample_users=${su}`);
    loading('evalLoading', false);
    renderMetrics(data, k);
    $('evalResults').style.display = 'block';
  } catch (err) {
    loading('evalLoading', false);
    showToast(`Evaluation error: ${err.message}`);
  }
}

let metricsRadarInstance = null;

function renderMetrics(data, k) {
  const grid = $('metricsGrid');
  grid.innerHTML = '';

  const defs = [
    { key: `Precision@${k}`, label: `Precision@${k}`, icon: '🎯', clr: '#1DB954',
      fmt: v => (v * 100).toFixed(1) + '%', pct: v => v },
    { key: `Recall@${k}`,    label: `Recall@${k}`,    icon: '🔍', clr: '#A29BFE',
      fmt: v => (v * 100).toFixed(1) + '%', pct: v => v },
    { key: `NDCG@${k}`,      label: `NDCG@${k}`,      icon: '📈', clr: '#FF6B6B',
      fmt: v => (v * 100).toFixed(1) + '%', pct: v => v },
    { key: 'n_users_evaluated', label: 'Users Evaluated', icon: '👥', clr: '#FFEAA7',
      fmt: v => v.toLocaleString(), pct: () => 0 },
  ];

  defs.forEach((m, i) => {
    if (!(m.key in data)) return;
    const raw  = data[m.key];
    const pct  = m.key === 'n_users_evaluated' ? 0 : Math.round(raw * 100);

    const card = el('div', 'metric-card');
    card.style.setProperty('--mc-clr', m.clr);
    card.style.animationDelay = `${i * 0.08}s`;
    card.innerHTML = `
      <div class="metric-icon">${m.icon}</div>
      <div class="metric-value" data-target="${raw}" data-isnum="${m.key === 'n_users_evaluated'}">${m.fmt(raw)}</div>
      <div class="metric-name">${m.label}</div>
      ${m.key !== 'n_users_evaluated' ? `
        <div class="metric-bar-wrap">
          <div class="metric-bar-track">
            <div class="metric-bar-fill" style="width:0%" id="mbar-${i}"></div>
          </div>
        </div>` : ''}`;
    grid.appendChild(card);

    // Animate progress bar
    if (m.key !== 'n_users_evaluated') {
      setTimeout(() => {
        const bar = $(`mbar-${i}`);
        if (bar) bar.style.width = Math.min(pct, 100) + '%';
      }, 120 + i * 80);
    }
  });

  // ── Bar chart ──────────────────────────────────────────────────────────────
  const canvas = $('metricsChart');
  if (metricsChartInstance) { metricsChartInstance.destroy(); }
  const labels = [`Precision@${k}`, `Recall@${k}`, `NDCG@${k}`];
  const values = [
    data[`Precision@${k}`] || 0,
    data[`Recall@${k}`]    || 0,
    data[`NDCG@${k}`]      || 0,
  ].map(v => +(v * 100).toFixed(2));

  metricsChartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Score (%)',
        data: values,
        backgroundColor: [
          'rgba(29,185,84,0.75)',
          'rgba(162,155,254,0.75)',
          'rgba(255,107,107,0.75)',
        ],
        borderColor: ['#1DB954', '#A29BFE', '#FF6B6B'],
        borderWidth: 2,
        borderRadius: 10,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      animation: { duration: 900, easing: 'easeOutQuart' },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.y.toFixed(2)}%`,
            title: ctx => ctx[0].label,
          },
          backgroundColor: 'rgba(22,22,33,0.95)',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          padding: 10,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: Math.max(...values, 10) * 1.2,
          ticks: { color: '#9090b0', callback: v => v.toFixed(1) + '%' },
          grid: { color: 'rgba(255,255,255,0.05)' },
          border: { color: 'transparent' },
        },
        x: {
          ticks: { color: '#9090b0' },
          grid: { display: false },
          border: { color: 'transparent' },
        },
      },
    },
  });

  // ── Radar chart ────────────────────────────────────────────────────────────
  const radar = $('metricsRadar');
  if (metricsRadarInstance) { metricsRadarInstance.destroy(); }
  metricsRadarInstance = new Chart(radar, {
    type: 'radar',
    data: {
      labels: [`Precision@${k}`, `Recall@${k}`, `NDCG@${k}`],
      datasets: [{
        label: 'Model Performance',
        data: values,
        backgroundColor: 'rgba(29,185,84,0.15)',
        borderColor: '#1DB954',
        borderWidth: 2,
        pointBackgroundColor: ['#1DB954', '#A29BFE', '#FF6B6B'],
        pointRadius: 5,
        pointHoverRadius: 7,
      }],
    },
    options: {
      responsive: true,
      animation: { duration: 900 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.raw.toFixed(2)}%` },
          backgroundColor: 'rgba(22,22,33,0.95)',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
        },
      },
      scales: {
        r: {
          beginAtZero: true,
          max: Math.max(...values, 15) * 1.3,
          ticks: { color: '#9090b0', backdropColor: 'transparent', callback: v => v + '%' },
          grid: { color: 'rgba(255,255,255,0.07)' },
          angleLines: { color: 'rgba(255,255,255,0.07)' },
          pointLabels: { color: '#9090b0', font: { size: 11 } },
        },
      },
    },
  });
}

// ── HTML escape helper ────────────────────────────────────────────────────────
function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Init ──────────────────────────────────────────────────────────────────────
(async function init() {
  await checkHealth();
  await loadDashboard();
  await loadQuickUsers();
})();
