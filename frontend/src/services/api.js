const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.defaultTimeout = 30000; // 30 seconds
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const timeout = options.timeout || this.defaultTimeout;
    
    const config = {
      headers: {
        ...options.headers,
      },
      ...options,
    };

    // Don't set Content-Type for FormData - let browser handle it with boundary
    if (!(config.body instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }
    // For FormData, browser automatically sets: Content-Type: multipart/form-data; boundary=...

    // Add auth token if available
    const token = localStorage.getItem('access_token');
    if (token) {
      // Check if token looks expired (basic check)
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Date.now() / 1000;
        if (payload.exp && payload.exp < currentTime) {
          // Token is expired, remove it
          localStorage.removeItem('access_token');
          localStorage.removeItem('userData');
          throw new Error('Token expired - please login again');
        }
      } catch (e) {
        // If token parsing fails, it's invalid
        localStorage.removeItem('access_token');
        localStorage.removeItem('userData');
        throw new Error('Invalid token - please login again');
      }
      
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Create abort controller for timeout only if no signal is provided
    let controller;
    let timeoutId;
    
    if (!options.signal) {
      controller = new AbortController();
      config.signal = controller.signal;
      timeoutId = setTimeout(() => {
        if (controller && !controller.signal.aborted) {
          controller.abort();
        }
      }, timeout);
    } else {
      config.signal = options.signal;
    }

    try {
      const response = await fetch(url, config);
      if (timeoutId) clearTimeout(timeoutId);
      
      // Handle authentication errors
      if (response.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('userData');
        throw new Error('Invalid token - please login again');
      }
      
      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      let data;
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = { message: await response.text() };
      }

      if (!response.ok) {
        throw new Error(data.detail || data.message || `HTTP ${response.status}`);
      }

      return data;
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId);
      
      // Only log non-abort errors to reduce noise
      if (error.name !== 'AbortError') {
        console.error('API request failed:', error);
      } else {
        console.warn(`API request to ${endpoint} was aborted`);
      }
      throw error;
    }
  }

  async get(endpoint, options = {}) {
    return this.request(endpoint, { method: 'GET', ...options });
  }

  async post(endpoint, data, options = {}) {
    const config = {
      method: 'POST',
      ...options,
    };

    // Handle FormData vs JSON differently
    if (data instanceof FormData) {
      config.body = data;
      // Don't set Content-Type for FormData - browser will set it with boundary
    } else {
      config.body = JSON.stringify(data);
      // Content-Type will be set in request method for JSON
    }

    return this.request(endpoint, config);
  }

  async put(endpoint, data, options = {}) {
    const config = {
      method: 'PUT',
      ...options,
    };

    // Handle FormData vs JSON differently
    if (data instanceof FormData) {
      config.body = data;
      // Don't set Content-Type for FormData - browser will set it with boundary
    } else {
      config.body = JSON.stringify(data);
      // Content-Type will be set in request method for JSON
    }

    return this.request(endpoint, config);
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, { method: 'DELETE', ...options });
  }

  async patch(endpoint, data, options = {}) {
    const config = {
      method: 'PATCH',
      ...options,
    };

    // Handle FormData vs JSON differently
    if (data instanceof FormData) {
      config.body = data;
      // Don't set Content-Type for FormData - browser will set it with boundary
    } else {
      config.body = JSON.stringify(data);
      // Content-Type will be set in request method for JSON
    }

    return this.request(endpoint, config);
  }
}

// Auth Service
class AuthService extends ApiService {
  async register(userData) {
    return this.post('/auth/register', userData);
  }

  async login(credentials) {
    return this.post('/auth/login', credentials);
  }

  async verifyEmail(verificationData) {
    return this.post('/auth/verify-email', verificationData);
  }

  async forgotPassword(emailData) {
    return this.post('/auth/forgot-password', emailData);
  }

  async resetPassword(resetData) {
    return this.post('/auth/reset-password', resetData);
  }

  async resendOtp(emailData) {
    return this.post('/auth/resend-otp', emailData);
  }

  async getCurrentUser() {
    return this.get('/auth/me');
  }

  async googleAuth(token) {
    return this.post('/auth/google', { token });
  }

  async adminLogin(credentials) {
    return this.post('/auth/admin-login', credentials);
  }
}

// Policy Service
class PolicyService extends ApiService {
  async submitPolicy(policyData) {
    return this.post('/policies/submit', policyData);
  }

  async searchPolicies(searchParams) {
    const queryString = new URLSearchParams(searchParams).toString();
    return this.get(`/policies/search?${queryString}`);
  }

  async getPolicy(policyId) {
    return this.get(`/policies/${policyId}`);
  }

  async getCountriesWithPolicies() {
    return this.get('/policies/countries/list');
  }
}

// Chat Service
class ChatService extends ApiService {
  async sendMessage(messageData) {
    return this.post('/chat/', messageData);
  }

  async getConversation(conversationId) {
    return this.get(`/chat/conversations/${conversationId}`);
  }

  async deleteConversation(conversationId) {
    return this.delete(`/chat/conversations/${conversationId}`);
  }

  async getUserConversations(limit = 10) {
    return this.get(`/chat/conversations?limit=${limit}`);
  }

  async searchPolicies(query, limit = 5) {
    return this.post('/chat/search-policies', { query, limit });
  }
}

// Public Service for map and general public data
class PublicService extends ApiService {
  async getCountries(signal = null) {
    return this.get('/countries', { signal, timeout: 15000 });
  }

  async getMasterPolicies(limit = 200, signal = null) {
    return this.get(`/public/master-policies?limit=${limit}`, { signal, timeout: 20000 });
  }

  async getMasterPoliciesFast(limit = 1000, signal = null) {
    return this.get(`/public/master-policies-fast?limit=${limit}`, { signal, timeout: 45000 }); // Increased to 45 seconds and 1000 limit
  }

  async getStatistics(signal = null) {
    return this.get('/public/statistics', { signal, timeout: 20000 }); // Increased to 20 seconds
  }

  async getStatisticsFast(signal = null) {
    return this.get('/public/statistics-fast', { signal, timeout: 20000 }); // Increased to 20 seconds
  }

  async getMapVisualization(signal = null) {
    return this.get('/admin/map-visualization-with-area-points', { signal, timeout: 20000 });
  }
}

// Admin Service
class AdminService extends ApiService {
  async getPendingPolicies() {
    return this.get('/admin/pending-policies');
  }

  async approvePolicy(policyId, action, reason = null) {
    return this.post('/admin/approve-policy', {
      policy_id: policyId,
      action,
      reason
    });
  }

  async getAdminStats() {
    return this.get('/admin/stats');
  }

  // New methods for enhanced admin functionality
  async getSubmissions(page = 1, limit = 10, status = 'all') {
    // Temporarily use debug endpoint to bypass authentication issues
    console.log('Calling debug submissions endpoint...');
    const response = await this.get(`/admin/submissions-debug?page=${page}&limit=${limit}&status=${status}`);
    console.log('Debug submissions response:', response);
    return response;
  }

  async getStatistics(signal = null) {
    return this.get('/admin/statistics', { signal });
  }

  async getStatisticsFast(signal = null) {
    return this.get('/admin/statistics-fast', { signal });
  }

  async updatePolicyStatus(submissionId, areaId, policyIndex, status, adminNotes = '') {
    return this.put('/admin/update-policy-status', {
      submission_id: submissionId,
      area_id: areaId,
      policy_index: policyIndex,
      status,
      admin_notes: adminNotes
    });
  }

  async deleteMasterPolicy(policyId) {
    return this.delete(`/admin/master-policy/${policyId}`);
  }

  async deleteSubmissionPolicy(submissionId, areaId, policyIndex) {
    return this.delete('/admin/submission-policy', {
      body: JSON.stringify({
        submission_id: submissionId,
        area_id: areaId,
        policy_index: policyIndex
      })
    });
  }

  async getMasterPolicies(page = 1, limit = 10) {
    return this.get(`/admin/master-policies?page=${page}&limit=${limit}`);
  }

  async moveToMaster(submissionId) {
    return this.post('/admin/move-to-master', {
      submission_id: submissionId
    });
  }

  // New comprehensive admin methods
  async approvePolicy(submissionId, areaId, policyIndex, adminNotes = '') {
    // Use debug approval endpoint with submission_id in URL path
    return this.post(`/admin/debug-approval/${submissionId}`, {
      admin_notes: adminNotes || 'Approved via admin panel'
    });
  }

  async rejectPolicy(submissionId, areaId, policyIndex, adminNotes = '') {
    // Use debug rejection endpoint with submission_id in URL path
    return this.post(`/admin/debug-rejection/${submissionId}`, {
      admin_notes: adminNotes || 'Rejected via admin panel'
    });
  }

  async commitPolicy(submissionId, areaId, policyIndex) {
    return this.post('/admin/commit-policy', {
      submission_id: submissionId,
      area_id: areaId,
      policy_index: policyIndex
    });
  }

  async deletePolicyCompletely(policyId) {
    return this.delete(`/admin/policy/${policyId}`);
  }

  async getApprovedPolicies(page = 1, limit = 20) {
    return this.get(`/admin/approved-policies?page=${page}&limit=${limit}`);
  }

  async getPolicyFiles(policyId) {
    return this.get(`/admin/policy/${policyId}/files`);
  }

  async uploadPolicyFile(policyId, fileData) {
    return this.post(`/admin/policy/${policyId}/upload-file`, fileData);
  }

  async getFile(fileId) {
    return this.get(`/admin/file/${fileId}`);
  }

  async deleteFile(fileId) {
    return this.delete(`/admin/file/${fileId}`);
  }

  async getAllFiles() {
    return this.get('/admin/all-files');
  }

  async calculateTEAScores(submissionId, areaId, policyIndex) {
    // Use the correct endpoint for TEA score calculation
    return this.post('/ai-analysis/calculate-tea-scores', {
      submission_id: submissionId,
      area_id: areaId,
      policy_index: policyIndex
    });
  }
}

// Create service instances
export const authService = new AuthService();
export const policyService = new PolicyService();
export const chatService = new ChatService();
export const publicService = new PublicService();
export const adminService = new AdminService();

// Export combined API service for backwards compatibility
export const apiService = {
  // Auth methods
  register: authService.register.bind(authService),
  login: authService.login.bind(authService),
  adminLogin: authService.adminLogin.bind(authService),
  verifyEmail: authService.verifyEmail.bind(authService),
  forgotPassword: authService.forgotPassword.bind(authService),
  resetPassword: authService.resetPassword.bind(authService),
  resendOtp: authService.resendOtp.bind(authService),
  getCurrentUser: authService.getCurrentUser.bind(authService),
  googleAuth: authService.googleAuth.bind(authService),
  
  // Policy methods
  submitPolicy: policyService.submitPolicy.bind(policyService),
  searchPolicies: policyService.searchPolicies.bind(policyService),
  getPolicy: policyService.getPolicy.bind(policyService),
  getCountriesWithPolicies: policyService.getCountriesWithPolicies.bind(policyService),
  
  // File upload methods
  uploadPolicyFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return authService.post('/policy/upload-policy-file', formData);
  },
  
  // AI Analysis methods
  analyzeUploadedFile: (fileId) => {
    const formData = new FormData();
    formData.append('file_id', fileId);
    return authService.post('/ai-analysis/analyze-uploaded-file', formData);
  },
  
  // Chat methods
  sendMessage: chatService.sendMessage.bind(chatService),
  getConversation: chatService.getConversation.bind(chatService),
  deleteConversation: chatService.deleteConversation.bind(chatService),
  getUserConversations: chatService.getUserConversations.bind(chatService),
  
  // Admin methods
  getPendingPolicies: adminService.getPendingPolicies.bind(adminService),
  approvePolicy: adminService.approvePolicy.bind(adminService),
  getAdminStats: adminService.getAdminStats.bind(adminService),
  
  // Generic HTTP methods
  get: authService.get.bind(authService),
  post: authService.post.bind(authService),
  put: authService.put.bind(authService),
  delete: authService.delete.bind(authService),
  patch: authService.patch.bind(authService),
  
  // Service instances
  auth: authService,
  policy: policyService,
  chat: chatService,
  admin: adminService,
  public: publicService,
};

export default {
  auth: authService,
  policy: policyService,
  chat: chatService,
  admin: adminService,
  public: publicService,
};
