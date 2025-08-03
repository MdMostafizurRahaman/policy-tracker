'use client'
import React, { useState, useEffect, useRef, useMemo, useCallback } from "react"
import { ComposableMap, Geographies, Geography } from "react-simple-maps"
import dynamic from "next/dynamic"
import { Search } from "lucide-react"
import CountryPolicyPopup from "./CountryPolicyPopup"
import { useMapData } from '../../context/MapDataContext'
import '../../styles/Worldmap.css'

// Country name mapping to normalize database names to geojson names
const COUNTRY_NAME_MAP = {
  // United States variants
  'USA': 'United States of America',
  'United States': 'United States of America',
  'US': 'United States of America',
  
  // Spelling corrections
  'Bagngladesh': 'Bangladesh',
  'Bagnngladesh': 'Bangladesh', 
  'Soudi Arabia': 'Saudi Arabia',
  
  // Case corrections
  'india': 'India',
  
  // UAE variants
  'UAE': 'United Arab Emirates',
  
  // Direct mappings (ensure consistency)
  'India': 'India',
  'China': 'China', 
  'Pakistan': 'Pakistan',
  'Nepal': 'Nepal',
  'Russia': 'Russia',
  'Mongolia': 'Mongolia',
  'Canada': 'Canada',
  'Brazil': 'Brazil',
  'Germany': 'Germany',
  'Greenland': 'Greenland',
  'Saudi Arabia': 'Saudi Arabia',
  'Bangladesh': 'Bangladesh',
  'Argentina': 'Argentina',
  'Australia': 'Australia',
  'Bulgaria': 'Bulgaria',
  'Chile': 'Chile',
  'Colombia': 'Colombia',
  'Egypt': 'Egypt',
  'Estonia': 'Estonia',
  'Italy': 'Italy',
  'Kenya': 'Kenya',
  'Mexico': 'Mexico',
  'Nigeria': 'Nigeria',
  'Somalia': 'Somalia',
  'Sweden': 'Sweden',
  'Iran': 'Iran',
  'United Arab Emirates': 'United Arab Emirates'
};

// Policy area name mapping to normalize different formats
const POLICY_AREA_MAP = {
  'ai-safety': 'AI Safety',
  'cyber-safety': 'CyberSafety', 
  'digital-education': 'Digital Education',
  'digital-inclusion': 'Digital Inclusion',
  'digital-work': 'Digital Work',
  'mental-health': 'Mental Health',
  'physical-health': 'Physical Health',
  'social-media-gaming': 'Social Media/Gaming Regulation',
  'disinformation': '(Dis)Information',
  'AI Safety': 'AI Safety',
  'CyberSafety': 'CyberSafety',
  'Digital Education': 'Digital Education',
  'Digital Inclusion': 'Digital Inclusion',
  'Digital Work': 'Digital Work',
  'Mental Health': 'Mental Health',
  'Physical Health': 'Physical Health',
  'Social Media/Gaming Regulation': 'Social Media/Gaming Regulation',
  '(Dis)Information': '(Dis)Information',
  'Digital Leisure': 'Digital Leisure'
};

// Reverse mapping: from geojson/display names to database names
const DATABASE_COUNTRY_MAP = {
  'United States of America': 'United States',
  'United States': 'United States',
  'USA': 'United States',
  'US': 'United States'
};

function normalizeCountryName(countryName) {
  if (!countryName) return null;
  
  // First try exact match
  if (COUNTRY_NAME_MAP[countryName]) {
    return COUNTRY_NAME_MAP[countryName];
  }
  
  // Try case-insensitive match
  const lowerName = countryName.toLowerCase();
  for (const [key, value] of Object.entries(COUNTRY_NAME_MAP)) {
    if (key.toLowerCase() === lowerName) {
      return value;
    }
  }
  
  // Return original if no mapping found
  return countryName;
}

function getDatabaseCountryName(displayCountryName) {
  if (!displayCountryName) return null;
  
  // First try exact match
  if (DATABASE_COUNTRY_MAP[displayCountryName]) {
    return DATABASE_COUNTRY_MAP[displayCountryName];
  }
  
  // Try case-insensitive match
  const lowerName = displayCountryName.toLowerCase();
  for (const [key, value] of Object.entries(DATABASE_COUNTRY_MAP)) {
    if (key.toLowerCase() === lowerName) {
      return value;
    }
  }
  
  // Return original if no mapping found
  return displayCountryName;
}

function normalizePolicyArea(areaName) {
  if (!areaName) return null;
  
  // Trim whitespace
  const trimmed = areaName.trim();
  
  // Try exact match first
  if (POLICY_AREA_MAP[trimmed]) {
    return POLICY_AREA_MAP[trimmed];
  }
  
  // Try case-insensitive match
  const lowerName = trimmed.toLowerCase();
  for (const [key, value] of Object.entries(POLICY_AREA_MAP)) {
    if (key.toLowerCase() === lowerName) {
      return value;
    }
  }
  
  // Return original if no mapping found
  return trimmed;
}

const GlobeView = dynamic(() => import("./GlobeView"), {
  ssr: false,
  loading: () => <p>Loading Globe...</p>,
})

const geoUrl = "/countries-110m.json"

function Worldmap({ viewMode: propViewMode }) {
  // Get map data from context
  const { 
    countries, 
    geoFeatures, 
    masterPolicies, 
    mapStats, 
    isLoaded, 
    isLoading, 
    fetchMapData 
  } = useMapData()

  const [viewMode, setViewMode] = useState(propViewMode || "map")
  const [countryStats, setCountryStats] = useState({})
  const [tooltipContent, setTooltipContent] = useState(null)
  const [highlightedCountry, setHighlightedCountry] = useState(null)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [selectedCountry, setSelectedCountry] = useState(null)
  const [showPolicyPopup, setShowPolicyPopup] = useState(false)
  const [searchValue, setSearchValue] = useState("")
  const [searchSuggestions, setSearchSuggestions] = useState([])
  const [filteredCountry, setFilteredCountry] = useState(null)

  const mapRef = useRef(null)
  let tooltipTimeout = useRef(null)

  // Fetch data when component mounts if not already loaded
  useEffect(() => {
    if (!isLoaded && !isLoading) {
      console.log('�️ WorldMap mounting - fetching data via context')
      fetchMapData()
    } else if (isLoaded) {
      console.log('�️ WorldMap mounting - using cached data from context')
    }
  }, [isLoaded, isLoading, fetchMapData])

  // Sync viewMode with prop
  useEffect(() => {
    if (propViewMode) {
      setViewMode(propViewMode)
    }
  }, [propViewMode])

  // Add keyboard and click handlers to hide tooltip
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && tooltipContent) {
        setTooltipContent(null)
        setHighlightedCountry(null)
      }
    }

    const handleClickOutside = (e) => {
      // Hide tooltip when clicking outside the map
      if (tooltipContent && mapRef.current && !mapRef.current.contains(e.target)) {
        setTooltipContent(null)
        setHighlightedCountry(null)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('click', handleClickOutside)
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('click', handleClickOutside)
    }
  }, [tooltipContent])

  // Memoized country statistics calculation using API color data
  const countryStatsData = useMemo(() => {
    console.log('🔍 Building country stats from API color data. Countries loaded:', countries.length);
    
    if (!countries.length) {
      console.log('⚠️ No countries data loaded yet, returning empty stats');
      return {};
    }
    
    const stats = {};
    
    // Process countries data from API which already includes colors
    countries.forEach((countryData) => {
      const rawCountry = countryData.country;
      
      if (!rawCountry) {
        console.warn('Country data missing country name:', countryData);
        return;
      }
      
      // Normalize country name for geojson matching
      const normalizedCountry = normalizeCountryName(rawCountry);
      if (!normalizedCountry) return;
      
      // Convert API color names to hex colors for the map
      let hexColor = "#d1d5db"; // Default gray
      switch(countryData.color) {
        case 'green':
          hexColor = "#22c55e";
          break;
        case 'yellow':
          hexColor = "#eab308";
          break;
        case 'red':
          hexColor = "#ef4444";
          break;
        case 'gray':
        default:
          hexColor = "#d1d5db";
          break;
      }
      
      stats[normalizedCountry] = {
        count: countryData.area_points || 0,
        totalPolicies: countryData.total_approved_policies || 0,
        approvedAreas: new Set(countryData.areas_with_approved_policies || []),
        color: hexColor,
        level: countryData.level || 'no_approved_areas',
        areas_detail: countryData.areas_detail || [],
        policies: [], // Will be populated from areas_detail if needed
        originalPolicies: []
      };
      
      // Extract policies from areas_detail for popup compatibility
      if (countryData.areas_detail) {
        countryData.areas_detail.forEach(area => {
          if (area.approved_policies) {
            area.approved_policies.forEach(policy => {
              stats[normalizedCountry].policies.push({
                policyName: policy.policy_name,
                policyDescription: policy.policy_description,
                policyArea: area.area_name,
                country: normalizedCountry,
                approved_at: policy.approved_at
              });
            });
          }
        });
      }
    });
    
    console.log(`📊 Country stats built from API for ${Object.keys(stats).length} countries:`);
    Object.keys(stats).forEach(country => {
      const countryData = stats[country];
      const areas = Array.from(countryData.approvedAreas);
      const colorName = countryData.color === "#22c55e" ? "GREEN" : 
                       countryData.color === "#eab308" ? "YELLOW" : 
                       countryData.color === "#ef4444" ? "RED" : "GRAY";
      console.log(`  ${country}: ${countryData.totalPolicies} policies, ${countryData.count} area points [${areas.join(', ')}] - ${colorName}`);
    });
    
    return stats;
  }, [countries])

  // Update country stats when memoized data changes
  useEffect(() => {
    setCountryStats(countryStatsData);
  }, [countryStatsData])

  // Debug log for map statistics
  useEffect(() => {
    console.log('📊 Current map stats in Worldmap component:', {
      isLoading,
      mapStats,
      countries: countries.length
    })
  }, [mapStats, isLoading, countries])

  // Autocomplete suggestions - use geoFeatures to show ALL countries (including those with 0 policies)
  useEffect(() => {
    if (!geoFeatures.length) return
    if (!searchValue) setSearchSuggestions([])
    else {
      // Extract country names from geoFeatures (all countries) and filter
      const allCountryNames = geoFeatures.map(feature => feature.properties.name).filter(Boolean)
      setSearchSuggestions(
        allCountryNames.filter(countryName =>
          countryName.toLowerCase().includes(searchValue.toLowerCase())
        ).slice(0, 10)
      )
    }
  }, [searchValue, geoFeatures])

  // Handle hover (with flicker fix) - memoized to prevent re-creation
  const handleMouseEnter = useCallback((geo, event) => {
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
  }, [countryStats])

  const handleMouseMove = useCallback((geo, event) => {
    // Update mouse position for tooltip following
    if (tooltipContent) {
      setMousePosition({ x: event.clientX, y: event.clientY })
    }
  }, [tooltipContent])

  const handleMouseLeave = useCallback(() => {
    tooltipTimeout.current = setTimeout(() => {
      setTooltipContent(null)
      setHighlightedCountry(null)
    }, 120)
  }, [])

  // Handle country search/filter - memoized
  const handleCountrySelect = useCallback((country) => {
    console.log('🔍 Searching for country:', country);
    const normalizedCountry = normalizeCountryName(country);
    
    setFilteredCountry(normalizedCountry)
    setSearchValue(country)
    setSearchSuggestions([]) // Clear suggestions
    setHighlightedCountry(normalizedCountry)
    
    // Check if we have policies for this country (check both original and normalized names)
    const countryPolicies = masterPolicies.filter(p => {
      if (!p.country) return false;
      const policyCountry = normalizeCountryName(p.country);
      return policyCountry.toLowerCase().includes(normalizedCountry.toLowerCase()) ||
             p.country.toLowerCase().includes(country.toLowerCase());
    });
    console.log(`📊 Found ${countryPolicies.length} policies for ${country} (normalized: ${normalizedCountry})`);
    
    const stat = countryStats[normalizedCountry] || { count: 0, color: "#e5e7eb" }
    setTooltipContent({
      name: normalizedCountry,
      count: stat.count || 0,
      color: stat.color
    })
    
    // Auto-hide tooltip after 5 seconds
    setTimeout(() => setTooltipContent(null), 5000)
  }, [countryStats, masterPolicies])

  const handleClick = useCallback((geo) => {
    const countryName = geo.properties.name
    const stat = countryStats[countryName] || { color: "#d1d5db", count: 0 }
    
    setSelectedCountry({
      name: countryName,
      color: stat.color,
      policies: stat.policies || [], // Pass the normalized policies to the popup
      areas: stat.approvedAreas ? Array.from(stat.approvedAreas) : []
    })
    setShowPolicyPopup(true)
  }, [countryStats])

  const handleViewToggle = useCallback(() => {
    setViewMode(viewMode === "map" ? "globe" : "map")
  }, [viewMode])

  const handleClosePolicyPopup = useCallback(() => {
    setShowPolicyPopup(false)
    setSelectedCountry(null)
  }, [])

  function getTooltipPosition(mouseX, mouseY) {
    const tooltipWidth = 240
    const tooltipHeight = 120
    const offset = 15  // Offset from the cursor
    const mapElement = mapRef.current
    
    if (!mapElement) {
      return { 
        position: "fixed", 
        left: `${mouseX + offset}px`, 
        top: `${mouseY + offset}px`, 
        zIndex: 1001,
        pointerEvents: 'none'
      }
    }
    
    const mapRect = mapElement.getBoundingClientRect()
    const relativeX = mouseX - mapRect.left
    const relativeY = mouseY - mapRect.top
    
    let left = relativeX + offset
    let top = relativeY + offset
    
    // Determine if we're near the edges of the map
    const nearRightEdge = relativeX > mapRect.width - tooltipWidth - offset * 2
    const nearBottomEdge = relativeY > mapRect.height - tooltipHeight - offset * 2
    const nearLeftEdge = relativeX < tooltipWidth / 2
    const nearTopEdge = relativeY < tooltipHeight / 2
    
    // Smart positioning based on cursor location within the map
    if (nearRightEdge && nearBottomEdge) {
      // Bottom-right corner: position to top-left of cursor
      left = relativeX - tooltipWidth - offset
      top = relativeY - tooltipHeight - offset
    } else if (nearRightEdge && nearTopEdge) {
      // Top-right corner: position to bottom-left of cursor
      left = relativeX - tooltipWidth - offset
      top = relativeY + offset
    } else if (nearLeftEdge && nearBottomEdge) {
      // Bottom-left corner: position to top-right of cursor
      left = relativeX + offset
      top = relativeY - tooltipHeight - offset
    } else if (nearLeftEdge && nearTopEdge) {
      // Top-left corner: position to bottom-right of cursor
      left = relativeX + offset
      top = relativeY + offset
    } else if (nearRightEdge) {
      // Right edge: position to left of cursor
      left = relativeX - tooltipWidth - offset
      top = relativeY - tooltipHeight / 2
    } else if (nearBottomEdge) {
      // Bottom edge: position above cursor
      left = relativeX - tooltipWidth / 2
      top = relativeY - tooltipHeight - offset
    } else if (nearLeftEdge) {
      // Left edge: position to right of cursor
      left = relativeX + offset
      top = relativeY - tooltipHeight / 2
    } else if (nearTopEdge) {
      // Top edge: position below cursor
      left = relativeX - tooltipWidth / 2
      top = relativeY + offset
    } else {
      // Default: position to bottom-right of cursor
      left = relativeX + offset
      top = relativeY + offset
    }
    
    // Final boundary checks to ensure tooltip stays within map bounds
    left = Math.max(5, Math.min(left, mapRect.width - tooltipWidth - 5))
    top = Math.max(5, Math.min(top, mapRect.height - tooltipHeight - 5))
    
    return { 
      position: "absolute", 
      left: `${left}px`, 
      top: `${top}px`, 
      zIndex: 1001,
      pointerEvents: 'none'
    }
  }

  return (
    <div className="worldmap-container">
      {/* Header Controls */}
      <div className="worldmap-header">
        <div className="header-left">
          {/* View toggle button now handled by parent IntegratedWorldMap */}
        </div>
        
        <div className="header-center">
          <div className="header-title">
            <h1>RGB Map</h1>            
            {/* Map Statistics */}
            <div className="map-stats">
              <div className="stat-item">
                <span className="stat-number">
                  {isLoading ? '...' : mapStats.countriesWithPolicies}
                </span>
                <span className="stat-label">Covered Countries</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">
                  {isLoading ? '...' : mapStats.totalPolicies}
                </span>
                <span className="stat-label">Total Policies</span>
              </div>
              {isLoading && (
                <div className="stat-item">
                  <span className="stat-number">🔄</span>
                  <span className="stat-label">Loading...</span>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="header-right">
          <div className="country-search">
            <div className="relative">
              <input
                type="text"
                placeholder="🔍 Search country..."
                value={searchValue}
                onChange={e => setSearchValue(e.target.value)}
                className="country-search-input text-black"
                autoComplete="off"
              />
              <Search className="absolute right-8 top-2 w-4 h-4 text-gray-400" />
              {searchValue && (
                <button
                  onClick={() => {
                    setSearchValue('');
                    setFilteredCountry(null);
                    setHighlightedCountry(null);
                    setSearchSuggestions([]);
                    setTooltipContent(null);
                  }}
                  className="absolute right-2 top-2 w-4 h-4 text-gray-500 hover:text-gray-700"
                  title="Clear search"
                >
                  ✕
                </button>
              )}
              {searchSuggestions.length > 0 && (
                <ul className="country-suggestions text-black">
                  {searchSuggestions.map((countryName, i) => {
                    const normalizedCountry = normalizeCountryName(countryName)
                    const stat = countryStats[normalizedCountry]
                    const hasPolicy = stat && (stat.count > 0 || stat.totalPolicies > 0)
                    
                    return (
                      <li key={i} onClick={() => handleCountrySelect(countryName)} className={!hasPolicy ? 'no-policies' : ''}>
                        <span className="country-name">{countryName}</span>
                        <span className="country-count">
                          {stat ? `${stat.count} areas, ${stat.totalPolicies} policies` : '0 areas, 0 policies'}
                        </span>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="worldmap-content">
        {/* Map Section */}
        <div className="map-section" ref={mapRef} style={{ position: 'relative' }}>
          {viewMode === "map" && (
            <div className="map-container">
              <ComposableMap projection="geoMercator" style={{ width: "100%", height: "100%" }}>
                <Geographies geography={geoUrl}>
                  {({ geographies }) =>
                    geographies.map(geo => {
                      const countryName = geo.properties.name
                      const stat = countryStats[countryName] || { color: "#e5e7eb", count: 0 } // Light gray for no data
                      const isHighlighted = highlightedCountry === countryName || filteredCountry === countryName
                      
                      // Debug first few countries
                      if (Object.keys(countryStats).length > 0 && Math.random() < 0.1) {
                        console.log(`🗺️ Map render: ${countryName} -> Color: ${stat.color}, Areas: ${stat.count}`);
                      }
                      
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
                          onMouseMove={e => handleMouseMove(geo, e)}
                          onMouseLeave={handleMouseLeave}
                          onClick={() => handleClick(geo)}
                        />
                      )
                    })
                  }
                </Geographies>
              </ComposableMap>
              {/* Floating Tooltip Positioned Relative to Map */}
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
                      {tooltipContent.count >= 8 ? "Excellent (8-10)" : tooltipContent.count >= 4 ? "Moderate (4-7)" : tooltipContent.count >= 1 ? "Needs Improvement (1-3)" : "No Policies"}
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

// Memoize the component to prevent unnecessary re-renders
export default React.memo(Worldmap)