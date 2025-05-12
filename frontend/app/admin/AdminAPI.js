// API base URL - centralized for easy changes
const API_BASE_URL = "http://localhost:8000"

// Utility function for making API requests with consistent options
const makeAPIRequest = async (endpoint, method = 'GET', body = null) => {
  const options = {
    method,
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    signal: AbortSignal.timeout(10000) // 10 second timeout
  }
  
  if (body) {
    options.body = JSON.stringify(body)
  }
  
  const url = `${API_BASE_URL}${endpoint}`
  console.log(`Making ${method} request to: ${url}`)
  
  const response = await fetch(url, options)
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || response.statusText || 'Unknown error')
  }
  
  return response
}

export const adminAPI = {
  API_BASE_URL,
  
  // Fetch submissions based on view
  fetchSubmissions: async (page = 0, view = 'unread', perPage = 5) => {
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
    
    const queryParams = `?page=${page}&per_page=${perPage}`
    const response = await makeAPIRequest(`${endpoint}${queryParams}`)
    return await response.json()
  },
  
  // Approve a policy
  approvePolicy: async (country, policyIndex, policyText) => {
    const policyData = {
      country,
      policyIndex,
      text: policyText
    }
    
    await makeAPIRequest('/api/approve-policy', 'POST', policyData)
    return true
  },
  
  // Reject/decline a policy
  rejectPolicy: async (country, policyIndex, policyText) => {
    const policyData = {
      country,
      policyIndex,
      text: policyText
    }
    
    await makeAPIRequest('/api/decline-policy', 'POST', policyData)
    return true
  },
  
  // Update an existing policy
  updatePolicy: async (country, policyIndex, policyText, status) => {
    const policyData = {
      country,
      policyIndex,
      text: policyText,
      status
    }
    
    await makeAPIRequest('/api/update-policy', 'POST', policyData)
    return true
  },
  
  // Remove a submission entirely
  removeSubmission: async (country) => {
    await makeAPIRequest('/api/remove-submission', 'POST', { country })
    return true
  },
  
  // Get a policy file
  getPolicyFileUrl: (filename) => {
    return `${API_BASE_URL}/api/policy-file/${filename}`
  }
}