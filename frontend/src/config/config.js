/**
 * Application Configuration
 * Centralized configuration management for the frontend
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
};

// Application Configuration
export const APP_CONFIG = {
  NAME: 'AI Policy Tracker',
  VERSION: '4.0.0',
  DESCRIPTION: 'Complete AI Policy Management System',
  ENVIRONMENT: process.env.NODE_ENV || 'development',
  GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
};

// Feature Flags
export const FEATURES = {
  GOOGLE_AUTH: !!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
  CHATBOT: true,
  ADMIN_PANEL: true,
  POLICY_SUBMISSION: true,
  WORLD_MAP: true,
};

// UI Configuration
export const UI_CONFIG = {
  THEME: {
    PRIMARY_COLOR: '#2563eb',
    SECONDARY_COLOR: '#64748b',
    SUCCESS_COLOR: '#10b981',
    ERROR_COLOR: '#ef4444',
    WARNING_COLOR: '#f59e0b',
  },
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 10,
    MAX_PAGE_SIZE: 100,
  },
  CHAT: {
    MAX_MESSAGE_LENGTH: 1000,
    MAX_CONVERSATION_HISTORY: 50,
  },
};

// Routes Configuration
export const ROUTES = {
  HOME: '/',
  AUTH: '/auth',
  ADMIN: '/admin',
  ADMIN_LOGIN: '/admin/login',
  POLICY_SUBMISSION: '/submit',
  CHATBOT: '/chat',
  WORLD_MAP: '/map',
};

export default {
  API_CONFIG,
  APP_CONFIG,
  FEATURES,
  UI_CONFIG,
  ROUTES,
};
