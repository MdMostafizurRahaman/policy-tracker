'use client'
import React, { useState, useEffect, useRef, useMemo, useCallback } from "react"
import { ComposableMap, Geographies, Geography } from "react-simple-maps"
import dynamic from "next/dynamic"
import { Search } from "lucide-react"
import CountryPolicyPopup from "./CountryPolicyPopup"
import { useMapData } from '../../context/MapDataContext'
import { policyAreas } from '../../utils/constants'
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

// Policy area colors - 10 distinct colors for 10 policy areas
const POLICY_AREA_COLORS = {
  'ai-safety': '#FF6B6B',        // Red
  'cyber-safety': '#4ECDC4',     // Teal
  'digital-education': '#45B7D1', // Blue
  'digital-inclusion': '#96CEB4', // Green
  'digital-work': '#FFEAA7',     // Yellow
  'mental-health': '#DDA0DD',    // Plum
  'physical-health': '#98D8C8',  // Mint
  'social-media-gaming': '#F7DC6F', // Light Yellow
  'disinformation': '#AED6F1',   // Light Blue
  'digital-leisure': '#FAD5A5'   // Peach
};

// Default color for countries with no policies
const DEFAULT_COLOR = '#E5E7EB'; // Light gray

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
  'digital-leisure': 'Digital Leisure',
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

function normalizePolicyAreaId(areaName) {
  if (!areaName) return null;
  
  // Convert area name to ID format
  const normalizedName = POLICY_AREA_MAP[areaName] || areaName;
  
  // Find matching policy area ID
  for (const [id, name] of Object.entries(POLICY_AREA_MAP)) {
    if (name === normalizedName) {
      return id;
    }
  }
  
  // Try to convert name to kebab-case ID
  return normalizedName.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
}

const GlobeView = dynamic(() => import("./GlobeView"), {
  ssr: false,
  loading: () => <p>Loading Globe...</p>,
})

const geoUrl = "/countries-110m.json"

function PolicyMap({ viewMode: propViewMode }) {
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
  const [selectedPolicyArea, setSelectedPolicyArea] = useState(null) // For filtering by policy area

  const mapRef = useRef(null)
  let tooltipTimeout = useRef(null)

  // Fetch data when component mounts if not already loaded
  useEffect(() => {
    if (!isLoaded && !isLoading) {
      console.log('🗺️ Policy Map mounting - fetching data via context')
      fetchMapData()
    } else if (isLoaded) {
      console.log('🗺️ Policy Map mounting - using cached data from context')
    }
  }, [isLoaded, isLoading, fetchMapData])

  // Sync viewMode with prop
  useEffect(() => {
    if (propViewMode) {
      setViewMode(propViewMode)
    }
  }, [propViewMode])

  // Memoized country statistics calculation for policy-based coloring
  const countryStatsData = useMemo(() => {
    console.log('🔍 Building Policy Map country stats. Countries loaded:', countries.length);
    
    if (!countries.length) {
      console.log('⚠️ No countries data loaded yet, returning empty stats');
      return {};
    }
    
    const stats = {};
    
    // Process countries data from API
    countries.forEach((countryData) => {
      const rawCountry = countryData.country;
      
      if (!rawCountry) {
        console.warn('Country data missing country name:', countryData);
        return;
      }
      
      // Normalize country name for geojson matching
      const normalizedCountry = normalizeCountryName(rawCountry);
      if (!normalizedCountry) return;
      
      // Determine color based on policy areas
      let countryColor = DEFAULT_COLOR;
      let dominantArea = null;
      let areaCount = 0;
      
      // If country has areas_detail, find the dominant policy area
      if (countryData.areas_detail && countryData.areas_detail.length > 0) {
        const areasWithPolicies = countryData.areas_detail.filter(area => 
          area.approved_policies && area.approved_policies.length > 0
        );
        
        if (areasWithPolicies.length > 0) {
          // Find the area with the most policies
          let maxPolicies = 0;
          areasWithPolicies.forEach(area => {
            const policyCount = area.approved_policies.length;
            if (policyCount > maxPolicies) {
              maxPolicies = policyCount;
              dominantArea = area.area_name;
            }
          });
          
          // Convert area name to area ID and get color
          if (dominantArea) {
            const areaId = normalizePolicyAreaId(dominantArea);
            countryColor = POLICY_AREA_COLORS[areaId] || DEFAULT_COLOR;
            areaCount = areasWithPolicies.length;
          }
        }
      }
      
      // Apply policy area filter if selected
      if (selectedPolicyArea) {
        const hasSelectedArea = countryData.areas_detail?.some(area => {
          const areaId = normalizePolicyAreaId(area.area_name);
          return areaId === selectedPolicyArea && area.approved_policies?.length > 0;
        });
        
        if (hasSelectedArea) {
          countryColor = POLICY_AREA_COLORS[selectedPolicyArea];
        } else {
          countryColor = DEFAULT_COLOR; // Gray out countries without the selected policy area
        }
      }
      
      stats[normalizedCountry] = {
        count: countryData.area_points || 0,
        totalPolicies: countryData.total_approved_policies || 0,
        approvedAreas: new Set(countryData.areas_with_approved_policies || []),
        color: countryColor,
        dominantArea: dominantArea,
        areaCount: areaCount,
        level: countryData.level || 'no_approved_areas',
        areas_detail: countryData.areas_detail || [],
        policies: [],
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
    
    console.log(`📊 Policy Map stats built for ${Object.keys(stats).length} countries`);
    if (selectedPolicyArea) {
      console.log(`🎯 Filtering by policy area: ${selectedPolicyArea}`);
    }
    
    return stats;
  }, [countries, selectedPolicyArea])

  // Update country stats when memoized data changes
  useEffect(() => {
    setCountryStats(countryStatsData);
  }, [countryStatsData])

  // Debug log for map statistics
  useEffect(() => {
    console.log('📊 Current Policy Map stats:', {
      isLoading,
      mapStats,
      countries: countries.length,
      selectedPolicyArea
    })
  }, [mapStats, isLoading, countries, selectedPolicyArea])

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
    const stat = countryStats[countryName] || { count: 0, color: DEFAULT_COLOR }
    setTooltipContent({
      name: countryName,
      count: stat.count || 0,
      color: stat.color,
      dominantArea: stat.dominantArea,
      areaCount: stat.areaCount || 0
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
    console.log('🔍 Policy Map searching for country:', country);
    const normalizedCountry = normalizeCountryName(country);
    
    setFilteredCountry(normalizedCountry)
    setSearchValue(country)
    setSearchSuggestions([]) // Clear suggestions
    setHighlightedCountry(normalizedCountry)
    
    const stat = countryStats[normalizedCountry] || { count: 0, color: DEFAULT_COLOR }
    setTooltipContent({
      name: normalizedCountry,
      count: stat.count || 0,
      color: stat.color,
      dominantArea: stat.dominantArea,
      areaCount: stat.areaCount || 0
    })
    
    // Auto-hide tooltip after 5 seconds
    setTimeout(() => setTooltipContent(null), 5000)
  }, [countryStats])

  const handleClick = useCallback((geo) => {
    const countryName = geo.properties.name
    const stat = countryStats[countryName] || { color: DEFAULT_COLOR, count: 0 }
    
    setSelectedCountry({
      name: countryName,
      color: stat.color,
      policies: stat.policies || [],
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

  const handlePolicyAreaFilter = useCallback((areaId) => {
    if (selectedPolicyArea === areaId) {
      setSelectedPolicyArea(null) // Clear filter if same area is clicked
    } else {
      setSelectedPolicyArea(areaId) // Set new filter
    }
  }, [selectedPolicyArea])

  function getTooltipPosition(mouseX, mouseY) {
    const tooltipWidth = 250
    const tooltipHeight = 100
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
            <h1>Policy Map</h1>            
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
              {selectedPolicyArea && (
                <div className="stat-item">
                  <span className="stat-number">🎯</span>
                  <span className="stat-label">
                    {POLICY_AREA_MAP[selectedPolicyArea] || selectedPolicyArea}
                  </span>
                </div>
              )}
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

      {/* Policy Area Filter Bar */}
      <div className="policy-filter-bar" style={{ 
        background: 'rgba(255,255,255,0.95)', 
        padding: '12px 20px', 
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        alignItems: 'center'
      }}>
        <span style={{ fontWeight: 'bold', marginRight: '10px', color: '#374151' }}>
          Filter by Policy Area:
        </span>
        <button
          onClick={() => setSelectedPolicyArea(null)}
          style={{
            padding: '6px 12px',
            borderRadius: '20px',
            border: 'none',
            background: selectedPolicyArea === null ? '#4F46E5' : '#E5E7EB',
            color: selectedPolicyArea === null ? 'white' : '#374151',
            fontSize: '12px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          All Areas
        </button>
        {Object.entries(POLICY_AREA_COLORS).map(([areaId, color]) => (
          <button
            key={areaId}
            onClick={() => handlePolicyAreaFilter(areaId)}
            style={{
              padding: '6px 12px',
              borderRadius: '20px',
              border: 'none',
              background: selectedPolicyArea === areaId ? color : '#E5E7EB',
              color: selectedPolicyArea === areaId ? 'white' : '#374151',
              fontSize: '12px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: selectedPolicyArea === areaId ? `0 0 0 2px ${color}40` : 'none'
            }}
          >
            {POLICY_AREA_MAP[areaId] || areaId}
          </button>
        ))}
      </div>

      {/* Policy Area Legend */}
      <div className="policy-legend" style={{
        background: 'rgba(255,255,255,0.95)',
        padding: '12px 20px',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        alignItems: 'center',
        fontSize: '12px'
      }}>
        <span style={{ fontWeight: 'bold', marginRight: '10px', color: '#374151' }}>
          Legend:
        </span>
        {Object.entries(POLICY_AREA_COLORS).map(([areaId, color]) => (
          <div key={areaId} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: color,
              border: '1px solid #00000020'
            }}></div>
            <span style={{ color: '#374151' }}>
              {POLICY_AREA_MAP[areaId] || areaId}
            </span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            background: DEFAULT_COLOR,
            border: '1px solid #00000020'
          }}></div>
          <span style={{ color: '#374151' }}>No Policies</span>
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
                      const stat = countryStats[countryName] || { color: DEFAULT_COLOR, count: 0 }
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
                      color: '#374151'
                    }}>
                      Policy Areas: {tooltipContent.count} / 10
                    </span>
                  </div>
                  {tooltipContent.dominantArea && (
                    <div style={{
                      marginTop: 4,
                      fontSize: 12,
                      color: '#6B7280'
                    }}>
                      Dominant Area: {tooltipContent.dominantArea}
                    </div>
                  )}
                  {selectedPolicyArea && (
                    <div style={{
                      marginTop: 4,
                      fontSize: 12,
                      color: tooltipContent.color,
                      fontWeight: 'bold'
                    }}>
                      {POLICY_AREA_MAP[selectedPolicyArea] || selectedPolicyArea}
                    </div>
                  )}
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
export default React.memo(PolicyMap)
