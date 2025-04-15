'use client'
import Globe from "react-globe.gl"
import { useRef, useState, useEffect } from "react"
import Tooltip from "./Tooltip"

export default function GlobeView({ countries, geoFeatures }) {
  const globeRef = useRef()
  const [tooltipContent, setTooltipContent] = useState(null)

  // Enable auto-rotation on mount
  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.controls().autoRotate = true
      globeRef.current.controls().autoRotateSpeed = 1.5 // Adjust rotation speed
    }
  }, [])

  const handlePolygonHover = (feat) => {
    if (feat) {
      const countryName = feat.properties.name
      const countryData = countries?.[countryName]
      setTooltipContent({
        name: countryName,
        total: countryData?.total_policies || 0
      })
      // Stop rotation on hover
      globeRef.current.controls().autoRotate = false
    } else {
      setTooltipContent(null)
      // Resume rotation when not hovering
      globeRef.current.controls().autoRotate = true
    }
  }

  const handlePolygonClick = (feat) => {
    const countryName = feat.properties.name
    alert(`You clicked on ${countryName}`)
    // Stop rotation on click
    globeRef.current.controls().autoRotate = false
  }

  const getColor = (totalPolicies) => {
    if (totalPolicies <= 3) return "#FF0000" // 0-3 Policies
    if (totalPolicies <= 7) return "#FFD700" // 4-7 Policies
    return "#00AA00" // 8-10 Policies
  }

  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      height: "100vh", // Full viewport height
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
          const countryData = countries?.[name]
          if (!countryData) return "rgba(200, 200, 200, 0.6)"
          return getColor(countryData.total_policies)
        }}
        polygonSideColor={() => "rgba(100, 100, 100, 0.2)"}
        polygonStrokeColor={() => "#111"}
        polygonLabel={({ properties: p }) => `
          <b>${p.name}</b><br />
          ${countries?.[p.name]?.total_policies ?? "N/A"} policies
        `}
        onPolygonHover={handlePolygonHover}
        onPolygonClick={handlePolygonClick}
        polygonsTransitionDuration={300}
      />

      {tooltipContent && (
        <Tooltip content={tooltipContent} /> 
      )}
    </div>
  )
}