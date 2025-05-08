'use client'
import { useState, useEffect } from "react"
import './AdminStyles.css' 

export default function AdminPanel() {
  // Main states
  const [submissions, setSubmissions] = useState([])
  const [filteredSubmissions, setFilteredSubmissions] = useState([])
  const [expandedSubmission, setExpandedSubmission] = useState(null)
  const [currentView, setCurrentView] = useState('unread') // 'unread', 'approved', 'rejected'
  const [currentPage, setCurrentPage] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [adminNotes, setAdminNotes] = useState({})
  const [editingNote, setEditingNote] = useState(null)
  const [noteText, setNoteText] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Edit mode states
  const [editMode, setEditMode] = useState(null) // Format: {country: 'countryName', policyIndex: 0}
  const [editedPolicyText, setEditedPolicyText] = useState("")
  
  const submissionsPerPage = 5
  
  // API base URL - centralized for easy changes
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  
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

  // Filter functions
  const filterSubmissions = (view) => {
    setCurrentView(view)
    setCurrentPage(0)
    setExpandedSubmission(null)
    fetchSubmissions(0, view)
  }
  
  // Initial load
  useEffect(() => {
    fetchSubmissions(currentPage, currentView)
    loadAdminNotes()
  }, [])
  
  // When page changes
  useEffect(() => {
    fetchSubmissions(currentPage, currentView)
  }, [currentPage])
  
  // Save admin notes to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('adminNotes', JSON.stringify(adminNotes))
  }, [adminNotes])
  
  // Load admin notes from localStorage on initial load
  const loadAdminNotes = () => {
    const savedNotes = localStorage.getItem('adminNotes')
    if (savedNotes) {
      try {
        setAdminNotes(JSON.parse(savedNotes))
      } catch (e) {
        console.error("Failed to parse saved notes:", e)
        localStorage.removeItem('adminNotes') // Remove corrupted data
      }
    }
  }

  const fetchSubmissions = async (page = 0, view = 'unread') => {
    setIsLoading(true)
    setError(null)
    
    try {
      // Endpoint changes based on the current view
      let endpoint = '/api/submissions'
      switch(view) {
        case 'unread':
          endpoint = '/api/pending-submissions'
          break
        case 'approved':
          endpoint = '/api/approved-submissions'
          break
        case 'rejected':
          endpoint = '/api/rejected-submissions'
          break
      }
      
      console.log(`Fetching from: ${API_BASE_URL}${endpoint}?page=${page}&per_page=${submissionsPerPage}`)
      
      const response = await fetch(`${API_BASE_URL}${endpoint}?page=${page}&per_page=${submissionsPerPage}`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        credentials: 'include', 
        signal: AbortSignal.timeout(10000) // 10 second timeout
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`)
      }
      
      const data = await response.json()
      
      setSubmissions(data.submissions || [])
      setFilteredSubmissions(data.submissions || [])
      setTotalPages(data.pagination?.total_pages || 0)
    } catch (error) {
      console.error(`Failed to fetch ${currentView} submissions:`, error)
      setError(error.message || `Failed to load ${currentView} submissions`)
    } finally {
      setIsLoading(false)
    }
  }

  const retryConnection = () => {
    fetchSubmissions(currentPage, currentView)
  }

  const approvePolicy = async (country, policyIndex) => {
    try {
      const policyData = {
        country,
        policyIndex,
        text: editMode && editMode.country === country && editMode.policyIndex === policyIndex 
          ? editedPolicyText 
          : filteredSubmissions.find(s => s.country === country)?.policies[policyIndex]?.text || ""
      }
      
      const response = await fetch(`${API_BASE_URL}/api/approve-policy`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(policyData),
      })
    
      if (response.ok) {
        // Reset edit mode if was editing
        if (editMode) {
          setEditMode(null)
          setEditedPolicyText("")
        }
        
        // Update the status in the UI
        const updatedSubmissions = [...filteredSubmissions]
        const countrySubmission = updatedSubmissions.find(sub => sub.country === country)
        if (countrySubmission) {
          countrySubmission.policies[policyIndex].status = "approved"
          // If we edited the text, update that too
          if (editMode && editMode.country === country && editMode.policyIndex === policyIndex) {
            countrySubmission.policies[policyIndex].text = editedPolicyText
          }
          setFilteredSubmissions(updatedSubmissions)
        }
        
        // Remove from unread view if all policies are handled
        if (currentView === 'unread') {
          checkAndRemoveCountry(country)
        }
        
        alert(`Policy "${policyNames[policyIndex]}" for ${country} approved!`)
      } else {
        const errorData = await response.json().catch(() => ({}))
        alert(`Failed to approve policy: ${errorData.detail || response.statusText || 'Unknown error'}`)
      }
    } catch (error) {
      console.error("Error approving policy:", error)
      alert("An error occurred while approving policy. Please check your network connection and ensure the API server is running.")
    }
  }

  const rejectPolicy = async (country, policyIndex) => {
    try {
      const policyData = {
        country,
        policyIndex,
        text: editMode && editMode.country === country && editMode.policyIndex === policyIndex 
          ? editedPolicyText 
          : filteredSubmissions.find(s => s.country === country)?.policies[policyIndex]?.text || ""
      }
      
      const response = await fetch(`${API_BASE_URL}/api/reject-policy`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          'Accept': 'application/json', 
        },
        credentials: 'include',
        body: JSON.stringify(policyData),
      })
    
      if (response.ok) {
        // Reset edit mode if was editing
        if (editMode) {
          setEditMode(null)
          setEditedPolicyText("")
        }
        
        // Update the status in the UI
        const updatedSubmissions = [...filteredSubmissions]
        const countrySubmission = updatedSubmissions.find(sub => sub.country === country)
        if (countrySubmission) {
          countrySubmission.policies[policyIndex].status = "rejected"
          // If we edited the text, update that too
          if (editMode && editMode.country === country && editMode.policyIndex === policyIndex) {
            countrySubmission.policies[policyIndex].text = editedPolicyText
          }
          setFilteredSubmissions(updatedSubmissions)
        }
        
        // Remove from unread view if all policies are handled
        if (currentView === 'unread') {
          checkAndRemoveCountry(country)
        }
        
        alert(`Policy "${policyNames[policyIndex]}" for ${country} rejected!`)
      } else {
        const errorData = await response.json().catch(() => ({}))
        alert(`Failed to reject policy: ${errorData.detail || response.statusText || 'Unknown error'}`)
      }
    } catch (error) {
      console.error("Error rejecting policy:", error)
      alert("An error occurred while rejecting policy. Please check your network connection and ensure the API server is running.")
    }
  }

  const checkAndRemoveCountry = (country) => {
    const updatedSubmissions = [...filteredSubmissions]
    const countryIndex = updatedSubmissions.findIndex(sub => sub.country === country)
    
    if (countryIndex >= 0) {
      const allPoliciesHandled = updatedSubmissions[countryIndex].policies.every(policy => 
        !policy.file && !policy.text || policy.status === "approved" || policy.status === "rejected"
      )
      
      if (allPoliciesHandled) {
        // Remove this country from the pending list if all policies are handled
        updatedSubmissions.splice(countryIndex, 1)
        setFilteredSubmissions(updatedSubmissions)
        
        // Reset expanded state if needed
        if (expandedSubmission === countryIndex) {
          setExpandedSubmission(null)
        } else if (expandedSubmission > countryIndex) {
          // Adjust the expanded index if it was after the removed item
          setExpandedSubmission(expandedSubmission - 1)
        }
        
        // If this was the last item on the page and not the first page, go to previous page
        if (updatedSubmissions.length === 0 && currentPage > 0) {
          setCurrentPage(currentPage - 1)
        } else if (updatedSubmissions.length === 0) {
          // If no more submissions on this page, refresh
          fetchSubmissions(currentPage, currentView)
        }
      }
    }
  }

  // Remove a country from the current view
  const removeSubmission = (country) => {
    const updatedSubmissions = filteredSubmissions.filter(sub => sub.country !== country)
    setFilteredSubmissions(updatedSubmissions)
    
    // Reset expanded state if needed
    const countryIndex = filteredSubmissions.findIndex(sub => sub.country === country)
    if (expandedSubmission === countryIndex) {
      setExpandedSubmission(null)
    } else if (expandedSubmission > countryIndex) {
      setExpandedSubmission(expandedSubmission - 1)
    }
    
    // Also remove any notes for this country
    const updatedNotes = { ...adminNotes }
    delete updatedNotes[`${country}_note`]
    setAdminNotes(updatedNotes)
    
    // If this was the last item on the page and not the first page, go to previous page
    if (updatedSubmissions.length === 0 && currentPage > 0) {
      setCurrentPage(currentPage - 1)
    } else if (updatedSubmissions.length === 0) {
      // If no more submissions on this page, refresh
      fetchSubmissions(currentPage, currentView)
    }
  }

  // Edit mode functions
  const startEditPolicy = (country, policyIndex) => {
    const policy = filteredSubmissions.find(s => s.country === country)?.policies[policyIndex]
    if (!policy) return
    
    setEditMode({ country, policyIndex })
    setEditedPolicyText(policy.text || "")
  }
  
  const cancelEditPolicy = () => {
    setEditMode(null)
    setEditedPolicyText("")
  }

  // Note functions
  const startEditNote = (country) => {
    const noteKey = `${country}_note`
    setEditingNote(country)
    setNoteText(adminNotes[noteKey] || "")
  }

  const saveNote = (country) => {
    const noteKey = `${country}_note`
    const updatedNotes = { ...adminNotes }
    
    if (noteText.trim() === "") {
      delete updatedNotes[noteKey]
    } else {
      updatedNotes[noteKey] = noteText
    }
    
    setAdminNotes(updatedNotes)
    setEditingNote(null)
    setNoteText("")
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
    window.open(`${API_BASE_URL}/api/policy-file/${filename}`, '_blank')
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
    if (policy.status === "approved") return "bg-approved"
    if (policy.status === "rejected") return "bg-rejected"
    return "bg-pending" // default background for pending
  }

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

  // Component for displaying connection error
  const ConnectionErrorDisplay = () => (
    <div className="error-container">
      <h3 className="error-title">Connection Error</h3>
      <p className="error-message">
        Failed to connect to the API server. Please ensure the server is running at:
        <br />
        <code className="error-code">{API_BASE_URL}</code>
      </p>
      <div className="error-checklist">
        <p>Please check:</p>
        <ul>
          <li>The FastAPI server is running</li>
          <li>The NEXT_PUBLIC_API_URL environment variable is set correctly</li>
          <li>CORS settings allow requests from this origin</li>
          <li>Network connectivity between frontend and API</li>
        </ul>
      </div>
      <button className="btn-primary" onClick={retryConnection}>
        Retry Connection
      </button>
    </div>
  )

  // Loading spinner component
  const LoadingSpinner = () => (
    <div className="spinner-container">
      <div className="spinner"></div>
    </div>
  )

  return (
    <div className="admin-container">
      <h2 className="admin-title">Policy Admin Panel</h2>
      
      {/* View selector tabs */}
      <div className="view-tabs">
        <button 
          className={`tab-btn ${currentView === 'unread' ? 'active' : ''}`}
          onClick={() => filterSubmissions('unread')}
        >
          Unread Submissions
        </button>
        <button 
          className={`tab-btn ${currentView === 'approved' ? 'active' : ''}`}
          onClick={() => filterSubmissions('approved')}
        >
          Approved Policies
        </button>
        <button 
          className={`tab-btn ${currentView === 'rejected' ? 'active' : ''}`}
          onClick={() => filterSubmissions('rejected')}
        >
          Rejected Policies
        </button>
      </div>
      
      {/* Loading spinner */}
      {isLoading && <LoadingSpinner />}
      
      {/* Error message */}
      {error && <ConnectionErrorDisplay />}
      
      {/* Content when loaded successfully */}
      {!isLoading && !error && (
        <>
          {filteredSubmissions.length === 0 ? (
            <div className="empty-state">
              <p>No {currentView} submissions to review.</p>
            </div>
          ) : (
            <div className="submissions-list">
              {filteredSubmissions.map((submission, index) => (
                <div key={index} className="submission-card">
                  <div className="submission-header">
                    <h3 
                      className="country-name"
                      onClick={() => toggleExpandSubmission(index)}
                    >
                      {submission.country}
                    </h3>
                    <div className="header-actions">
                      {/* Note button/editor */}
                      {editingNote === submission.country ? (
                        <div className="note-editor">
                          <input 
                            type="text" 
                            value={noteText} 
                            onChange={(e) => setNoteText(e.target.value)}
                            placeholder="Add admin note..."
                            className="note-input"
                          />
                          <button className="btn-save" onClick={() => saveNote(submission.country)}>
                            Save
                          </button>
                        </div>
                      ) : (
                        <button
                          className="btn-note"
                          onClick={() => startEditNote(submission.country)}
                        >
                          {adminNotes[`${submission.country}_note`] ? "Edit Note" : "Add Note"}
                        </button>
                      )}
                      
                      {/* Remove button - only in approved/rejected views */}
                      {currentView !== 'unread' && (
                        <button
                          className="btn-remove"
                          onClick={() => removeSubmission(submission.country)}
                        >
                          Remove
                        </button>
                      )}
                      
                      {/* View details button */}
                      <button 
                        className={`btn-details ${expandedSubmission === index ? 'expanded' : ''}`}
                        onClick={() => toggleExpandSubmission(index)}
                      >
                        {expandedSubmission === index ? "Hide Details" : "View Details"}
                      </button>
                    </div>
                  </div>
                  
                  {/* Admin Note Display */}
                  {adminNotes[`${submission.country}_note`] && (
                    <div className="admin-note">
                      <p>
                        <strong>Admin Note:</strong> {adminNotes[`${submission.country}_note`]}
                      </p>
                    </div>
                  )}
                  
                  {expandedSubmission === index && (
                    <div className="submission-details">
                      <h4 className="details-title">Policy Details:</h4>
                      <div className="policies-grid">
                        {submission.policies.map((policy, policyIndex) => (
                          policy.file || policy.text ? (
                            <div 
                              key={policyIndex} 
                              className={`policy-card ${getPolicyStatusColor(policy)}`}
                            >
                              <div className="policy-header">
                                <h5 className="policy-title">
                                  {policyNames[policyIndex]}
                                  {policy.status === "approved" && " (Approved)"}
                                  {policy.status === "rejected" && " (Rejected)"}
                                </h5>
                                
                                {/* Actions for unread policies */}
                                {currentView === 'unread' && policy.status !== "approved" && policy.status !== "rejected" && (
                                  <div className="policy-actions">
                                    <button
                                      className="btn-reject"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        rejectPolicy(submission.country, policyIndex);
                                      }}
                                    >
                                      Reject
                                    </button>
                                    <button
                                      className="btn-approve"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        approvePolicy(submission.country, policyIndex);
                                      }}
                                    >
                                      Approve
                                    </button>
                                  </div>
                                )}
                              </div>
                              
                              <div className="policy-content">
                                {policy.file && (
                                  <div className="policy-file">
                                    <p className="file-name">
                                      File: {policy.file.split('/').pop()}
                                    </p>
                                    <button
                                      className="btn-view"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        viewFile(policy.file);
                                      }}
                                    >
                                      View File
                                    </button>
                                  </div>
                                )}
                                
                                {/* Edit mode for policy text */}
                                {editMode && editMode.country === submission.country && editMode.policyIndex === policyIndex ? (
                                  <div className="policy-edit">
                                    <textarea
                                      value={editedPolicyText}
                                      onChange={(e) => setEditedPolicyText(e.target.value)}
                                      className="policy-textarea"
                                      rows={3}
                                    />
                                    <div className="edit-actions">
                                      <button className="btn-cancel" onClick={cancelEditPolicy}>
                                        Cancel
                                      </button>
                                      <button 
                                        className="btn-save"
                                        onClick={() => {
                                          if (currentView === 'unread') {
                                            // For unread, save happens when approving/rejecting
                                            alert("Please approve or reject the policy to save changes")
                                          } else {
                                            // For approved/rejected, update directly
                                            const updatedSubmissions = [...filteredSubmissions]
                                            const countrySubmission = updatedSubmissions.find(sub => sub.country === submission.country)
                                            if (countrySubmission) {
                                              countrySubmission.policies[policyIndex].text = editedPolicyText
                                              setFilteredSubmissions(updatedSubmissions)
                                              // API call to update the policy would go here
                                              setEditMode(null)
                                              setEditedPolicyText("")
                                              alert("Policy updated successfully")
                                            }
                                          }
                                        }}
                                      >
                                        Save Changes
                                      </button>
                                    </div>
                                  </div>
                                ) : policy.text && (
                                  <div className="policy-text">
                                    <p className="text-content">
                                      Link: {policy.text}
                                    </p>
                                    <div className="text-actions">
                                      <button
                                        className="btn-view"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          openLink(policy.text);
                                        }}
                                      >
                                        Open Link
                                      </button>
                                      {/* Edit button */}
                                      <button
                                        className="btn-edit"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          startEditPolicy(submission.country, policyIndex);
                                        }}
                                      >
                                        Edit
                                      </button>
                                    </div>
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
              ))}
              
              {/* Pagination controls */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="btn-page"
                    onClick={prevPage}
                    disabled={currentPage === 0}
                  >
                    Previous
                  </button>
                  <span className="page-info">
                    Page {currentPage + 1} of {totalPages}
                  </span>
                  <button
                    className="btn-page"
                    onClick={nextPage}
                    disabled={currentPage >= totalPages - 1}
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}