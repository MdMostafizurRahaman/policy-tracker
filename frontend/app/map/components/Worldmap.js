'use client'
import { ComposableMap, Geographies, Geography } from "react-simple-maps"
import { useEffect, useState } from "react"
import Tooltip from "./Tooltip"

const geoUrl = "/countries-110m.json"

export default function WorldMap() {
  const [countries, setCountries] = useState(null)
  const [tooltipContent, setTooltipContent] = useState(null)

  // Load policy data
  useEffect(() => {
    fetch("http://localhost:8000/api/countries")
      .then(res => res.json())
      .then(setCountries)
  }, [])

  return (
    <div style={{ position: "relative" }}>
      <ComposableMap projection="geoMercator">
        <Geographies geography={geoUrl}>
          {({ geographies }) =>
            geographies.map(geo => {
              const countryName = geo.properties.name
              const countryData = countries?.[countryName]
              
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={countryData?.color || "#EEE"}
                  stroke="#FFF"
                  strokeWidth={0.5}
                  onMouseEnter={() => {
                    if (countryData) {
                      setTooltipContent({
                        name: countryName,
                        total: countryData.total_policies,
                        color: countryData.color
                      })
                    }
                  }}
                  onMouseLeave={() => setTooltipContent(null)}
                />
              )
            })
          }
        </Geographies>
      </ComposableMap>
      
      
      {tooltipContent && <Tooltip content={tooltipContent} />}
    </div>
  )
}