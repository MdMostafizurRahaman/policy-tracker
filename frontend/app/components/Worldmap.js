'use client'
import { useState, useEffect, useRef } from "react"
import { ComposableMap, Geographies, Geography } from "react-simple-maps"
import dynamic from "next/dynamic"
import { MessageCircle, X, Maximize2, Minimize2, Search } from "lucide-react"
import CountryPolicyPopup from "./CountryPolicyPopup"
import PolicyChatAssistant from "../chatBot/PolicyChatAssistant"
import './Worldmap.css'

const GlobeView = dynamic(() => import("./GlobeView"), {
  ssr: false,
  loading: () => <p>Loading Globe...</p>,
})

const geoUrl = "/countries-110m.json"

export default function Worldmap() {
  const [viewMode, setViewMode] = useState("map")
  const [countries, setCountries] = useState([])
  const [geoFeatures, setGeoFeatures] = useState([])
  const [masterPolicies, setMasterPolicies] = useState([])
  const [countryStats, setCountryStats] = useState({})
  const [tooltipContent, setTooltipContent] = useState(null)
  const [highlightedCountry, setHighlightedCountry] = useState(null)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [selectedCountry, setSelectedCountry] = useState(null)
  const [showPolicyPopup, setShowPolicyPopup] = useState(false)
  const [searchValue, setSearchValue] = useState("")
  const [searchSuggestions, setSearchSuggestions] = useState([])
  const [filteredCountry, setFilteredCountry] = useState(null)
  // Chat-related states
  const [showChat, setShowChat] = useState(false)
  const [chatFullscreen, setChatFullscreen] = useState(false)
  const [chatWidth, setChatWidth] = useState(50)

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://policy-tracker-5.onrender.com/api'
  const mapRef = useRef(null)
  let tooltipTimeout = useRef(null)

  // Fetch all country names for suggestions
  useEffect(() => {
    fetch(`${API_BASE_URL}/countries`)
      .then(res => res.json())
      .then(data => setCountries(data.countries || []))
  }, [])

  // Fetch geo features
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

  // Fetch admin-approved master policies
  useEffect(() => {
    fetch(`${API_BASE_URL}/admin/master-policies?limit=100`)
      .then(async res => {
        if (!res.ok) {
          const text = await res.text();
          console.error("Failed to fetch policies:", res.status, text);
          return { policies: [] };
        }
        return res.json();
      })
      .then(data => setMasterPolicies(data.policies || []))
      .catch(err => {
        console.error("Fetch error:", err);
        setMasterPolicies([]);
      });
  }, [])

  // Build country stats for coloring
  useEffect(() => {
    if (!masterPolicies.length) return
    // countryStats: { [country]: { approvedAreas: Set, color, count } }
    const stats = {}
    masterPolicies.forEach(policy => {
      const country = policy.country
      const area = policy.policyArea || policy.area_id
      if (!country || !area) return
      if (!stats[country]) stats[country] = { approvedAreas: new Set() }
      // Only count fully approved/active policies
      if (policy.status === "approved" || policy.master_status === "active") {
        stats[country].approvedAreas.add(area)
      }
    })
    Object.keys(stats).forEach(country => {
      const count = stats[country].approvedAreas.size
      if (count >= 8) stats[country].color = "#22c55e" // green
      else if (count >= 4) stats[country].color = "#FFE600" // yellow
      else stats[country].color = "#ef4444" // red
      stats[country].count = count
    })
    setCountryStats(stats)
  }, [masterPolicies])

  // Autocomplete suggestions
  useEffect(() => {
    if (!countries.length) return
    if (!searchValue) setSearchSuggestions([])
    else {
      setSearchSuggestions(
        countries.filter(c =>
          c.toLowerCase().includes(searchValue.toLowerCase())
        ).slice(0, 10)
      )
    }
  }, [searchValue, countries])

  // Handle hover (with flicker fix)
  const handleMouseEnter = (geo, event) => {
    clearTimeout(tooltipTimeout.current)
    const countryName = geo.properties.name
    const stat = countryStats[countryName] || { count: 0, color: "#4B0082" }
    setTooltipContent({
      name: countryName,
      count: stat.count || 0,
      color: stat.color
    })
    setMousePosition({ x: event.clientX, y: event.clientY })
    setHighlightedCountry(countryName)
  }
  const handleMouseLeave = () => {
    tooltipTimeout.current = setTimeout(() => {
      setTooltipContent(null)
      setHighlightedCountry(null)
    }, 120)
  }

  // Handle country search/filter
  const handleCountrySelect = (country) => {
    setFilteredCountry(country)
    setSearchValue(country)
    setHighlightedCountry(country)
    const stat = countryStats[country] || { count: 0, color: "#e5e7eb" }
    setTooltipContent({
      name: country,
      count: stat.count || 0,
      color: stat.color
    })
    setTimeout(() => setTooltipContent(null), 3000)
  }

  const handleClick = (geo) => {
    const countryName = geo.properties.name
    const stat = countryStats[countryName]
    if (stat) {
      setSelectedCountry({
        name: countryName,
        color: stat.color
      })
      setShowPolicyPopup(true)
    }
  }

  const handleViewToggle = () => {
    setViewMode(viewMode === "map" ? "globe" : "map")
  }

  const handleClosePolicyPopup = () => {
    setShowPolicyPopup(false)
    setSelectedCountry(null)
  }

  const handleChatToggle = () => {
    if (chatFullscreen) setChatFullscreen(false)
    setShowChat(!showChat)
  }

  const handleChatFullscreen = () => {
    setChatFullscreen(!chatFullscreen)
    if (!showChat) setShowChat(true)
  }

  const handleChatClose = () => {
    setShowChat(false)
    setChatFullscreen(false)
  }

  function getTooltipPosition(mouseX, mouseY) {
    const tooltipWidth = 220
    const tooltipHeight = 80
    const offset = 16
    if (!mapRef.current) return { top: mouseY + offset, left: mouseX + offset }
    const rect = mapRef.current.getBoundingClientRect()
    let left = mouseX - rect.left + offset
    let top = mouseY - rect.top + offset
    if (left + tooltipWidth > rect.width) left = rect.width - tooltipWidth - 8
    if (top + tooltipHeight > rect.height) top = mouseY - rect.top - tooltipHeight - offset
    if (left < 0) left = 8
    return { top, left, position: "absolute", zIndex: 100 }
  }

  return (
    <div className={`worldmap-container ${chatFullscreen ? 'chat-fullscreen' : ''}`}>
      {/* Header Controls */}
      <div className={`worldmap-header ${chatFullscreen ? 'chat-fullscreen' : ''}`}>
        <button onClick={handleViewToggle} className="view-toggle-btn">
          Switch to {viewMode === "map" ? "Globe" : "Map"} View
        </button>
        <div className="header-title">
          <h1>Policy World Map</h1>
          <p>Explore All policies and governance frameworks worldwide</p>
        </div>
        <div className="country-search">
          <div className="relative">
            <input
              type="text"
              placeholder="Search country..."
              value={searchValue}
              onChange={e => setSearchValue(e.target.value)}
              className="country-search-input"
              autoComplete="off"
            />
            <Search className="absolute right-2 top-2 w-4 h-4 text-gray-400" />
            {searchSuggestions.length > 0 && (
              <ul className="country-suggestions">
                {searchSuggestions.map((c, i) => (
                  <li key={i} onClick={() => handleCountrySelect(c)}>{c}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
        <button
          onClick={handleChatToggle}
          className={`chat-toggle-btn ${showChat ? 'active' : ''} ${chatFullscreen ? 'fullscreen' : ''}`}
        >
          <MessageCircle className="w-4 h-4" />
          {chatFullscreen ? 'Exit Chat' : showChat ? 'Hide Chat' : 'AI Assistant'}
        </button>
      </div>

      {/* Main Content */}
      <div className={`worldmap-content ${showChat ? 'with-chat' : ''} ${chatFullscreen ? 'chat-fullscreen' : ''}`}>
        {/* Map Section */}
        <div className={`map-section ${showChat ? 'with-chat' : ''} ${chatFullscreen ? 'chat-fullscreen' : ''}`} ref={mapRef}>
          {viewMode === "map" && (
            <div className="map-container">
              <ComposableMap projection="geoMercator" style={{ width: "100%", height: "100%" }}>
                <Geographies geography={geoUrl}>
                  {({ geographies }) =>
                    geographies.map(geo => {
                      const countryName = geo.properties.name
                      const stat = countryStats[countryName] || { color: "#F5DEB3", count: 0 }
                      const isHighlighted = highlightedCountry === countryName || filteredCountry === countryName
                      return (
                        <Geography
                          key={geo.rsmKey}
                          geography={geo}
                          fill={stat.color}
                          stroke={isHighlighted ? "#222" : "#FFF"}
                          strokeWidth={isHighlighted ? 2 : 0.5}
                          style={{
                            default: { outline: "none", filter: isHighlighted ? "brightness(1.1)" : "none" },
                            hover: { outline: "none", filter: "brightness(1.15)" },
                            pressed: { outline: "none" }
                          }}
                          onMouseEnter={e => handleMouseEnter(geo, e)}
                          onMouseLeave={handleMouseLeave}
                          onClick={() => handleClick(geo)}
                        />
                      )
                    })
                  }
                </Geographies>
              </ComposableMap>
              {/* Floating Tooltip Near Mouse */}
              {tooltipContent && (
                <div
                  className="tooltip-floating"
                  style={getTooltipPosition(mousePosition.x, mousePosition.y)}
                >
                  <div style={{
                    fontWeight: 700,
                    fontSize: 18,
                    color: tooltipContent.color,
                    marginBottom: 4
                  }}>{tooltipContent.name}</div>
                  <div>
                    <span style={{
                      fontWeight: 600,
                      color: tooltipContent.color
                    }}>
                      Approved Policy Areas: {tooltipContent.count} / 10
                    </span>
                  </div>
                  <div style={{
                    marginTop: 6,
                    fontSize: 13,
                    color: "#555"
                  }}>
                    <span style={{
                      background: tooltipContent.count >= 8 ? "#22c55e" : tooltipContent.count >= 4 ? "#eab308" : "#ef4444",
                      color: "#fff",
                      borderRadius: 6,
                      padding: "2px 8px",
                      fontWeight: 500
                    }}>
                      {tooltipContent.count >= 8 ? "Excellent" : tooltipContent.count >= 4 ? "Moderate" : "Needs Improvement"}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
          {viewMode === "globe" && (
            <div className="globe-container">
              <GlobeView
                countries={countryStats}
                geoFeatures={geoFeatures}
                onCountryClick={handleClick}
              />
            </div>
          )}
        </div>
        {/* Chat Panel */}
        <div className={`chat-panel ${showChat ? 'open' : 'closed'} ${chatFullscreen ? 'fullscreen' : ''}`}>
          {/* Resize Bar */}
          {showChat && !chatFullscreen && (
            <div className="chat-resize-bar"></div>
          )}
          {/* Chat Header */}
          {showChat && (
            <div className="chat-panel-header">
              <h3>Policy Assistant</h3>
              <div className="chat-header-controls">
                <button
                  onClick={handleChatFullscreen}
                  className="chat-fullscreen-btn"
                  title={chatFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                >
                  {chatFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
                <button
                  onClick={handleChatClose}
                  className="chat-close-btn"
                  title="Close Chat"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
          {/* Chat Content */}
          {showChat && (
            <div className="chat-panel-content">
              <PolicyChatAssistant />
            </div>
          )}
          {/* Status Indicator */}
          {showChat && (
            <div className="chat-status-indicator">
              <div className="chat-status-dot"></div>
              Chat Active
            </div>
          )}
        </div>
      </div>
      {/* Policy Popup */}
      {showPolicyPopup && selectedCountry && (
        <CountryPolicyPopup
          country={selectedCountry}
          onClose={handleClosePolicyPopup}
        />
      )}
    </div>
  )
}