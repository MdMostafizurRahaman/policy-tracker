// 'use client'

// import { useState } from "react"
// import dynamic from "next/dynamic"
// import WorldMap from "./components/Worldmap.js"
// import PolicySubmissionForm from "./Submission/PolicySubmissionForm.js"

// // Dynamically import GlobeView with SSR disabled
// const GlobeView = dynamic(() => import("./components/GlobeView.js"), { ssr: false })

// export default function HomePage() {
//   const [view, setView] = useState("home") // Options: "home", "worldmap", "globeview", "submission"

//   const renderContent = () => {
//     switch (view) {
//       case "worldmap":
//         return <WorldMap />
//       case "globeview":
//         return <GlobeView />
//       case "submission":
//         return <PolicySubmissionForm />
//       default:
//         return (
//           <div style={{ textAlign: "center", marginTop: "50px" }}>
//             <h2 style={{ fontSize: "28px", color: "#333" }}>Welcome to the Global Policy Tracker</h2>
//             <p style={{ fontSize: "18px", color: "#555", marginTop: "10px" }}>
//               Track and manage global policies with ease. Use the options below to explore the map or submit new policies.
//             </p>
//             <div style={{ marginTop: "30px", display: "flex", justifyContent: "center", gap: "20px" }}>
//               <button
//                 onClick={() => setView("worldmap")}
//                 style={{
//                   padding: "10px 20px",
//                   background: "#007BFF",
//                   color: "#FFF",
//                   border: "none",
//                   borderRadius: "5px",
//                   cursor: "pointer",
//                   fontSize: "16px",
//                   boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
//                 }}
//               >
//                 View World Map
//               </button>
//               <button
//                 onClick={() => setView("globeview")}
//                 style={{
//                   padding: "10px 20px",
//                   background: "#28A745",
//                   color: "#FFF",
//                   border: "none",
//                   borderRadius: "5px",
//                   cursor: "pointer",
//                   fontSize: "16px",
//                   boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
//                 }}
//               >
//                 View Globe
//               </button>
//               <button
//                 onClick={() => setView("submission")}
//                 style={{
//                   padding: "10px 20px",
//                   background: "#FFC107",
//                   color: "#FFF",
//                   border: "none",
//                   borderRadius: "5px",
//                   cursor: "pointer",
//                   fontSize: "16px",
//                   boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
//                 }}
//               >
//                 Submit Policies
//               </button>
//             </div>
//           </div>
//         )
//     }
//   }

//   return (
//     <main style={{ maxWidth: "1000px", margin: "0 auto", padding: "20px" }}>
//       <header style={{ textAlign: "center", marginBottom: "30px" }}>
//         <h1 style={{ fontSize: "36px", color: "#333" }}>Global Policy Tracker</h1>
//         <p style={{ fontSize: "18px", color: "#666" }}>
//           A platform to track, manage, and visualize global digital policies.
//         </p>
//       </header>

//       <section>{renderContent()}</section>
//     </main>
//   )
// }











'use client'

import { useState } from "react"
import dynamic from "next/dynamic"
import WorldMap from "./components/Worldmap.js"
import PolicySubmissionForm from "./Submission/PolicySubmissionForm.js"

// Dynamically import GlobeView with SSR disabled
const GlobeView = dynamic(() => import("./components/GlobeView.js"), { ssr: false })

export default function HomePage() {
  const [view, setView] = useState("home") // Options: "home", "worldmap", "globeview", "submission"

  const navigateBack = () => {
    setView("home")
  }

  // Simple icon components to replace lucide-react
  const BackIcon = () => <span className="icon">←</span>
  const HomeIcon = () => <span className="icon">🏠</span>
  const MapIcon = () => <span className="icon">🗺️</span>
  const GlobeIcon = () => <span className="icon">🌐</span>
  const FileIcon = () => <span className="icon">📄</span>

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
                onClick={() => setView("globeview")}
                className="nav-button globe-button"
              >
                <GlobeIcon />
                View Globe
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
          <GlobeIcon />
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
          <button className={`navbar-link ${view === "globeview" ? "active" : ""}`} onClick={() => setView("globeview")}>
            <GlobeIcon />
            Globe View
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

      <style jsx global>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        
        body {
          background-color: #f5f8fa;
          color: #333;
        }
        
        .app-container {
          display: flex;
          flex-direction: column;
          min-height: 100vh;
        }
        
        .navbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 2rem;
          background-color: #1e3a8a;
          color: white;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          position: sticky;
          top: 0;
          z-index: 100;
        }
        
        .navbar-logo {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 1.2rem;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s ease;
        }
        
        .navbar-logo:hover {
          transform: scale(1.05);
        }
        
        .navbar-links {
          display: flex;
          gap: 1rem;
        }
        
        .navbar-link {
          display: flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.5rem 0.75rem;
          background: transparent;
          color: #e5e7eb;
          border: none;
          border-radius: 0.25rem;
          cursor: pointer;
          font-size: 0.9rem;
          font-weight: 500;
          transition: all 0.2s ease;
        }
        
        .navbar-link:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }
        
        .navbar-link.active {
          background-color: rgba(255, 255, 255, 0.2);
          color: white;
        }
        
        .main-content {
          max-width: 1200px;
          width: 100%;
          margin: 0 auto;
          padding: 1.5rem;
          position: relative;
          flex: 1;
        }
        
        .back-button {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.5rem 1rem;
          background-color: #f3f4f6;
          color: #4b5563;
          border: none;
          border-radius: 0.25rem;
          cursor: pointer;
          font-size: 0.875rem;
          font-weight: 500;
          margin-bottom: 1.5rem;
          transition: all 0.2s ease;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        
        .back-button:hover {
          background-color: #e5e7eb;
          color: #111827;
        }
        
        .page-header {
          text-align: center;
          margin-bottom: 2rem;
          animation: fadeIn 0.5s ease;
        }
        
        .page-title {
          font-size: 2.25rem;
          color: #1e3a8a;
          margin-bottom: 0.5rem;
        }
        
        .page-description {
          font-size: 1.125rem;
          color: #4b5563;
          max-width: 800px;
          margin: 0 auto;
        }
        
        .content-section {
          background-color: white;
          border-radius: 0.5rem;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
          padding: 2rem;
          min-height: 400px;
          animation: slideUp 0.5s ease;
        }
        
        .home-content {
          text-align: center;
        }
        
        .home-title {
          font-size: 1.75rem;
          color: #1e3a8a;
          margin-bottom: 1rem;
        }
        
        .home-description {
          font-size: 1.125rem;
          color: #4b5563;
          margin-bottom: 2rem;
          max-width: 800px;
          margin-left: auto;
          margin-right: auto;
        }
        
        .button-container {
          display: flex;
          justify-content: center;
          gap: 1rem;
          flex-wrap: wrap;
        }
        
        .nav-button {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          padding: 0.75rem 1.5rem;
          color: white;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
          font-size: 1rem;
          font-weight: 500;
          transition: all 0.3s ease;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .worldmap-button {
          background-color: #2563eb;
        }
        
        .worldmap-button:hover {
          background-color: #1d4ed8;
          transform: translateY(-2px);
        }
        
        .globe-button {
          background-color: #10b981;
        }
        
        .globe-button:hover {
          background-color: #059669;
          transform: translateY(-2px);
        }
        
        .submission-button {
          background-color: #f59e0b;
        }
        
        .submission-button:hover {
          background-color: #d97706;
          transform: translateY(-2px);
        }
        
        .icon {
          font-size: 1.2rem;
          display: inline-block;
          margin-right: 0.25rem;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideUp {
          from { 
            opacity: 0;
            transform: translateY(20px);
          }
          to { 
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @media (max-width: 768px) {
          .navbar {
            flex-direction: column;
            padding: 1rem;
          }
          
          .navbar-logo {
            margin-bottom: 0.75rem;
          }
          
          .navbar-links {
            width: 100%;
            justify-content: space-between;
            overflow-x: auto;
            padding-bottom: 0.5rem;
          }
          
          .navbar-link {
            padding: 0.5rem;
            font-size: 0.8rem;
          }
          
          .button-container {
            flex-direction: column;
            gap: 1rem;
            max-width: 300px;
            margin: 0 auto;
          }
          
          .page-title {
            font-size: 1.75rem;
          }
          
          .page-description {
            font-size: 1rem;
          }
        }
      `}</style>
    </div>
  )
}