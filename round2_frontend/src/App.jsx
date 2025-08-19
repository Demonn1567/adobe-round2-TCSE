import "./App.css";
import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import Navbar from "./components/navbar/Navbar";
import Hero from "./components/hero/Hero";
import UploadModal from "./components/modals/UploadModal.jsx";

import Home from "./pages/Home.jsx";


import { useEffect } from "react";
function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}



function App() {
  const location = useLocation();
  const [showUpload, setShowUpload] = useState(false);

  const handleStartSession = () => setShowUpload(true);
  const handleWatchDemo = () => {
    window.open(
      "https://www.youtube.com/results?search_query=pdf+insights+demo",
      "_blank"
    );
  };

  const isHome = location.pathname === "/";

  return (
    <>
      <div className="mainContainer">
        <ScrollToTop/>
        <div className="navHeroContainer">
          <Navbar />

          {isHome ? (
            <>
              {/* <Hero
                onStartSession={handleStartSession}
                onWatchDemo={handleWatchDemo}
              /> */}

              <div className="heroParent">
                  <Hero/>
              </div>

              <Home />
            </>
          ) : (
            <Outlet />
          )}
        </div>
      </div>

      <UploadModal open={showUpload} onClose={() => setShowUpload(false)} />
    </>
  );
}

export default App;
