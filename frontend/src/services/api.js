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

  // ============================================================
  // Analysis Endpoints
  // ============================================================

  async submitAnalysis(question, context = null) {
    return this.request(API_CONFIG.ENDPOINTS.ANALYZE, {
      method: 'POST',
      body: JSON.stringify({ question, context })
    });
  }

  // ============================================================
  // Job Endpoints
  // ============================================================

  async getDashboardStats() {
    // Use the new e-commerce stats endpoint which fetches from PostgreSQL
    return this.request(API_CONFIG.ENDPOINTS.ECOMMERCE_STATS);
  }

  async getJob(jobId) {
    return this.request(API_CONFIG.ENDPOINTS.JOB_DETAIL(jobId));
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

  async approveProposal(jobId, approvedIds, rejectedIds, approver = null, notes = null) {
    return this.request(API_CONFIG.ENDPOINTS.PROPOSALS_APPROVE(jobId), {
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
  // Stock Update HITL Endpoints
  // ============================================================

  /**
   * Get all pending stock update proposals
   * @param {string} status - Optional status filter (pending, approved, rejected, executed)
   * @returns {Promise<Object>} List of stock update actions
   */
  async getStockUpdates(status = null) {
    let endpoint = API_CONFIG.ENDPOINTS.STOCK_UPDATES;
    if (status) {
      endpoint += `?status=${status}`;
    }
    return this.request(endpoint);
  }

  /**
   * Approve or reject a stock update proposal
   * @param {string} proposalId - The proposal ID
   * @param {boolean} approved - Whether to approve (true) or reject (false)
   * @param {string} approver - Who is approving/rejecting
   * @param {string} rejectionReason - Reason for rejection (if rejected)
   * @returns {Promise<Object>} Approval result
   */
  async approveStockUpdate(proposalId, approved, approver = null, rejectionReason = null) {
    return this.request(API_CONFIG.ENDPOINTS.STOCK_UPDATE_APPROVE(proposalId), {
      method: 'POST',
      body: JSON.stringify({
        approved,
        approver,
        rejection_reason: rejectionReason
      })
    });
  }

  // ============================================================
  // Memory Endpoints
  // ============================================================

  async getMemoryStats() {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_STATS);
  }

  /**
   * Get short-term memory (conversation history)
   * @param {number} limit - Max entries to retrieve (1-10)
   * @returns {Promise<Object>} Short-term memory entries
   */
  async getShortTermMemory(limit = 10) {
    return this.request(`${API_CONFIG.ENDPOINTS.MEMORY_SHORT_TERM}?limit=${limit}`);
  }

  /**
   * Clear short-term memory
   * @returns {Promise<Object>} Clear result
   */
  async clearShortTermMemory() {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_SHORT_TERM, {
      method: 'DELETE'
    });
  }

  /**
   * Get long-term memory (preferences, facts, knowledge)
   * @returns {Promise<Object>} Long-term memory data
   */
  async getLongTermMemory() {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_LONG_TERM);
  }

  /**
   * Clear long-term memory
   * @returns {Promise<Object>} Clear result
   */
  async clearLongTermMemory() {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_LONG_TERM, {
      method: 'DELETE'
    });
  }

  /**
   * Save a preference to long-term memory
   * @param {string} key - Preference key
   * @param {any} value - Preference value
   * @returns {Promise<Object>} Save result
   */
  async savePreference(key, value) {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_SAVE_PREFERENCE, {
      method: 'POST',
      body: JSON.stringify({ key, value })
    });
  }

  /**
   * Save a fact to long-term memory
   * @param {string} fact - The fact to store
   * @param {string} category - Category of the fact
   * @returns {Promise<Object>} Save result
   */
  async saveFact(fact, category = 'general') {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_SAVE_FACT, {
      method: 'POST',
      body: JSON.stringify({ fact, category })
    });
  }

  /**
   * Save knowledge to long-term memory
   * @param {string} topic - Topic/title
   * @param {string} content - Knowledge content
   * @param {string} source - Source of knowledge
   * @returns {Promise<Object>} Save result
   */
  async saveKnowledge(topic, content, source = 'user') {
    return this.request(API_CONFIG.ENDPOINTS.MEMORY_SAVE_KNOWLEDGE, {
      method: 'POST',
      body: JSON.stringify({ topic, content, source })
    });
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
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
