// 'use client'
// import { useState, useEffect } from "react"
// import { ComposableMap, Geographies, Geography } from "react-simple-maps"
// import dynamic from "next/dynamic"

// const GlobeView = dynamic(() => import("./GlobeView"), {
//   ssr: false,
//   loading: () => <p>Loading Globe...</p>,
// })

// const geoUrl = "/countries-110m.json"

// export default function Worldmap() {
//   const [viewMode, setViewMode] = useState("map")
//   const [countries, setCountries] = useState(null)
//   const [geoFeatures, setGeoFeatures] = useState([])
//   const [tooltipContent, setTooltipContent] = useState(null)
//   const [highlightedCountry, setHighlightedCountry] = useState(null)
//   const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

//   useEffect(() => {
//     fetch("http://localhost:8000/api/countries")
//       .then(res => res.json())
//       .then(setCountries)
//   }, [])

//   useEffect(() => {
//     fetch(geoUrl)
//       .then(res => res.json())
//       .then(data => {
//         import("topojson-client").then(topojson => {
//           const features = topojson.feature(data, data.objects.countries).features
//           setGeoFeatures(features)
//         })
//       })
//   }, [])

//   const handleMouseEnter = (geo, event) => {
//     const countryName = geo.properties.name
//     const countryData = countries?.[countryName]

//     setTooltipContent({
//       name: countryName,
//       total: countryData?.total_policies || 0
//     })

//     setMousePosition({
//       x: event.clientX,
//       y: event.clientY
//     })

//     setHighlightedCountry(countryName)
//   }

//   const handleMouseLeave = () => {
//     setTooltipContent(null)
//     setHighlightedCountry(null)
//   }

//   const handleClick = (geo) => {
//     const countryName = geo.properties.name
//     alert(`You clicked on ${countryName}`)
//   }

//   const handleViewToggle = () => {
//     setViewMode(viewMode === "map" ? "globe" : "map")
//   }

//   return (
//     <div style={{ padding: "20px" }}>
//       <button onClick={handleViewToggle} style={{ marginBottom: "20px", padding: "10px", cursor: "pointer" }}>
//         Switch to {viewMode === "map" ? "Globe" : "Map"} View
//       </button>

//       {viewMode === "map" && (
//         <div style={{ position: "relative" }}>
//           <ComposableMap projection="geoMercator" style={{ width: "100%", height: "500px" }}>
//             <Geographies geography={geoUrl}>
//               {({ geographies }) =>
//                 geographies.map(geo => {
//                   const countryName = geo.properties.name
//                   const countryData = countries?.[countryName]
//                   const isHighlighted = highlightedCountry === countryName
//                   const fillColor = countryData ? countryData.color : "#EEE"

//                   return (
//                     <Geography
//                       key={geo.rsmKey}
//                       geography={geo}
//                       fill={isHighlighted ? "#FFD700" : fillColor}
//                       stroke="#FFF"
//                       strokeWidth={0.5}
//                       onMouseEnter={(event) => handleMouseEnter(geo, event)}
//                       onMouseLeave={handleMouseLeave}
//                       onClick={() => handleClick(geo)}
//                       style={{
//                         default: { outline: "none" },
//                         hover: { outline: "none" },
//                         pressed: { outline: "none" }
//                       }}
//                     />
//                   )
//                 })
//               }
//             </Geographies>
//           </ComposableMap>

//           {/* Fixed Top-Left Tooltip */}
//           {tooltipContent && (
//             <div style={{
//               position: "absolute",
//               top: "10px",
//               left: "10px",
//               background: "rgba(0, 0, 0, 0.7)",
//               color: "#FFF",
//               padding: "5px 10px",
//               borderRadius: "4px",
//               pointerEvents: "none"
//             }}>
//               <strong>{tooltipContent.name}</strong>
//               <div>Total Policies: {tooltipContent.total}</div>
//             </div>
//           )}

//           {/* Floating Tooltip Near Mouse */}
//           {tooltipContent && (
//             <div style={{
//               position: "fixed",
//               top: mousePosition.y + 12,
//               left: mousePosition.x + 12,
//               background: "#222",
//               color: "#FFF",
//               padding: "6px 10px",
//               borderRadius: "5px",
//               pointerEvents: "none",
//               zIndex: 9999,
//               fontSize: "13px",
//               boxShadow: "0 0 5px rgba(0,0,0,0.3)"
//             }}>
//               <strong>{tooltipContent.name}</strong><br />
//               Policies: {tooltipContent.total}
//             </div>
//           )}
//         </div>
//       )}

//       {viewMode === "globe" && (
//         <GlobeView countries={countries} geoFeatures={geoFeatures} />
//       )}
//     </div>
//   )
// }




















'use client'
import { useState, useEffect } from "react"
import { ComposableMap, Geographies, Geography } from "react-simple-maps"
import dynamic from "next/dynamic"
import CountryPolicyPopup from "./CountryPolicyPopup"

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
  const [selectedCountry, setSelectedCountry] = useState(null)
  const [showPolicyPopup, setShowPolicyPopup] = useState(false)

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
    const countryData = countries?.[countryName]
    
    if (countryData) {
      // Create mock policies for demonstration
      // In a real app, you'd fetch these from your API
      const mockPolicies = [
        {
          id: 1,
          name: "Clean Energy Initiative",
          type: "environmental",
          year: "2022",
          description: "A comprehensive plan to transition to renewable energy sources by 2030, including tax incentives for solar and wind power installation.",
          metrics: [
            "Reduced carbon emissions by 15% since implementation",
            "Created 5,000 new jobs in the renewable sector",
            "Increased renewable energy capacity by 25 gigawatts"
          ]
        },
        {
          id: 2,
          name: "Universal Healthcare Act",
          type: "social",
          year: "2020",
          description: "Legislation providing universal healthcare coverage to all citizens, including preventative care and mental health services.",
          metrics: [
            "Decreased uninsured rate from 12% to 2%",
            "Reduced average healthcare costs by 18%",
            "Improved preventative care participation by 45%"
          ]
        },
        {
          id: 3,
          name: "Digital Economy Tax",
          type: "economic",
          year: "2021",
          description: "New tax framework for digital businesses operating within the country, addressing tax avoidance by multinational tech companies.",
          metrics: [
            "Generated $2.5 billion in additional annual tax revenue",
            "Reduced tax disparity between traditional and digital businesses",
            "Improved compliance rate by 35% among tech companies"
          ]
        },
        {
          id: 4,
          name: "Education Modernization Program",
          type: "social",
          year: "2023",
          description: "A national initiative to update curriculum, improve technology access in schools, and provide teacher development programs.",
          metrics: [
            "Equipped 85% of classrooms with modern technology",
            "Increased graduation rates by 12%",
            "Improved digital literacy scores by 25 points nationally"
          ]
        }
      ];

      setSelectedCountry({
        name: countryName,
        color: countryData.color,
        policies: mockPolicies
      });
      setShowPolicyPopup(true);
    }
  }

  const handleViewToggle = () => {
    setViewMode(viewMode === "map" ? "globe" : "map")
  }

  const handleClosePolicyPopup = () => {
    setShowPolicyPopup(false);
    setSelectedCountry(null);
  }

  return (
    <div style={{ padding: "20px" }}>
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
        <GlobeView 
          countries={countries} 
          geoFeatures={geoFeatures} 
          onCountryClick={handleClick}
        />
      )}

      {showPolicyPopup && selectedCountry && (
        <CountryPolicyPopup 
          country={selectedCountry} 
          policies={selectedCountry.policies}
          onClose={handleClosePolicyPopup}
        />
      )}
    </div>
  )
}