'use client'
import React, { useState } from "react"
import WorldMap from "./Worldmap"
import RGBMap from "./RGBMap"
import PolicyMap from "./PolicyMap"
import '../../styles/Worldmap.css'

const MAP_TYPES = {
  WORLD_MAP: 'world_map',
  WORLD_GLOBE: 'world_globe',
  RGB_MAP: 'rgb_map',
  RGB_GLOBE: 'rgb_globe',
  POLICY_MAP: 'policy_map',
  POLICY_GLOBE: 'policy_globe'
}

const MAP_INFO = {
  [MAP_TYPES.WORLD_MAP]: {
    title: 'Policy World Map',
    description: 'Countries colored by policy coverage level',
    component: WorldMap,
    icon: '🗺️',
    shortName: 'Policy Map',
    viewMode: 'map'
  },
  [MAP_TYPES.WORLD_GLOBE]: {
    title: 'Policy World Globe',
    description: 'Globe view with policy coverage colors',
    component: WorldMap,
    icon: '🌍',
    shortName: 'Policy Globe',
    viewMode: 'globe'
  },
  [MAP_TYPES.RGB_MAP]: {
    title: 'RGB Map',
    description: 'Pure RGB colors showing policy coverage',
    component: RGBMap,
    icon: '🎨',
    shortName: 'RGB Map',
    viewMode: 'map'
  },
  [MAP_TYPES.RGB_GLOBE]: {
    title: 'RGB Globe',
    description: 'Globe view with pure RGB colors',
    component: RGBMap,
    icon: '🎨',
    shortName: 'RGB Globe',
    viewMode: 'globe'
  },
  [MAP_TYPES.POLICY_MAP]: {
    title: 'Policy Area Map',
    description: '10 distinct colors for policy areas',
    component: PolicyMap,
    icon: '📊',
    shortName: 'Policy Areas Map',
    viewMode: 'map'
  },
  [MAP_TYPES.POLICY_GLOBE]: {
    title: 'Policy Area Globe',
    description: 'Globe view with policy area colors',
    component: PolicyMap,
    icon: '📊',
    shortName: 'Policy Areas Globe',
    viewMode: 'globe'
  }
}

function IntegratedWorldMap() {
  const [selectedMap, setSelectedMap] = useState(MAP_TYPES.WORLD_MAP)
  const [showMapSelector, setShowMapSelector] = useState(false)

  const handleMapChange = (mapType) => {
    setSelectedMap(mapType)
    setShowMapSelector(false)
  }

  const SelectedMapComponent = MAP_INFO[selectedMap].component
  const currentViewMode = MAP_INFO[selectedMap].viewMode

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      {/* Map Selection Dropdown */}
      {showMapSelector && (
        <div style={{
          position: 'absolute',
          top: '70px',
          left: '20px',
          zIndex: 1001,
          background: 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(20px)',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          minWidth: '280px',
          maxWidth: '320px'
        }}>
          {/* Header */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <h3 style={{
              margin: 0,
              fontSize: '18px',
              fontWeight: '700',
              color: '#1F2937'
            }}>
              Select Map View
            </h3>
            <button
              onClick={() => setShowMapSelector(false)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '20px',
                cursor: 'pointer',
                color: '#6B7280',
                padding: '4px',
                borderRadius: '4px'
              }}
            >
              ×
            </button>
          </div>

          {/* Map Options - Organized by type */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Policy World Map Section */}
            <div>
              <div style={{
                fontSize: '12px',
                fontWeight: '600',
                color: '#6B7280',
                marginBottom: '6px',
                padding: '0 4px'
              }}>
                Policy World Map
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {[MAP_TYPES.WORLD_MAP, MAP_TYPES.WORLD_GLOBE].map(key => {
                  const info = MAP_INFO[key]
                  return (
                    <button
                      key={key}
                      onClick={() => handleMapChange(key)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '10px 12px',
                        border: selectedMap === key ? '2px solid #4F46E5' : '1px solid #E5E7EB',
                        borderRadius: '8px',
                        background: selectedMap === key ? 'rgba(79, 70, 229, 0.1)' : 'white',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        textAlign: 'left',
                        width: '100%'
                      }}
                      onMouseEnter={(e) => {
                        if (selectedMap !== key) {
                          e.target.style.background = 'rgba(79, 70, 229, 0.05)'
                          e.target.style.borderColor = '#C7D2FE'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (selectedMap !== key) {
                          e.target.style.background = 'white'
                          e.target.style.borderColor = '#E5E7EB'
                        }
                      }}
                    >
                      <span style={{ fontSize: '20px' }}>{info.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontWeight: '600',
                          color: '#1F2937',
                          fontSize: '13px'
                        }}>
                          {info.shortName}
                        </div>
                      </div>
                      {selectedMap === key && (
                        <div style={{
                          width: '16px',
                          height: '16px',
                          background: '#4F46E5',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '10px'
                        }}>
                          ✓
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* RGB Map Section */}
            <div>
              <div style={{
                fontSize: '12px',
                fontWeight: '600',
                color: '#6B7280',
                marginBottom: '6px',
                padding: '0 4px'
              }}>
                RGB Map
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {[MAP_TYPES.RGB_MAP, MAP_TYPES.RGB_GLOBE].map(key => {
                  const info = MAP_INFO[key]
                  return (
                    <button
                      key={key}
                      onClick={() => handleMapChange(key)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '10px 12px',
                        border: selectedMap === key ? '2px solid #4F46E5' : '1px solid #E5E7EB',
                        borderRadius: '8px',
                        background: selectedMap === key ? 'rgba(79, 70, 229, 0.1)' : 'white',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        textAlign: 'left',
                        width: '100%'
                      }}
                      onMouseEnter={(e) => {
                        if (selectedMap !== key) {
                          e.target.style.background = 'rgba(79, 70, 229, 0.05)'
                          e.target.style.borderColor = '#C7D2FE'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (selectedMap !== key) {
                          e.target.style.background = 'white'
                          e.target.style.borderColor = '#E5E7EB'
                        }
                      }}
                    >
                      <span style={{ fontSize: '20px' }}>{info.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontWeight: '600',
                          color: '#1F2937',
                          fontSize: '13px'
                        }}>
                          {info.shortName}
                        </div>
                      </div>
                      {selectedMap === key && (
                        <div style={{
                          width: '16px',
                          height: '16px',
                          background: '#4F46E5',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '10px'
                        }}>
                          ✓
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Policy Area Map Section */}
            <div>
              <div style={{
                fontSize: '12px',
                fontWeight: '600',
                color: '#6B7280',
                marginBottom: '6px',
                padding: '0 4px'
              }}>
                Policy Area Map
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {[MAP_TYPES.POLICY_MAP, MAP_TYPES.POLICY_GLOBE].map(key => {
                  const info = MAP_INFO[key]
                  return (
                    <button
                      key={key}
                      onClick={() => handleMapChange(key)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '10px 12px',
                        border: selectedMap === key ? '2px solid #4F46E5' : '1px solid #E5E7EB',
                        borderRadius: '8px',
                        background: selectedMap === key ? 'rgba(79, 70, 229, 0.1)' : 'white',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        textAlign: 'left',
                        width: '100%'
                      }}
                      onMouseEnter={(e) => {
                        if (selectedMap !== key) {
                          e.target.style.background = 'rgba(79, 70, 229, 0.05)'
                          e.target.style.borderColor = '#C7D2FE'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (selectedMap !== key) {
                          e.target.style.background = 'white'
                          e.target.style.borderColor = '#E5E7EB'
                        }
                      }}
                    >
                      <span style={{ fontSize: '20px' }}>{info.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontWeight: '600',
                          color: '#1F2937',
                          fontSize: '13px'
                        }}>
                          {info.shortName}
                        </div>
                      </div>
                      {selectedMap === key && (
                        <div style={{
                          width: '16px',
                          height: '16px',
                          background: '#4F46E5',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '10px'
                        }}>
                          ✓
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Quick info */}
          <div style={{
            marginTop: '16px',
            padding: '12px',
            background: 'rgba(79, 70, 229, 0.05)',
            borderRadius: '8px',
            fontSize: '11px',
            color: '#6B7280',
            textAlign: 'center'
          }}>
            Choose between Map and Globe views for each visualization type
          </div>
        </div>
      )}

      {/* Overlay to close dropdown */}
      {showMapSelector && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 1000,
            background: 'rgba(0, 0, 0, 0.1)'
          }}
          onClick={() => setShowMapSelector(false)}
        />
      )}

      {/* Enhanced Map Component with Custom Header */}
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        {/* Custom View Toggle Button */}
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          zIndex: 999,
          display: 'flex',
          gap: '12px'
        }}>
          {/* Map Type Selector Button */}
          <button
            onClick={() => setShowMapSelector(!showMapSelector)}
            style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              border: 'none',
              borderRadius: '12px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              color: '#374151',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
              transition: 'all 0.3s ease',
              fontSize: '14px'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)'
              e.target.style.boxShadow = '0 6px 25px rgba(0, 0, 0, 0.15)'
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)'
              e.target.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)'
            }}
          >
            <span>{MAP_INFO[selectedMap].icon}</span>
            <span>{MAP_INFO[selectedMap].shortName}</span>
            <svg 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
              style={{
                transform: showMapSelector ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s ease'
              }}
            >
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </button>
        </div>

        {/* Render Selected Map Component */}
        <SelectedMapComponent viewMode={currentViewMode} />
      </div>
    </div>
  )
}

export default React.memo(IntegratedWorldMap)
