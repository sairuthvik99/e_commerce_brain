import API_CONFIG from '../config/api';
import { getRandomErrorMessage } from '../constants/errorMessages';

/**
 * API Service for making HTTP requests to the backend
 */
class ApiService {
  constructor() {
    this.baseUrl = API_CONFIG.FULL_URL;
  }

  /**
   * Make a fetch request with error handling
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise<Object>} Response data
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    const config = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // ============================================================
  // Health Endpoints
  // ============================================================

  async getHealth() {
    return this.request(API_CONFIG.ENDPOINTS.HEALTH);
  }

  async getLiveness() {
    return this.request(API_CONFIG.ENDPOINTS.HEALTH_LIVE);
  }

  async getReadiness() {
    return this.request(API_CONFIG.ENDPOINTS.HEALTH_READY);
  }

  // ============================================================
  // Analysis Endpoints
  // ============================================================

  async submitAnalysis(question, context = null) {
    return this.request(API_CONFIG.ENDPOINTS.ANALYZE, {
      method: 'POST',
      body: JSON.stringify({ question, context })
    });
  }

  async submitAnalysisSync(question, context = null) {
    return this.request(API_CONFIG.ENDPOINTS.ANALYZE_SYNC, {
      method: 'POST',
      body: JSON.stringify({ question, context })
    });
  }

  // ============================================================
  // Job Endpoints
  // ============================================================

  async getJobs(status = null, limit = 10, page = 1) {
    let endpoint = `${API_CONFIG.ENDPOINTS.JOBS}?limit=${limit}&page=${page}`;
    if (status) {
      endpoint += `&status=${status}`;
    }
    return this.request(endpoint);
  }

  async getJobStats() {
    return this.request(API_CONFIG.ENDPOINTS.JOB_STATS);
  }

  async getDashboardStats() {
    // Use the new e-commerce stats endpoint which fetches from PostgreSQL
    return this.request(API_CONFIG.ENDPOINTS.ECOMMERCE_STATS);
  }

  async getEcommerceStats(days = 7) {
    return this.request(`${API_CONFIG.ENDPOINTS.ECOMMERCE_STATS}?days=${days}`);
  }

  async getSalesData(days = 7) {
    return this.request(`${API_CONFIG.ENDPOINTS.ECOMMERCE_SALES}?days=${days}`);
  }

  async getInventoryData(days = 7) {
    return this.request(`${API_CONFIG.ENDPOINTS.ECOMMERCE_INVENTORY}?days=${days}`);
  }

  async getMarketingData(days = 7) {
    return this.request(`${API_CONFIG.ENDPOINTS.ECOMMERCE_MARKETING}?days=${days}`);
  }

  async getSupportData(days = 7) {
    return this.request(`${API_CONFIG.ENDPOINTS.ECOMMERCE_SUPPORT}?days=${days}`);
  }

  async getJob(jobId) {
    return this.request(API_CONFIG.ENDPOINTS.JOB_DETAIL(jobId));
  }

  async getJobResult(jobId) {
    return this.request(API_CONFIG.ENDPOINTS.JOB_RESULT(jobId));
  }

  async getJobProgress(jobId) {
    return this.request(API_CONFIG.ENDPOINTS.JOB_PROGRESS(jobId));
  }

  async cancelJob(jobId) {
    return this.request(API_CONFIG.ENDPOINTS.JOB_CANCEL(jobId), {
      method: 'DELETE'
    });
  }

  // ============================================================
  // HITL Endpoints
  // ============================================================

  async getJobActions(jobId) {
    return this.request(API_CONFIG.ENDPOINTS.JOB_ACTIONS(jobId));
  }

  async approveProposal(proposalId, approvedIds, rejectedIds, approver = null, notes = null) {
    return this.request(API_CONFIG.ENDPOINTS.PROPOSALS_APPROVE(proposalId), {
      method: 'POST',
      body: JSON.stringify({
        approved_action_ids: approvedIds,
        rejected_action_ids: rejectedIds,
        approver,
        notes
      })
    });
  }

  // ============================================================
  // Memory Endpoints
  // ============================================================

  async searchMemory(query, limit = 5, minConfidence = 0) {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_SEARCH, {
      method: 'POST',
      body: JSON.stringify({ query, limit, min_confidence: minConfidence })
    });
  }

  async getMemoryInsights(jobId) {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_INSIGHTS(jobId));
  }

  // ============================================================
  // Settings Endpoints
  // ============================================================

  /**
   * Change the LLM model for all agents
   * @param {string} modelId - The model ID to set
   * @returns {Promise<Object>} Response with updated model info
   */
  async changeAgentModel(modelId) {
    return this.request(API_CONFIG.ENDPOINTS.CHANGE_MODEL, {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId })
    });
  }

  /**
   * Get the current LLM model configuration
   * @returns {Promise<Object>} Current model info
   */
  async getCurrentModel() {
    return this.request(API_CONFIG.ENDPOINTS.GET_MODEL);
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
