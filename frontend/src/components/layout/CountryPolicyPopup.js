'use client'
import { useState, useEffect } from 'react'
import { publicService } from '../../services/api'
import "../../styles/CountryPolicyPopup.css"

export default function CountryPolicyPopup({ country, onClose }) {
  const [visible, setVisible] = useState(false)
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [policyAreas, setPolicyAreas] = useState([])
  const [refreshKey, setRefreshKey] = useState(0) // Force refresh mechanism
  const [lastRefresh, setLastRefresh] = useState(null) // Track last refresh time

  // Define policy types with their icons and colors
  const policyTypes = {
    "AI Safety": {
      name: "AI Safety",
      icon: "🛡️",
      color: "bg-red-500",
      description: "Policies ensuring AI systems are safe and beneficial"
    },
    "CyberSafety": {
      name: "CyberSafety", 
      icon: "🔒",
      color: "bg-blue-500",
      description: "Policies for cybersecurity and online protection"
    },
    "Digital Education": {
      name: "Digital Education",
      icon: "🎓", 
      color: "bg-green-500",
      description: "Initiatives for education in digital skills and technologies"
    },
    "Digital Inclusion": {
      name: "Digital Inclusion",
      icon: "🌐",
      color: "bg-teal-500", 
      description: "Efforts to ensure universal access to digital resources"
    },
    "Digital Leisure": {
      name: "Digital Leisure",
      icon: "🎮",
      color: "bg-indigo-500",
      description: "Regulations concerning digital entertainment and leisure activities"
    },
    "(Dis)Information": {
      name: "(Dis)Information",
      icon: "📰",
      color: "bg-yellow-500",
      description: "Policies addressing misinformation and promoting accurate information"
    },
    "Digital Work": {
      name: "Digital Work", 
      icon: "💼",
      color: "bg-red-500",
      description: "Regulations for digital work environments and remote work"
    },
    "Mental Health": {
      name: "Mental Health",
      icon: "🧠",
      color: "bg-pink-500",
      description: "Policies addressing digital impact on mental wellbeing"
    },
    "Physical Health": {
      name: "Physical Health",
      icon: "❤️", 
      color: "bg-red-400",
      description: "Regulations focused on physical health aspects of digital use"
    },
    "Social Media/Gaming Regulation": {
      name: "Social Media/Gaming Regulation",
      icon: "📱",
      color: "bg-orange-500", 
      description: "Rules governing social media platforms and gaming content"
    },
    // Add legacy/alternative mappings
    "ai-safety": {
      name: "AI Safety",
      icon: "🛡️",
      color: "bg-red-500",
      description: "Policies ensuring AI systems are safe and beneficial"
    },
    "cyber-safety": {
      name: "CyberSafety",
      icon: "🔒", 
      color: "bg-blue-500",
      description: "Policies for cybersecurity and online protection"
    },
    "digital-education": {
      name: "Digital Education",
      icon: "🎓",
      color: "bg-green-500",
      description: "Initiatives for education in digital skills and technologies"
    },
    "digital-inclusion": {
      name: "Digital Inclusion",
      icon: "🌐",
      color: "bg-teal-500", 
      description: "Efforts to ensure universal access to digital resources"
    },
    "digital-leisure": {
      name: "Digital Leisure", 
      icon: "🎮",
      color: "bg-indigo-500",
      description: "Regulations concerning digital entertainment and leisure activities"
    },
    "disinformation": {
      name: "(Dis)Information",
      icon: "📰",
      color: "bg-yellow-500", 
      description: "Policies addressing misinformation and promoting accurate information"
    },
    "digital-work": {
      name: "Digital Work",
      icon: "💼",
      color: "bg-red-500",
      description: "Regulations for digital work environments and remote work"
    },
    "mental-health": {
      name: "Mental Health",
      icon: "🧠",
      color: "bg-pink-500",
      description: "Policies addressing digital impact on mental wellbeing"
    },
    "physical-health": {
      name: "Physical Health",
      icon: "❤️",
      color: "bg-red-400", 
      description: "Regulations focused on physical health aspects of digital use"
    },
    "social-media-gaming": {
      name: "Social Media/Gaming Regulation",
      icon: "📱",
      color: "bg-orange-500",
      description: "Rules governing social media platforms and gaming content"
    }
  }

  useEffect(() => {
    // Trigger animation after component mounts
    const timer = setTimeout(() => setVisible(true), 100)
    return () => clearTimeout(timer)
  }, [])

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://policy-tracker-5.onrender.com/api';

  useEffect(() => {
    if (country && country.name) {
      setLoading(true)
      
      // Use the API service instead of direct fetch
      const loadCountryPolicies = async () => {
        try {
          // Add timestamp and refresh key to prevent any caching
          const timestamp = new Date().getTime();
          const cacheBuster = `${timestamp}_${refreshKey}_${Math.random()}`;
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/public/master-policies-no-dedup?country=${encodeURIComponent(country.name)}&limit=1000&_t=${cacheBuster}`, {
            method: 'GET',
            headers: {
              'Cache-Control': 'no-cache, no-store, must-revalidate',
              'Pragma': 'no-cache',
              'Expires': '0'
            }
          });
          const data = await response.json();
          
          console.log("Country policies data:", data);
          
          if (data.success && data.policies) {
            // Enhanced filtering - remove any policies that should be hidden
            const activePolicies = data.policies.filter(policy => {
              // Must have active master status
              if (policy.master_status !== 'active') {
                console.log(`Filtering out policy ${policy.policyName} - master_status: ${policy.master_status}`);
                return false;
              }
              
              // Must not be deleted or rejected
              if (policy.status === 'deleted' || policy.status === 'rejected') {
                console.log(`Filtering out policy ${policy.policyName} - status: ${policy.status}`);
                return false;
              }
              
              // Must not have deleted master status (double check)
              if (policy.master_status === 'deleted') {
                console.log(`Filtering out policy ${policy.policyName} - master_status deleted`);
                return false;
              }
              
              return true;
            });
            
            console.log(`Found ${activePolicies.length} active policies for ${country.name} (filtered from ${data.policies.length})`);
            
            // Log any filtered policies for debugging
            const filteredOut = data.policies.length - activePolicies.length;
            if (filteredOut > 0) {
              console.log(`⚠️ Filtered out ${filteredOut} policies that should not be displayed`);
            }
            
            setPolicies(activePolicies)
            
            // Group policies by area with better fallback handling
            const areas = {}
            activePolicies.forEach((policy, index) => {
              const areaId = policy.policyArea || policy.area_id || "unknown"
              console.log(`Policy ${index}: ${policy.policyName || policy.name} -> Area: ${areaId}, Status: ${policy.status}`);
              
              if (!areas[areaId]) {
                const areaInfo = policyTypes[areaId] || {
                  name: policy.area_name || areaId || "Unknown Area",
                  icon: policy.area_icon || "📄",
                  color: "bg-gray-500",
                  description: "Policy area"
                };
                
                areas[areaId] = {
                  id: areaId,
                  name: areaInfo.name,
                  icon: areaInfo.icon,
                  color: areaInfo.color,
                  description: areaInfo.description,
                  policies: []
                }
              }
              // Add the policy to the area
              areas[areaId].policies.push(policy)
            })
            
            console.log("Grouped areas:", areas);
            setPolicyAreas(Object.values(areas))
          } else {
            console.warn("No policies found or API error:", data);
            setPolicies([])
            setPolicyAreas([])
          }
          setLoading(false)
          setLastRefresh(new Date().toLocaleTimeString()) // Update last refresh time
        } catch (err) {
          console.error("Error fetching policy data:", err)
          setPolicies([])
          setPolicyAreas([])
          setLoading(false)
          setLastRefresh(new Date().toLocaleTimeString()) // Update even on error
        }
      };
      
      loadCountryPolicies();
    }
  }, [country, refreshKey]) // Add refreshKey as dependency

  const handlePolicyClick = (policy) => {
    setSelectedPolicy(policy)
  }

  const closeSelectedPolicy = () => {
    setSelectedPolicy(null)
  }

  const handleClose = () => {
    setVisible(false)
    // Allow animation to complete before unmounting
    setTimeout(onClose, 500)
  }

  // Get country flag
  const getFlagUrl = (countryName) => {
    return `https://flagcdn.com/w160/${getCountryCode(countryName).toLowerCase()}.png`
  }

  // Helper function to get country code (simplified version)
  const getCountryCode = (countryName) => {
    const codes = {
      "United States": "us",
      "United Kingdom": "gb",
      "Canada": "ca",
      "Australia": "au",
      "Germany": "de",
      "France": "fr",
      "Japan": "jp",
      "China": "cn",
      "India": "in",
      "Brazil": "br",
      "Bangladesh": "bd",
      // Add more countries as needed
    }
    return codes[countryName] || "un" // default to UN flag if not found
  }

  if (!country) return null

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      {/* Backdrop */}
      <div 
        className={`absolute inset-0 bg-black transition-opacity duration-500 ${visible ? 'opacity-60' : 'opacity-0'}`} 
        onClick={handleClose}
      />
      
      {/* Main popup container */}
      <div className={`relative bg-gradient-to-br from-slate-900 to-blue-900 rounded-xl shadow-2xl max-w-5xl w-full m-4 overflow-hidden transition-all duration-500 max-h-[90vh] ${
        visible ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
      }`}>
        {/* Header with country name and flag */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 flex items-center justify-between">
          <div className="flex items-center">
            <img 
              src={getFlagUrl(country.name)}
              alt={`${country.name} flag`}
              className="h-8 mr-3 rounded shadow"
              onError={(e) => {
                e.target.src = "https://flagcdn.com/w160/un.png" // Fallback to UN flag
              }}
            />
            <h2 className="text-2xl font-bold text-white">{country.name}</h2>
          </div>
          <div className="flex items-center gap-2">
            {/* Refresh button */}
            <button 
              onClick={() => {
                console.log('🔄 Manually refreshing policies for', country.name);
                setRefreshKey(prev => prev + 1);
                setLoading(true);
                setPolicies([]); // Clear existing data
                setPolicyAreas([]); // Clear areas
                setSelectedPolicy(null); // Reset selection
              }}
              className="text-white hover:text-blue-300 transition-colors p-2 rounded-lg hover:bg-white/10"
              title="Refresh policies"
              disabled={loading}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            {/* Close button */}
            <button 
              onClick={handleClose}
              className="text-white hover:text-red-300 transition-colors p-2 rounded-lg hover:bg-white/10"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content area with scroll */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-300"></div>
            </div>
          ) : !selectedPolicy ? (
            <>
              <div className="text-center mb-6">
                <h3 className="text-xl text-white mb-2">
                  Policy Areas ({policyAreas.length}/10)
                </h3>
                <p className="text-blue-200 text-sm">
                  {policyAreas.length > 0 
                    ? "Click on a policy area to view policies"
                    : "No approved policies available for this country"}
                </p>
                {lastRefresh && (
                  <p className="text-blue-300 text-xs mt-2">
                    Last updated: {lastRefresh}
                  </p>
                )}
              </div>

              {/* Policy Score Bar */}
              <div className="mb-6 bg-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-semibold">Policy Area Coverage</span>
                  <span className="text-white">{policyAreas.length}/10</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full transition-all duration-500 ${
                      policyAreas.length >= 8 ? 'bg-green-500' : 
                      policyAreas.length >= 4 ? 'bg-yellow-500' : 
                      policyAreas.length >= 1 ? 'bg-red-500' : 'bg-gray-500'
                    }`}
                    style={{ width: `${(policyAreas.length / 10) * 100}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-blue-200 mt-1">
                  <span>1-3: Emerging</span>
                  <span>4-7: Developing</span>
                  <span>8-10: Advanced</span>
                </div>
              </div>

              {/* Policy Areas grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* First show areas that have policies */}
                {policyAreas.map((areaData) => {
                  const policyCount = areaData?.policies?.length || 0
                  
                  return (
                    <div
                      key={areaData.id}
                      className="policy-area-card cursor-pointer active"
                      onClick={() => setSelectedPolicy({ isAreaView: true, areaData })}
                    >
                      <div className="bg-white/10 hover:bg-white/20 rounded-lg p-4 h-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg border border-white/20">
                        <div className="policy-icon mb-2 flex justify-center">
                          <div className={`w-12 h-12 rounded-full ${areaData.color} flex items-center justify-center text-xl`}>
                            {areaData.icon}
                          </div>
                        </div>
                        <h4 className="text-white font-semibold text-center mb-2">
                          {areaData.name}
                        </h4>
                        <div className="text-center">
                          <span className="inline-block px-2 py-1 rounded-full text-xs bg-green-600 text-white">
                            {policyCount} {policyCount === 1 ? 'Policy' : 'Policies'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
                
                {/* Then show standard areas that don't have policies */}
                {Object.keys(policyTypes).filter(areaId => 
                  !areaId.includes('-') && // Only show the main format (not hyphenated versions)
                  !policyAreas.find(area => area.id === areaId || area.name === policyTypes[areaId].name)
                ).map((areaId) => {
                  return (
                    <div key={areaId} className="policy-area-card inactive">
                      <div className="bg-white/5 rounded-lg p-4 h-full transition-all duration-300 border border-white/10">
                        <div className="policy-icon mb-2 flex justify-center">
                          <div className={`w-12 h-12 rounded-full ${policyTypes[areaId].color} opacity-50 flex items-center justify-center text-xl`}>
                            {policyTypes[areaId].icon}
                          </div>
                        </div>
                        <h4 className="text-gray-400 font-semibold text-center mb-2">
                          {policyTypes[areaId].name}
                        </h4>
                        <div className="text-center">
                          <span className="inline-block px-2 py-1 rounded-full text-xs bg-gray-600 text-gray-300">
                            No Policies
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          ) : selectedPolicy.isAreaView ? (
            // Area view showing policies in this area
            <div className="area-policies-view animate-fadeIn">
              <button 
                onClick={closeSelectedPolicy}
                className="mb-4 flex items-center text-blue-300 hover:text-white transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to policy areas
              </button>
              
              <div className="mb-6">
                <div className="flex items-center mb-4">
                  <div className={`w-12 h-12 rounded-full ${selectedPolicy.areaData.color} flex items-center justify-center text-2xl mr-4`}>
                    {selectedPolicy.areaData.icon}
                  </div>
                  <div>
                    <h3 className="text-2xl text-white font-bold">{selectedPolicy.areaData.name}</h3>
                    <p className="text-blue-300">{selectedPolicy.areaData.policies.length} approved policies</p>
                  </div>
                </div>
                <p className="text-blue-200 text-sm">{selectedPolicy.areaData.description}</p>
              </div>

              {/* Policies in this area */}
              <div className="space-y-4">
                {selectedPolicy.areaData.policies.map((policy, index) => (
                  <div
                    key={index}
                    className="bg-white/10 rounded-lg p-4 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300"
                    onClick={() => setSelectedPolicy(policy)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="text-white font-semibold text-lg mb-1">
                          {policy.policyName || policy.name || 'Unnamed Policy'}
                        </h4>
                        <p className="text-blue-300 text-sm mb-2">
                          ID: {policy.policyId || 'N/A'}
                        </p>
                        {policy.policyDescription && (
                          <p className="text-blue-200 text-sm">{policy.policyDescription}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <span className="inline-block px-3 py-1 rounded-full text-sm bg-green-600 text-white">
                          Active
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            // Individual policy view
            <div className="policy-detail-view animate-fadeIn">
              <button 
                onClick={closeSelectedPolicy}
                className="mb-4 flex items-center text-blue-300 hover:text-white transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to policies
              </button>
              
              <div className="bg-white/5 rounded-lg p-6 border border-white/10">
                <div className="flex items-center mb-4">
                  <div className={`w-12 h-12 rounded-full ${policyTypes[selectedPolicy.policyArea]?.color || "bg-gray-500"} flex items-center justify-center text-2xl mr-4`}>
                    {policyTypes[selectedPolicy.policyArea]?.icon || "📄"}
                  </div>
                  <div>
                    <h3 className="text-2xl text-white">{selectedPolicy.policyName || selectedPolicy.name}</h3>
                    <p className="text-blue-300">{policyTypes[selectedPolicy.policyArea]?.name || selectedPolicy.policyArea}</p>
                  </div>
                </div>
                
                <div className="mb-4 flex flex-wrap gap-2">
                  <span className="inline-block px-3 py-1 rounded-full text-sm bg-blue-600 text-white">
                    {policyTypes[selectedPolicy.policyArea]?.name || selectedPolicy.policyArea}
                  </span>
                  {selectedPolicy.implementation?.deploymentYear && (
                    <span className="inline-block px-3 py-1 rounded-full text-sm bg-purple-600 text-white">
                      Deployed: {selectedPolicy.implementation.deploymentYear}
                    </span>
                  )}
                  <span className="inline-block px-3 py-1 rounded-full text-sm bg-green-600 text-white">
                    Approved
                  </span>
                </div>
                
                <div className="space-y-6">
                  {/* Policy Description */}
                  {selectedPolicy.policyDescription && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Description</h4>
                      <p className="text-blue-100">{selectedPolicy.policyDescription}</p>
                    </div>
                  )}

                  {/* Implementation Details */}
                  {selectedPolicy.implementation && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Implementation</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {selectedPolicy.implementation.yearlyBudget && (
                          <div>
                            <span className="text-blue-300 text-sm">Budget:</span>
                            <p className="text-white font-semibold">
                              {selectedPolicy.implementation.budgetCurrency || 'USD'} {parseFloat(selectedPolicy.implementation.yearlyBudget).toLocaleString()}
                            </p>
                          </div>
                        )}
                        {selectedPolicy.implementation.deploymentYear && (
                          <div>
                            <span className="text-blue-300 text-sm">Deployment Year:</span>
                            <p className="text-white font-semibold">{selectedPolicy.implementation.deploymentYear}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Target Groups */}
                  {selectedPolicy.targetGroups && selectedPolicy.targetGroups.length > 0 && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Target Groups</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedPolicy.targetGroups.map((group, idx) => (
                          <span key={idx} className="px-2 py-1 bg-blue-600 text-white rounded text-sm">
                            {group}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Policy Link */}
                  {selectedPolicy.policyLink && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">External Link</h4>
                      <a 
                        href={selectedPolicy.policyLink} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline flex items-center"
                      >
                        View Full Policy Document
                        <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}