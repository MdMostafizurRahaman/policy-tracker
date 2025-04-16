'use client'
import { useState, useEffect } from "react"
import { ComposableMap, Geographies, Geography } from "react-simple-maps"
import dynamic from "next/dynamic"

const GlobeView = dynamic(() => import("./GlobeView"), {
  ssr: false,
  loading: () => <p>Loading Globe...</p>,
})

const geoUrl = "/countries-110m.json"

export default function Worldmap() {
  const [viewMode, setViewMode] = useState("map")
  const [countries, setCountries] = useState(null)
  const [geoFeatures, setGeoFeatures] = useState([])
  const [tooltipContent, setTooltipContent] = useState(null)
  const [highlightedCountry, setHighlightedCountry] = useState(null)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

  useEffect(() => {
    fetch("http://localhost:8000/api/countries")
      .then(res => res.json())
      .then(setCountries)
  }, [])

  useEffect(() => {
    fetch(geoUrl)
      .then(res => res.json())
      .then(data => {
        import("topojson-client").then(topojson => {
          const features = topojson.feature(data, data.objects.countries).features
          setGeoFeatures(features)
        })
      })
  }, [])

  const handleMouseEnter = (geo, event) => {
    const countryName = geo.properties.name
    const countryData = countries?.[countryName]

    setTooltipContent({
      name: countryName,
      total: countryData?.total_policies || 0
    })

    setMousePosition({
      x: event.clientX,
      y: event.clientY
    })

    setHighlightedCountry(countryName)
  }

  const handleMouseLeave = () => {
    setTooltipContent(null)
    setHighlightedCountry(null)
  }

  const handleClick = (geo) => {
    const countryName = geo.properties.name
    alert(`You clicked on ${countryName}`)
  }

  const handleViewToggle = () => {
    setViewMode(viewMode === "map" ? "globe" : "map")
  }

  return (
    <div style={{ padding: "20px" }}>
      <h1>Global Policy Implementation Tracker</h1>

      <button onClick={handleViewToggle} style={{ marginBottom: "20px", padding: "10px", cursor: "pointer" }}>
        Switch to {viewMode === "map" ? "Globe" : "Map"} View
      </button>

      {viewMode === "map" && (
        <div style={{ position: "relative" }}>
          <ComposableMap projection="geoMercator" style={{ width: "100%", height: "500px" }}>
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map(geo => {
                  const countryName = geo.properties.name
                  const countryData = countries?.[countryName]
                  const isHighlighted = highlightedCountry === countryName
                  const fillColor = countryData ? countryData.color : "#EEE"

                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={isHighlighted ? "#FFD700" : fillColor}
                      stroke="#FFF"
                      strokeWidth={0.5}
                      onMouseEnter={(event) => handleMouseEnter(geo, event)}
                      onMouseLeave={handleMouseLeave}
                      onClick={() => handleClick(geo)}
                      style={{
                        default: { outline: "none" },
                        hover: { outline: "none" },
                        pressed: { outline: "none" }
                      }}
                    />
                  )
                })
              }
            </Geographies>
          </ComposableMap>

          {/* Fixed Top-Left Tooltip */}
          {tooltipContent && (
            <div style={{
              position: "absolute",
              top: "10px",
              left: "10px",
              background: "rgba(0, 0, 0, 0.7)",
              color: "#FFF",
              padding: "5px 10px",
              borderRadius: "4px",
              pointerEvents: "none"
            }}>
              <strong>{tooltipContent.name}</strong>
              <div>Total Policies: {tooltipContent.total}</div>
            </div>
          )}

          {/* Floating Tooltip Near Mouse */}
          {tooltipContent && (
            <div style={{
              position: "fixed",
              top: mousePosition.y + 12,
              left: mousePosition.x + 12,
              background: "#222",
              color: "#FFF",
              padding: "6px 10px",
              borderRadius: "5px",
              pointerEvents: "none",
              zIndex: 9999,
              fontSize: "13px",
              boxShadow: "0 0 5px rgba(0,0,0,0.3)"
            }}>
              <strong>{tooltipContent.name}</strong><br />
              Policies: {tooltipContent.total}
            </div>
          )}
        </div>
      )}

      {viewMode === "globe" && (
        <GlobeView countries={countries} geoFeatures={geoFeatures} />
      )}
    </div>
  )
}
