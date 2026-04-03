import React from "react";

export default function Sidebar({ activeTab, setActiveTab, isOpen }) {
  const tabs = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
      ),
    },
    {
      id: "user-recs",
      label: "For You",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      ),
    },
    {
      id: "similar-songs",
      label: "Similar Songs",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 18V5l12-2v13" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </svg>
      ),
    },
    {
      id: "trending",
      label: "Trending",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
          <polyline points="16 7 22 7 22 13" />
        </svg>
      ),
    },
    {
      id: "evaluate",
      label: "Metrics",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      ),
    },
  ];

  return (
    <nav className={`sidebar ${isOpen ? "open" : ""}`} id="sidebar">
      <div className="sidebar-logo">
        <svg className="logo-icon" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="11" fill="#1DB954" opacity="0.15" />
          <path d="M7 17c2.5-1.5 6-1.8 8.5-.5" stroke="#1DB954" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M6 13c3-2 7.5-2.2 10-.5" stroke="#1DB954" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M5 9c3.5-2.5 9-2.8 12-.8" stroke="#1DB954" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <span className="logo-text">Music</span>
      </div>

      <div className="sidebar-menu">
        {tabs.map((tab) => (
          <a
            key={tab.id}
            href="#"
            className={`nav-item ${activeTab === tab.id ? "active" : ""}`}
            onClick={(e) => {
              e.preventDefault();
              setActiveTab(tab.id);
            }}
          >
            {tab.icon}
            {tab.label}
          </a>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="engine-badge">
          <span className="badge-dot"></span>
          Engine Online
        </div>
      </div>
    </nav>
  );
}
