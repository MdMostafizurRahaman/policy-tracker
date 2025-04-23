// 'use client'
// import Globe from "react-globe.gl"
// import { useRef, useState, useEffect } from "react"
// import Tooltip from "./Tooltip"

// export default function GlobeView({ countries, geoFeatures }) {
//   const globeRef = useRef()
//   const [tooltipContent, setTooltipContent] = useState(null)
//   const [hoveredCountry, setHoveredCountry] = useState(null)

//   // Enable auto-rotation
//   useEffect(() => {
//     if (globeRef.current) {
//       globeRef.current.controls().autoRotate = true
//       globeRef.current.controls().autoRotateSpeed = 1.5
//     }
//   }, [])

//   const handlePolygonHover = (feat) => {
//     if (feat) {
//       const countryName = feat.properties.name
//       const countryData = countries?.[countryName]
//       setHoveredCountry(countryName)
//       setTooltipContent({
//         name: countryName,
//         total: countryData?.total_policies || 0
//       })
//       globeRef.current.controls().autoRotate = false
//     } else {
//       setHoveredCountry(null)
//       setTooltipContent(null)
//       globeRef.current.controls().autoRotate = true
//     }
//   }

//   const handlePolygonClick = (feat) => {
//     const countryName = feat.properties.name
//     alert(`You clicked on ${countryName}`)
//     globeRef.current.controls().autoRotate = false
//   }

//   return (
//     <div style={{
//       display: "flex",
//       justifyContent: "center",
//       alignItems: "center",
//       height: "100vh",
//       width: "100%",
//       position: "relative"
//     }}>
//       <Globe
//         ref={globeRef}
//         globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
//         backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
//         polygonsData={geoFeatures}
//         polygonCapColor={(feat) => {
//           const name = feat.properties.name
//           if (hoveredCountry === name) return "#FFD700" // Highlight color on hover
//           const countryData = countries?.[name]
//           return countryData ? countryData.color : "rgba(200, 200, 200, 0.6)"
//         }}
//         polygonSideColor={() => "rgba(100, 100, 100, 0.2)"}
//         polygonStrokeColor={() => "#111"}
//         polygonLabel={({ properties: p }) => `
//           <b>${p.name}</b><br />
//           ${countries?.[p.name]?.total_policies ?? "N/A"} policies
//         `}
//         onPolygonHover={handlePolygonHover}
//         onPolygonClick={handlePolygonClick}
//         polygonsTransitionDuration={300}
//       />

//       {tooltipContent && (
//         <Tooltip content={tooltipContent} />
//       )}
//     </div>
//   )
// }

























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
        total: countryData?.total_policies || 0
      })
      globeRef.current.controls().autoRotate = false
    } else {
      setHoveredCountry(null)
      setTooltipContent(null)
      globeRef.current.controls().autoRotate = true
    }
  }
  
  const handlePolygonClick = (feat) => {
    const countryName = feat.properties.name
    globeRef.current.controls().autoRotate = false
    
    // Call the parent onCountryClick handler with the geo object
    if (onCountryClick) {
      onCountryClick({
        properties: {
          name: countryName
        }
      });
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
          return countryData ? countryData.color : "rgba(200, 200, 200, 0.6)"
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