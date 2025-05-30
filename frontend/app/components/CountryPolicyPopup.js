'use client'
import { useState, useEffect } from 'react'
import "./CountryPolicyPopup.css"

export default function CountryPolicyPopup({ country, onClose }) {
  const [visible, setVisible] = useState(false)
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)

  // Define policy types with their icons and colors
  const policyTypes = {
    "AI Safety": {
      icon: "🤖",
      color: "bg-purple-500",
      description: "Policies regarding artificial intelligence safety and regulation"
    },
    "CyberSafety": {
      icon: "🔒",
      color: "bg-blue-500",
      description: "Policies for cybersecurity and online protection"
    },
    "Digital Education": {
      icon: "🎓",
      color: "bg-green-500",
      description: "Initiatives for education in digital skills and technologies"
    },
    "Digital Inclusion": {
      icon: "🌐",
      color: "bg-teal-500",
      description: "Efforts to ensure universal access to digital resources"
    },
    "Digital Leisure": {
      icon: "🎮",
      color: "bg-indigo-500",
      description: "Regulations concerning digital entertainment and leisure activities"
    },
    "(Dis)Information": {
      icon: "📰",
      color: "bg-yellow-500",
      description: "Policies addressing misinformation and promoting accurate information"
    },
    "Digital Work": {
      icon: "💼",
      color: "bg-red-500",
      description: "Regulations for digital work environments and remote work"
    },
    "Mental Health": {
      icon: "🧠",
      color: "bg-pink-500",
      description: "Policies addressing digital impact on mental wellbeing"
    },
    "Physical Health": {
      icon: "❤️",
      color: "bg-red-400",
      description: "Regulations focused on physical health aspects of digital use"
    },
    "Social Media/Gaming Regulation": {
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
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL|| 'https://policy-tracker-5.onrender.com/api';

  useEffect(() => {
    if (country && country.name) {
      setLoading(true)
      // Fetch policy data for this country
      fetch(`${API_BASE_URL}/api/country-policies/${encodeURIComponent(country.name)}`)
        .then(res => res.json())
        .then(data => {
          // Transform the data into a more usable format
          const policyList = []
          
          // Check each policy field and create entries for those that exist
          const policyFields = [
            "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
            "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
            "Physical Health", "Social Media/Gaming Regulation"
          ]
          
          policyFields.forEach((field, index) => {
            if (data.policies[index] && data.policies[index].status === "approved") {
              policyList.push({
                id: index,
                name: field,
                type: field,
                file: data.policies[index].file || null,
                text: data.policies[index].text || null,
                year: data.policies[index].year || "N/A",
                description: data.policies[index].description || 
                            policyTypes[field]?.description || 
                            "No detailed description available",
                metrics: data.policies[index].metrics || [],
                policy_name: data.policies[index].policy_name || field,
                target_groups: data.policies[index].target_groups || [],
                policy_link: data.policies[index].policy_link || "",
                ai_principles: data.policies[index].ai_principles || [],
                human_rights_alignment: data.policies[index].human_rights_alignment || false,
                environmental_considerations: data.policies[index].environmental_considerations || false,
                international_cooperation: data.policies[index].international_cooperation || false,
                has_consultation: data.policies[index].has_consultation || false,
                is_evaluated: data.policies[index].is_evaluated || false,
                risk_assessment: data.policies[index].risk_assessment || false
              })
            }
          })
          
          setPolicies(policyList)
          setLoading(false)
        })
        .catch(err => {
          console.error("Error fetching policy data:", err)
          setLoading(false)
        })
    }
  }, [country])

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
    // This function would normally use a proper API or database
    // For demo purposes, using a flag API service
    return `https://flagcdn.com/w160/${getCountryCode(countryName).toLowerCase()}.png`
  }

  // Helper function to get country code (simplified version)
  const getCountryCode = (countryName) => {
    // This would be a more complete mapping in production
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
            />
            <h2 className="text-2xl font-bold text-white">{country.name}</h2>
          </div>
          <button 
            onClick={handleClose}
            className="text-white hover:text-red-300 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
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
                  Available Policies ({policies.length}/10)
                </h3>
                <p className="text-blue-200 text-sm">
                  {policies.length > 0 
                    ? "Click on a policy to view details"
                    : "No policies available for this country"}
                </p>
              </div>

              {/* Policy Score Bar */}
              <div className="mb-6 bg-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-semibold">Policy Completion</span>
                  <span className="text-white">{policies.length}/10</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full transition-all duration-500 ${
                      policies.length >= 8 ? 'bg-green-500' : 
                      policies.length >= 4 ? 'bg-yellow-500' : 
                      policies.length >= 1 ? 'bg-red-500' : 'bg-gray-500'
                    }`}
                    style={{ width: `${(policies.length / 10) * 100}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-blue-200 mt-1">
                  <span>0-3: Emerging</span>
                  <span>4-7: Developing</span>
                  <span>8-10: Advanced</span>
                </div>
              </div>

              {/* Policies grid - animated entrance for each policy */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {policies.map((policy, index) => (
                  <div
                    key={policy.id}
                    className="policy-card cursor-pointer"
                    style={{
                      animationDelay: `${index * 0.1}s`,
                    }}
                    onClick={() => handlePolicyClick(policy)}
                  >
                    <div className={`bg-white/10 hover:bg-white/20 rounded-lg p-4 h-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg border border-white/20`}>
                      <div className="policy-icon mb-2 flex justify-center">
                        <div className={`w-12 h-12 rounded-full ${policyTypes[policy.type]?.color || "bg-gray-500"} flex items-center justify-center text-xl`}>
                          {policyTypes[policy.type]?.icon || "📄"}
                        </div>
                      </div>
                      <h4 className="text-white font-semibold text-center mb-2">{policy.name}</h4>
                      <div className="text-center">
                        <span className="inline-block px-2 py-1 rounded-full text-xs bg-green-600 text-white">
                          Active
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Show missing policies */}
              {policies.length < 10 && (
                <div className="mt-8">
                  <h4 className="text-white text-lg mb-4">Areas for Development</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.keys(policyTypes).filter(type => 
                      !policies.some(p => p.type === type)
                    ).map((missingType, index) => (
                      <div key={missingType} className="bg-white/5 rounded-lg p-3 border border-white/10">
                        <div className="flex items-center">
                          <div className={`w-8 h-8 rounded-full ${policyTypes[missingType]?.color || "bg-gray-500"} flex items-center justify-center text-sm opacity-50 mr-3`}>
                            {policyTypes[missingType]?.icon || "📄"}
                          </div>
                          <span className="text-blue-300 text-sm">{missingType}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
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
                  <div className={`w-12 h-12 rounded-full ${policyTypes[selectedPolicy.type]?.color || "bg-gray-500"} flex items-center justify-center text-2xl mr-4`}>
                    {policyTypes[selectedPolicy.type]?.icon || "📄"}
                  </div>
                  <div>
                    <h3 className="text-2xl text-white">{selectedPolicy.policy_name || selectedPolicy.name}</h3>
                    <p className="text-blue-300">{selectedPolicy.type}</p>
                  </div>
                </div>
                
                <div className="mb-4 flex flex-wrap gap-2">
                  <span className="inline-block px-3 py-1 rounded-full text-sm bg-blue-600 text-white">
                    {selectedPolicy.type}
                  </span>
                  <span className="inline-block px-3 py-1 rounded-full text-sm bg-purple-600 text-white">
                    Enacted: {selectedPolicy.year}
                  </span>
                  {selectedPolicy.is_evaluated && (
                    <span className="inline-block px-3 py-1 rounded-full text-sm bg-green-600 text-white">
                      Evaluated
                    </span>
                  )}
                  {selectedPolicy.risk_assessment && (
                    <span className="inline-block px-3 py-1 rounded-full text-sm bg-orange-600 text-white">
                      Risk Assessed
                    </span>
                  )}
                </div>
                
                <p className="text-blue-200 text-sm mb-4">
                  {policyTypes[selectedPolicy.type]?.description || "Policy information"}
                </p>
                
                <div className="space-y-6">
                  {/* Policy Description */}
                  {selectedPolicy.description && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Description</h4>
                      <p className="text-blue-100">{selectedPolicy.description}</p>
                    </div>
                  )}

                  {/* Target Groups */}
                  {selectedPolicy.target_groups && selectedPolicy.target_groups.length > 0 && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Target Groups</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedPolicy.target_groups.map((group, idx) => (
                          <span key={idx} className="px-2 py-1 bg-blue-600 text-white rounded text-sm">
                            {group}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* AI Principles */}
                  {selectedPolicy.ai_principles && selectedPolicy.ai_principles.length > 0 && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">AI Principles</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedPolicy.ai_principles.map((principle, idx) => (
                          <span key={idx} className="px-2 py-1 bg-purple-600 text-white rounded text-sm">
                            {principle}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Alignment Features */}
                  {(selectedPolicy.human_rights_alignment || selectedPolicy.environmental_considerations || selectedPolicy.international_cooperation) && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Policy Alignment</h4>
                      <div className="space-y-2">
                        {selectedPolicy.human_rights_alignment && (
                          <div className="flex items-center text-green-300">
                            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            Human Rights Aligned
                          </div>
                        )}
                        {selectedPolicy.environmental_considerations && (
                          <div className="flex items-center text-green-300">
                            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            Environmental Considerations
                          </div>
                        )}
                        {selectedPolicy.international_cooperation && (
                          <div className="flex items-center text-green-300">
                            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            International Cooperation
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Process Features */}
                  {(selectedPolicy.has_consultation || selectedPolicy.is_evaluated || selectedPolicy.risk_assessment) && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Policy Process</h4>
                      <div className="space-y-2">
                        {selectedPolicy.has_consultation && (
                          <div className="flex items-center text-blue-300">
                            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                            </svg>
                            Public Consultation Conducted
                          </div>
                        )}
                        {selectedPolicy.is_evaluated && (
                          <div className="flex items-center text-blue-300">
                            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            Policy Evaluated
                          </div>
                        )}
                        {selectedPolicy.risk_assessment && (
                          <div className="flex items-center text-orange-300">
                            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            Risk Assessment Completed
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Metrics */}
                  {selectedPolicy.metrics && selectedPolicy.metrics.length > 0 && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Policy Metrics</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {selectedPolicy.metrics.map((metric, idx) => (
                          <div key={idx} className="bg-white/10 rounded p-2">
                            <span className="text-blue-100 text-sm">{metric}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Policy Text/Content */}
                  {selectedPolicy.text && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Policy Content</h4>
                      <div className="text-blue-100 text-sm whitespace-pre-wrap max-h-40 overflow-y-auto">
                        {selectedPolicy.text}
                      </div>
                    </div>
                  )}

                  {/* Policy Link */}
                  {selectedPolicy.policy_link && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">External Link</h4>
                      <a 
                        href={selectedPolicy.policy_link} 
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

                  {/* File Download */}
                  {selectedPolicy.file && (
                    <div className="bg-black/20 rounded-lg p-4">
                      <h4 className="text-white text-lg mb-2">Policy Document</h4>
                      <button 
                        onClick={() => window.open(`http://localhost:8000/api/policy-file/${selectedPolicy.file}`, '_blank')}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center transition-colors"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Download Policy File
                      </button>
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