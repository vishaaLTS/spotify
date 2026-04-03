import React, { useState } from "react";
import { Bar, Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip
);

export default function EvaluateTab({ showToast }) {
  const [evalK, setEvalK] = useState(10);
  const [evalSampleUsers, setEvalSampleUsers] = useState(50);
  const [loading, setLoading] = useState(false);
  const [metricsData, setMetricsData] = useState(null);

  const runEvaluation = async () => {
    setLoading(true);
    setMetricsData(null);
    try {
      const res = await fetch(`/api/evaluate?k=${evalK}&sample_users=${evalSampleUsers}`);
      if (!res.ok) throw new Error("HTTP Error");
      const data = await res.json();
      setMetricsData(data);
    } catch (err) {
      showToast(`Evaluation error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getChartData = () => {
    if (!metricsData) return { barData: null, radarData: null };
    
    const labels = [`Precision@${evalK}`, `Recall@${evalK}`, `NDCG@${evalK}`];
    const values = [
      metricsData[`Precision@${evalK}`] || 0,
      metricsData[`Recall@${evalK}`] || 0,
      metricsData[`NDCG@${evalK}`] || 0,
    ].map(v => +(v * 100).toFixed(2));

    const barData = {
      labels,
      datasets: [
        {
          label: "Score (%)",
          data: values,
          backgroundColor: [
            "rgba(29,185,84,0.75)",
            "rgba(162,155,254,0.75)",
            "rgba(255,107,107,0.75)",
          ],
          borderColor: ["#1DB954", "#A29BFE", "#FF6B6B"],
          borderWidth: 2,
          borderRadius: 10,
        },
      ],
    };

    const radarData = {
      labels,
      datasets: [
        {
          label: "Model Performance",
          data: values,
          backgroundColor: "rgba(29,185,84,0.15)",
          borderColor: "#1DB954",
          borderWidth: 2,
          pointBackgroundColor: ["#1DB954", "#A29BFE", "#FF6B6B"],
          pointRadius: 5,
        },
      ],
    };

    return { barData, radarData, values };
  };

  const { barData, radarData, values } = getChartData();

  return (
    <section className="tab-pane active" id="tab-evaluate">
      <div className="metrics-hero">
        <div className="metrics-hero-text">
          <h2>📊 Model Evaluation Metrics</h2>
          <p>
            Hold-out evaluation: each user's history is split train/test. Recommendations are scored against held-out
            interactions using Precision@K, Recall@K, and NDCG@K.
          </p>
        </div>
      </div>

      <div className="eval-controls">
        <div className="input-group-inline">
          <label htmlFor="evalK">K (cutoff):</label>
          <input
            type="number"
            id="evalK"
            value={evalK}
            onChange={(e) => setEvalK(Number(e.target.value))}
            min="1"
            max="50"
            className="num-input"
          />
        </div>
        <div className="input-group-inline">
          <label htmlFor="evalSampleUsers">Sample users:</label>
          <input
            type="number"
            id="evalSampleUsers"
            value={evalSampleUsers}
            onChange={(e) => setEvalSampleUsers(Number(e.target.value))}
            min="5"
            max="200"
            className="num-input"
          />
        </div>
        <button className="btn-primary" onClick={runEvaluation} disabled={loading}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          {loading ? "Evaluating..." : "Run Evaluation"}
        </button>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Evaluating model on sample users…</p>
        </div>
      )}

      {metricsData && !loading && (
        <div id="evalResults">
          <div className="metrics-grid">
            {[
              { key: `Precision@${evalK}`, label: `Precision@${evalK}`, icon: "🎯", clr: "#1DB954" },
              { key: `Recall@${evalK}`, label: `Recall@${evalK}`, icon: "🔍", clr: "#A29BFE" },
              { key: `NDCG@${evalK}`, label: `NDCG@${evalK}`, icon: "📈", clr: "#FF6B6B" },
              { key: "n_users_evaluated", label: "Users Evaluated", icon: "👥", clr: "#FFEAA7" },
            ].map((m, i) => {
              if (!(m.key in metricsData)) return null;
              const raw = metricsData[m.key];
              const isNum = m.key === "n_users_evaluated";
              const displayVal = isNum ? raw.toLocaleString() : (raw * 100).toFixed(1) + "%";
              const pct = isNum ? 0 : Math.round(raw * 100);

              return (
                <div key={m.key} className="metric-card" style={{ "--mc-clr": m.clr, animationDelay: `${i * 0.08}s` }}>
                  <div className="metric-icon">{m.icon}</div>
                  <div className="metric-value">{displayVal}</div>
                  <div className="metric-name">{m.label}</div>
                  {!isNum && (
                    <div className="metric-bar-wrap">
                      <div className="metric-bar-track">
                        <div className="metric-bar-fill" style={{ width: `${pct}%` }}></div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="metrics-charts-row">
            <div className="card metrics-chart-card">
              <h3 className="card-title">Score Comparison</h3>
              <div className="metrics-chart-wrap">
                {barData && (
                  <Bar
                    data={barData}
                    options={{
                      responsive: true,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          callbacks: { label: (ctx) => ` ${ctx.parsed.y.toFixed(2)}%` },
                        },
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: Math.max(...values, 10) * 1.2,
                          ticks: { color: "#9090b0", callback: (v) => v.toFixed(1) + "%" },
                          grid: { color: "rgba(255,255,255,0.05)" },
                        },
                        x: {
                          ticks: { color: "#9090b0" },
                          grid: { display: false },
                        },
                      },
                    }}
                  />
                )}
              </div>
            </div>
            <div className="card metrics-chart-card">
              <h3 className="card-title">Radar Overview</h3>
              <div className="metrics-chart-wrap">
                {radarData && (
                  <Radar
                    data={radarData}
                    options={{
                      responsive: true,
                      plugins: {
                        legend: { display: false },
                      },
                      scales: {
                        r: {
                          beginAtZero: true,
                          max: Math.max(...values, 15) * 1.3,
                          ticks: { color: "#9090b0", backdropColor: "transparent" },
                          grid: { color: "rgba(255,255,255,0.07)" },
                          angleLines: { color: "rgba(255,255,255,0.07)" },
                          pointLabels: { color: "#9090b0" },
                        },
                      },
                    }}
                  />
                )}
              </div>
            </div>
          </div>

          <div className="card metrics-interpretation">
            <h3 className="card-title">📖 Metric Interpretation</h3>
            <div className="interp-grid">
              <div className="interp-item">
                <div className="interp-icon" style={{ "--clr": "#1DB954" }}>P</div>
                <div>
                  <div className="interp-name">Precision@K</div>
                  <div className="interp-desc">
                    Fraction of the top-K recommended songs that were actually relevant to the user. Higher = fewer
                    wasted recommendations.
                  </div>
                </div>
              </div>
              <div className="interp-item">
                <div className="interp-icon" style={{ "--clr": "#A29BFE" }}>R</div>
                <div>
                  <div className="interp-name">Recall@K</div>
                  <div className="interp-desc">
                    Fraction of all songs the user would have liked that appear in the top-K. Higher = better coverage
                    of user preferences.
                  </div>
                </div>
              </div>
              <div className="interp-item">
                <div className="interp-icon" style={{ "--clr": "#FF6B6B" }}>N</div>
                <div>
                  <div className="interp-name">NDCG@K</div>
                  <div className="interp-desc">
                    Normalised Discounted Cumulative Gain. Rewards placing relevant songs earlier in the list. Perfect
                    ranking = 1.0.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
