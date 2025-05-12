'use client'
import { useState, useEffect } from "react"
import './AdminStyles.css'

import { adminAPI } from './AdminAPI'
import { AdminUIComponents } from './AdminUIComponents '

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
      const data = await adminAPI.fetchSubmissions(page, view, submissionsPerPage)
      
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
      const policyText = editMode && editMode.country === country && editMode.policyIndex === policyIndex 
        ? editedPolicyText 
        : filteredSubmissions.find(s => s.country === country)?.policies[policyIndex]?.text || ""
      
      const success = await adminAPI.approvePolicy(country, policyIndex, policyText)
    
      if (success) {
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
      }
    } catch (error) {
      console.error("Error approving policy:", error)
      alert("An error occurred while approving policy. Please check your network connection and ensure the API server is running.")
    }
  }

  const rejectPolicy = async (country, policyIndex) => {
    try {
      const policyText = editMode && editMode.country === country && editMode.policyIndex === policyIndex 
        ? editedPolicyText 
        : filteredSubmissions.find(s => s.country === country)?.policies[policyIndex]?.text || ""
      
      const success = await adminAPI.rejectPolicy(country, policyIndex, policyText)
    
      if (success) {
        // Reset edit mode if was editing
        if (editMode) {
          setEditMode(null)
          setEditedPolicyText("")
        }
        
        // Update the status in the UI
        const updatedSubmissions = [...filteredSubmissions]
        const countrySubmission = updatedSubmissions.find(sub => sub.country === country)
        if (countrySubmission) {
          countrySubmission.policies[policyIndex].status = "declined" // Match backend terminology
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
        !policy.file && !policy.text || policy.status === "approved" || policy.status === "declined"
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

  // Remove a country permanently from the system
  const removeSubmission = async (country) => {
    try {
      const success = await adminAPI.removeSubmission(country)
      
      if (success) {
        // Update the UI after successful removal
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
        
        alert(`Successfully removed ${country} and all its policies from the system.`)
      }
    } catch (error) {
      console.error("Error removing submission:", error)
      alert("An error occurred while removing the submission. Please check your connection and try again.")
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

  // Update a policy in approved/rejected views
  const updatePolicy = async (country, policyIndex) => {
    try {
      const status = filteredSubmissions.find(s => s.country === country)?.policies[policyIndex]?.status || "pending"
      const success = await adminAPI.updatePolicy(country, policyIndex, editedPolicyText, status)
    
      if (success) {
        // Update the UI
        const updatedSubmissions = [...filteredSubmissions]
        const countrySubmission = updatedSubmissions.find(sub => sub.country === country)
        if (countrySubmission) {
          countrySubmission.policies[policyIndex].text = editedPolicyText
          setFilteredSubmissions(updatedSubmissions)
        }
        
        // Reset edit mode
        setEditMode(null)
        setEditedPolicyText("")
        
        alert(`Policy "${policyNames[policyIndex]}" for ${country} updated successfully!`)
      }
    } catch (error) {
      console.error("Error updating policy:", error)
      alert("An error occurred while updating the policy. Please check your connection and try again.")
    }
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

  const getPolicyStatusColor = (policy) => {
    if (policy.status === "approved") return "bg-approved"
    if (policy.status === "declined" || policy.status === "rejected") return "bg-rejected"
    return "bg-pending" // default background for pending
  }

  // Destructuring UI components
  const { 
    ConnectionErrorDisplay, 
    LoadingSpinner, 
    SubmissionsList 
  } = AdminUIComponents

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
      {error && <ConnectionErrorDisplay onRetry={retryConnection} apiBaseUrl={adminAPI.API_BASE_URL} />}
      
      {/* Content when loaded successfully */}
      {!isLoading && !error && (
        <>
          {filteredSubmissions.length === 0 ? (
            <div className="empty-state">
              <p>No {currentView} submissions to review.</p>
            </div>
          ) : (
            <SubmissionsList 
              submissions={filteredSubmissions}
              expandedSubmission={expandedSubmission}
              toggleExpandSubmission={toggleExpandSubmission}
              editingNote={editingNote}
              noteText={noteText}
              setNoteText={setNoteText}
              saveNote={saveNote}
              startEditNote={startEditNote}
              adminNotes={adminNotes}
              removeSubmission={removeSubmission}
              policyNames={policyNames}
              getPolicyStatusColor={getPolicyStatusColor}
              editMode={editMode}
              editedPolicyText={editedPolicyText}
              setEditedPolicyText={setEditedPolicyText}
              cancelEditPolicy={cancelEditPolicy}
              approvePolicy={approvePolicy}
              rejectPolicy={rejectPolicy}
              updatePolicy={updatePolicy}
              startEditPolicy={startEditPolicy}
              currentView={currentView}
            />
          )}
          
          {/* Pagination controls */}
          {totalPages > 1 && (
            <div className="pagination">
              <button 
                className="page-btn"
                onClick={prevPage}
                disabled={currentPage === 0}
              >
                Previous
              </button>
              <span className="page-info">
                Page {currentPage + 1} of {totalPages}
              </span>
              <button 
                className="page-btn"
                onClick={nextPage}
                disabled={currentPage === totalPages - 1}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}