/**
 * API Configuration
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  API_PREFIX: API_PREFIX,
  FULL_URL: `${API_BASE_URL}${API_PREFIX}`,
  
  // WebSocket URL
  WS_URL: API_BASE_URL.replace('http', 'ws'),
  
  // Endpoints
  ENDPOINTS: {
    // Health
    HEALTH: '/health',
    HEALTH_LIVE: '/health/live',
    HEALTH_READY: '/health/ready',
    
    // Analysis
    ANALYZE: '/analyze',
    ANALYZE_SYNC: '/analyze/sync',
    
    // Jobs
    JOBS: '/jobs',
    JOB_STATS: '/jobs/stats',
    DASHBOARD_STATS: '/dashboard/stats',
    JOB_DETAIL: (jobId) => `/jobs/${jobId}`,
    JOB_RESULT: (jobId) => `/jobs/${jobId}/result`,
    JOB_PROGRESS: (jobId) => `/jobs/${jobId}/progress`,
    JOB_CANCEL: (jobId) => `/jobs/${jobId}`,
    JOB_ACTIONS: (jobId) => `/jobs/${jobId}/actions`,
    
    // E-Commerce Data (PostgreSQL)
    ECOMMERCE_STATS: '/ecommerce/stats',
    ECOMMERCE_SALES: '/ecommerce/sales',
    ECOMMERCE_INVENTORY: '/ecommerce/inventory',
    ECOMMERCE_MARKETING: '/ecommerce/marketing',
    ECOMMERCE_SUPPORT: '/ecommerce/support',
    
    // Memory
    MEMORY_SEARCH: '/memory/search',
    MEMORY_INSIGHTS: (jobId) => `/memory/insights/${jobId}`,
    MEMORY_STATS: '/memory/stats',
    MEMORY_SHORT_TERM: '/memory/short-term',
    MEMORY_LONG_TERM: '/memory/long-term',
    MEMORY_SAVE_PREFERENCE: '/memory/long-term/preference',
    MEMORY_SAVE_FACT: '/memory/long-term/fact',
    MEMORY_SAVE_KNOWLEDGE: '/memory/long-term/knowledge',
    
    // HITL
    PROPOSALS_APPROVE: (jobId) => `/jobs/${jobId}/actions/approve`,
    
    // Stock Updates HITL
    STOCK_UPDATES: '/stock-updates',
    STOCK_UPDATE_DETAIL: (proposalId) => `/stock-updates/${proposalId}`,
    STOCK_UPDATE_APPROVE: (proposalId) => `/stock-updates/${proposalId}/approve`,
    STOCK_UPDATE_EXECUTE: (proposalId) => `/stock-updates/${proposalId}/execute`,
    
    // WebSocket
    WS_JOB: (jobId) => `/ws/jobs/${jobId}`,
    WS_ALL: '/ws/jobs',
    
    // Settings
    CHANGE_MODEL: '/settings/model',
    GET_MODEL: '/settings/model'
  },
  
  // Polling intervals
  POLLING: {
    JOB_STATUS: 2000,  // 2 seconds
    DASHBOARD: 30000,  // 30 seconds
    HEALTH: 60000      // 1 minute
  }
};

export default API_CONFIG;
