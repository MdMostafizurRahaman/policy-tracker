import React from 'react'
//form submission successful
export const AdminUIComponents = {
  // Component for displaying connection error
  ConnectionErrorDisplay: ({ onRetry, apiBaseUrl }) => (
    <div className="error-container">
      <h3 className="error-title">Connection Error</h3>
      <p className="error-message">
        Failed to connect to the API server. Please ensure the server is running at:
        <br />
        <code className="error-code">{apiBaseUrl}</code>
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
      <button className="btn-primary" onClick={onRetry}>
        Retry Connection
      </button>
    </div>
  ),

  // Loading spinner component
  LoadingSpinner: () => (
    <div className="spinner-container">
      <div className="spinner"></div>
    </div>
  ),

  // Main submissions list component
  SubmissionsList: ({ 
    submissions, 
    expandedSubmission, 
    toggleExpandSubmission, 
    editingNote, 
    noteText, 
    setNoteText, 
    saveNote, 
    startEditNote, 
    adminNotes, 
    removeSubmission, 
    policyNames, 
    getPolicyStatusColor, 
    editMode, 
    editedPolicyText, 
    setEditedPolicyText, 
    cancelEditPolicy, 
    approvePolicy, 
    rejectPolicy, 
    updatePolicy, 
    startEditPolicy, 
    currentView 
  }) => (
    <div className="submissions-list">
      {submissions.map((submission, index) => (
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
              
              {/* Remove button - for all views */}
              <button
                className="btn-remove"
                onClick={() => {
                  if (window.confirm(`Are you sure you want to permanently remove ${submission.country} and all its policies from the system?`)) {
                    removeSubmission(submission.country)
                  }
                }}
              >
                Remove
              </button>
              
              <button 
                className="btn-expand"
                onClick={() => toggleExpandSubmission(index)}
              >
                {expandedSubmission === index ? 'Collapse' : 'Expand'}
              </button>
            </div>
          </div>
          
          {/* Show admin note if exists */}
          {adminNotes[`${submission.country}_note`] && (
            <div className="admin-note">
              <strong>Note:</strong> {adminNotes[`${submission.country}_note`]}
            </div>
          )}
          
          {/* Expanded view with policies */}
          {expandedSubmission === index && (
            <div className="policies-container">
              {submission.policies.map((policy, policyIndex) => (
                <div 
                  key={policyIndex} 
                  className={`policy-item ${getPolicyStatusColor(policy)}`}
                >
                  <div className="policy-header">
                    <h4 className="policy-name">
                      {policyNames[policyIndex]}
                    </h4>
                    <div className="policy-status">
                      Status: {policy.status || "pending"}
                    </div>
                  </div>
                  
                  {/* Display policy content */}
                  <div className="policy-content">
                    {editMode && 
                     editMode.country === submission.country && 
                     editMode.policyIndex === policyIndex ? (
                      <div className="policy-edit-mode">
                        <textarea
                          value={editedPolicyText}
                          onChange={(e) => setEditedPolicyText(e.target.value)}
                          className="policy-textarea"
                          rows={10}
                        />
                        <div className="edit-actions">
                          <button 
                            className="btn-cancel"
                            onClick={cancelEditPolicy}
                          >
                            Cancel
                          </button>
                          
                          {currentView === 'unread' ? (
                            <>
                              <button 
                                className="btn-approve"
                                onClick={() => approvePolicy(submission.country, policyIndex)}
                              >
                                Approve with Edits
                              </button>
                              <button 
                                className="btn-reject"
                                onClick={() => rejectPolicy(submission.country, policyIndex)}
                              >
                                Reject with Comments
                              </button>
                            </>
                          ) : (
                            <button 
                              className="btn-save"
                              onClick={() => updatePolicy(submission.country, policyIndex)}
                            >
                              Save Changes
                            </button>
                          )}
                        </div>
                      </div>
                    ) : (
                      <PolicyContent 
                        policy={policy}
                        submission={submission}
                        policyIndex={policyIndex}
                        currentView={currentView}
                        startEditPolicy={startEditPolicy}
                        approvePolicy={approvePolicy}
                        rejectPolicy={rejectPolicy}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  ),
}

// Helper component for policy content
const PolicyContent = ({ 
  policy, 
  submission, 
  policyIndex, 
  currentView, 
  startEditPolicy, 
  approvePolicy, 
  rejectPolicy 
}) => {
  // Function to view file
  const viewFile = (filePath) => {
    // Extract just the filename from the path
    const filename = filePath.split('/').pop()
    // Open file in a new tab
    window.open(`${window.location.origin}/api/policy-file/${filename}`, '_blank')
  }

  // Function to open external link
  const openLink = (url) => {
    // Check if URL has http/https prefix, if not add it
    let finalUrl = url
    if (!/^https?:\/\//i.test(url)) {
      finalUrl = 'https://' + url
    }
    window.open(finalUrl, '_blank')
  }

  return (
    <>
      {/* Display file link if exists */}
      {policy.file && (
        <div className="policy-file">
          <button 
            className="btn-file"
            onClick={() => viewFile(policy.file)}
          >
            View Uploaded File
          </button>
        </div>
      )}
      
      {/* Display link if exists */}
      {policy.link && (
        <div className="policy-link">
          <button 
            className="btn-link"
            onClick={() => openLink(policy.link)}
          >
            Open External Link
          </button>
          <span className="link-display">{policy.link}</span>
        </div>
      )}
      
      {/* Display text content */}
      {policy.text && (
        <div className="policy-text">
          {policy.text}
        </div>
      )}
      
      {/* Actions based on current view */}
      <div className="policy-actions">
        <button 
          className="btn-edit"
          onClick={() => startEditPolicy(submission.country, policyIndex)}
        >
          Edit
        </button>
        
        {currentView === 'unread' && (
          <>
            <button 
              className="btn-approve"
              onClick={() => approvePolicy(submission.country, policyIndex)}
            >
              Approve
            </button>
            <button 
              className="btn-reject"
              onClick={() => rejectPolicy(submission.country, policyIndex)}
            >
              Reject
            </button>
          </>
        )}
        
        {/* For approved view, allow rejecting */}
        {currentView === 'approved' && (
          <button 
            className="btn-reject"
            onClick={() => rejectPolicy(submission.country, policyIndex)}
          >
            Move to Rejected
          </button>
        )}
        
        {/* For rejected view, allow approving */}
        {currentView === 'rejected' && (
          <button 
            className="btn-approve"
            onClick={() => approvePolicy(submission.country, policyIndex)}
          >
            Move to Approved
          </button>
        )}
      </div>
    </>
  )
}