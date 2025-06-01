'use client'
import { useState, useEffect } from "react"
import { ComposableMap, Geographies, Geography } from "react-simple-maps"
import dynamic from "next/dynamic"
import { MessageCircle, X, Maximize2, Minimize2 } from "lucide-react"
import CountryPolicyPopup from "./CountryPolicyPopup"
import PolicyChatAssistant from "../chatBot/PolicyChatAssistant"
import './Worldmap.css'; // Import the external CSS file

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
  
  // Chat-related states
  const [showChat, setShowChat] = useState(false)
  const [chatFullscreen, setChatFullscreen] = useState(false)
  const [chatWidth, setChatWidth] = useState(50) // Percentage width for chat panel

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL|| 'https://policy-tracker-5.onrender.com/api';

  useEffect(() => {
    fetch(`${API_BASE_URL}/countries`)
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
      setSelectedCountry({
        name: countryName,
        color: countryData.color
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

  const handleChatToggle = () => {
    if (chatFullscreen) {
      setChatFullscreen(false)
    }
    setShowChat(!showChat)
  }

  const handleChatFullscreen = () => {
    setChatFullscreen(!chatFullscreen)
    if (!showChat) {
      setShowChat(true)
    }
  }

  const handleChatClose = () => {
    setShowChat(false)
    setChatFullscreen(false)
  }

  return (
    <div className={`worldmap-container ${chatFullscreen ? 'chat-fullscreen' : ''}`}>
      {/* Header Controls */}
      <div className={`worldmap-header ${chatFullscreen ? 'chat-fullscreen' : ''}`}>
        <button 
          onClick={handleViewToggle} 
          className="view-toggle-btn"
        >
          Switch to {viewMode === "map" ? "Globe" : "Map"} View
        </button>
        
        <div className="header-title">
          <h1>AI Policy World Map</h1>
          <p>Explore AI policies and governance frameworks worldwide</p>
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
        <div className={`map-section ${showChat ? 'with-chat' : ''} ${chatFullscreen ? 'chat-fullscreen' : ''}`}>
          {viewMode === "map" && (
            <div className="map-container">
              <ComposableMap projection="geoMercator" style={{ width: "100%", height: "100%" }}>
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
                <div className="tooltip-fixed">
                  <strong>{tooltipContent.name}</strong>
                  <div>Total Policies: {tooltipContent.total}</div>
                </div>
              )}

              {/* Floating Tooltip Near Mouse */}
              {tooltipContent && (
                <div 
                  className="tooltip-floating"
                  style={{
                    top: mousePosition.y + 12,
                    left: mousePosition.x + 12,
                  }}
                >
                  <strong>{tooltipContent.name}</strong><br />
                  Policies: {tooltipContent.total}
                </div>
              )}
            </div>
          )}

          {viewMode === "globe" && (
            <div className="globe-container">
              <GlobeView 
                countries={countries} 
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
              <h3>AI Policy Assistant</h3>
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