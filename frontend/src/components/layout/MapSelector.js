'use client'
import React, { useState } from "react"
import WorldMap from "./Worldmap"
import RGBMap from "./RGBMap"
import PolicyMap from "./PolicyMap"
import '../../styles/Worldmap.css'

const MAP_TYPES = {
  WORLD: 'world',
  RGB: 'rgb',
  POLICY: 'policy'
}

const MAP_INFO = {
  [MAP_TYPES.WORLD]: {
    title: 'Policy World Map',
    description: 'Countries colored by policy coverage level (overall)',
    component: WorldMap,
    icon: '🌍',
    color: 'from-blue-500 to-cyan-600'
  },
  [MAP_TYPES.RGB]: {
    title: 'RGB Map',
    description: 'Pure RGB colors showing policy coverage levels',
    component: RGBMap,
    icon: '🎨',
    color: 'from-purple-500 to-indigo-600'
  },
  [MAP_TYPES.POLICY]: {
    title: 'Policy Map',
    description: '10 distinct colors for 10 different policy areas',
    component: PolicyMap,
    icon: '📊',
    color: 'from-green-500 to-emerald-600'
  }
}

function MapSelector() {
  const [selectedMap, setSelectedMap] = useState(MAP_TYPES.WORLD)
  const [showSelector, setShowSelector] = useState(true)

  const handleMapChange = (mapType) => {
    setSelectedMap(mapType)
    setShowSelector(false)
  }

  const SelectedMapComponent = MAP_INFO[selectedMap].component

  if (!showSelector) {
    return (
      <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
        {/* Map Switcher Button */}
        <button
          onClick={() => setShowSelector(true)}
          style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            zIndex: 1000,
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            border: 'none',
            borderRadius: '12px',
            padding: '12px 20px',
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
          <span>Switch Map ({MAP_INFO[selectedMap].title})</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </button>
        
        <SelectedMapComponent />
      </div>
    )
  }

  return (
    <div style={{
      width: '100%',
      height: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      position: 'relative'
    }}>
      {/* Background decoration */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%), linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%), linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%), linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%)',
        backgroundSize: '60px 60px',
        backgroundPosition: '0 0, 0 30px, 30px -30px, -30px 0px',
        opacity: 0.3
      }}></div>

      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '24px',
        padding: '48px',
        maxWidth: '900px',
        width: '100%',
        boxShadow: '0 25px 50px rgba(0, 0, 0, 0.25)',
        position: 'relative',
        zIndex: 1
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <h1 style={{
            fontSize: '48px',
            fontWeight: '800',
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            margin: '0 0 16px 0',
            lineHeight: '1.1'
          }}>
            Choose Your Map View
          </h1>
          <p style={{
            fontSize: '18px',
            color: '#6B7280',
            margin: 0,
            lineHeight: '1.6'
          }}>
            Select from three different visualization approaches to explore global policy data
          </p>
        </div>

        {/* Map Selection Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '24px',
          marginBottom: '32px'
        }}>
          {Object.entries(MAP_INFO).map(([key, info]) => (
            <div
              key={key}
              onClick={() => handleMapChange(key)}
              style={{
                background: selectedMap === key ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1))' : 'white',
                border: selectedMap === key ? '2px solid #667eea' : '2px solid transparent',
                borderRadius: '16px',
                padding: '24px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                textAlign: 'center',
                position: 'relative',
                overflow: 'hidden'
              }}
              onMouseEnter={(e) => {
                if (selectedMap !== key) {
                  e.target.style.transform = 'translateY(-4px)'
                  e.target.style.boxShadow = '0 12px 25px rgba(0, 0, 0, 0.15)'
                  e.target.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05))'
                }
              }}
              onMouseLeave={(e) => {
                if (selectedMap !== key) {
                  e.target.style.transform = 'translateY(0)'
                  e.target.style.boxShadow = 'none'
                  e.target.style.background = 'white'
                }
              }}
            >
              {/* Icon */}
              <div style={{
                fontSize: '48px',
                marginBottom: '16px',
                display: 'flex',
                justifyContent: 'center'
              }}>
                {info.icon}
              </div>

              {/* Title */}
              <h3 style={{
                fontSize: '20px',
                fontWeight: '700',
                color: '#1F2937',
                margin: '0 0 8px 0'
              }}>
                {info.title}
              </h3>

              {/* Description */}
              <p style={{
                fontSize: '14px',
                color: '#6B7280',
                margin: '0 0 16px 0',
                lineHeight: '1.5'
              }}>
                {info.description}
              </p>

              {/* Selection indicator */}
              {selectedMap === key && (
                <div style={{
                  position: 'absolute',
                  top: '12px',
                  right: '12px',
                  width: '24px',
                  height: '24px',
                  background: '#667eea',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '12px'
                }}>
                  ✓
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '16px',
          marginTop: '32px'
        }}>
          <button
            onClick={() => handleMapChange(selectedMap)}
            style={{
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              padding: '16px 32px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)'
              e.target.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.5)'
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)'
              e.target.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)'
            }}
          >
            Launch {MAP_INFO[selectedMap].title}
          </button>
        </div>

        {/* Feature comparison */}
        <div style={{
          marginTop: '48px',
          padding: '24px',
          background: 'rgba(102, 126, 234, 0.05)',
          borderRadius: '12px',
          border: '1px solid rgba(102, 126, 234, 0.1)'
        }}>
          <h4 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: '#374151',
            margin: '0 0 16px 0',
            textAlign: 'center'
          }}>
            Map Features Comparison
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            fontSize: '12px',
            color: '#6B7280'
          }}>
            <div>
              <strong>Policy World Map:</strong> Traditional coverage-based coloring (Green/Yellow/Red)
            </div>
            <div>
              <strong>RGB Map:</strong> Pure color representation (Red/Green/Blue/Gray)
            </div>
            <div>
              <strong>Policy Map:</strong> Area-specific coloring with filtering capabilities
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default React.memo(MapSelector)
