'use client'
import { useState, useEffect } from "react"

export default function page(){
  const [pendingSubmissions, setPendingSubmissions] = useState([])
  const [expandedSubmission, setExpandedSubmission] = useState(null)
  const [currentPage, setCurrentPage] = useState(0)
  const submissionsPerPage = 5
  
  const policyNames = [
    "AI Safety",
    "CyberSafety",
    "Digital Education",
    "Digital Inclusion",
    "Digital Leisure",
    "(Dis)Information",
    "Digital Work",
    "Mental Health",
    "Physical Health",
    "Social Media/Gaming Regulation",
  ]

  useEffect(() => {
    fetchPendingSubmissions()
  }, [])

  const fetchPendingSubmissions = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/pending-submissions")
      const data = await response.json()
      setPendingSubmissions(data)
    } catch (error) {
      console.error("Failed to fetch pending submissions:", error)
      alert("Failed to load pending submissions.")
    }
  }

  const approvePolicy = async (country, policyIndex) => {
    try {
      const response = await fetch("http://localhost:8000/api/approve-policy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ country, policyIndex }),
      })
    
      if (response.ok) {
        alert(`Policy "${policyNames[policyIndex]}" for ${country} approved!`)
        
        // Remove the approved policy from the pending submissions UI
        const updatedSubmissions = [...pendingSubmissions]
        const countrySubmission = updatedSubmissions.find(sub => sub.country === country)
        if (countrySubmission) {
          countrySubmission.policies[policyIndex].status = "approved"
          setPendingSubmissions(updatedSubmissions)
        }
        
        // If all policies in this submission are now handled, remove the country from the list
        checkAndRemoveCountry(country)
      } else {
        alert("Failed to approve policy.")
      }
    } catch (error) {
      console.error("Error approving policy:", error)
      alert("An error occurred while approving policy.")
    }
  }

  const declinePolicy = async (country, policyIndex) => {
    try {
      const response = await fetch("http://localhost:8000/api/decline-policy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ country, policyIndex }),
      })
    
      if (response.ok) {
        alert(`Policy "${policyNames[policyIndex]}" for ${country} declined!`)
        
        // Remove the declined policy from the pending submissions UI
        const updatedSubmissions = [...pendingSubmissions]
        const countrySubmission = updatedSubmissions.find(sub => sub.country === country)
        if (countrySubmission) {
          countrySubmission.policies[policyIndex].status = "declined"
          setPendingSubmissions(updatedSubmissions)
        }
        
        // If all policies in this submission are now handled, remove the country from the list
        checkAndRemoveCountry(country)
      } else {
        alert("Failed to decline policy.")
      }
    } catch (error) {
      console.error("Error declining policy:", error)
      alert("An error occurred while declining policy.")
    }
  }

  const checkAndRemoveCountry = (country) => {
    const updatedSubmissions = [...pendingSubmissions]
    const countryIndex = updatedSubmissions.findIndex(sub => sub.country === country)
    
    if (countryIndex >= 0) {
      const allPoliciesHandled = updatedSubmissions[countryIndex].policies.every(policy => 
        !policy.file && !policy.text || policy.status === "approved" || policy.status === "declined"
      )
      
      if (allPoliciesHandled) {
        // Remove this country from the pending list
        updatedSubmissions.splice(countryIndex, 1)
        setPendingSubmissions(updatedSubmissions)
        
        // If this was the expanded submission, reset the expanded state
        if (expandedSubmission === countryIndex) {
          setExpandedSubmission(null)
        } else if (expandedSubmission > countryIndex) {
          // Adjust the expanded index if it was after the removed item
          setExpandedSubmission(expandedSubmission - 1)
        }
      }
    }
  }

  const toggleExpandSubmission = (index) => {
    if (expandedSubmission === index) {
      setExpandedSubmission(null)
    } else {
      setExpandedSubmission(index)
    }
  }

  const viewFile = (filePath) => {
    // Extract just the filename from the path
    const filename = filePath.split('/').pop()
    // Open file in a new tab
    window.open(`http://localhost:8000/api/policy-file/${filename}`, '_blank')
  }

  const openLink = (url) => {
    // Check if URL has http/https prefix, if not add it
    let finalUrl = url
    if (!/^https?:\/\//i.test(url)) {
      finalUrl = 'https://' + url
    }
    window.open(finalUrl, '_blank')
  }

  const getPolicyStatusColor = (policy) => {
    if (policy.status === "approved") return "#28A745"
    if (policy.status === "declined") return "#dc3545"
    return "#f8f9fa" // default background for pending
  }

  // Calculate pagination indexes
  const startIndex = currentPage * submissionsPerPage
  const endIndex = Math.min(startIndex + submissionsPerPage, pendingSubmissions.length)
  const totalPages = Math.ceil(pendingSubmissions.length / submissionsPerPage)
  
  // Get current page submissions
  const currentSubmissions = pendingSubmissions.slice(startIndex, endIndex)

  const nextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1)
      setExpandedSubmission(null) // Reset expanded state when changing pages
    }
  }

  const prevPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1)
      setExpandedSubmission(null) // Reset expanded state when changing pages
    }
  }

  return (
    <div style={{ 
      maxWidth: "800px", 
      margin: "0 auto", 
      padding: "20px",
      fontFamily: "Arial, sans-serif",
      color: "#333"
    }}>
      <h2 style={{ 
        textAlign: "center", 
        marginBottom: "30px",
        color: "#1a365d",
        fontSize: "28px"
      }}>
        Policy Admin Panel
      </h2>
      
      {pendingSubmissions.length === 0 ? (
        <div style={{ 
          textAlign: "center", 
          padding: "30px", 
          background: "#f0f4f8", 
          borderRadius: "8px",
          boxShadow: "0 2px 4px rgba(0,0,0,0.05)"
        }}>
          <p style={{ fontSize: "18px", color: "#4a5568" }}>
            No pending submissions to review.
          </p>
        </div>
      ) : (
        <div>
          {currentSubmissions.map((submission, index) => {
            // Calculate the actual index in the full array
            const actualIndex = startIndex + index;
            
            return (
              <div 
                key={index} 
                style={{ 
                  marginBottom: "24px", 
                  border: "1px solid #e2e8f0", 
                  padding: "18px", 
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px rgba(0,0,0,0.05)",
                  background: "#fff"
                }}
              >
                <div 
                  style={{ 
                    display: "flex", 
                    justifyContent: "space-between", 
                    alignItems: "center",
                    cursor: "pointer",
                    padding: "5px 0"
                  }} 
                  onClick={() => toggleExpandSubmission(actualIndex)}
                >
                  <h3 style={{ 
                    margin: 0, 
                    color: "#2c5282", 
                    fontSize: "22px", 
                    fontWeight: "600" 
                  }}>
                    {submission.country}
                  </h3>
                  <button 
                    style={{ 
                      padding: "8px 16px", 
                      background: expandedSubmission === actualIndex ? "#4a5568" : "#3182ce", 
                      color: "#FFFFFF", 
                      border: "none", 
                      borderRadius: "6px", 
                      cursor: "pointer",
                      fontWeight: "500",
                      fontSize: "14px",
                      transition: "all 0.2s ease"
                    }}
                  >
                    {expandedSubmission === actualIndex ? "Hide Details" : "View Details"}
                  </button>
                </div>
                
                {expandedSubmission === actualIndex && (
                  <div style={{ 
                    marginTop: "20px",
                    borderTop: "1px solid #e2e8f0",
                    paddingTop: "15px" 
                  }}>
                    <h4 style={{ 
                      color: "#4a5568", 
                      marginBottom: "15px",
                      fontSize: "18px"
                    }}>
                      Policy Details:
                    </h4>
                    <div style={{ display: "grid", gap: "18px" }}>
                      {submission.policies.map((policy, policyIndex) => (
                        policy.file || policy.text ? (
                          <div 
                            key={policyIndex} 
                            style={{ 
                              padding: "18px", 
                              border: "1px solid #e2e8f0", 
                              borderRadius: "6px",
                              background: getPolicyStatusColor(policy),
                              opacity: policy.status === "approved" || policy.status === "declined" ? 0.8 : 1,
                              boxShadow: "0 2px 4px rgba(0,0,0,0.05)"
                            }}
                          >
                            <div style={{ 
                              display: "flex", 
                              justifyContent: "space-between", 
                              alignItems: "flex-start" 
                            }}>
                              <h5 style={{ 
                                marginTop: 0, 
                                color: policy.status === "approved" || policy.status === "declined" ? "#fff" : "#2d3748",
                                fontSize: "17px",
                                fontWeight: "600" 
                              }}>
                                {policyNames[policyIndex]}
                                {policy.status === "approved" && " (Approved)"}
                                {policy.status === "declined" && " (Declined)"}
                              </h5>
                              
                              {policy.status !== "approved" && policy.status !== "declined" && (
                                <div style={{ display: "flex", gap: "10px" }}>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      declinePolicy(submission.country, policyIndex);
                                    }}
                                    style={{
                                      padding: "6px 12px",
                                      background: "#e53e3e",
                                      color: "#FFFFFF",
                                      border: "none",
                                      borderRadius: "4px",
                                      cursor: "pointer",
                                      fontSize: "14px",
                                      fontWeight: "500",
                                      transition: "background 0.2s ease",
                                      boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
                                    }}
                                    onMouseOver={(e) => e.target.style.background = "#c53030"}
                                    onMouseOut={(e) => e.target.style.background = "#e53e3e"}
                                  >
                                    Decline
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      approvePolicy(submission.country, policyIndex);
                                    }}
                                    style={{
                                      padding: "6px 12px",
                                      background: "#38a169",
                                      color: "#FFFFFF",
                                      border: "none",
                                      borderRadius: "4px",
                                      cursor: "pointer",
                                      fontSize: "14px",
                                      fontWeight: "500",
                                      transition: "background 0.2s ease",
                                      boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
                                    }}
                                    onMouseOver={(e) => e.target.style.background = "#2f855a"}
                                    onMouseOut={(e) => e.target.style.background = "#38a169"}
                                  >
                                    Approve
                                  </button>
                                </div>
                              )}
                            </div>
                            
                            <div style={{ 
                              marginTop: "12px",
                              color: policy.status === "approved" || policy.status === "declined" ? "#fff" : "#4a5568"
                            }}>
                              {policy.file && (
                                <div style={{ marginBottom: "12px" }}>
                                  <p style={{ 
                                    marginBottom: "8px", 
                                    fontWeight: "500",
                                    fontSize: "15px" 
                                  }}>
                                    File: {policy.file.split('/').pop()}
                                  </p>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      viewFile(policy.file);
                                    }}
                                    style={{
                                      padding: "6px 12px",
                                      background: policy.status === "approved" || policy.status === "declined" ? 
                                        "rgba(255,255,255,0.3)" : "#4299e1",
                                      color: "#FFFFFF",
                                      border: "none",
                                      borderRadius: "4px",
                                      cursor: "pointer",
                                      fontSize: "14px",
                                      fontWeight: "500",
                                      transition: "background 0.2s ease",
                                      boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
                                    }}
                                    onMouseOver={(e) => e.target.style.background = policy.status === "approved" || policy.status === "declined" ? 
                                      "rgba(255,255,255,0.5)" : "#3182ce"}
                                    onMouseOut={(e) => e.target.style.background = policy.status === "approved" || policy.status === "declined" ? 
                                      "rgba(255,255,255,0.3)" : "#4299e1"}
                                  >
                                    View File
                                  </button>
                                </div>
                              )}
                              {policy.text && (
                                <div>
                                  <p style={{ 
                                    marginBottom: "8px", 
                                    wordBreak: "break-all",
                                    fontWeight: "500",
                                    fontSize: "15px" 
                                  }}>
                                    Link: {policy.text}
                                  </p>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      openLink(policy.text);
                                    }}
                                    style={{
                                      padding: "6px 12px",
                                      background: policy.status === "approved" || policy.status === "declined" ? 
                                        "rgba(255,255,255,0.3)" : "#4299e1",
                                      color: "#FFFFFF",
                                      border: "none",
                                      borderRadius: "4px",
                                      cursor: "pointer",
                                      fontSize: "14px",
                                      fontWeight: "500",
                                      transition: "background 0.2s ease",
                                      boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
                                    }}
                                    onMouseOver={(e) => e.target.style.background = policy.status === "approved" || policy.status === "declined" ? 
                                      "rgba(255,255,255,0.5)" : "#3182ce"}
                                    onMouseOut={(e) => e.target.style.background = policy.status === "approved" || policy.status === "declined" ? 
                                      "rgba(255,255,255,0.3)" : "#4299e1"}
                                  >
                                    Open Link
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        ) : null
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
          
          {/* Pagination controls */}
          {pendingSubmissions.length > submissionsPerPage && (
            <div style={{ 
              display: "flex", 
              justifyContent: "center", 
              alignItems: "center", 
              marginTop: "30px", 
              gap: "15px" 
            }}>
              <button
                onClick={prevPage}
                disabled={currentPage === 0}
                style={{
                  padding: "8px 16px",
                  background: currentPage === 0 ? "#cbd5e0" : "#3182ce",
                  color: "#FFFFFF",
                  border: "none",
                  borderRadius: "6px",
                  cursor: currentPage === 0 ? "not-allowed" : "pointer",
                  fontWeight: "500",
                  fontSize: "14px",
                  transition: "all 0.2s ease",
                  opacity: currentPage === 0 ? 0.6 : 1
                }}
              >
                Previous
              </button>
              <span style={{ fontSize: "16px", color: "#4a5568" }}>
                Page {currentPage + 1} of {totalPages}
              </span>
              <button
                onClick={nextPage}
                disabled={currentPage >= totalPages - 1}
                style={{
                  padding: "8px 16px",
                  background: currentPage >= totalPages - 1 ? "#cbd5e0" : "#3182ce",
                  color: "#FFFFFF",
                  border: "none",
                  borderRadius: "6px",
                  cursor: currentPage >= totalPages - 1 ? "not-allowed" : "pointer",
                  fontWeight: "500",
                  fontSize: "14px",
                  transition: "all 0.2s ease",
                  opacity: currentPage >= totalPages - 1 ? 0.6 : 1
                }}
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}