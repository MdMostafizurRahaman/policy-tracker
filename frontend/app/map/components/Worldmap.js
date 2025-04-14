'use client'
import { useState, useEffect } from "react"
import { ComposableMap, Geographies, Geography } from "react-simple-maps"
import dynamic from "next/dynamic"

// Dynamically import the GlobeView component
const GlobeView = dynamic(() => import("./GlobeView"), { ssr: false, loading: () => <p>Loading Globe...</p> })

const geoUrl = "/countries-110m.json"

export default function Worldmap() {
  const [viewMode, setViewMode] = useState("map") // State to toggle between map and globe view
  const [countries, setCountries] = useState(null)
  const [geoFeatures, setGeoFeatures] = useState([])
  const [tooltipContent, setTooltipContent] = useState(null)
  const [highlightedCountry, setHighlightedCountry] = useState(null)

  // Fetch policy data for countries
  useEffect(() => {
    fetch("http://localhost:8000/api/countries")
      .then(res => res.json())
      .then(setCountries)
  }, [])

  // Fetch geo data for the countries
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

  const getColor = (totalPolicies) => {
    if (totalPolicies <= 3) return "#FF0000" // 0-3 Policies
    if (totalPolicies <= 7) return "#FFD700" // 4-7 Policies
    return "#00AA00" // 8-10 Policies
  }

  const handleMouseEnter = (geo) => {
    const countryName = geo.properties.name
    const countryData = countries?.[countryName]
    setTooltipContent({
      name: countryName,
      total: countryData?.total_policies || 0
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
                  const fillColor = countryData ? getColor(countryData.total_policies) : "#EEE"

                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={isHighlighted ? "#FFD700" : fillColor}
                      stroke="#FFF"
                      strokeWidth={0.5}
                      onMouseEnter={() => handleMouseEnter(geo)}
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
        </div>
      )}

      {viewMode === "globe" && (
        <GlobeView countries={countries} geoFeatures={geoFeatures} />
      )}
    </div>
  )
}