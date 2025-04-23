'use client'

import { useState } from "react"
import dynamic from "next/dynamic"
import WorldMap from "./components/Worldmap.js"
import PolicySubmissionForm from "./Submission/PolicySubmissionForm.js"

// Dynamically import GlobeView with SSR disabled
const GlobeView = dynamic(() => import("./components/GlobeView.js"), { ssr: false })

import './page.css'

export default function HomePage() {
  const [view, setView] = useState("home") // Options: "home", "worldmap", "submission", "globeview"

  const navigateBack = () => {
    setView("home")
  }

  // Simple icon components to replace lucide-react
  const BackIcon = () => <span className="icon">←</span>
  const HomeIcon = () => <span className="icon">🏠</span>
  const MapIcon = () => <span className="icon">🗺️</span>
  const FileIcon = () => <span className="icon">📄</span>

  const renderContent = () => {
    switch (view) {
      case "worldmap":
        return (
          <div>
            <WorldMap />
            <button
              className="switch-button globe-button"
              onClick={() => setView("globeview")}
            >
              Switch to Globe View
            </button>
          </div>
        )
      case "globeview":
        return <GlobeView />
      case "submission":
        return <PolicySubmissionForm />
      default:
        return (
          <div className="home-content">
            <h2 className="home-title">Welcome to the Global Policy Tracker</h2>
            <p className="home-description">
              Track and manage global policies with ease. Use the options below to explore the map or submit new policies.
            </p>
            <div className="button-container">
              <button
                onClick={() => setView("worldmap")}
                className="nav-button worldmap-button"
              >
                <MapIcon />
                View World Map
              </button>
              <button
                onClick={() => setView("submission")}
                className="nav-button submission-button"
              >
                <FileIcon />
                Submit Policies
              </button>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="navbar-logo" onClick={() => setView("home")}>
          <span>Global Policy Tracker</span>
        </div>
        <div className="navbar-links">
          <button className={`navbar-link ${view === "home" ? "active" : ""}`} onClick={() => setView("home")}>
            <HomeIcon />
            Home
          </button>
          <button className={`navbar-link ${view === "worldmap" ? "active" : ""}`} onClick={() => setView("worldmap")}>
            <MapIcon />
            World Map
          </button>
          <button className={`navbar-link ${view === "submission" ? "active" : ""}`} onClick={() => setView("submission")}>
            <FileIcon />
            Submit Policy
          </button>
        </div>
      </nav>

      <main className="main-content">
        {view !== "home" && (
          <button className="back-button" onClick={navigateBack}>
            <BackIcon />
            Back to Home
          </button>
        )}
        
        <header className="page-header">
          <h1 className="page-title">
            {view === "home" ? "Global Policy Tracker" : 
             view === "worldmap" ? "World Map View" :
             view === "globeview" ? "Interactive Globe View" : "Policy Submission"}
          </h1>
          <p className="page-description">
            {view === "home" ? "A platform to track, manage, and visualize global digital policies." :
             view === "worldmap" ? "Explore policies across different regions." :
             view === "globeview" ? "Interactive 3D visualization of global policies." :
             "Submit new policies to our database."}
          </p>
        </header>

        <section className="content-section">
          {renderContent()}
        </section>
      </main>
    </div>
  )
}