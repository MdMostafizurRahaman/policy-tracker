'use client';
import { useState } from "react";
import GlobeView from "./GlobeView";
import Worldmap from "./Worldmap";

export default function MapToggle() {
  const [view, setView] = useState("globe"); // Default to Globe View

  return (
    <div>
      {/* Toggle Buttons */}
      <div style={{ marginBottom: "20px", textAlign: "center" }}>
        <button
          onClick={() => setView("globe")}
          style={{
            padding: "10px 20px",
            marginRight: "10px",
            backgroundColor: view === "globe" ? "#007BFF" : "#CCC",
            color: "#FFF",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          Globe View
        </button>
        <button
          onClick={() => setView("map")}
          style={{
            padding: "10px 20px",
            backgroundColor: view === "map" ? "#007BFF" : "#CCC",
            color: "#FFF",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          World Map View
        </button>
      </div>

      {/* Render the Selected View */}
      {view === "globe" ? <GlobeView /> : <Worldmap />}
    </div>
  );
}