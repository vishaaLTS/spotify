import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import DashboardTab from "./components/DashboardTab";
import ForYouTab from "./components/ForYouTab";
import SimilarSongsTab from "./components/SimilarSongsTab";
import TrendingTab from "./components/TrendingTab";
import EvaluateTab from "./components/EvaluateTab";
import Toast from "./components/Toast";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState("");

  const showToast = (msg, duration = 3000) => {
    setToastMsg(msg);
    setTimeout(() => {
      setToastMsg("");
    }, duration);
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    if (window.innerWidth <= 768) {
      setSidebarOpen(false);
    }
  };

  return (
    <>
      <Sidebar activeTab={activeTab} setActiveTab={handleTabChange} isOpen={sidebarOpen} />
      
      <main className="main-content">
        <Topbar activeTab={activeTab} toggleSidebar={toggleSidebar} />
        
        {activeTab === "dashboard" && <DashboardTab showToast={showToast} />}
        {activeTab === "user-recs" && <ForYouTab showToast={showToast} />}
        {activeTab === "similar-songs" && <SimilarSongsTab showToast={showToast} />}
        {activeTab === "trending" && <TrendingTab showToast={showToast} />}
        {activeTab === "evaluate" && <EvaluateTab showToast={showToast} />}
      </main>

      <Toast message={toastMsg} />
    </>
  );
}

export default App;
