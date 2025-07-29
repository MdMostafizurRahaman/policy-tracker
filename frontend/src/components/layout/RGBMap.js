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

function RGBMap({ viewMode: propViewMode }) {
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
      console.log('🗺️ RGB Map mounting - fetching data via context')
      fetchMapData()
    } else if (isLoaded) {
      console.log('🗺️ RGB Map mounting - using cached data from context')
    }
  }, [isLoaded, isLoading, fetchMapData])

  // Sync viewMode with prop
  useEffect(() => {
    if (propViewMode) {
      setViewMode(propViewMode)
    }
  }, [propViewMode])

  // Memoized country statistics calculation using API color data
  const countryStatsData = useMemo(() => {
    console.log('🔍 Building RGB country stats from API color data. Countries loaded:', countries.length);
    
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
      
      // Convert API color names to RGB colors for the RGB map
      let rgbColor = "#808080"; // Default gray
      switch(countryData.color) {
        case 'green':
          rgbColor = "#00FF00"; // Pure green
          break;
        case 'yellow':
          rgbColor = "#FFFF00"; // Pure yellow
          break;
        case 'red':
          rgbColor = "#FF0000"; // Pure red
          break;
        case 'gray':
        default:
          rgbColor = "#808080"; // Pure gray
          break;
      }
      
      stats[normalizedCountry] = {
        count: countryData.area_points || 0,
        totalPolicies: countryData.total_approved_policies || 0,
        approvedAreas: new Set(countryData.areas_with_approved_policies || []),
        color: rgbColor,
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
    
    console.log(`📊 RGB Country stats built from API for ${Object.keys(stats).length} countries:`);
    Object.keys(stats).forEach(country => {
      const countryData = stats[country];
      const areas = Array.from(countryData.approvedAreas);
      const colorName = countryData.color === "#00FF00" ? "GREEN" : 
                       countryData.color === "#FFFF00" ? "YELLOW" : 
                       countryData.color === "#FF0000" ? "RED" : "GRAY";
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
    console.log('📊 Current RGB map stats in RGBMap component:', {
      isLoading,
      mapStats,
      countries: countries.length
    })
  }, [mapStats, isLoading, countries])

  // Autocomplete suggestions
  useEffect(() => {
    if (!countries.length) return
    if (!searchValue) setSearchSuggestions([])
    else {
      // Extract country names from countries array and filter
      const countryNames = countries.map(countryData => countryData.country).filter(Boolean)
      setSearchSuggestions(
        countryNames.filter(countryName =>
          countryName.toLowerCase().includes(searchValue.toLowerCase())
        ).slice(0, 10)
      )
    }
  }, [searchValue, countries])

  // Handle hover (with flicker fix) - memoized to prevent re-creation
  const handleMouseEnter = useCallback((geo, event) => {
    clearTimeout(tooltipTimeout.current)
    const countryName = geo.properties.name
    const stat = countryStats[countryName] || { count: 0, color: "#808080" }
    setTooltipContent({
      name: countryName,
      count: stat.count || 0,
      color: stat.color
    })
    setMousePosition({ x: event.clientX, y: event.clientY })
    setHighlightedCountry(countryName)
  }, [countryStats])

  const handleMouseLeave = useCallback(() => {
    tooltipTimeout.current = setTimeout(() => {
      setTooltipContent(null)
      setHighlightedCountry(null)
    }, 120)
  }, [])

  // Handle country search/filter - memoized
  const handleCountrySelect = useCallback((country) => {
    console.log('🔍 RGB Map searching for country:', country);
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
    
    const stat = countryStats[normalizedCountry] || { count: 0, color: "#808080" }
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
    const stat = countryStats[countryName] || { color: "#808080", count: 0 }
    
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
                    return (
                      <li key={i} onClick={() => handleCountrySelect(countryName)}>
                        <span className="country-name">{countryName}</span>
                        <span className="country-count">
                          {stat ? `${stat.count} areas, ${stat.totalPolicies} policies` : 'No policies'}
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
        <div className="map-section" ref={mapRef}>
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
                        console.log(`🗺️ RGB Map render: ${countryName} -> Color: ${stat.color}, Areas: ${stat.count}`);
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
                      background: tooltipContent.count >= 8 ? "#00FF00" : tooltipContent.count >= 4 ? "#FFFF00" : "#FF0000",
                      color: "#000",
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
export default React.memo(RGBMap)
