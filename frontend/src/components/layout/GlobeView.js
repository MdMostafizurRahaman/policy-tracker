'use client'
import Globe from "react-globe.gl"
import { useRef, useState, useEffect } from "react"
import Tooltip from "./Tooltip"

export default function GlobeView({ countries, geoFeatures, onCountryClick }) {
  const globeRef = useRef()
  const [tooltipContent, setTooltipContent] = useState(null)
  const [hoveredCountry, setHoveredCountry] = useState(null)
  
  // Enable auto-rotation
  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.controls().autoRotate = true
      globeRef.current.controls().autoRotateSpeed = 1.5
    }
  }, [])
  
  const handlePolygonHover = (feat) => {
    if (feat) {
      const countryName = feat.properties.name
      const countryData = countries?.[countryName]
      setHoveredCountry(countryName)
      setTooltipContent({
        name: countryName,
        count: countryData?.count || 0,
        color: countryData?.color || "#6b7280",
        total: countryData?.totalPolicies || 0
      })
      if (globeRef.current) {
        globeRef.current.controls().autoRotate = false
      }
    } else {
      setHoveredCountry(null)
      setTooltipContent(null)
      if (globeRef.current) {
        globeRef.current.controls().autoRotate = true
      }
    }
  }
  
  const handlePolygonClick = (feat) => {
    if (!feat) return
    
    const countryName = feat.properties.name
    const countryData = countries?.[countryName]
    
    // Stop auto-rotation when country is clicked
    if (globeRef.current) {
      globeRef.current.controls().autoRotate = false
    }
    
    // Only trigger popup if country has policies
    if (countryData && countryData.count > 0) {
      // Call the parent onCountryClick handler with proper geo object format
      if (onCountryClick) {
        onCountryClick({
          properties: {
            name: countryName
          }
        });
      }
    }
  }
  
  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      height: "100vh",
      width: "100%",
      position: "relative"
    }}>
      <Globe
        ref={globeRef}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        polygonsData={geoFeatures}
        polygonCapColor={(feat) => {
          const name = feat.properties.name
          if (hoveredCountry === name) return "#FFD700" // Highlight color on hover
          const countryData = countries?.[name]
          return countryData?.color || "rgba(200, 200, 200, 0.6)"
        }}
        polygonSideColor={() => "rgba(100, 100, 100, 0.2)"}
        polygonStrokeColor={() => "#111"}
        polygonLabel={({ properties: p }) => {
          const countryData = countries?.[p.name]
          return `
            <div style="
              background: rgba(0,0,0,0.8); 
              color: white; 
              padding: 8px 12px; 
              border-radius: 6px; 
              font-family: sans-serif;
              box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            ">
              <div style="font-weight: bold; margin-bottom: 4px;">${p.name}</div>
              <div style="font-size: 12px;">
                Policy Areas: ${countryData?.count || 0}/10
              </div>
              <div style="font-size: 12px;">
                Total Policies: ${countryData?.totalPolicies || 0}
              </div>
              ${countryData?.count > 0 ? '<div style="font-size: 11px; margin-top: 4px; opacity: 0.8;">Click to view details</div>' : ''}
            </div>
          `
        }}
        onPolygonHover={handlePolygonHover}
        onPolygonClick={handlePolygonClick}
        polygonsTransitionDuration={300}
        polygonAltitude={0.01}
        polygonCapCurvatureResolution={4}
        enablePointerInteraction={true}
      />
      {tooltipContent && (
        <div style={{
          position: "absolute",
          top: "20px",
          left: "20px",
          background: "rgba(0,0,0,0.8)",
          color: "white",
          padding: "12px",
          borderRadius: "8px",
          fontSize: "14px",
          pointerEvents: "none",
          zIndex: 1000,
          fontFamily: "sans-serif"
        }}>
          <div style={{ fontWeight: "bold", marginBottom: "4px" }}>{tooltipContent.name}</div>
          <div>Policy Areas: {tooltipContent.count}/10</div>
          <div>Total Policies: {tooltipContent.total}</div>
        </div>
      )}
    </div>
  )
}