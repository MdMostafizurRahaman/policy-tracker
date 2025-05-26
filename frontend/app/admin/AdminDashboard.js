import { useState, useEffect } from "react"

// API base URL
const API_BASE_URL = 'http://localhost:8000/api'

export default function AdminDashboard() {
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [selectedSubmission, setSelectedSubmission] = useState(null)
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [selectedPolicyIndex, setSelectedPolicyIndex] = useState(null)
  const [showPolicyModal, setShowPolicyModal] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editedPolicy, setEditedPolicy] = useState(null)
  const [adminNotes, setAdminNotes] = useState("")
  const [filterStatus, setFilterStatus] = useState("all")
  const [searchTerm, setSearchTerm] = useState("")
  const [statistics, setStatistics] = useState({})
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  // Fetch all submissions on component mount
  useEffect(() => {
    fetchSubmissions()
    fetchStatistics()
  }, [currentPage, filterStatus])

  const fetchSubmissions = async () => {
    setLoading(true)
    try {
      let url = `${API_BASE_URL}/admin/submissions?page=${currentPage}&limit=10`
      if (filterStatus !== "all") {
        url += `&status=${filterStatus}`
      }
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('Failed to fetch submissions')
      }
      const data = await response.json()
      setSubmissions(data.submissions || [])
      setTotalPages(data.total_pages || 1)
    } catch (error) {
      setError(`Error fetching submissions: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/statistics`)
      if (response.ok) {
        const data = await response.json()
        setStatistics(data)
      }
    } catch (error) {
      console.error('Error fetching statistics:', error)
    }
  }

  // Handle policy status update
  const updatePolicyStatus = async (submissionId, policyIndex, status, notes = "") => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/update-policy-status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
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
        fetchSubmissions()
        fetchStatistics()
        
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
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          submission_id: submissionId,
          policy_index: policyIndex
        })
      })
      
      if (response.ok) {
        setSuccess("Policy approved and moved to master database")
      }
    } catch (error) {
      console.error('Error moving to master:', error)
    }
  }

  // Delete policy
  const deletePolicy = async (submissionId, policyIndex) => {
    if (window.confirm('Are you sure you want to delete this policy?')) {
      try {
        const response = await fetch(`${API_BASE_URL}/admin/delete-policy`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            submission_id: submissionId,
            policy_index: policyIndex
          })
        })
        
        if (!response.ok) {
          throw new Error('Failed to delete policy')
        }
        
        setSuccess("Policy deleted successfully")
        fetchSubmissions()
        fetchStatistics()
        setShowPolicyModal(false)
      } catch (error) {
        setError(`Error deleting policy: ${error.message}`)
      }
    }
  }

  // Edit policy
  const saveEditedPolicy = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/edit-policy`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          submission_id: selectedSubmission._id,
          policy_index: selectedPolicyIndex,
          updated_policy: editedPolicy
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to save policy changes')
      }
      
      setSuccess("Policy updated successfully")
      setEditMode(false)
      fetchSubmissions()
    } catch (error) {
      setError(`Error saving policy: ${error.message}`)
    }
  }

  // Open policy modal
  const openPolicyModal = (submission, policy, index) => {
    setSelectedSubmission(submission)
    setSelectedPolicy(policy)
    setSelectedPolicyIndex(index)
    setEditedPolicy({ ...policy })
    setAdminNotes(policy.admin_notes || "")
    setShowPolicyModal(true)
    setEditMode(false)
  }

  // Filter submissions based on search term
  const filteredSubmissions = submissions.filter(submission =>
    submission.country.toLowerCase().includes(searchTerm.toLowerCase()) ||
    submission.policyInitiatives.some(policy =>
      policy.policyName.toLowerCase().includes(searchTerm.toLowerCase())
    )
  )

  // Clear messages after 5 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError("")
        setSuccess("")
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, success])

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-600 bg-green-100'
      case 'rejected': return 'text-red-600 bg-red-100'
      case 'needs_revision': return 'text-yellow-600 bg-yellow-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">Manage AI policy submissions and approvals</p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-semibold text-gray-900">{statistics.pending_submissions || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Partially Approved</p>
                <p className="text-2xl font-semibold text-gray-900">{statistics.partially_approved || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Fully Approved</p>
                <p className="text-2xl font-semibold text-gray-900">{statistics.fully_approved || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Master Policies</p>
                <p className="text-2xl font-semibold text-gray-900">{statistics.total_approved_policies || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input
                type="text"
                placeholder="Search by country or policy name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="partially_approved">Partially Approved</option>
                <option value="fully_approved">Fully Approved</option>
                <option value="fully_processed">Fully Processed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {success}
          </div>
        )}

        {/* Submissions Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Policy Submissions</h2>
          </div>

          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Country
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Policies
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Submitted
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredSubmissions.map((submission) => (
                    <tr key={submission._id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{submission.country}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-2">
                          {submission.policyInitiatives.map((policy, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between p-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100"
                              onClick={() => openPolicyModal(submission, policy, index)}
                            >
                              <div>
                                <div className="text-sm font-medium text-gray-900">{policy.policyName}</div>
                                <div className="text-xs text-gray-500">{policy.policyArea}</div>
                              </div>
                              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(policy.status)}`}>
                                {policy.status || 'pending'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(submission.submission_status)}`}>
                          {submission.submission_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(submission.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => {
                            setSelectedSubmission(submission)
                            // Could open a submission details modal here
                          }}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Policy Detail Modal */}
        {showPolicyModal && selectedPolicy && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                {/* Modal Header */}
                <div className="flex justify-between items-center pb-4 border-b">
                  <h3 className="text-lg font-medium text-gray-900">
                    Policy Details: {selectedPolicy.policyName}
                  </h3>
                  <button
                    onClick={() => setShowPolicyModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Modal Content */}
                <div className="mt-4 max-h-96 overflow-y-auto">
                  {editMode ? (
                    // Edit Mode
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Policy Name</label>
                        <input
                          type="text"
                          value={editedPolicy.policyName}
                          onChange={(e) => setEditedPolicy({ ...editedPolicy, policyName: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Policy Area</label>
                        <input
                          type="text"
                          value={editedPolicy.policyArea}
                          onChange={(e) => setEditedPolicy({ ...editedPolicy, policyArea: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea
                          value={editedPolicy.policyDescription}
                          onChange={(e) => setEditedPolicy({ ...editedPolicy, policyDescription: e.target.value })}
                          rows={4}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  ) : (
                    // View Mode
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium text-gray-900">Policy Information</h4>
                        <div className="mt-2 grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600">Policy Name</p>
                            <p className="text-sm font-medium">{selectedPolicy.policyName}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Policy Area</p>
                            <p className="text-sm font-medium">{selectedPolicy.policyArea || 'Not specified'}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Status</p>
                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(selectedPolicy.status)}`}>
                              {selectedPolicy.status || 'pending'}
                            </span>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Country</p>
                            <p className="text-sm font-medium">{selectedSubmission.country}</p>
                          </div>
                        </div>
                      </div>

                      {selectedPolicy.policyDescription && (
                        <div>
                          <h4 className="font-medium text-gray-900">Description</h4>
                          <p className="mt-1 text-sm text-gray-700">{selectedPolicy.policyDescription}</p>
                        </div>
                      )}

                      {selectedPolicy.targetGroups && selectedPolicy.targetGroups.length > 0 && (
                        <div>
                          <h4 className="font-medium text-gray-900">Target Groups</h4>
                          <div className="mt-1 flex flex-wrap gap-2">
                            {selectedPolicy.targetGroups.map((group, index) => (
                              <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                {group}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {selectedPolicy.admin_notes && (
                        <div>
                          <h4 className="font-medium text-gray-900">Admin Notes</h4>
                          <p className="mt-1 text-sm text-gray-700">{selectedPolicy.admin_notes}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Admin Notes Section */}
                <div className="mt-6 pt-4 border-t">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Admin Notes</label>
                  <textarea
                    value={adminNotes}
                    onChange={(e) => setAdminNotes(e.target.value)}
                    rows={3}
                    placeholder="Add notes for this policy..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Modal Actions */}
                <div className="mt-6 flex flex-wrap gap-2 justify-end">
                  {editMode ? (
                    <>
                      <button
                        onClick={() => setEditMode(false)}
                        className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                      >
                        Cancel Edit
                      </button>
                      <button
                        onClick={saveEditedPolicy}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        Save Changes
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => setEditMode(true)}
                        className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                      >
                        Edit Policy
                      </button>
                      <button
                        onClick={() => updatePolicyStatus(selectedSubmission._id, selectedPolicyIndex, 'needs_revision', adminNotes)}
                        className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                      >
                        Needs Revision
                      </button>
                      <button
                        onClick={() => updatePolicyStatus(selectedSubmission._id, selectedPolicyIndex, 'rejected', adminNotes)}
                        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => updatePolicyStatus(selectedSubmission._id, selectedPolicyIndex, 'approved', adminNotes)}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => deletePolicy(selectedSubmission._id, selectedPolicyIndex)}
                        className="px-4 py-2 bg-red-800 text-white rounded hover:bg-red-900"
                      >
                        Delete Policy
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}