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
  const [showSubmissionModal, setShowSubmissionModal] = useState(false)
  const [selectedSubmissionDetails, setSelectedSubmissionDetails] = useState(null)

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

    const handleOpenSubmissionDetails = (submission) => {
    setSelectedSubmissionDetails(submission)
    setShowSubmissionModal(true)
  }

  const handleOpenFile = async (fileInfo) => {
  try {
    if (fileInfo.file_path) {
      // For server-stored files
      const response = await fetch(`${API_BASE_URL}/files/${fileInfo.file_path}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        window.open(url, '_blank')
      }
    } else if (fileInfo.data) {
      // For base64 stored files  
      const byteCharacters = atob(fileInfo.data)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: fileInfo.type })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    }
  } catch (error) {
    setError(`Error opening file: ${error.message}`)
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
    submission.country?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    submission.policyInitiatives?.some(policy =>
      policy.policyName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      policy.policyId?.toLowerCase().includes(searchTerm.toLowerCase())
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
      case 'approved': return 'text-emerald-700 bg-emerald-50 border-emerald-200'
      case 'rejected': return 'text-red-700 bg-red-50 border-red-200'
      case 'needs_revision': return 'text-amber-700 bg-amber-50 border-amber-200'
      case 'active': return 'text-blue-700 bg-blue-50 border-blue-200'
      default: return 'text-slate-700 bg-slate-50 border-slate-200'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatCurrency = (amount, currency) => {
    if (!amount) return 'N/A'
    return `${currency || 'USD'} ${parseFloat(amount).toLocaleString()}`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent mb-3">
            Admin Dashboard
          </h1>
          <p className="text-slate-600 text-lg">Manage AI policy submissions and approvals</p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6 hover:shadow-lg transition-all duration-300">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Pending</p>
                <p className="text-2xl font-bold text-slate-900">{statistics.pending_submissions || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6 hover:shadow-lg transition-all duration-300">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Partially Approved</p>
                <p className="text-2xl font-bold text-slate-900">{statistics.partially_approved || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6 hover:shadow-lg transition-all duration-300">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-emerald-500 to-green-500 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Fully Approved</p>
                <p className="text-2xl font-bold text-slate-900">{statistics.fully_approved || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6 hover:shadow-lg transition-all duration-300">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Master Policies</p>
                <p className="text-2xl font-bold text-slate-900">{statistics.total_approved_policies || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 mb-6 p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-sm font-semibold text-slate-700 mb-2">Search</label>
              <input
                type="text"
                placeholder="Search by country, policy name, or policy ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/70"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Filter by Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/70"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="needs_revision">Needs Revision</option>
                <option value="active">Active (Master)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-6 py-4 rounded-xl mb-4 shadow-sm">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          </div>
        )}
        {success && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-6 py-4 rounded-xl mb-4 shadow-sm">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              {success}
            </div>
          </div>
        )}

        {/* Submissions Table */}
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-200">
            <h2 className="text-xl font-bold text-slate-900">Policy Submissions</h2>
          </div>

          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50/80">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Country
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Policies
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Budget
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Submitted
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white/50 divide-y divide-slate-200">
                  {filteredSubmissions.map((submission) => (
                    <tr key={submission._id} className="hover:bg-slate-50/50 transition-colors duration-150">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-slate-900">{submission.country}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-3">
                          {submission.policyInitiatives?.map((policy, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between p-3 bg-white/80 rounded-lg border border-slate-200 cursor-pointer hover:bg-blue-50/50 hover:border-blue-200 transition-all duration-200 shadow-sm"
                              onClick={() => openPolicyModal(submission, policy, index)}
                            >
                              <div className="flex-1">
                                <div className="text-sm font-semibold text-slate-900">{policy.policyName}</div>
                                <div className="text-xs text-slate-600 mt-1">
                                  ID: {policy.policyId} | Area: {policy.policyArea}
                                </div>
                                <div className="text-xs text-slate-500 mt-1">
                                  Deployment: {policy.implementation?.deploymentYear || 'TBD'}
                                </div>
                              </div>
                              <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(policy.status)}`}>
                                {policy.status || 'pending'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-slate-700">
                          {submission.policyInitiatives?.map((policy, index) => (
                            <div key={index} className="mb-1 font-medium">
                              {formatCurrency(policy.implementation?.yearlyBudget, policy.implementation?.budgetCurrency)}
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(submission.submission_status)}`}>
                          {submission.submission_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {formatDate(submission.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleOpenSubmissionDetails(submission)}
                          className="text-blue-600 hover:text-blue-800 font-semibold transition-colors duration-150"
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
          {showSubmissionModal && selectedSubmissionDetails && (
            <div className="fixed inset-0 bg-black/40 backdrop-blur-sm overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
              <div className="relative w-full max-w-3xl bg-white rounded-2xl shadow-2xl border border-white/20 my-8 overflow-hidden">
                {/* Modal Header */}
                <div className="p-6 flex justify-between items-center border-b border-slate-200">
                  <h3 className="text-2xl font-bold text-slate-900">Submission Details</h3>
                  <button
                    onClick={() => setShowSubmissionModal(false)}
                    className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                {/* Submission Details Content */}
                <div className="p-6 max-h-[80vh] overflow-y-auto">
                  {/* Display selected submission info - customize as needed */}
                  <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-gray-700 mb-2">Country: {selectedSubmissionDetails.country}</h4>
                    <p><strong>Submitted At:</strong> {formatDate(selectedSubmissionDetails.created_at)}</p>
                    {/* List policies or other details as needed */}
                    {selectedSubmissionDetails.policyInitiatives?.map((policy, index) => (
                      <div key={index} className="border rounded p-3 mb-2 bg-gray-50">
                        <p><strong>Policy Name:</strong> {policy.policyName}</p>
                        <p><strong>Status:</strong> {policy.status}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between bg-slate-50/50">
              <div className="text-sm text-slate-700 font-medium">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Policy Detail Modal */}
        {showPolicyModal && selectedPolicy && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
            <div className="relative w-full max-w-6xl bg-white rounded-2xl shadow-2xl border border-white/20 my-8">
              <div className="p-8">
                {/* Modal Header */}
                <div className="flex justify-between items-center pb-6 border-b border-slate-200">
                  <div>
                    <h3 className="text-2xl font-bold text-slate-900">
                      {selectedPolicy.policyName}
                    </h3>
                    <p className="text-slate-600 mt-1">Policy Details & Management</p>
                  </div>
                  <button
                    onClick={() => setShowPolicyModal(false)}
                    className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200"
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
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Policy Name</label>
                          <input
                            type="text"
                            value={editedPolicy.policyName || ''}
                            onChange={(e) => setEditedPolicy({ ...editedPolicy, policyName: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Policy ID</label>
                          <input
                            type="text"
                            value={editedPolicy.policyId || ''}
                            onChange={(e) => setEditedPolicy({ ...editedPolicy, policyId: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Policy Area</label>
                          <input
                            type="text"
                            value={editedPolicy.policyArea || ''}
                            onChange={(e) => setEditedPolicy({ ...editedPolicy, policyArea: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                          <textarea
                            value={editedPolicy.policyDescription || ''}
                            onChange={(e) => setEditedPolicy({ ...editedPolicy, policyDescription: e.target.value })}
                            rows={4}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Yearly Budget</label>
                          <input
                            type="text"
                            value={editedPolicy.implementation?.yearlyBudget || ''}
                            onChange={(e) => setEditedPolicy({
                              ...editedPolicy,
                              implementation: { ...editedPolicy.implementation, yearlyBudget: e.target.value }
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                          <input
                            type="text"
                            value={editedPolicy.implementation?.budgetCurrency || ''}
                            onChange={(e) => setEditedPolicy({
                              ...editedPolicy,
                              implementation: { ...editedPolicy.implementation, budgetCurrency: e.target.value }
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Deployment Year</label>
                          <input
                            type="number"
                            value={editedPolicy.implementation?.deploymentYear || ''}
                            onChange={(e) => setEditedPolicy({
                              ...editedPolicy,
                              implementation: { ...editedPolicy.implementation, deploymentYear: parseInt(e.target.value) }
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    </div>
                  ) : (
                    // View Mode
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-6">
                        <div>
                          <h4 className="font-medium text-gray-900 mb-3">Basic Information</h4>
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Policy Name</p>
                                <p className="text-sm font-medium">{selectedPolicy.policyName}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Policy ID</p>
                                <p className="text-sm font-medium">{selectedPolicy.policyId || 'N/A'}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Policy Area</p>
                                <p className="text-sm font-medium">{selectedPolicy.policyArea || 'N/A'}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Country</p>
                                <p className="text-sm font-medium">{selectedSubmission.country}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Status</p>
                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(selectedPolicy.status)}`}>
                                  {selectedPolicy.status || 'pending'}
                                </span>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Master Status</p>
                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(selectedPolicy.master_status)}`}>
                                  {selectedPolicy.master_status || 'N/A'}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {selectedPolicy.policyDescription && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                            <p className="text-sm text-gray-700">{selectedPolicy.policyDescription}</p>
                          </div>
                        )}

                        {selectedPolicy.targetGroups && selectedPolicy.targetGroups.length > 0 && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Target Groups</h4>
                            <div className="flex flex-wrap gap-2">
                              {selectedPolicy.targetGroups.map((group, index) => (
                                <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                  {group}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {selectedPolicy.policyFile && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Policy File</h4>
                            <div className="bg-gray-50 p-3 rounded">
                              <p className="text-sm"><strong>Name:</strong> {selectedPolicy.policyFile.name}</p>
                              <p className="text-sm"><strong>Type:</strong> {selectedPolicy.policyFile.type}</p>
                              <p className="text-sm"><strong>Size:</strong> {(selectedPolicy.policyFile.size / 1024).toFixed(2)} KB</p>
                              <p className="text-sm"><strong>Upload Date:</strong> {formatDate(selectedPolicy.policyFile.upload_date)}</p>
                              <button onClick={() => handleOpenFile(selectedPolicy.policyFile)} className="mt-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">Open File</button>
                            </div>
                          </div>
                        )}

                        {selectedPolicy.policyLink && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Policy Link</h4>
                            <div className="flex items-center gap-2"> {/* ADD flex container */}
                              <a href={selectedPolicy.policyLink} target="_blank" rel="noopener noreferrer" 
                                className="text-blue-600 hover:text-blue-800 text-sm">
                                {selectedPolicy.policyLink}
                              </a>
                              <button
                                onClick={() => window.open(selectedPolicy.policyLink, '_blank')}
                                className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                              >
                                Open Link
                              </button>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="space-y-6">
                        {/* Implementation Details */}
                        {selectedPolicy.implementation && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-3">Implementation Details</h4>
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm text-gray-600">Yearly Budget</p>
                                  <p className="text-sm font-medium">
                                    {formatCurrency(selectedPolicy.implementation.yearlyBudget, selectedPolicy.implementation.budgetCurrency)}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Private Sector Funding</p>
                                  <p className="text-sm font-medium">
                                    {selectedPolicy.implementation.privateSecFunding ? 'Yes' : 'No'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Deployment Year</p>
                                  <p className="text-sm font-medium">{selectedPolicy.implementation.deploymentYear || 'TBD'}</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Evaluation Details */}
                        {selectedPolicy.evaluation && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-3">Evaluation & Assessment</h4>
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm text-gray-600">Is Evaluated</p>
                                  <p className="text-sm font-medium">
                                    {selectedPolicy.evaluation.isEvaluated ? 'Yes' : 'No'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Evaluation Type</p>
                                  <p className="text-sm font-medium">{selectedPolicy.evaluation.evaluationType || 'N/A'}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Risk Assessment</p>
                                  <p className="text-sm font-medium">
                                    {selectedPolicy.evaluation.riskAssessment ? 'Yes' : 'No'}
                                  </p>
                                </div>
                              </div>
                              
                              <div className="mt-4">
                                <h5 className="text-sm font-medium text-gray-700 mb-2">Scores</h5>
                                <div className="grid grid-cols-3 gap-4">
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">Transparency</p>
                                    <p className="text-lg font-semibold text-blue-600">
                                      {selectedPolicy.evaluation.transparencyScore || 0}/10
                                    </p>
                                  </div>
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">Explainability</p>
                                    <p className="text-lg font-semibold text-green-600">
                                      {selectedPolicy.evaluation.explainabilityScore || 0}/10
                                    </p>
                                  </div>
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">Accountability</p>
                                    <p className="text-lg font-semibold text-purple-600">
                                      {selectedPolicy.evaluation.accountabilityScore || 0}/10
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Participation Details */}
                        {selectedPolicy.participation && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-3">Public Participation</h4>
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm text-gray-600">Has Consultation</p>
                                  <p className="text-sm font-medium">
                                    {selectedPolicy.participation.hasConsultation ? 'Yes' : 'No'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Comments Public</p>
                                  <p className="text-sm font-medium">
                                    {selectedPolicy.participation.commentsPublic ? 'Yes' : 'No'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Stakeholder Score</p>
                                  <p className="text-sm font-medium">{selectedPolicy.participation.stakeholderScore || 0}/10</p>
                                </div>
                              </div>
                              
                              {selectedPolicy.participation.consultationStartDate && (
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <p className="text-sm text-gray-600">Consultation Start</p>
                                    <p className="text-sm font-medium">
                                      {formatDate(selectedPolicy.participation.consultationStartDate)}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-sm text-gray-600">Consultation End</p>
                                    <p className="text-sm font-medium">
                                      {formatDate(selectedPolicy.participation.consultationEndDate)}
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Dates and Tracking */}
                        <div>
                          <h4 className="font-medium text-gray-900 mb-3">Tracking Information</h4>
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-4">
                              {selectedPolicy.original_submission_id && (
                                <div>
                                  <p className="text-sm text-gray-600">Original Submission ID</p>
                                  <p className="text-sm font-medium font-mono">{selectedPolicy.original_submission_id}</p>
                                </div>
                              )}
                              {selectedPolicy.moved_to_master_at && (
                                <div>
                                  <p className="text-sm text-gray-600">Moved to Master</p>
                                  <p className="text-sm font-medium">{formatDate(selectedPolicy.moved_to_master_at)}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {selectedPolicy.admin_notes && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Admin Notes</h4>
                            <div className="bg-yellow-50 p-3 rounded">
                              <p className="text-sm text-gray-700">{selectedPolicy.admin_notes}</p>
                            </div>
                          </div>
                        )}
                      </div>
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