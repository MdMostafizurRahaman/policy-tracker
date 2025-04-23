'use client'

import { useState } from "react"
import dynamic from "next/dynamic"
import WorldMap from "./components/Worldmap.js"
import PolicySubmissionForm from "./Submission/PolicySubmissionForm.js"

// Dynamically import GlobeView with SSR disabled
const GlobeView = dynamic(() => import("./components/GlobeView.js"), { ssr: false })

export default function HomePage() {
  const [view, setView] = useState("home") // Options: "home", "worldmap", "globeview", "submission"

  const renderContent = () => {
    switch (view) {
      case "worldmap":
        return <WorldMap />
      case "globeview":
        return <GlobeView />
      case "submission":
        return <PolicySubmissionForm />
      default:
        return (
          <div style={{ textAlign: "center", marginTop: "50px" }}>
            <h2 style={{ fontSize: "28px", color: "#333" }}>Welcome to the Global Policy Tracker</h2>
            <p style={{ fontSize: "18px", color: "#555", marginTop: "10px" }}>
              Track and manage global policies with ease. Use the options below to explore the map or submit new policies.
            </p>
            <div style={{ marginTop: "30px", display: "flex", justifyContent: "center", gap: "20px" }}>
              <button
                onClick={() => setView("worldmap")}
                style={{
                  padding: "10px 20px",
                  background: "#007BFF",
                  color: "#FFF",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                  fontSize: "16px",
                  boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
                }}
              >
                View World Map
              </button>
              <button
                onClick={() => setView("globeview")}
                style={{
                  padding: "10px 20px",
                  background: "#28A745",
                  color: "#FFF",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                  fontSize: "16px",
                  boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
                }}
              >
                View Globe
              </button>
              <button
                onClick={() => setView("submission")}
                style={{
                  padding: "10px 20px",
                  background: "#FFC107",
                  color: "#FFF",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                  fontSize: "16px",
                  boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
                }}
              >
                Submit Policies
              </button>
            </div>
          </div>
        )
    }
  }

  return (
    <main style={{ maxWidth: "1000px", margin: "0 auto", padding: "20px" }}>
      <header style={{ textAlign: "center", marginBottom: "30px" }}>
        <h1 style={{ fontSize: "36px", color: "#333" }}>Global Policy Tracker</h1>
        <p style={{ fontSize: "18px", color: "#666" }}>
          A platform to track, manage, and visualize global digital policies.
        </p>
      </header>

      <section>{renderContent()}</section>
    </main>
  )
}