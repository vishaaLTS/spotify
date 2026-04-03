import React, { useState, useEffect } from "react";

const TAB_TITLES = {
  "dashboard": "Dashboard",
  "user-recs": "For You",
  "similar-songs": "Similar Songs",
  "trending": "Trending",
  "evaluate": "Model Metrics",
};

export default function Topbar({ activeTab, toggleSidebar }) {
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch("/api/health");
        if (res.ok) {
          setIsOnline(true);
        } else {
          setIsOnline(false);
        }
      } catch (err) {
        setIsOnline(false);
      }
    };
    checkHealth();
  }, []);

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button className="menu-toggle" aria-label="Toggle menu" onClick={toggleSidebar}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <h1 className="page-title">{TAB_TITLES[activeTab] || activeTab}</h1>
      </div>
      <div className="topbar-right">
        <div className={`status-pill ${isOnline ? "online" : ""}`}>
          <span className="status-dot"></span>
          <span>{isOnline ? "Engine Online" : "Waiting..."}</span>
        </div>
      </div>
    </header>
  );
}
