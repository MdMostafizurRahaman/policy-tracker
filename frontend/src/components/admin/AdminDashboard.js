import { useState, useEffect } from "react"
import '../../styles/admin-dashboard.css'
import { apiService, publicService } from '../../services/api'
import { policyAreas } from '../../utils/constants'
import AdminLogin from './AdminLogin'
import VisitCounter from '../common/VisitCounter'
import { useVisitTracker } from '../../hooks/useVisitTracker'

// Use the imported policy areas instead of hardcoded ones
const POLICY_AREAS = policyAreas;

export default function AdminDashboard() {
  // State management
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [selectedSubmission, setSelectedSubmission] = useState(null)
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [selectedPolicyArea, setSelectedPolicyArea] = useState(null)
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
  const [view, setView] = useState("dashboard")
  const [user, setUser] = useState(null)
  const [showFilesModal, setShowFilesModal] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])

  // Get token for authenticated requests
  const token = localStorage.getItem('access_token');

  // Visit tracking hook
  const { visitStats, fetchDetailedStats } = useVisitTracker()

  // Check authentication on mount
  useEffect(() => {
    if (!token) {
      setView('admin-login');
      return;
    }
    
    // Try to get user data from localStorage
    const userData = localStorage.getItem('userData');
    if (userData) {
      try {
        setUser(JSON.parse(userData));
      } catch (e) {
        console.error('Error parsing user data:', e);
        // Clear invalid data and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('userData');
        setView('admin-login');
        return;
      }
    }
  }, [token]);

  // Fetch data on component mount and dependencies
  useEffect(() => {
    if (token && view === 'dashboard') {
      fetchSubmissions()
      fetchStatistics()
      fetchDetailedStats() // Fetch detailed visit statistics
    }
  }, [currentPage, filterStatus, fetchDetailedStats])

  // API Functions
  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      console.log('Fetching submissions...');
      const data = await apiService.admin.getSubmissions(currentPage, 10, filterStatus);
      console.log('Received data:', data);
      console.log('Setting submissions to:', data.data);
      setSubmissions(data.data || [])  // Fix: use data.data instead of data.submissions
      setTotalPages(data.total_pages || 1)
    } catch (error) {
      // Handle authentication errors
      if (error.message.includes('Invalid token')) {
        setView('admin-login');
        setError('Session expired. Please login again.');
        return;
      }
      setError(`Error fetching submissions: ${error.message}`)
    } finally {
      setLoading(false);
    }
  }

  const fetchStatistics = async () => {
    try {
      // Try to load from cache first for instant display
      const cached = localStorage.getItem('admin_stats_cache');
      if (cached) {
        try {
          const cachedData = JSON.parse(cached);
          const age = Date.now() - cachedData.timestamp;
          if (age < 120000) { // Use cache if less than 2 minutes old
            setStatistics(cachedData.statistics);
            console.log('📊 Using cached statistics');
            return; // Don't fetch new data if cache is fresh
          }
        } catch (e) {
          console.warn('Cache parsing error:', e);
        }
      }
      
      // Remove the aggressive timeout that's causing AbortError
      // Try the fast statistics endpoint first
      let data;
      try {
        data = await publicService.getStatisticsFast();
      } catch (fastError) {
        console.warn('Fast stats failed, trying admin endpoint:', fastError);
        data = await apiService.admin.getStatistics();
      }
      
      // Extract the statistics object from the response  
      const statisticsData = data.statistics || data;
      
      // Cache the successful response
      localStorage.setItem('admin_stats_cache', JSON.stringify({
        statistics: statisticsData,
        timestamp: Date.now()
      }));
      
      // Handle graceful errors from backend
      if (data.error || data.note) {
        console.warn('Statistics warning:', data.error || data.note);
      }
      setStatistics(statisticsData);
      
    } catch (error) {
      if (error.name === 'AbortError' || error.message.includes('timeout')) {
        console.warn('Statistics request timeout');
        
        // Try to use cache on timeout
        const cached = localStorage.getItem('admin_stats_cache');
        if (cached) {
          try {
            const cachedData = JSON.parse(cached);
            setStatistics(cachedData.statistics);
            console.log('📊 Using cached statistics due to timeout');
            return;
          } catch (e) {
            console.warn('Cache error:', e);
          }
        }
      } else {
        console.error('Error fetching statistics:', error);
      }
      
      // Set default values as last resort
      setStatistics({
        users: { total: 0, verified: 0, admin: 0 },
        submissions: { total: 0, pending: 0 },
        policies: { master: 0, approved: 0, rejected: 0, under_review: 0 }
      });
    }
  }

  // Policy Management Functions
  const updatePolicyStatus = async (submissionId, policyArea, policyIndex, status, notes = "") => {
    try {
      const result = await apiService.admin.updatePolicyStatus(
        submissionId, 
        policyArea,
        policyIndex, 
        status, 
        notes
      );
      
      if (result.success) {
        setSuccess(`Policy status updated to ${status}`)
        fetchSubmissions()
        fetchStatistics()
      }
    } catch (error) {
      setError(`Error updating policy: ${error.message}`)
    }
  }

  const movePolicyToMaster = async (submissionId) => {
    try {
      const result = await apiService.admin.moveToMaster(submissionId);
      
      if (result) {
        setSuccess("Policy approved and moved to master database")
      }
    } catch (error) {
      console.error('Error moving to master:', error)
    }
  }

  const deletePolicy = async (submissionId, policyArea, policyIndex) => {
    if (window.confirm('Are you sure you want to delete this policy?')) {
      try {
        await apiService.admin.deleteSubmissionPolicy(submissionId, policyArea, policyIndex);
        
        setSuccess("Policy deleted successfully")
        fetchSubmissions()
        fetchStatistics()
        setShowPolicyModal(false)
      } catch (error) {
        setError(`Error deleting policy: ${error.message}`)
      }
    }
  }

  const saveEditedPolicy = async () => {
    try {
      await apiService.put('/admin/edit-policy', {
        submission_id: selectedSubmission._id,
        policy_area: selectedPolicyArea,
        policy_index: selectedPolicyIndex,
        updated_policy: editedPolicy
      });
      
      setSuccess("Policy updated successfully")
      setEditMode(false)
      fetchSubmissions()
    } catch (error) {
      setError(`Error saving policy: ${error.message}`)
    }
  }

  // New Comprehensive Admin Actions
  const approvePolicy = async (submissionId, areaId, policyIndex, adminNotes = "") => {
    try {
      setLoading(true);
      const result = await apiService.admin.approvePolicy(submissionId, areaId, policyIndex, adminNotes);
      
      if (result.success) {
        setSuccess("Policy approved successfully and made visible on map");
        setShowPolicyModal(false); // Close modal after successful approval
        setShowSubmissionModal(false); // Close submission modal too
        fetchSubmissions();
        fetchStatistics();
      }
    } catch (error) {
      setError(`Error approving policy: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const rejectPolicy = async (submissionId, areaId, policyIndex, adminNotes = "") => {
    if (window.confirm('Are you sure you want to reject this policy?')) {
      try {
        setLoading(true);
        const result = await apiService.admin.rejectPolicy(submissionId, areaId, policyIndex, adminNotes);
        
        if (result.success) {
          setSuccess("Policy rejected and removed from map visibility");
          setShowPolicyModal(false); // Close modal after successful rejection
          setShowSubmissionModal(false); // Close submission modal too
          fetchSubmissions();
          fetchStatistics();
        }
      } catch (error) {
        setError(`Error rejecting policy: ${error.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const commitPolicy = async (submissionId, areaId, policyIndex) => {
    if (window.confirm('Are you sure you want to commit this approved policy to master database?')) {
      try {
        setLoading(true);
        const result = await apiService.admin.commitPolicy(submissionId, areaId, policyIndex);
        
        if (result.success) {
          setSuccess("Policy committed to master database successfully");
          fetchSubmissions();
          fetchStatistics();
        }
      } catch (error) {
        setError(`Error committing policy: ${error.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const deletePolicyCompletely = async (policyId) => {
    if (window.confirm('Are you sure you want to permanently delete this policy? This action cannot be undone.')) {
      try {
        setLoading(true);
        const result = await apiService.admin.deletePolicyCompletely(policyId);
        
        if (result.success) {
          setSuccess("Policy permanently deleted from database and map");
          fetchSubmissions();
          fetchStatistics();
        }
      } catch (error) {
        setError(`Error deleting policy: ${error.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const uploadPolicyFile = async (policyId, file) => {
    try {
      setLoading(true);
      
      // First upload file to S3
      const formData = new FormData();
      formData.append('file', file);
      const uploadResult = await apiService.uploadPolicyFile(file);
      
      if (uploadResult.success) {
        // Then associate with policy
        const fileData = {
          file_id: uploadResult.file_id,
          filename: file.name,
          file_type: file.type,
          file_size: file.size,
          s3_url: uploadResult.s3_url
        };
        
        const result = await apiService.admin.uploadPolicyFile(policyId, fileData);
        
        if (result.success) {
          setSuccess(`File "${file.name}" uploaded successfully for policy`);
        }
      }
    } catch (error) {
      setError(`Error uploading file: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const viewPolicyFiles = async (policyId) => {
    try {
      setLoading(true);
      const result = await apiService.admin.getPolicyFiles(policyId);
      
      if (result.success) {
        setSelectedFiles(result.files);
        setShowFilesModal(true);
      }
    } catch (error) {
      setError(`Error getting policy files: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFile = async (fileInfo) => {
    try {
      if (fileInfo.s3_key || fileInfo.file_path) {
        // Use the public file serving endpoint
        const fileIdentifier = fileInfo.s3_key || fileInfo.file_path;
        const fileUrl = `${process.env.NEXT_PUBLIC_API_URL || 'https://policy-tracker-platform-backend.onrender.com/api'}/public/files/${encodeURIComponent(fileIdentifier)}`;
        window.open(fileUrl, '_blank');
      } else if (fileInfo.s3_url) {
        // Fallback to direct S3 URL if available
        window.open(fileInfo.s3_url, '_blank');
      } else if (fileInfo.data) {
        // For base64 stored files
        const byteCharacters = atob(fileInfo.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: fileInfo.type || 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      } else {
        setError('File data not available');
      }
    } catch (error) {
      setError(`Error opening file: ${error.message}`);
    }
  };

  const deleteFileFromPolicy = async (fileId) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      try {
        setLoading(true);
        const result = await apiService.admin.deleteFile(fileId);
        
        if (result.success) {
          setSuccess('File deleted successfully');
          // Refresh the files list
          if (selectedSubmission) {
            await viewPolicyFiles(selectedSubmission.policy_id || selectedSubmission._id);
          }
        }
      } catch (error) {
        setError(`Error deleting file: ${error.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  // Modal Management
  const openPolicyModal = (submission, policy, policyArea, index) => {
    setSelectedSubmission(submission)
    setSelectedPolicy(policy)
    setSelectedPolicyArea(policyArea)
    setSelectedPolicyIndex(index)
    setEditedPolicy({ ...policy })
    setAdminNotes(policy.admin_notes || "")
    setShowPolicyModal(true)
    setEditMode(false)
  }

  const handleOpenSubmissionDetails = (submission) => {
    setSelectedSubmissionDetails(submission)
    setShowSubmissionModal(true)
  }

  // Helper Functions
  const getPolicyAreaInfo = (areaId) => {
    return POLICY_AREAS.find(area => area.id === areaId) || { 
      name: areaId, 
      color: "from-gray-500 to-gray-600",
      icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
    }
  }

  const getAllPoliciesFromSubmission = (submission) => {
    const allPolicies = [];

    // New format: policyAreas is an array of { area_id, area_name, policies }
    // Handle both policyAreas and policy_areas field names
    const policyAreas = submission.policyAreas || submission.policy_areas;
    if (Array.isArray(policyAreas)) {
      policyAreas.forEach(area => {
        if (Array.isArray(area.policies) && area.policies.length > 0) {
          area.policies.forEach((policy, index) => {
            allPolicies.push({
              ...policy,
              policyArea: area.area_id,
              areaInfo: getPolicyAreaInfo(area.area_id),
              areaIndex: index
            });
          });
        }
      });
    }
    // Old format: policyAreas is an object
    else if (submission.policyAreas && typeof submission.policyAreas === "object") {
      Object.keys(submission.policyAreas).forEach(areaId => {
        if (Array.isArray(submission.policyAreas[areaId]) && submission.policyAreas[areaId].length > 0) {
          submission.policyAreas[areaId].forEach((policy, index) => {
            allPolicies.push({
              ...policy,
              policyArea: areaId,
              areaInfo: getPolicyAreaInfo(areaId),
              areaIndex: index
            });
          });
        }
      });
    }
    // Old fallback
    else if (Array.isArray(submission.policyInitiatives)) {
      submission.policyInitiatives.forEach((policy, index) => {
        allPolicies.push({
          ...policy,
          policyArea: policy.policyArea || 'unknown',
          areaInfo: getPolicyAreaInfo(policy.policyArea || 'unknown'),
          areaIndex: index
        });
      });
    }

    return allPolicies;
  }

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

  // Filter submissions based on search term
  const filteredSubmissions = submissions.filter(submission =>
    submission.country?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    getAllPoliciesFromSubmission(submission).some(policy =>
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

  // Render admin login if needed
  if (view === "admin-login") {
    return <AdminLogin setUser={setUser} setView={setView} />;
  }

  // Main dashboard render
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
            Admin Dashboard
          </h1>
          <p className="text-xl text-slate-600">Manage AI policy submissions and approvals</p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Pending</p>
                <p className="text-2xl font-bold text-slate-900">{statistics.submissions?.pending || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Under Review</p>
                <p className="text-2xl font-bold text-slate-900">{statistics.policies?.under_review || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-emerald-500 to-green-500 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Approved Policies</p>
                <p className="text-2xl font-bold text-slate-900">{statistics.policies?.approved || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Master Policies</p>
                <p className="text-2xl font-bold text-slate-900">{statistics.policies?.master || 0}</p>
              </div>
            </div>
          </div>
          
          {/* Visit Statistics Card */}
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Website Visits</p>
                <p className="text-2xl font-bold text-slate-900">
                  {visitStats.loading ? '...' : visitStats.total_visits.toLocaleString()}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {visitStats.unique_visitors > 0 && `${visitStats.unique_visitors} unique`}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Visit Analytics */}
        <div className="mb-8">
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-900">Website Analytics</h3>
              <div className="text-sm text-slate-500">
                Real-time visitor tracking
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {visitStats.loading ? '...' : visitStats.total_visits.toLocaleString()}
                </div>
                <div className="text-sm text-slate-600">Total Visits</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {visitStats.loading ? '...' : visitStats.unique_visitors.toLocaleString()}
                </div>
                <div className="text-sm text-slate-600">Unique Visitors</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {visitStats.loading ? '...' : visitStats.today_visits || 0}
                </div>
                <div className="text-sm text-slate-600">Today's Visits</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-slate-600 mb-2">User Types</div>
                <div className="flex justify-center gap-4 text-xs">
                  <span className="text-slate-700">
                    👁️ {visitStats.user_type_breakdown?.viewer || 0}
                  </span>
                  <span className="text-blue-700">
                    👤 {visitStats.user_type_breakdown?.registered || 0}
                  </span>
                  <span className="text-purple-700">
                    ⚙️ {visitStats.user_type_breakdown?.admin || 0}
                  </span>
                </div>
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
                className="text-black w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/70"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Filter by Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className=" text-black px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/70"
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
            <div className="text-sm text-gray-600 mt-2">
              Debug: {submissions.length} submissions loaded, {filteredSubmissions.length} after filtering
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50/80">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Country</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">User Info</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Policies</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Budget</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Submitted</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white/50 divide-y divide-slate-200">
                  {filteredSubmissions.map((submission) => {
                    const allPolicies = getAllPoliciesFromSubmission(submission);
                    
                    return (
                      <tr key={submission.submission_id || submission._id} className="hover:bg-slate-50/50 transition-colors duration-150">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-semibold text-slate-900">{submission.country}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm">
                            <div className="font-semibold text-slate-900">{submission.user_name || 'N/A'}</div>
                            <div className="text-slate-600">{submission.user_email || 'N/A'}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="space-y-3">
                            {allPolicies.map((policy, index) => (
                              <div
                                key={`${policy.policyArea}-${policy.areaIndex}`}
                                className="flex items-center justify-between p-3 bg-white/80 rounded-lg border border-slate-200 cursor-pointer hover:bg-blue-50/50 hover:border-blue-200 transition-all duration-200 shadow-sm"
                                onClick={() => openPolicyModal(submission, policy, policy.policyArea, policy.areaIndex)}
                              >
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${policy.areaInfo.color}`}></div>
                                    <span className="text-xs font-medium text-slate-600">{policy.areaInfo.name}</span>
                                  </div>
                                  <div className="text-sm font-semibold text-slate-900">{policy.policyName || 'Unnamed Policy'}</div>
                                  <div className="text-xs text-slate-600 mt-1">ID: {policy.policyId || 'N/A'}</div>
                                  <div className="text-xs text-slate-500 mt-1">Deployment: {policy.implementation?.deploymentYear || 'TBD'}</div>
                                </div>
                                <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(policy.status)}`}>
                                  {policy.status || 'pending'}
                                </span>
                              </div>
                            ))}
                            {allPolicies.length === 0 && (
                              <div className="text-sm text-slate-500 italic">No policies submitted</div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-slate-700">
                            {allPolicies.map((policy, index) => (
                              <div key={index} className="mb-1 font-medium">
                                {formatCurrency(policy.implementation?.yearlyBudget, policy.implementation?.budgetCurrency)}
                              </div>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(submission.status || submission.submission_status)}`}>
                            {submission.status || submission.submission_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                          {formatDate(submission.submitted_at || submission.created_at)}
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
                    );
                  })}
                  {filteredSubmissions.length === 0 && (
                    <tr>
                      <td colSpan="7" className="px-6 py-8 text-center text-gray-500">
                        No submissions found. {submissions.length > 0 ? 'Try adjusting your search/filter.' : 'No data loaded from API.'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Submission Details Modal */}
          {showSubmissionModal && selectedSubmissionDetails && (
            <div className="fixed inset-0 bg-black/40 backdrop-blur-sm overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
              <div className="relative w-full max-w-5xl bg-white rounded-2xl shadow-2xl border border-white/20 my-8">
                <div className="p-8">
                  <div className="flex justify-between items-center border-b pb-4 mb-4">
                    <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-700 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                      Submission Details
                    </h3>
                    <button
                      onClick={() => setShowSubmissionModal(false)}
                      className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200"
                      aria-label="Close"
                    >
                      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg">
                        <h4 className="text-lg font-semibold text-blue-900 mb-3">Country & User Information</h4>
                        <div className="space-y-2">
                          <div>
                            <span className="text-sm font-medium text-blue-700">Country:</span>
                            <span className="ml-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-lg text-sm font-semibold">
                              {selectedSubmissionDetails.country}
                            </span>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-blue-700">User Name:</span>
                            <span className="ml-2 text-sm text-gray-700">{selectedSubmissionDetails.user_name || 'N/A'}</span>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-blue-700">Email:</span>
                            <span className="ml-2 text-sm text-gray-700">{selectedSubmissionDetails.user_email || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg">
                        <h4 className="text-lg font-semibold text-green-900 mb-3">Submission Status</h4>
                        <div className="space-y-2">
                          <div>
                            <span className="text-sm font-medium text-green-700">Status:</span>
                            <span className={`ml-2 px-3 py-1 text-xs font-semibold rounded-full border ${getStatusColor(selectedSubmissionDetails.submission_status)}`}>
                              {selectedSubmissionDetails.submission_status}
                            </span>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-green-700">Submitted At:</span>
                            <span className="ml-2 text-sm text-gray-700">{formatDate(selectedSubmissionDetails.submitted_at || selectedSubmissionDetails.created_at)}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h5 className="text-xl font-semibold text-indigo-700 mb-4">Policy Areas & Policies</h5>
                      
                      {selectedSubmissionDetails.policyAreas ? (
                        <div className="space-y-6">
                          {Object.keys(selectedSubmissionDetails.policyAreas).map(areaId => {
                            const policies = selectedSubmissionDetails.policyAreas[areaId];
                            const areaInfo = getPolicyAreaInfo(areaId);
                            
                            if (!Array.isArray(policies) || policies.length === 0) return null;

                            return (
                              <div key={areaId} className="border border-gray-200 rounded-xl overflow-hidden">
                                <div className={`p-4 bg-gradient-to-r ${areaInfo.color} text-white`}>
                                  <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={areaInfo.icon} />
                                      </svg>
                                    </div>
                                    <div>
                                      <h6 className="text-lg font-bold">{areaInfo.name}</h6>
                                      <p className="text-sm opacity-90">{policies.length} policies</p>
                                    </div>
                                  </div>
                                </div>
                                
                                <div className="p-4 bg-white">
                                  <div className="grid gap-4">
                                    {policies.map((policy, policyIndex) => (
                                      <div key={policyIndex} className="border-l-4 border-blue-400 bg-gradient-to-br from-blue-50 via-white to-indigo-50 rounded-xl p-4 shadow transition hover:shadow-lg">
                                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                                          <div className="flex-1">
                                            <h6 className="font-bold text-slate-900 text-lg mb-1">{policy.policyName || 'Unnamed Policy'}</h6>
                                            <div className="text-xs text-slate-500 mb-2 space-y-1">
                                              <div><span className="font-medium">Policy ID:</span> {policy.policyId || 'N/A'}</div>
                                              <div><span className="font-medium">Deployment Year:</span> {policy.implementation?.deploymentYear || 'TBD'}</div>
                                              <div><span className="font-medium">Budget:</span> {formatCurrency(policy.implementation?.yearlyBudget, policy.implementation?.budgetCurrency)}</div>
                                            </div>
                                            {policy.policyDescription && (
                                              <p className="text-sm text-slate-700 italic mb-2">{policy.policyDescription}</p>
                                            )}
                                            {policy.targetGroups && policy.targetGroups.length > 0 && (
                                              <div className="flex flex-wrap gap-1 mb-2">
                                                {policy.targetGroups.map((group, i) => (
                                                  <span key={i} className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded">{group}</span>
                                                ))}
                                              </div>
                                            )}
                                          </div>
                                          <div className="flex flex-col items-end gap-2">
                                            <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(policy.status)}`}>
                                              {policy.status || 'pending'}
                                            </span>
                                            <button
                                              onClick={() => openPolicyModal(selectedSubmissionDetails, policy, areaId, policyIndex)}
                                              className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
                                            >
                                              View Details
                                            </button>
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : selectedSubmissionDetails.policyInitiatives ? (
                        <div className="grid gap-4">
                          {selectedSubmissionDetails.policyInitiatives.map((policy, index) => (
                            <div key={index} className="border-l-4 border-blue-400 bg-gradient-to-br from-blue-50 via-white to-indigo-50 rounded-xl p-4 shadow transition hover:shadow-lg">
                              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                                <div>
                                  <p className="font-bold text-slate-900 text-lg mb-1">{policy.policyName}</p>
                                  <p className="text-xs text-slate-500 mb-1">
                                    <span className="mr-2">ID: <span className="font-mono">{policy.policyId || 'N/A'}</span></span>
                                    <span>Area: <span className="font-semibold te">{policy.policyArea || 'N/A'}</span></span>
                                  </p>
                                  <p className="text-xs text-slate-500">Deployment: <span className="font-semibold">{policy.implementation?.deploymentYear || 'TBD'}</span></p>
                                </div>
                                <div className="flex flex-col items-end gap-2">
                                  <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(policy.status)}`}>
                                    {policy.status || 'pending'}
                                  </span>
                                  <span className="text-xs text-slate-700">
                                    Budget: <span className="font-semibold">{formatCurrency(policy.implementation?.yearlyBudget, policy.implementation?.budgetCurrency)}</span>
                                  </span>
                                </div>
                              </div>
                              {policy.policyDescription && (
                                <div className="mt-2 text-sm text-slate-700 italic">{policy.policyDescription}</div>
                              )}
                              {policy.targetGroups && policy.targetGroups.length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {policy.targetGroups.map((group, i) => (
                                    <span key={i} className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded">{group}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">No policies found in this submission.</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between bg-slate-50/50">
              <div className="text-sm text-slate-700 font-medium">Page {currentPage} of {totalPages}</div>
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
                <div className="flex justify-between items-center pb-6 border-b border-slate-200">
                  <div>
                    <h3 className="text-2xl font-bold text-slate-900">{selectedPolicy.policyName || 'Unnamed Policy'}</h3>
                    <p className="text-slate-600 mt-1">{getPolicyAreaInfo(selectedPolicyArea).name} - Policy Details & Management</p>
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

                <div className="mt-4 max-h-96 overflow-y-auto">
                  {editMode ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Policy Name</label>
                          <input
                            type="text"
                            value={editedPolicy.policyName || ''}
                            onChange={(e) => setEditedPolicy({ ...editedPolicy, policyName: e.target.value })}
                            className="text-black w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Policy ID</label>
                          <input
                            type="text"
                            value={editedPolicy.policyId || ''}
                            onChange={(e) => setEditedPolicy({ ...editedPolicy, policyId: e.target.value })}
                            className="text-black w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                          <textarea
                            value={editedPolicy.policyDescription || ''}
                            onChange={(e) => setEditedPolicy({ ...editedPolicy, policyDescription: e.target.value })}
                            rows={4}
                            className="text-black w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                            className="text-black w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                            className="text-black w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                            className="text-black w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-6">
                        <div>
                          <h4 className="font-medium text-gray-900 mb-3">Basic Information</h4>
                          <div className="space-y-3">
                            <div className="text-gray-800 grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-sm text-gray-700">Policy Name</p>
                                <p className="text-sm font-medium">{selectedPolicy.policyName || 'N/A'}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Policy ID</p>
                                <p className="text-sm font-medium">{selectedPolicy.policyId || 'N/A'}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Policy Area</p>
                                <p className="text-sm font-medium">{getPolicyAreaInfo(selectedPolicyArea).name}</p>
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
                                <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">{group}</span>
                              ))}
                            </div>
                          </div>
                        )}

                        {selectedPolicy.policyFile && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Policy File</h4>
                            <div className="bg-gray-50 p-3 rounded text-black">
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
                            <div className="flex items-center gap-2">
                              <a href={selectedPolicy.policyLink} target="_blank" rel="noopener noreferrer" 
                                className="text-blue-600 hover:text-blue-800 text-sm truncate">{selectedPolicy.policyLink}</a>
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
                        {selectedPolicy.implementation && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-3">Implementation Details</h4>
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm text-gray-600">Yearly Budget</p>
                                  <p className="text-sm font-medium text-black">{formatCurrency(selectedPolicy.implementation.yearlyBudget, selectedPolicy.implementation.budgetCurrency)}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Private Sector Funding</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.implementation.privateSecFunding ? 'Yes' : 'No'}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Deployment Year</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.implementation.deploymentYear || 'TBD'}</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {selectedPolicy.evaluation && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-3">Evaluation & Assessment</h4>
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm text-gray-600">Is Evaluated</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.evaluation.isEvaluated ? 'Yes' : 'No'}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Evaluation Type</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.evaluation.evaluationType || 'N/A'}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Risk Assessment</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.evaluation.riskAssessment ? 'Yes' : 'No'}</p>
                                </div>
                              </div>
                              <div className="mt-4">
                                <h5 className="text-sm font-medium text-gray-700 mb-2">Scores</h5>
                                <div className="grid grid-cols-3 gap-4">
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">Transparency</p>
                                    <p className="text-lg font-semibold text-blue-600">{selectedPolicy.evaluation.transparencyScore || 0}/10</p>
                                  </div>
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">Explainability</p>
                                    <p className="text-lg font-semibold text-green-600">{selectedPolicy.evaluation.explainabilityScore || 0}/10</p>
                                  </div>
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">Accountability</p>
                                    <p className="text-lg font-semibold text-purple-600">{selectedPolicy.evaluation.accountabilityScore || 0}/10</p>
                                  </div>
                                </div>
                                {/* Calculate TEA Button Logic */}
                                {((!selectedPolicy.evaluation.transparencyScore || selectedPolicy.evaluation.transparencyScore === 0) ||
                                  (!selectedPolicy.evaluation.explainabilityScore || selectedPolicy.evaluation.explainabilityScore === 0) ||
                                  (!selectedPolicy.evaluation.accountabilityScore || selectedPolicy.evaluation.accountabilityScore === 0)) &&
                                  selectedPolicy.policyFile && (
                                  <div className="mt-4 text-center">
                                    <button
                                      className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                                      onClick={async () => {
                                        setLoading(true);
                                        setError("");
                                        setSuccess("");
                                        try {
                                          // Check what type of file data we have
                                          console.log("Policy file data:", selectedPolicy.policyFile);
                                          let response;
                                          let fileToSend;

                                          if (selectedPolicy.policyFile instanceof File) {
                                            fileToSend = selectedPolicy.policyFile;
                                          } else if (selectedPolicy.policyFile.file_url || selectedPolicy.policyFile.cdn_url) {
                                            // Try both file_url and cdn_url
                                            const fileUrl = selectedPolicy.policyFile.file_url || selectedPolicy.policyFile.cdn_url;
                                            console.log("Fetching file from S3:", fileUrl);
                                            const fileResponse = await fetch(fileUrl);
                                            if (!fileResponse.ok) {
                                              setError("Could not download the policy file.");
                                              return;
                                            }
                                            const fileBlob = await fileResponse.blob();
                                            const fileName = selectedPolicy.policyFile.name || selectedPolicy.policyFile.filename || 'policy_document.pdf';
                                            fileToSend = new File([fileBlob], fileName, { type: fileBlob.type || selectedPolicy.policyFile.type || 'application/pdf' });
                                          } else {
                                            setError("Unsupported file format for TEA analysis.");
                                            return;
                                          }

                                          // Send to backend
                                          const formData = new FormData();
                                          formData.append('file', fileToSend);
                                          response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/ai-analysis/calculate-tea-scores`, {
                                            method: 'POST',
                                            body: formData,
                                          });
                                          const result = await response.json();
                                          console.log("TEA API response:", result);
                                          if (response.ok && result.scores) {
                                            selectedPolicy.evaluation.transparencyScore = result.scores.transparency_score;
                                            selectedPolicy.evaluation.explainabilityScore = result.scores.explainability_score;
                                            selectedPolicy.evaluation.accountabilityScore = result.scores.accountability_score;
                                            setSuccess("TEA scores calculated and updated successfully.");
                                            await fetchSubmissions();
                                          } else {
                                            const errorDetail = result.detail;
                                            const errorMessage = typeof errorDetail === 'string' ? errorDetail : 
                                              (errorDetail && errorDetail.msg ? errorDetail.msg : JSON.stringify(errorDetail || result));
                                            setError("Failed to calculate TEA scores: " + errorMessage);
                                          }
                                        } catch (err) {
                                          const errorMessage = err.message || (typeof err === 'string' ? err : JSON.stringify(err));
                                          setError("Error calculating TEA scores: " + errorMessage);
                                        } finally {
                                          setLoading(false);
                                        }
                                      }}
                                    >
                                      Calculate TEA Scores
                                    </button>
                                    <p className="text-xs text-gray-500 mt-2">Upload a policy document to enable AI-powered scoring.</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )}

                        {selectedPolicy.participation && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-3">Public Participation</h4>
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm text-gray-600">Has Consultation</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.participation.hasConsultation ? 'Yes' : 'No'}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Comments Public</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.participation.commentsPublic ? 'Yes' : 'No'}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Stakeholder Score</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.participation.stakeholderScore || 0}/10</p>
                                </div>
                              </div>
                              
                              {selectedPolicy.participation.consultationStartDate && (
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <p className="text-sm text-gray-600">Consultation Start</p>
                                    <p className="text-sm font-medium text-black">{formatDate(selectedPolicy.participation.consultationStartDate)}</p>
                                  </div>
                                  <div>
                                    <p className="text-sm text-gray-600">Consultation End</p>
                                    <p className="text-sm font-medium text-black">{formatDate(selectedPolicy.participation.consultationEndDate)}</p>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {selectedPolicy.alignment && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-3">Alignment & Principles</h4>
                            <div className="space-y-3">
                              {selectedPolicy.alignment.aiPrinciples && selectedPolicy.alignment.aiPrinciples.length > 0 && (
                                <div>
                                  <p className="text-sm font-medium text-gray-700 mb-2">AI Principles</p>
                                  <div className="flex flex-wrap gap-1">
                                    {selectedPolicy.alignment.aiPrinciples.map((principle, index) => (
                                      <span key={index} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">{principle}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm text-gray-600">Human Rights Alignment</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.alignment.humanRightsAlignment ? 'Yes' : 'No'}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">Environmental Considerations</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.alignment.environmentalConsiderations ? 'Yes' : 'No'}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-gray-600">International Cooperation</p>
                                  <p className="text-sm font-medium text-black">{selectedPolicy.alignment.internationalCooperation ? 'Yes' : 'No'}</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

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

                {/* File Upload Section */}
                <div className="mt-6 pt-4 border-t">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Upload Files for this Policy</h4>
                  <div className="flex items-center gap-3">
                    <input
                      type="file"
                      id="policyFileUpload"
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) {
                          uploadPolicyFile(selectedSubmission.policy_id || selectedSubmission._id, file);
                        }
                      }}
                      className="text-black text-sm file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    <p className="text-xs text-gray-500">PDF, DOC, DOCX, TXT, RTF (Max 50MB)</p>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Admin Notes</label>
                  <textarea
                    value={adminNotes}
                    onChange={(e) => setAdminNotes(e.target.value)}
                    rows={3}
                    placeholder="Add notes for this policy..."
                    className="text-black w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

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
                        onClick={() => rejectPolicy(selectedSubmission.policy_id || selectedSubmission._id, selectedPolicyArea, selectedPolicyIndex, adminNotes)}
                        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        Reject & Remove from Map
                      </button>
                      <button
                        onClick={() => approvePolicy(selectedSubmission.policy_id || selectedSubmission._id, selectedPolicyArea, selectedPolicyIndex, adminNotes)}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Approve & Show on Map
                      </button>
                      <button
                        onClick={() => deletePolicyCompletely(selectedSubmission.policy_id || selectedSubmission._id)}
                        className="px-4 py-2 bg-red-800 text-white rounded hover:bg-red-900"
                      >
                        Delete Permanently
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Files Modal */}
        {showFilesModal && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
            <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-white/20 my-8">
              <div className="p-8">
                               <div className="flex justify-between items-center pb-6 border-b border-slate-200">
                  <div>
                    <h3 className="text-2xl font-bold text-slate-900">Policy Files</h3>
                    <p className="text-slate-600 mt-1">All files associated with this policy</p>
                  </div>
                  <button
                    onClick={() => setShowFilesModal(false)}
                    className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="mt-6">
                  {selectedFiles.length === 0 ? (
                    <div className="text-center py-8">
                      <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-gray-500">No files found for this policy</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {selectedFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900">{file.name}</h4>
                              <div className="flex items-center space-x-4 text-sm text-gray-500">
                                <span>{file.type}</span>
                                <span>{(file.size / 1024).toFixed(1)} KB</span>
                                {file.policy_area && <span>Area: {file.policy_area}</span>}
                                {file.policy_name && <span>Policy: {file.policy_name}</span>}
                                {file.upload_date && <span>Uploaded: {new Date(file.upload_date).toLocaleDateString()}</span>}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleOpenFile(file)}
                              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-all"
                            >
                              Open
                            </button>
                            <button
                              onClick={() => deleteFileFromPolicy(file.file_id)}
                              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-all"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
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