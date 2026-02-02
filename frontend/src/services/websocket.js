import API_CONFIG from '../config/api';

/**
 * WebSocket Service for real-time job updates
 */
class WebSocketService {
  constructor() {
    this.connections = new Map();
    this.listeners = new Map();
    this.reconnectAttempts = new Map();
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000;
  }

  /**
   * Connect to a job-specific WebSocket
   * @param {string} jobId - Job ID to subscribe to
   * @param {Function} onMessage - Callback for messages
   * @param {Function} onError - Callback for errors
   * @param {Function} onClose - Callback for connection close
   * @returns {WebSocket} WebSocket instance
   */
  connectToJob(jobId, onMessage, onError = null, onClose = null) {
    const url = `${API_CONFIG.WS_URL}${API_CONFIG.API_PREFIX}${API_CONFIG.ENDPOINTS.WS_JOB(jobId)}`;
    return this._connect(jobId, url, onMessage, onError, onClose);
  }

  /**
   * Connect to the general jobs WebSocket
   * @param {Function} onMessage - Callback for messages
   * @param {Function} onError - Callback for errors
   * @param {Function} onClose - Callback for connection close
   * @returns {WebSocket} WebSocket instance
   */
  connectToAllJobs(onMessage, onError = null, onClose = null) {
    const url = `${API_CONFIG.WS_URL}${API_CONFIG.API_PREFIX}${API_CONFIG.ENDPOINTS.WS_ALL}`;
    return this._connect('all', url, onMessage, onError, onClose);
  }

  /**
   * Internal connect method
   */
  _connect(key, url, onMessage, onError, onClose) {
    // Close existing connection if any
    this.disconnect(key);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log(`WebSocket connected: ${key}`);
        this.reconnectAttempts.set(key, 0);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
          
          // Notify all listeners
          const listeners = this.listeners.get(key) || [];
          listeners.forEach(listener => listener(data));
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      ws.onerror = (error) => {
        console.error(`WebSocket error [${key}]:`, error);
        if (onError) onError(error);
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${key}`, event.code, event.reason);
        this.connections.delete(key);
        
        if (onClose) onClose(event);

        // Attempt reconnect if not intentional close
        if (event.code !== 1000) {
          this._attemptReconnect(key, url, onMessage, onError, onClose);
        }
      };

      this.connections.set(key, ws);
      return ws;
    } catch (error) {
      console.error(`WebSocket connection failed [${key}]:`, error);
      if (onError) onError(error);
      return null;
    }
  }

  /**
   * Attempt to reconnect
   */
  _attemptReconnect(key, url, onMessage, onError, onClose) {
    const attempts = this.reconnectAttempts.get(key) || 0;
    
    if (attempts < this.maxReconnectAttempts) {
      this.reconnectAttempts.set(key, attempts + 1);
      console.log(`Reconnecting WebSocket [${key}] attempt ${attempts + 1}...`);
      
      setTimeout(() => {
        this._connect(key, url, onMessage, onError, onClose);
      }, this.reconnectDelay * Math.pow(2, attempts));
    } else {
      console.error(`WebSocket reconnection failed after ${this.maxReconnectAttempts} attempts`);
    }
  }

  /**
   * Disconnect a specific WebSocket
   * @param {string} key - Connection key
   */
  disconnect(key) {
    const ws = this.connections.get(key);
    if (ws) {
      ws.close(1000, 'Client disconnect');
      this.connections.delete(key);
      this.listeners.delete(key);
    }
  }

  /**
   * Disconnect all WebSockets
   */
  disconnectAll() {
    this.connections.forEach((ws, key) => {
      ws.close(1000, 'Client disconnect all');
    });
    this.connections.clear();
    this.listeners.clear();
  }

  /**
   * Add a listener for a connection
   * @param {string} key - Connection key
   * @param {Function} callback - Listener callback
   */
  addListener(key, callback) {
    const listeners = this.listeners.get(key) || [];
    listeners.push(callback);
    this.listeners.set(key, listeners);
  }

  /**
   * Remove a listener
   * @param {string} key - Connection key
   * @param {Function} callback - Listener callback to remove
   */
  removeListener(key, callback) {
    const listeners = this.listeners.get(key) || [];
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
      this.listeners.set(key, listeners);
    }
  }

  /**
   * Check if connected
   * @param {string} key - Connection key
   * @returns {boolean} Whether connected
   */
  isConnected(key) {
    const ws = this.connections.get(key);
    return ws && ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const wsService = new WebSocketService();
export default wsService;
