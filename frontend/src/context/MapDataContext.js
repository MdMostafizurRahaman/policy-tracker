'use client'
import React, { createContext, useContext, useState, useEffect } from 'react'
import { publicService } from '../services/api'

const MapDataContext = createContext()

export const useMapData = () => {
  const context = useContext(MapDataContext)
  if (!context) {
    throw new Error('useMapData must be used within a MapDataProvider')
  }
  return context
}

export const MapDataProvider = ({ children }) => {
  const [mapData, setMapData] = useState({
    countries: [],
    geoFeatures: [],
    masterPolicies: [],
    countryStats: {},
    mapStats: {
      countriesWithPolicies: 0,
      totalPolicies: 0,
      totalCountries: 0
    },
    isLoaded: false,
    isLoading: false,
    lastFetch: null
  })

  // Cache duration in milliseconds (5 minutes)
  const CACHE_DURATION = 5 * 60 * 1000

  const isCacheValid = () => {
    if (!mapData.lastFetch) return false
    return Date.now() - mapData.lastFetch < CACHE_DURATION
  }

  const fetchMapData = async (force = false) => {
    // If data is already loaded and cache is valid, don't refetch
    if (!force && mapData.isLoaded && isCacheValid()) {
      console.log('📋 Using cached map data')
      return mapData
    }

    if (mapData.isLoading) {
      console.log('📋 Map data fetch already in progress')
      return mapData
    }

    console.log('📋 Fetching fresh map data...')
    setMapData(prev => ({ ...prev, isLoading: true }))

    try {
      // Fetch all data in parallel
      const [
        mapVisualizationResponse,
        geoResponse,
        policiesResponse,
        statsResponse
      ] = await Promise.all([
        publicService.getMapVisualization().catch(err => ({ countries: [] })),
        fetch('/countries-110m.json').then(res => res.json()).catch(err => ({ objects: { countries: { geometries: [] } } })),
        publicService.getMasterPoliciesFast().catch(err => ({ policies: [] })),
        publicService.getStatisticsFast().catch(err => ({ countries_with_policies: 0, total_policies: 0, total_countries: 0 }))
      ])

      // Process geo features
      const topojson = await import('topojson-client')
      const geoFeatures = geoResponse.objects?.countries ? 
        topojson.feature(geoResponse, geoResponse.objects.countries).features : []

      const newMapData = {
        countries: mapVisualizationResponse.countries || [],
        geoFeatures,
        masterPolicies: policiesResponse.policies || [],
        mapStats: {
          countriesWithPolicies: statsResponse.countries_with_policies || 0,
          totalPolicies: statsResponse.total_policies || 0,
          totalCountries: statsResponse.total_countries || 0
        },
        isLoaded: true,
        isLoading: false,
        lastFetch: Date.now()
      }

      setMapData(newMapData)
      console.log(`📋 Map data loaded successfully: ${newMapData.masterPolicies.length} policies, ${newMapData.countries.length} countries`)
      
      return newMapData
    } catch (error) {
      console.error('📋 Failed to fetch map data:', error)
      setMapData(prev => ({ 
        ...prev, 
        isLoading: false,
        // Keep existing data if fetch fails, or provide defaults
        isLoaded: prev.isLoaded || false,
        countries: prev.countries || [],
        geoFeatures: prev.geoFeatures || [],
        masterPolicies: prev.masterPolicies || [],
        mapStats: prev.mapStats || {
          countriesWithPolicies: 0,
          totalPolicies: 0,
          totalCountries: 0
        }
      }))
      return mapData
    }
  }

  const refreshMapData = () => {
    return fetchMapData(true)
  }

  const value = {
    ...mapData,
    fetchMapData,
    refreshMapData,
    isCacheValid
  }

  return (
    <MapDataContext.Provider value={value}>
      {children}
    </MapDataContext.Provider>
  )
}
