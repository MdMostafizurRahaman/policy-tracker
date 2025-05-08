// 'use client'
// import { useState, useEffect } from "react"

// export default function page(){
//   const [pendingSubmissions, setPendingSubmissions] = useState([])
//   const [expandedSubmission, setExpandedSubmission] = useState(null)
//   const [currentPage, setCurrentPage] = useState(0)
//   const [totalPages, setTotalPages] = useState(0)
//   const [adminNotes, setAdminNotes] = useState({})
//   const [editingNote, setEditingNote] = useState(null)
//   const [noteText, setNoteText] = useState("")
//   const [isLoading, setIsLoading] = useState(true)
//   const [error, setError] = useState(null)
//   const submissionsPerPage = 5
  
//   // API base URL - centralized for easy changes
//   // Ensure it's correctly set in your .env.local file: NEXT_PUBLIC_API_URL=http://localhost:8000
//   const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  
//   const policyNames = [
//     "AI Safety",
//     "CyberSafety",
//     "Digital Education",
//     "Digital Inclusion",
//     "Digital Leisure",
//     "(Dis)Information",
//     "Digital Work",
//     "Mental Health",
//     "Physical Health",
//     "Social Media/Gaming Regulation",
//   ]

//   useEffect(() => {
//     fetchPendingSubmissions()
//   }, [currentPage]) // Fetch when page changes

//   // Load admin notes from localStorage on initial load
//   useEffect(() => {
//     const savedNotes = localStorage.getItem('adminNotes')
//     if (savedNotes) {
//       try {
//         setAdminNotes(JSON.parse(savedNotes))
//       } catch (e) {
//         console.error("Failed to parse saved notes:", e)
//         localStorage.removeItem('adminNotes') // Remove corrupted data
//       }
//     }
//   }, [])

//   // Save admin notes to localStorage whenever they change
//   useEffect(() => {
//     localStorage.setItem('adminNotes', JSON.stringify(adminNotes))
//   }, [adminNotes])

//   const fetchPendingSubmissions = async () => {
//     setIsLoading(true)
//     setError(null)
    
//     try {
//       console.log(`Fetching from: ${API_BASE_URL}/api/pending-submissions?page=${currentPage}&per_page=${submissionsPerPage}`)
      
//       const response = await fetch(`${API_BASE_URL}/api/pending-submissions?page=${currentPage}&per_page=${submissionsPerPage}`, {
//         headers: {
//           'Accept': 'application/json',
//           'Content-Type': 'application/json',
//         },
//         credentials: 'include', // This requires specific origins in CORS settings
//         signal: AbortSignal.timeout(10000) // 10 second timeout
//       })
      
//       if (!response.ok) {
//         throw new Error(`HTTP error! Status: ${response.status}`)
//       }
      
//       const data = await response.json()
      
//       // Extract the submissions array and pagination info
//       setPendingSubmissions(data.submissions || [])
//       setTotalPages(data.pagination?.total_pages || 0)
//     } catch (error) {
//       console.error("Failed to fetch pending submissions:", error)
//       setError(error.message || "Failed to load pending submissions")
//     } finally {
//       setIsLoading(false)
//     }
//   }

//   const retryConnection = () => {
//     fetchPendingSubmissions()
//   }

//   const approvePolicy = async (country, policyIndex) => {
//     try {
//       const response = await fetch(`${API_BASE_URL}/api/approve-policy`, {
//         method: "POST",
//         headers: { 
//           "Content-Type": "application/json",
//           'Accept': 'application/json',
//         },
//         credentials: 'include',
//         body: JSON.stringify({ country, policyIndex }),
//       })
    
//       if (response.ok) {
//         alert(`Policy "${policyNames[policyIndex]}" for ${country} approved!`)
        
//         // Update the status in the UI
//         const updatedSubmissions = [...pendingSubmissions]
//         const countrySubmission = updatedSubmissions.find(sub => sub.country === country)
//         if (countrySubmission) {
//           countrySubmission.policies[policyIndex].status = "approved"
//           setPendingSubmissions(updatedSubmissions)
//         }
        
//         // If all policies in this submission are now handled, we'll check in checkAndRemoveCountry
//         checkAndRemoveCountry(country)
//       } else {
//         const errorData = await response.json().catch(() => ({}))
//         alert(`Failed to approve policy: ${errorData.detail || response.statusText || 'Unknown error'}`)
//       }
//     } catch (error) {
//       console.error("Error approving policy:", error)
//       alert("An error occurred while approving policy. Please check your network connection and ensure the API server is running.")
//     }
//   }

//   const declinePolicy = async (country, policyIndex) => {
//     try {
//       const response = await fetch(`${API_BASE_URL}/api/decline-policy`, {
//         method: "POST",
//         headers: { 
//           "Content-Type": "application/json",
//           'Accept': 'application/json', 
//         },
//         credentials: 'include',
//         body: JSON.stringify({ country, policyIndex }),
//       })
    
//       if (response.ok) {
//         alert(`Policy "${policyNames[policyIndex]}" for ${country} declined!`)
        
//         // Update the status in the UI
//         const updatedSubmissions = [...pendingSubmissions]
//         const countrySubmission = updatedSubmissions.find(sub => sub.country === country)
//         if (countrySubmission) {
//           countrySubmission.policies[policyIndex].status = "declined"
//           setPendingSubmissions(updatedSubmissions)
//         }
        
//         // If all policies in this submission are now handled, we'll check in checkAndRemoveCountry
//         checkAndRemoveCountry(country)
//       } else {
//         const errorData = await response.json().catch(() => ({}))
//         alert(`Failed to decline policy: ${errorData.detail || response.statusText || 'Unknown error'}`)
//       }
//     } catch (error) {
//       console.error("Error declining policy:", error)
//       alert("An error occurred while declining policy. Please check your network connection and ensure the API server is running.")
//     }
//   }

//   const checkAndRemoveCountry = (country) => {
//     const updatedSubmissions = [...pendingSubmissions]
//     const countryIndex = updatedSubmissions.findIndex(sub => sub.country === country)
    
//     if (countryIndex >= 0) {
//       const allPoliciesHandled = updatedSubmissions[countryIndex].policies.every(policy => 
//         !policy.file && !policy.text || policy.status === "approved" || policy.status === "declined"
//       )
      
//       if (allPoliciesHandled) {
//         // Instead of immediately removing, now we check if admin wants to keep it
//         const noteKey = `${country}_note`
//         const hasKeepNote = adminNotes[noteKey]?.toLowerCase().includes('keep') || 
//                             adminNotes[noteKey]?.toLowerCase().includes('change later') ||
//                             adminNotes[noteKey]?.toLowerCase().includes('will change')
        
//         if (!hasKeepNote) {
//           // Remove this country from the pending list
//           updatedSubmissions.splice(countryIndex, 1)
//           setPendingSubmissions(updatedSubmissions)
          
//           // If this was the expanded submission, reset the expanded state
//           if (expandedSubmission === countryIndex) {
//             setExpandedSubmission(null)
//           } else if (expandedSubmission > countryIndex) {
//             // Adjust the expanded index if it was after the removed item
//             setExpandedSubmission(expandedSubmission - 1)
//           }
          
//           // If this was the last item on the page and not the first page, go to previous page
//           if (updatedSubmissions.length === 0 && currentPage > 0) {
//             setCurrentPage(currentPage - 1)
//           } else {
//             // Otherwise, refresh the current page
//             fetchPendingSubmissions()
//           }
//         }
//       }
//     }
//   }

//   // New function for manually removing a country from the list
//   const removeCountry = (country) => {
//     const updatedSubmissions = [...pendingSubmissions]
//     const countryIndex = updatedSubmissions.findIndex(sub => sub.country === country)
    
//     if (countryIndex >= 0) {
//       // Remove the country
//       updatedSubmissions.splice(countryIndex, 1)
//       setPendingSubmissions(updatedSubmissions)
      
//       // Also remove any notes for this country
//       const updatedNotes = { ...adminNotes }
//       delete updatedNotes[`${country}_note`]
//       setAdminNotes(updatedNotes)
      
//       // If this was the expanded submission, reset the expanded state
//       if (expandedSubmission === countryIndex) {
//         setExpandedSubmission(null)
//       } else if (expandedSubmission > countryIndex) {
//         // Adjust the expanded index if it was after the removed item
//         setExpandedSubmission(expandedSubmission - 1)
//       }
      
//       // If this was the last item on the page and not the first page, go to previous page
//       if (updatedSubmissions.length === 0 && currentPage > 0) {
//         setCurrentPage(currentPage - 1)
//       }
//     }
//   }

//   // New function to start editing a note
//   const startEditNote = (country) => {
//     const noteKey = `${country}_note`
//     setEditingNote(country)
//     setNoteText(adminNotes[noteKey] || "")
//   }

//   // New function to save a note
//   const saveNote = (country) => {
//     const noteKey = `${country}_note`
//     const updatedNotes = { ...adminNotes }
    
//     if (noteText.trim() === "") {
//       delete updatedNotes[noteKey]
//     } else {
//       updatedNotes[noteKey] = noteText
//     }
    
//     setAdminNotes(updatedNotes)
//     setEditingNote(null)
//     setNoteText("")
//   }

//   const toggleExpandSubmission = (index) => {
//     if (expandedSubmission === index) {
//       setExpandedSubmission(null)
//     } else {
//       setExpandedSubmission(index)
//     }
//   }

//   const viewFile = (filePath) => {
//     // Extract just the filename from the path
//     const filename = filePath.split('/').pop()
//     // Open file in a new tab
//     window.open(`${API_BASE_URL}/api/policy-file/${filename}`, '_blank')
//   }

//   const openLink = (url) => {
//     // Check if URL has http/https prefix, if not add it
//     let finalUrl = url
//     if (!/^https?:\/\//i.test(url)) {
//       finalUrl = 'https://' + url
//     }
//     window.open(finalUrl, '_blank')
//   }

//   const getPolicyStatusColor = (policy) => {
//     if (policy.status === "approved") return "#28A745"
//     if (policy.status === "declined") return "#dc3545"
//     return "#f8f9fa" // default background for pending
//   }

//   const nextPage = () => {
//     if (currentPage < totalPages - 1) {
//       setCurrentPage(currentPage + 1)
//       setExpandedSubmission(null) // Reset expanded state when changing pages
//     }
//   }

//   const prevPage = () => {
//     if (currentPage > 0) {
//       setCurrentPage(currentPage - 1)
//       setExpandedSubmission(null) // Reset expanded state when changing pages
//     }
//   }

//   const ConnectionErrorDisplay = () => (
//     <div style={{ 
//       textAlign: "center", 
//       padding: "30px", 
//       background: "#fff3f3", 
//       borderRadius: "8px",
//       boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
//       margin: "30px 0",
//       border: "1px solid #ffcccc"
//     }}>
//       <h3 style={{ color: "#d32f2f", marginBottom: "15px" }}>Connection Error</h3>
//       <p style={{ marginBottom: "20px", fontSize: "16px" }}>
//         Failed to connect to the API server. Please ensure the server is running at:
//         <br />
//         <code style={{ 
//           background: "#f5f5f5", 
//           padding: "4px 8px", 
//           borderRadius: "4px",
//           display: "inline-block",
//           margin: "8px 0" 
//         }}>
//           {API_BASE_URL}
//         </code>
//       </p>
//       <div style={{ marginBottom: "15px" }}>
//         <p style={{ fontWeight: "500", marginBottom: "10px" }}>Please check:</p>
//         <ul style={{ 
//           textAlign: "left", 
//           maxWidth: "450px", 
//           margin: "0 auto",
//           listStyle: "disc inside" 
//         }}>
//           <li style={{ marginBottom: "5px" }}>The FastAPI server is running</li>
//           <li style={{ marginBottom: "5px" }}>The NEXT_PUBLIC_API_URL environment variable is set correctly</li>
//           <li style={{ marginBottom: "5px" }}>CORS settings allow requests from this origin</li>
//           <li style={{ marginBottom: "5px" }}>Network connectivity between frontend and API</li>
//         </ul>
//       </div>
//       <button
//         onClick={retryConnection}
//         style={{
//           padding: "10px 20px",
//           background: "#1976d2",
//           color: "#FFFFFF",
//           border: "none",
//           borderRadius: "6px",
//           cursor: "pointer",
//           fontWeight: "500",
//           fontSize: "16px",
//           transition: "background 0.2s ease"
//         }}
//       >
//         Retry Connection
//       </button>
//     </div>
//   );

//   const LoadingSpinner = () => (
//     <div style={{ 
//       display: "flex", 
//       justifyContent: "center", 
//       padding: "50px 0" 
//     }}>
//       <div style={{ 
//         border: "4px solid #f3f3f3",
//         borderTop: "4px solid #3182ce",
//         borderRadius: "50%",
//         width: "40px",
//         height: "40px",
//         animation: "spin 1s linear infinite"
//       }}></div>
//       <style jsx>{`
//         @keyframes spin {
//           0% { transform: rotate(0deg); }
//           100% { transform: rotate(360deg); }
//         }
//       `}</style>
//     </div>
//   );

//   return (
//     <div style={{ 
//       maxWidth: "800px", 
//       margin: "0 auto", 
//       padding: "20px",
//       fontFamily: "Arial, sans-serif",
//       color: "#333"
//     }}>
//       <h2 style={{ 
//         textAlign: "center", 
//         marginBottom: "30px",
//         color: "#1a365d",
//         fontSize: "28px"
//       }}>
//         Policy Admin Panel
//       </h2>
      
//       {/* Loading spinner */}
//       {isLoading && <LoadingSpinner />}
      
//       {/* Error message */}
//       {error && <ConnectionErrorDisplay />}
      
//       {/* Content when loaded successfully */}
//       {!isLoading && !error && (
//         <>
//           {pendingSubmissions.length === 0 ? (
//             <div style={{ 
//               textAlign: "center", 
//               padding: "30px", 
//               background: "#f0f4f8", 
//               borderRadius: "8px",
//               boxShadow: "0 2px 4px rgba(0,0,0,0.05)"
//             }}>
//               <p style={{ fontSize: "18px", color: "#4a5568" }}>
//                 No pending submissions to review.
//               </p>
//             </div>
//           ) : (
//             <div>
//               {pendingSubmissions.map((submission, index) => (
//                 <div 
//                   key={index} 
//                   style={{ 
//                     marginBottom: "24px", 
//                     border: "1px solid #e2e8f0", 
//                     padding: "18px", 
//                     borderRadius: "8px",
//                     boxShadow: "0 4px 6px rgba(0,0,0,0.05)",
//                     background: "#fff"
//                   }}
//                 >
//                   <div 
//                     style={{ 
//                       display: "flex", 
//                       justifyContent: "space-between", 
//                       alignItems: "center",
//                       padding: "5px 0"
//                     }}
//                   >
//                     <h3 
//                       style={{ 
//                         margin: 0, 
//                         color: "#2c5282", 
//                         fontSize: "22px", 
//                         fontWeight: "600",
//                         cursor: "pointer",
//                       }}
//                       onClick={() => toggleExpandSubmission(index)}
//                     >
//                       {submission.country}
//                     </h3>
//                     <div style={{ display: "flex", gap: "10px" }}>
//                       {/* Note button/editor */}
//                       {editingNote === submission.country ? (
//                         <div style={{ display: "flex", gap: "5px" }}>
//                           <input 
//                             type="text" 
//                             value={noteText} 
//                             onChange={(e) => setNoteText(e.target.value)}
//                             placeholder="Add admin note..."
//                             style={{
//                               padding: "8px",
//                               borderRadius: "4px",
//                               border: "1px solid #cbd5e0",
//                               width: "200px"
//                             }}
//                           />
//                           <button
//                             onClick={() => saveNote(submission.country)}
//                             style={{
//                               padding: "8px 12px",
//                               background: "#38a169",
//                               color: "#FFFFFF",
//                               border: "none",
//                               borderRadius: "4px",
//                               cursor: "pointer"
//                             }}
//                           >
//                             Save
//                           </button>
//                         </div>
//                       ) : (
//                         <button
//                           onClick={() => startEditNote(submission.country)}
//                           style={{
//                             padding: "8px 12px",
//                             background: "#6b7280",
//                             color: "#FFFFFF",
//                             border: "none",
//                             borderRadius: "4px",
//                             cursor: "pointer",
//                             display: "flex",
//                             alignItems: "center",
//                             gap: "5px"
//                           }}
//                         >
//                           {adminNotes[`${submission.country}_note`] ? "Edit Note" : "Add Note"}
//                         </button>
//                       )}
                      
//                       {/* Remove button */}
//                       <button
//                         onClick={() => removeCountry(submission.country)}
//                         style={{
//                           padding: "8px 12px",
//                           background: "#e53e3e",
//                           color: "#FFFFFF",
//                           border: "none",
//                           borderRadius: "4px",
//                           cursor: "pointer"
//                         }}
//                       >
//                         Remove
//                       </button>
                      
//                       {/* View details button */}
//                       <button 
//                         onClick={() => toggleExpandSubmission(index)}
//                         style={{ 
//                           padding: "8px 16px", 
//                           background: expandedSubmission === index ? "#4a5568" : "#3182ce", 
//                           color: "#FFFFFF", 
//                           border: "none", 
//                           borderRadius: "6px", 
//                           cursor: "pointer",
//                           fontWeight: "500",
//                           fontSize: "14px",
//                           transition: "all 0.2s ease"
//                         }}
//                       >
//                         {expandedSubmission === index ? "Hide Details" : "View Details"}
//                       </button>
//                     </div>
//                   </div>
                  
//                   {/* Admin Note Display */}
//                   {adminNotes[`${submission.country}_note`] && (
//                     <div style={{
//                       marginTop: "10px",
//                       padding: "10px",
//                       background: "#fffbeb",
//                       borderRadius: "4px",
//                       borderLeft: "4px solid #f59e0b"
//                     }}>
//                       <p style={{ margin: 0, fontSize: "14px" }}>
//                         <strong>Admin Note:</strong> {adminNotes[`${submission.country}_note`]}
//                       </p>
//                     </div>
//                   )}
                  
//                   {expandedSubmission === index && (
//                     <div style={{ 
//                       marginTop: "20px",
//                       borderTop: "1px solid #e2e8f0",
//                       paddingTop: "15px" 
//                     }}>
//                       <h4 style={{ 
//                         color: "#4a5568", 
//                         marginBottom: "15px",
//                         fontSize: "18px"
//                       }}>
//                         Policy Details:
//                       </h4>
//                       <div style={{ display: "grid", gap: "18px" }}>
//                         {submission.policies.map((policy, policyIndex) => (
//                           policy.file || policy.text ? (
//                             <div 
//                               key={policyIndex} 
//                               style={{ 
//                                 padding: "18px", 
//                                 border: "1px solid #e2e8f0", 
//                                 borderRadius: "6px",
//                                 background: getPolicyStatusColor(policy),
//                                 opacity: policy.status === "approved" || policy.status === "declined" ? 0.8 : 1,
//                                 boxShadow: "0 2px 4px rgba(0,0,0,0.05)"
//                               }}
//                             >
//                               <div style={{ 
//                                 display: "flex", 
//                                 justifyContent: "space-between", 
//                                 alignItems: "flex-start" 
//                               }}>
//                                 <h5 style={{ 
//                                   marginTop: 0, 
//                                   color: policy.status === "approved" || policy.status === "declined" ? "#fff" : "#2d3748",
//                                   fontSize: "17px",
//                                   fontWeight: "600" 
//                                 }}>
//                                   {policyNames[policyIndex]}
//                                   {policy.status === "approved" && " (Approved)"}
//                                   {policy.status === "declined" && " (Declined)"}
//                                 </h5>
                                
//                                 {policy.status !== "approved" && policy.status !== "declined" && (
//                                   <div style={{ display: "flex", gap: "10px" }}>
//                                     <button
//                                       onClick={(e) => {
//                                         e.stopPropagation();
//                                         declinePolicy(submission.country, policyIndex);
//                                       }}
//                                       style={{
//                                         padding: "6px 12px",
//                                         background: "#e53e3e",
//                                         color: "#FFFFFF",
//                                         border: "none",
//                                         borderRadius: "4px",
//                                         cursor: "pointer",
//                                         fontSize: "14px",
//                                         fontWeight: "500",
//                                         transition: "background 0.2s ease",
//                                         boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
//                                       }}
//                                       onMouseOver={(e) => e.target.style.background = "#c53030"}
//                                       onMouseOut={(e) => e.target.style.background = "#e53e3e"}
//                                     >
//                                       Decline
//                                     </button>
//                                     <button
//                                       onClick={(e) => {
//                                         e.stopPropagation();
//                                         approvePolicy(submission.country, policyIndex);
//                                       }}
//                                       style={{
//                                         padding: "6px 12px",
//                                         background: "#38a169",
//                                         color: "#FFFFFF",
//                                         border: "none",
//                                         borderRadius: "4px",
//                                         cursor: "pointer",
//                                         fontSize: "14px",
//                                         fontWeight: "500",
//                                         transition: "background 0.2s ease",
//                                         boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
//                                       }}
//                                       onMouseOver={(e) => e.target.style.background = "#2f855a"}
//                                       onMouseOut={(e) => e.target.style.background = "#38a169"}
//                                     >
//                                       Approve
//                                     </button>
//                                   </div>
//                                 )}
//                               </div>
                              
//                               <div style={{ 
//                                 marginTop: "12px",
//                                 color: policy.status === "approved" || policy.status === "declined" ? "#fff" : "#4a5568"
//                               }}>
//                                 {policy.file && (
//                                   <div style={{ marginBottom: "12px" }}>
//                                     <p style={{ 
//                                       marginBottom: "8px", 
//                                       fontWeight: "500",
//                                       fontSize: "15px" 
//                                     }}>
//                                       File: {policy.file.split('/').pop()}
//                                     </p>
//                                     <button
//                                       onClick={(e) => {
//                                         e.stopPropagation();
//                                         viewFile(policy.file);
//                                       }}
//                                       style={{
//                                         padding: "6px 12px",
//                                         background: policy.status === "approved" || policy.status === "declined" ? 
//                                           "rgba(255,255,255,0.3)" : "#4299e1",
//                                         color: "#FFFFFF",
//                                         border: "none",
//                                         borderRadius: "4px",
//                                         cursor: "pointer",
//                                         fontSize: "14px",
//                                         fontWeight: "500",
//                                         transition: "background 0.2s ease",
//                                         boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
//                                       }}
//                                       onMouseOver={(e) => e.target.style.background = policy.status === "approved" || policy.status === "declined" ? 
//                                         "rgba(255,255,255,0.5)" : "#3182ce"}
//                                       onMouseOut={(e) => e.target.style.background = policy.status === "approved" || policy.status === "declined" ? 
//                                         "rgba(255,255,255,0.3)" : "#4299e1"}
//                                     >
//                                       View File
//                                     </button>
//                                   </div>
//                                 )}
//                                 {policy.text && (
//                                   <div>
//                                     <p style={{ 
//                                       marginBottom: "8px", 
//                                       wordBreak: "break-all",
//                                       fontWeight: "500",
//                                       fontSize: "15px" 
//                                     }}>
//                                       Link: {policy.text}
//                                     </p>
//                                     <button
//                                       onClick={(e) => {
//                                         e.stopPropagation();
//                                         openLink(policy.text);
//                                       }}
//                                       style={{
//                                         padding: "6px 12px",
//                                         background: policy.status === "approved" || policy.status === "declined" ? 
//                                           "rgba(255,255,255,0.3)" : "#4299e1",
//                                         color: "#FFFFFF",
//                                         border: "none",
//                                         borderRadius: "4px",
//                                         cursor: "pointer",
//                                         fontSize: "14px",
//                                         fontWeight: "500",
//                                         transition: "background 0.2s ease",
//                                         boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
//                                       }}
//                                       onMouseOver={(e) => e.target.style.background = policy.status === "approved" || policy.status === "declined" ? 
//                                         "rgba(255,255,255,0.5)" : "#3182ce"}
//                                       onMouseOut={(e) => e.target.style.background = policy.status === "approved" || policy.status === "declined" ? 
//                                         "rgba(255,255,255,0.3)" : "#4299e1"}
//                                     >
//                                       Open Link
//                                     </button>
//                                   </div>
//                                 )}
//                               </div>
//                             </div>
//                           ) : null
//                         ))}
//                       </div>
//                     </div>
//                   )}
//                 </div>
//               ))}
              
//               {/* Pagination controls */}
//               {totalPages > 1 && (
//                 <div style={{ 
//                   display: "flex", 
//                   justifyContent: "center", 
//                   alignItems: "center", 
//                   marginTop: "30px", 
//                   gap: "15px" 
//                 }}>
//                   <button
//                     onClick={prevPage}
//                     disabled={currentPage === 0}
//                     style={{
//                       padding: "8px 16px",
//                       background: currentPage === 0 ? "#cbd5e0" : "#3182ce",
//                       color: "#FFFFFF",
//                       border: "none",
//                       borderRadius: "6px",
//                       cursor: currentPage === 0 ? "not-allowed" : "pointer",
//                       fontWeight: "500",
//                       fontSize: "14px",
//                       transition: "all 0.2s ease",
//                       opacity: currentPage === 0 ? 0.6 : 1
//                     }}
//                   >
//                     Previous
//                   </button>
//                   <span style={{ fontSize: "16px", color: "#4a5568" }}>
//                     Page {currentPage + 1} of {totalPages}
//                   </span>
//                   <button
//                     onClick={nextPage}
//                     disabled={currentPage >= totalPages - 1}
//                     // The pagination button styling was cut off - here's the complete code
//                     style={{
//                       padding: "8px 16px",
//                       background: currentPage >= totalPages - 1 ? "#cbd5e0" : "#3182ce",
//                       color: "#FFFFFF",
//                       border: "none",
//                       borderRadius: "6px",
//                       cursor: currentPage >= totalPages - 1 ? "not-allowed" : "pointer",
//                       fontWeight: "500",
//                       fontSize: "14px",
//                       transition: "all 0.2s ease",
//                       opacity: currentPage >= totalPages - 1 ? 0.6 : 1
//                     }}
//                   >
//                     Next
//                   </button>
//                 </div>
//               )}
//             </div>
//           )}
//         </>
//       )}
//     </div>
//   )
// }