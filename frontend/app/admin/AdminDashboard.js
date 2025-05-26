'use client'
import { useState, useEffect } from "react"
import './AdminStyles.css'

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Policy status options
const POLICY_STATUSES = ["pending", "approved", "rejected", "needs_revision"]

export default function AdminDashboard() {
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [selectedSubmission, setSelectedSubmission] = useState(null)
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [showPolicyModal, setShowPolicyModal] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editedPolicy, setEditedPolicy] = useState(null)
  const [adminNotes, setAdminNotes] = useState("")
  const [filterStatus, setFilterStatus] = useState("all")
  const [searchTerm, setSearchTerm] = useState("")

  // Fetch all pending submissions on component mount
  useEffect(() => {
    fetchSubmissions()
  }, [])

  const fetchSubmissions = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/admin/submissions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}` // Assuming admin auth
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch submissions')
      }

      const data = await response.json()
      setSubmissions(data.submissions || [])
    } catch (error) {
      setError(`Error fetching submissions: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Handle policy status update
  const updatePolicyStatus = async (submissionId, policyIndex, status, notes = "") => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/update-policy-status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
        },
        body: JSON.stringify({
          submission_id: submissionId,
          policy_index: policyIndex,
          status: status,
          admin_notes: notes
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update policy status')
      }

      const result = await response.json()
      
      if (result.success) {
        setSuccess(`Policy status updated to ${status}`)
        fetchSubmissions() // Refresh the list
        
        // If approved, move to master DB
        if (status === 'approved') {
          await movePolicyToMaster(submissionId, policyIndex)
        }
      }
    } catch (error) {
      setError(`Error updating policy: ${error.message}`)
    }
  }

  // Move approved policy to master database
  const movePolicyToMaster = async (submissionId, policyIndex) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/move-to-master`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
        },
        body: JSON.stringify({
          submission_id: submissionId,
          policy_index: policyIndex
        })
      })

      if (!response.ok) {
        throw new Error('Failed to move policy to master database')
      }

      const result = await response.json()
      if (result.success) {
        setSuccess(prev => prev + " and moved to master database")
      }
    } catch (error) {
      setError(`Error moving to master DB: ${error.message}`)
    }
  }

  // Handle policy edit
  const handleEditPolicy = async (submissionId, policyIndex, updatedPolicy) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/edit-policy`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
        },
        body: JSON.stringify({
          submission_id: submissionId,
          policy_index: policyIndex,
          updated_policy: updatedPolicy
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update policy')
      }

      const result = await response.json()
      
      if (result.success) {
        setSuccess("Policy updated successfully")
        fetchSubmissions()
        setEditMode(false)
        setEditedPolicy(null)
      }
    } catch (error) {
      setError(`Error updating policy: ${error.message}`)
    }
  }

  // Handle policy deletion
  const deletePolicy = async (submissionId, policyIndex) => {
    if (!confirm("Are you sure you want to delete this policy? This action cannot be undone.")) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/admin/delete-policy`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
        },
        body: JSON.stringify({
          submission_id: submissionId,
          policy_index: policyIndex
        })
      })

      if (!response.ok) {
        throw new Error('Failed to delete policy')
      }

      const result = await response.json()
      
      if (result.success) {
        setSuccess("Policy deleted successfully")
        fetchSubmissions()
        setShowPolicyModal(false)
      }
    } catch (error) {
      setError(`Error deleting policy: ${error.message}`)
    }
  }

  // Filter submissions based on status and search term
  const filteredSubmissions = submissions.filter(submission => {
    const matchesStatus = filterStatus === "all" || 
      submission.policyInitiatives.some(policy => policy.status === filterStatus)
    
    const matchesSearch = searchTerm === "" || 
      submission.country.toLowerCase().includes(searchTerm.toLowerCase()) ||
      submission.policyInitiatives.some(policy => 
        policy.policyName.toLowerCase().includes(searchTerm.toLowerCase())
      )
    
    return matchesStatus && matchesSearch
  })

  // Handle policy field updates in edit mode
  const updateEditedPolicy = (field, value) => {
    setEditedPolicy(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const updateEditedPolicySection = (section, field, value) => {
    setEditedPolicy(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }))
  }

  // Clear messages after 5 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(""), 5000)
      return () => clearTimeout(timer)
    }
  }, [success])

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 5000)
      return () => clearTimeout(timer)
    }
  }, [error])

  // Render policy details modal
  const renderPolicyModal = () => {
    if (!showPolicyModal || !selectedPolicy) return null

    const policy = editMode ? editedPolicy : selectedPolicy
    
    return (
      <div className="modal-overlay" onClick={() => {
        setShowPolicyModal(false)
        setEditMode(false)
        setEditedPolicy(null)
      }}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h2>
              {editMode ? "Edit Policy" : "Policy Details"}: {policy.policyName}
            </h2>
            <button 
              className="close-btn"
              onClick={() => {
                setShowPolicyModal(false)
                setEditMode(false)
                setEditedPolicy(null)
              }}
            >
              ×
            </button>
          </div>

          <div className="modal-body">
            {editMode ? (
              <div className="edit-form">
                <div className="form-group">
                  <label>Policy Name:</label>
                  <input
                    type="text"
                    value={policy.policyName}
                    onChange={e => updateEditedPolicy("policyName", e.target.value)}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>Policy Description:</label>
                  <textarea
                    value={policy.policyDescription}
                    onChange={e => updateEditedPolicy("policyDescription", e.target.value)}
                    className="form-textarea"
                    rows="4"
                  />
                </div>

                <div className="form-group">
                  <label>Policy Area:</label>
                  <input
                    type="text"
                    value={policy.policyArea}
                    onChange={e => updateEditedPolicy("policyArea", e.target.value)}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>Yearly Budget:</label>
                  <input
                    type="number"
                    value={policy.implementation?.yearlyBudget || ""}
                    onChange={e => updateEditedPolicySection("implementation", "yearlyBudget", e.target.value)}
                    className="form-input"
                  />
                </div>

                <div className="form-actions">
                  <button 
                    className="btn btn-primary"
                    onClick={() => handleEditPolicy(selectedSubmission.submission_id, selectedPolicy.policy_index, editedPolicy)}
                  >
                    Save Changes
                  </button>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => {
                      setEditMode(false)
                      setEditedPolicy(null)
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="policy-details">
                <div className="detail-section">
                  <h3>Basic Information</h3>
                  <p><strong>Policy ID:</strong> {policy.policyId}</p>
                  <p><strong>Policy Area:</strong> {policy.policyArea}</p>
                  <p><strong>Target Groups:</strong> {policy.targetGroups?.join(", ")}</p>
                  <p><strong>Description:</strong> {policy.policyDescription}</p>
                  <p><strong>Link:</strong> 
                    {policy.policyLink && (
                      <a href={policy.policyLink} target="_blank" rel="noopener noreferrer">
                        {policy.policyLink}
                      </a>
                    )}
                  </p>
                </div>

                {policy.policyFile && (
                  <div className="detail-section">
                    <h3>Attached File</h3>
                    <div className="file-info">
                      <p><strong>File:</strong> {policy.policyFile.name}</p>
                      <p><strong>Size:</strong> {(policy.policyFile.size / 1024).toFixed(1)} KB</p>
                      <p><strong>Type:</strong> {policy.policyFile.type}</p>
                      {policy.policyFile.content && (
                        <div className="file-content">
                          <h4>File Content:</h4>
                          <pre className="content-preview">{policy.policyFile.content.substring(0, 500)}...</pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="detail-section">
                  <h3>Implementation</h3>
                  <p><strong>Budget:</strong> {policy.implementation?.yearlyBudget} {policy.implementation?.budgetCurrency}</p>
                  <p><strong>Deployment Year:</strong> {policy.implementation?.deploymentYear}</p>
                  <p><strong>Private Funding:</strong> {policy.implementation?.privateSecFunding ? "Yes" : "No"}</p>
                </div>

                <div className="detail-section">
                  <h3>Evaluation</h3>
                  <p><strong>Evaluated:</strong> {policy.evaluation?.isEvaluated ? "Yes" : "No"}</p>
                  {policy.evaluation?.isEvaluated && (
                    <>
                      <p><strong>Type:</strong> {policy.evaluation.evaluationType}</p>
                      <p><strong>Transparency Score:</strong> {policy.evaluation.transparencyScore}/10</p>
                      <p><strong>Explainability Score:</strong> {policy.evaluation.explainabilityScore}/10</p>
                      <p><strong>Accountability Score:</strong> {policy.evaluation.accountabilityScore}/10</p>
                    </>
                  )}
                </div>

                <div className="admin-actions">
                  <h3>Admin Actions</h3>
                  <div className="action-buttons">
                    <button 
                      className="btn btn-success"
                      onClick={() => updatePolicyStatus(selectedSubmission.submission_id, policy.policy_index, "approved", adminNotes)}
                    >
                      Approve
                    </button>
                    <button 
                      className="btn btn-warning"
                      onClick={() => updatePolicyStatus(selectedSubmission.submission_id, policy.policy_index, "needs_revision", adminNotes)}
                    >
                      Needs Revision
                    </button>
                    <button 
                      className="btn btn-danger"
                      onClick={() => updatePolicyStatus(selectedSubmission.submission_id, policy.policy_index, "rejected", adminNotes)}
                    >
                      Reject
                    </button>
                    <button 
                      className="btn btn-info"
                      onClick={() => {
                        setEditMode(true)
                        setEditedPolicy({...policy})
                      }}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-danger"
                      onClick={() => deletePolicy(selectedSubmission.submission_id, policy.policy_index)}
                    >
                      Delete
                    </button>
                  </div>

                  <div className="admin-notes">
                    <label>Admin Notes:</label>
                    <textarea
                      value={adminNotes}
                      onChange={e => setAdminNotes(e.target.value)}
                      placeholder="Add notes for this policy..."
                      className="form-textarea"
                      rows="3"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Main render
  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h1>Policy Administration Dashboard</h1>
        <p>Review and manage policy submissions</p>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="dashboard-controls">
        <div className="search-filter">
          <input
            type="text"
            placeholder="Search by country or policy name..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="search-input"
          />
          
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="needs_revision">Needs Revision</option>
          </select>
        </div>

        <button 
          className="btn btn-primary"
          onClick={fetchSubmissions}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="submissions-list">
        {loading ? (
          <div className="loading">Loading submissions...</div>
        ) : filteredSubmissions.length === 0 ? (
          <div className="no-data">No submissions found</div>
        ) : (
          filteredSubmissions.map(submission => (
            <div key={submission.submission_id} className="submission-card">
              <div className="submission-header">
                <h3>{submission.country}</h3>
                <span className="submission-id">ID: {submission.submission_id}</span>
                <span className="submission-date">
                  {new Date(submission.submitted_at).toLocaleDateString()}
                </span>
              </div>

              <div className="policies-grid">
                {submission.policyInitiatives.map((policy, index) => (
                  <div 
                    key={index} 
                    className={`policy-card status-${policy.status}`}
                    onClick={() => {
                      setSelectedSubmission(submission)
                      setSelectedPolicy({...policy, policy_index: index})
                      setShowPolicyModal(true)
                      setAdminNotes(policy.admin_notes || "")
                    }}
                  >
                    <div className="policy-header">
                      <h4>{policy.policyName}</h4>
                      <span className={`status-badge status-${policy.status}`}>
                        {policy.status}
                      </span>
                    </div>
                    
                    <p className="policy-description">
                      {policy.policyDescription.substring(0, 100)}...
                    </p>
                    
                    <div className="policy-meta">
                      <span className="policy-area">{policy.policyArea}</span>
                      {policy.policyFile && (
                        <span className="has-file">📄 File Attached</span>
                      )}
                    </div>

                    {policy.admin_notes && (
                      <div className="admin-notes-preview">
                        <strong>Admin Notes:</strong> {policy.admin_notes.substring(0, 50)}...
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {renderPolicyModal()}
    </div>
  )
}