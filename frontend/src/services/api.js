const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add auth token if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);
      
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
      console.error('API request failed:', error);
      throw error;
    }
  }

  async get(endpoint, options = {}) {
    return this.request(endpoint, { method: 'GET', ...options });
  }

  async post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options,
    });
  }

  async put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options,
    });
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, { method: 'DELETE', ...options });
  }

  async patch(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
      ...options,
    });
  }

  async put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options,
    });
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, { method: 'DELETE', ...options });
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
    return this.post('/chat/chat', messageData);
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
}

// Create service instances
export const authService = new AuthService();
export const policyService = new PolicyService();
export const chatService = new ChatService();
export const adminService = new AdminService();

// Export combined API service for backwards compatibility
export const apiService = {
  ...authService,
  auth: authService,
  policy: policyService,
  chat: chatService,
  admin: adminService,
};

export default {
  auth: authService,
  policy: policyService,
  chat: chatService,
  admin: adminService,
};
