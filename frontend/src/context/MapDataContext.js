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
      console.log('📋 Starting parallel API calls...')
      const [
        mapVisualizationResponse,
        geoResponse,
        policiesResponse,
        statsResponse
      ] = await Promise.all([
        publicService.getMapVisualization()
          .then(res => {
            console.log('📊 Map visualization response:', res)
            return res
          })
          .catch(err => {
            console.warn('📊 Map visualization failed:', err)
            return { countries: [] }
          }),
        fetch('/countries-110m.json').then(res => res.json()).catch(err => ({ objects: { countries: { geometries: [] } } })),
        publicService.getMasterPoliciesFast()
          .then(res => {
            console.log('📚 Master policies response:', res)
            return res
          })
          .catch(err => {
            console.warn('📚 Master policies failed:', err)
            return { policies: [] }
          }),
        publicService.getStatisticsFast()
          .then(res => {
            console.log('📈 Statistics response:', res)
            return res
          })
          .catch(err => {
            console.warn('📈 Statistics failed:', err)
            return { countries_with_policies: 0, total_policies: 0, total_countries: 0 }
          })
      ])

      // Process geo features
      const topojson = await import('topojson-client')
      const geoFeatures = geoResponse.objects?.countries ? 
        topojson.feature(geoResponse, geoResponse.objects.countries).features : []

      // Calculate real-time statistics from actual data
      const countries = mapVisualizationResponse.countries || []
      const policies = policiesResponse.policies || []
      
      console.log('📊 Raw data loaded:', {
        countriesCount: countries.length,
        policiesCount: policies.length,
        mapVisualizationTotal: mapVisualizationResponse.total_approved_policies,
        sampleCountry: countries[0]
      })
      
      // Calculate countries with policies - a country has policies if it has area_points > 0
      const countriesWithPolicies = countries.filter(country => {
        const areaPoints = country.area_points || 0
        return areaPoints > 0
      }).length

      // Use the total from map visualization API as it's more reliable
      let totalPolicies = mapVisualizationResponse.total_approved_policies || 0
      
      // Fallback: use policies array length if map visualization doesn't have total
      if (totalPolicies === 0 && policies.length > 0) {
        totalPolicies = policies.length
      }
      
      // Fallback: sum from countries data if both above are 0
      if (totalPolicies === 0 && countries.length > 0) {
        totalPolicies = countries.reduce((sum, country) => {
          const policyCount = country.total_approved_policies || 
                             country.policy_count ||
                             0
          return sum + policyCount
        }, 0)
      }

      console.log('📊 Calculated statistics:', {
        countriesWithPolicies,
        totalPolicies,
        totalCountries: mapVisualizationResponse.total_countries || statsResponse.total_countries || countries.length
      })

      const newMapData = {
        countries: countries,
        geoFeatures,
        masterPolicies: policies,
        mapStats: {
          countriesWithPolicies: countriesWithPolicies,
          totalPolicies: totalPolicies,
          totalCountries: mapVisualizationResponse.total_countries || statsResponse.total_countries || 0
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
