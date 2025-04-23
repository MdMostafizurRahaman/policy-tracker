// 'use client'
// import { useState, useEffect } from 'react'
// import "./CountryPolicyPopup.css"

// export default function CountryPolicyPopup({ country, policies, onClose }) {
//   const [visible, setVisible] = useState(false)
//   const [selectedPolicy, setSelectedPolicy] = useState(null)

//   useEffect(() => {
//     // Trigger animation after component mounts
//     const timer = setTimeout(() => setVisible(true), 100)
//     return () => clearTimeout(timer)
//   }, [])

//   const handlePolicyClick = (policy) => {
//     setSelectedPolicy(policy)
//   }

//   const closeSelectedPolicy = () => {
//     setSelectedPolicy(null)
//   }

//   const handleClose = () => {
//     setVisible(false)
//     // Allow animation to complete before unmounting
//     setTimeout(onClose, 500)
//   }

//   if (!country) return null

//   return (
//     <div className="fixed inset-0 flex items-center justify-center z-50">
//       {/* Backdrop */}
//       <div 
//         className={`absolute inset-0 bg-black transition-opacity duration-500 ${visible ? 'opacity-60' : 'opacity-0'}`} 
//         onClick={handleClose}
//       />
      
//       {/* Main popup container */}
//       <div className={`relative bg-gradient-to-br from-slate-900 to-blue-900 rounded-xl shadow-2xl max-w-4xl w-full m-4 overflow-hidden transition-all duration-500 ${
//         visible ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
//       }`}>
//         {/* Header with country name */}
//         <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 flex items-center justify-between">
//           <h2 className="text-2xl font-bold text-white">{country.name}</h2>
//           <button 
//             onClick={handleClose}
//             className="text-white hover:text-red-300 transition-colors"
//           >
//             <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
//             </svg>
//           </button>
//         </div>

//         {/* Content area */}
//         <div className="p-6">
//           {!selectedPolicy ? (
//             <>
//               <div className="text-center mb-6">
//                 <h3 className="text-xl text-white mb-2">
//                   Available Policies
//                 </h3>
//                 <p className="text-blue-200 text-sm">
//                   Click on a policy to view details
//                 </p>
//               </div>

//               {/* Policies grid - animated entrance for each policy */}
//               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
//                 {policies.map((policy, index) => (
//                   <div
//                     key={policy.id}
//                     className="policy-card cursor-pointer"
//                     style={{
//                       animationDelay: `${index * 0.1}s`,
//                     }}
//                     onClick={() => handlePolicyClick(policy)}
//                   >
//                     <div className="bg-white/10 hover:bg-white/20 rounded-lg p-4 h-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg border border-white/20">
//                       <div className="policy-icon mb-2 flex justify-center">
//                         {policy.type === 'economic' && (
//                           <div className="w-12 h-12 rounded-full bg-yellow-500 flex items-center justify-center">
//                             <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//                               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
//                             </svg>
//                           </div>
//                         )}
//                         {policy.type === 'environmental' && (
//                           <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center">
//                             <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//                               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
//                             </svg>
//                           </div>
//                         )}
//                         {policy.type === 'social' && (
//                           <div className="w-12 h-12 rounded-full bg-purple-500 flex items-center justify-center">
//                             <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//                               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
//                             </svg>
//                           </div>
//                         )}
//                       </div>
//                       <h4 className="text-white font-semibold text-center">{policy.name}</h4>
//                       <p className="text-blue-200 text-sm mt-2 text-center">{policy.type}</p>
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </>
//           ) : (
//             <div className="policy-detail-view animate-fadeIn">
//               <button 
//                 onClick={closeSelectedPolicy}
//                 className="mb-4 flex items-center text-blue-300 hover:text-white transition-colors"
//               >
//                 <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
//                 </svg>
//                 Back to policies
//               </button>
              
//               <div className="bg-white/5 rounded-lg p-6 border border-white/10">
//                 <h3 className="text-xl text-white mb-4">{selectedPolicy.name}</h3>
//                 <div className="mb-4">
//                   <span className="inline-block px-3 py-1 rounded-full text-sm bg-blue-600 text-white">
//                     {selectedPolicy.type}
//                   </span>
//                   <span className="inline-block px-3 py-1 rounded-full text-sm bg-purple-600 text-white ml-2">
//                     Enacted: {selectedPolicy.year}
//                   </span>
//                 </div>
//                 <p className="text-blue-100 mb-4">{selectedPolicy.description}</p>
                
//                 <div className="mt-6 bg-black/20 rounded-lg p-4">
//                   <h4 className="text-white text-lg mb-2">Impact & Metrics</h4>
//                   <ul className="space-y-2">
//                     {selectedPolicy.metrics.map((metric, idx) => (
//                       <li key={idx} className="flex items-start">
//                         <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-400 mr-2 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//                           <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
//                         </svg>
//                         <span className="text-blue-200">{metric}</span>
//                       </li>
//                     ))}
//                   </ul>
//                 </div>
//               </div>
//             </div>
//           )}
//         </div>
//       </div>
//     </div>
//   )
// }


































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

  useEffect(() => {
    if (country && country.name) {
      setLoading(true)
      // Fetch policy data for this country
      fetch(`http://localhost:8000/api/country-policies/${encodeURIComponent(country.name)}`)
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
      <div className={`relative bg-gradient-to-br from-slate-900 to-blue-900 rounded-xl shadow-2xl max-w-4xl w-full m-4 overflow-hidden transition-all duration-500 ${
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

        {/* Content area */}
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-300"></div>
            </div>
          ) : !selectedPolicy ? (
            <>
              <div className="text-center mb-6">
                <h3 className="text-xl text-white mb-2">
                  Available Policies
                </h3>
                <p className="text-blue-200 text-sm">
                  {policies.length > 0 
                    ? "Click on a policy to view details" 
                    : "No policies available for this country"}
                </p>
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
                      <h4 className="text-white font-semibold text-center">{policy.name}</h4>
                    </div>
                  </div>
                ))}
              </div>
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
                  <div className={`w-10 h-10 rounded-full ${policyTypes[selectedPolicy.type]?.color || "bg-gray-500"} flex items-center justify-center text-xl mr-3`}>
                    {policyTypes[selectedPolicy.type]?.icon || "📄"}
                  </div>
                  <h3 className="text-xl text-white">{selectedPolicy.name}</h3>
                </div>
                
                <div className="mb-4">
                  <p className="text-blue-200 text-sm mb-2">
                    {policyTypes[selectedPolicy.type]?.description || "Policy information"}
                  </p>
                </div>
                
                {selectedPolicy.text && (
                  <div className="mt-4 bg-white/5 rounded-lg p-4 text-blue-100">
                    <h4 className="text-white text-lg mb-2">Policy Text</h4>
                    <p>{selectedPolicy.text}</p>
                  </div>
                )}
                
                {selectedPolicy.file && (
                  <div className="mt-4">
                    <h4 className="text-white text-lg mb-2">Policy Document</h4>
                    <a 
                      href={`http://localhost:8000/api/policy-file/${selectedPolicy.file.split('/').pop()}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      View Policy Document
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}