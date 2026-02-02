import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AGENT_MODELS, DEFAULT_MODEL_ID, getModelById } from '../constants/agentModels';
import apiService from '../services/api';

// Create context
const ModelContext = createContext(null);

/**
 * Model Provider Component
 * Manages the current LLM model selection for all agents
 */
export function ModelProvider({ children }) {
  const [currentModelId, setCurrentModelId] = useState(() => {
    const saved = localStorage.getItem('stebs-agent-model');
    return saved && AGENT_MODELS.some(m => m.id === saved) ? saved : DEFAULT_MODEL_ID;
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Get current model object
  const currentModel = getModelById(currentModelId) || getModelById(DEFAULT_MODEL_ID);

  // Save preference to localStorage
  useEffect(() => {
    localStorage.setItem('stebs-agent-model', currentModelId);
  }, [currentModelId]);

  /**
   * Change the model for all agents
   * @param {string} newModelId - The new model ID to set
   * @returns {Promise<boolean>} - Whether the change was successful
   */
  const changeModel = useCallback(async (newModelId) => {
    if (newModelId === currentModelId) return true;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Call backend API to update model
      await apiService.changeAgentModel(newModelId);
      setCurrentModelId(newModelId);
      setIsLoading(false);
      return true;
    } catch (err) {
      console.error('Failed to change model:', err);
      setError(err.message || 'Failed to change model');
      setIsLoading(false);
      return false;
    }
  }, [currentModelId]);

  const value = {
    currentModelId,
    currentModel,
    isLoading,
    error,
    changeModel,
    models: AGENT_MODELS,
  };

  return (
    <ModelContext.Provider value={value}>
      {children}
    </ModelContext.Provider>
  );
}

/**
 * Hook to use model context
 */
export function useModel() {
  const context = useContext(ModelContext);
  if (!context) {
    throw new Error('useModel must be used within a ModelProvider');
  }
  return context;
}

export default ModelContext;
