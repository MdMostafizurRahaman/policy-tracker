'use client'
import { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import WorldMap from "./components/Worldmap.js"
import PolicySubmissionForm from "./Submission/PolicySubmissionForm.js"
import AdminPanel from "./admin/AdminDashboard.js"
import './page.css'
// Dynamically import GlobeView with SSR disabled
const GlobeView = dynamic(() => import("./components/GlobeView.js"), { ssr: false })

export default function Page() {
  const [view, setView] = useState("home") 
  const [theme, setTheme] = useState("purple") // Default theme
  const [animate, setAnimate] = useState(false)
  
  // Available themes: purple, blue, green, orange, pink
  const themes = {
    purple: {
      primary: "#7c3aed",
      secondary: "#a78bfa",
      accent: "#8b5cf6",
      background: "linear-gradient(135deg, #c4b5fd 0%, #ddd6fe 100%)",
      text: "#4c1d95"
    },
    blue: {
      primary: "#2563eb",
      secondary: "#60a5fa",
      accent: "#3b82f6", 
      background: "linear-gradient(135deg, #93c5fd 0%, #bfdbfe 100%)",
      text: "#1e3a8a"
    },
    green: {
      primary: "#10b981",
      secondary: "#6ee7b7",
      accent: "#34d399",
      background: "linear-gradient(135deg, #a7f3d0 0%, #d1fae5 100%)",
      text: "#065f46"
    },
    orange: {
      primary: "#f59e0b",
      secondary: "#fcd34d",
      accent: "#fbbf24",
      background: "linear-gradient(135deg, #fde68a 0%, #fef3c7 100%)",
      text: "#92400e"
    },
    pink: {
      primary: "#ec4899",
      secondary: "#f9a8d4",
      accent: "#f472b6",
      background: "linear-gradient(135deg, #fbcfe8 0%, #fce7f3 100%)",
      text: "#9d174d"
    }
  }
  
  // Cycle through themes
  const cycleTheme = () => {
    const themeKeys = Object.keys(themes)
    const currentIndex = themeKeys.indexOf(theme)
    const nextIndex = (currentIndex + 1) % themeKeys.length
    setTheme(themeKeys[nextIndex])
  }
  
  useEffect(() => {
    // Trigger animation when theme changes
    setAnimate(true)
    const timeoutId = setTimeout(() => setAnimate(false), 500)
    return () => clearTimeout(timeoutId)
  }, [theme])
  
  const navigateBack = () => {
    setView("home")
  }
  
  // Enhanced icon components with theme colors
  const BackIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 12H5M12 19l-7-7 7-7"/>
    </svg>
  )
  
  const HomeIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
      <polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
  )
  
  const MapIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
      <line x1="8" y1="2" x2="8" y2="18"/>
      <line x1="16" y1="6" x2="16" y2="22"/>
    </svg>
  )
  
  const FileIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10 9 9 9 8 9"/>
    </svg>
  )
  
  const AdminIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>
  )
  
  const GlobeIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
  )
  
  const PaletteIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="13.5" cy="6.5" r="2.5"/>
      <circle cx="17.5" cy="10.5" r="2.5"/>
      <circle cx="8.5" cy="7.5" r="2.5"/>
      <circle cx="6.5" cy="12.5" r="2.5"/>
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>
    </svg>
  )
  
  const renderContent = () => {
    switch (view) {
      case "worldmap":
        return (
          <div className="content-card">
            <WorldMap />
          </div>
        );
      case "globeview":
        return (
          <div className="content-card">
            <GlobeView />
          </div>
        );
      case "submission":
        return (
          <div className="content-card">
            <PolicySubmissionForm />
          </div>
        );
      case "admin":
        return (
          <div className="content-card">
            <AdminPanel />
          </div>
        );
      default:
        return (
          <div className={`home-content ${animate ? 'animate-fade-in' : ''}`}>
            <h1 className="home-title">
              <span className="gradient-text">Global Policy Tracker</span>
            </h1>
            <div className="hero-container">
              <div className="hero-content">
                <p className="home-description">
                  Track and manage global policies with our interactive visualization tools. 
                  Explore geopolitical trends, submit new policies, and gain valuable insights 
                  into regulatory landscapes around the world.
                </p>
                
                <div className="features-grid">
                  <div className="feature-card">
                    <div className="feature-icon">
                      <MapIcon />
                    </div>
                    <h3>Interactive Maps</h3>
                    <p>Visualize policies geographically</p>
                  </div>
                  
                  <div className="feature-card">
                    <div className="feature-icon">
                      <GlobeIcon />
                    </div>
                    <h3>3D Globe View</h3>
                    <p>Experience global data in an immersive way</p>
                  </div>
                  
                  <div className="feature-card">
                    <div className="feature-icon">
                      <FileIcon />
                    </div>
                    <h3>Policy Database</h3>
                    <p>Access and submit comprehensive policy information</p>
                  </div>
                </div>
                
                <div className="button-container">
                  <button
                    onClick={() => setView("worldmap")}
                    className="nav-button worldmap-button"
                    style={{backgroundColor: themes[theme].primary}}
                  >
                    <MapIcon />
                    <span>View World Map</span>
                  </button>
                  
                  {/* <button
                    onClick={() => setView("globeview")}
                    className="nav-button globe-button"
                    style={{backgroundColor: themes[theme].accent}}
                  >
                    <GlobeIcon />
                    <span>Explore 3D Globe</span>
                  </button> */}
                  
                  <button
                    onClick={() => setView("submission")}
                    className="nav-button submission-button"
                    style={{backgroundColor: themes[theme].secondary}}
                  >
                    <FileIcon />
                    <span>Submit Policy</span>
                  </button>
                </div>
              </div>
              
              <div className="globe-decoration">
                <div className="globe-sphere">
                  <div className="meridian"></div>
                  <div className="meridian"></div>
                  <div className="meridian"></div>
                  <div className="meridian"></div>
                  <div className="equator"></div>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };
  
  return (
    <div 
      className="app-container"
      style={{
        backgroundColor: view === "home" ? "#f8fafc" : "#ffffff"
      }}
    >
      <nav 
        className={`navbar ${view === "home" ? "navbar-transparent" : ""}`}
        style={{
          background: view === "home" ? "transparent" : themes[theme].background,
          boxShadow: view === "home" ? "none" : "0 4px 6px rgba(0, 0, 0, 0.1)"
        }}
      >
        <div 
          className="navbar-logo" 
          onClick={() => setView("home")}
          style={{color: themes[theme].text}}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" 
            stroke={themes[theme].primary} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2a4.5 4.5 0 0 0 0 9 4.5 4.5 0 0 1 0 9 4.5 4.5 0 1 0 0-9 4.5 4.5 0 1 1 0-9z" />
            <line x1="2" y1="12" x2="22" y2="12"/>
          </svg>
          <span>Global Policy Tracker</span>
        </div>
        
        <div className="navbar-links">
          <button 
            className={`navbar-link ${view === "home" ? "active" : ""}`} 
            onClick={() => setView("home")}
            style={{
              backgroundColor: view === "home" ? themes[theme].primary : "transparent",
              color: view === "home" ? "white" : themes[theme].text
            }}
          >
            <HomeIcon />
            <span>Home</span>
          </button>
          
          <button 
            className={`navbar-link ${view === "worldmap" ? "active" : ""}`} 
            onClick={() => setView("worldmap")}
            style={{
              backgroundColor: view === "worldmap" ? themes[theme].primary : "transparent",
              color: view === "worldmap" ? "white" : themes[theme].text
            }}
          >
            <MapIcon />
            <span>World Map</span>
          </button>
          
          <button 
            className={`navbar-link ${view === "submission" ? "active" : ""}`} 
            onClick={() => setView("submission")}
            style={{
              backgroundColor: view === "submission" ? themes[theme].primary : "transparent",
              color: view === "submission" ? "white" : themes[theme].text
            }}
          >
            <FileIcon />
            <span>Submit</span>
          </button>
          
          <button 
            className={`navbar-link ${view === "admin" ? "active" : ""}`} 
            onClick={() => setView("admin")}
            style={{
              backgroundColor: view === "admin" ? themes[theme].primary : "transparent",
              color: view === "admin" ? "white" : themes[theme].text
            }}
          >
            <AdminIcon />
            <span>Admin</span>
          </button>
          
          <button
            className={`navbar-link ${view === "theme" ? "active" : ""}`}
            onClick={cycleTheme}
            style={{
              backgroundColor: view === "theme" ? themes[theme].primary : "transparent",
              color: view === "theme" ? "white" : themes[theme].text
            }}
          >
            <PaletteIcon />
            <span>Theme</span>
          </button>
        </div>
      </nav>
      
      <main className={`main-content ${view !== "home" ? "inner-page" : ""}`}>
        {view !== "home" && (
          <button 
            className="back-button" 
            onClick={navigateBack}
            style={{
              backgroundColor: "#f3f4f6",
              color: themes[theme].text
            }}
          >
            <BackIcon />
            <span>Back to Home</span>
          </button>
        )}
        
        {renderContent()}
      </main>
      
      <footer className="app-footer" style={{backgroundColor: themes[theme].primary, color: "#fff"}}>
        <div className="footer-content">
          <div className="footer-logo">
            <span style={{color: "white"}}>Global Policy Tracker</span>
          </div>
          <div className="footer-links">
            <a href="#" className="footer-link">About</a>
            <a href="#" className="footer-link">Contact</a>
            <a href="#" className="footer-link">API</a>
            <a href="#" className="footer-link">Privacy</a>
          </div>
        </div>
        <div className="footer-copyright">
          <p>© {new Date().getFullYear()} Global Policy Tracker. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

// Add this CSS directly in the file (or import it from an external file)


