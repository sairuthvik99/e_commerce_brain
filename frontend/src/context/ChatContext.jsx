import { createContext, useContext, useState, useCallback, useRef } from 'react';
import { apiService } from '../services/api';
import { wsService } from '../services/websocket';
import { getRandomErrorMessage } from '../constants/errorMessages';

// Message types
export const MESSAGE_TYPES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
  ERROR: 'error'
};

// Message status
export const MESSAGE_STATUS = {
  SENDING: 'sending',
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
};

// Create context
const ChatContext = createContext(null);

/**
 * Generate unique message ID
 */
const generateMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

/**
 * Chat Provider Component
 * Manages chat state and interactions
 */
export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [jobProgress, setJobProgress] = useState(null);
  
  // Polling interval ref
  const pollingRef = useRef(null);

  /**
   * Add a message to the chat
   */
  const addMessage = useCallback((type, content, metadata = {}) => {
    const message = {
      id: generateMessageId(),
      type,
      content,
      timestamp: new Date().toISOString(),
      status: metadata.status || MESSAGE_STATUS.COMPLETED,
      ...metadata
    };
    
    setMessages(prev => [...prev, message]);
    return message;
  }, []);

  /**
   * Update an existing message
   */
  const updateMessage = useCallback((messageId, updates) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId ? { ...msg, ...updates } : msg
      )
    );
  }, []);

  /**
   * Clear all messages and reset session
   */
  const clearSession = useCallback(() => {
    // Stop any ongoing polling
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    
    // Disconnect WebSocket if connected
    if (currentJobId) {
      wsService.disconnect(currentJobId);
    }
    
    // Reset state
    setMessages([]);
    setIsLoading(false);
    setCurrentJobId(null);
    setJobStatus(null);
    setJobProgress(null);
  }, [currentJobId]);

  /**
   * Poll for job status
   */
  const pollJobStatus = useCallback(async (jobId, messageId) => {
    try {
      const job = await apiService.getJob(jobId);
      
      setJobStatus(job.status);
      setJobProgress(job.progress);

      if (job.status === 'completed') {
        // Stop polling
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
        
        setIsLoading(false);
        
        // Format and display result
        const resultContent = formatJobResult(job.result);
        updateMessage(messageId, {
          content: resultContent,
          status: MESSAGE_STATUS.COMPLETED,
          result: job.result
        });
        
      } else if (job.status === 'failed') {
        // Stop polling
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
        
        setIsLoading(false);
        
        updateMessage(messageId, {
          content: getRandomErrorMessage(),
          status: MESSAGE_STATUS.FAILED,
          error: job.error
        });
        
      } else if (job.status === 'cancelled') {
        // Stop polling
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
        
        setIsLoading(false);
        
        updateMessage(messageId, {
          content: 'Analysis was cancelled.',
          status: MESSAGE_STATUS.CANCELLED
        });
      }
      // Continue polling for pending/running status
      
    } catch (error) {
      console.error('Error polling job status:', error);
    }
  }, [updateMessage]);

  /**
   * Format job result for display
   */
  const formatJobResult = (result) => {
    if (!result) return 'No results available.';
    
    let content = '';
    
    // Root cause summary - commented out per user request
    // if (result.root_cause) {
    //   const rc = result.root_cause;
    //   content += `## Analysis Summary\n\n`;
      
    //   if (rc.primary_cause) {
    //     content += `**Primary Cause:** ${rc.primary_cause}\n\n`;
    //   }
      
    //   // Handle root_cause field (might be JSON string or plain text)
    //   if (rc.root_cause) {
    //     let rootCauseText = rc.root_cause;
        
    //     // Try to parse if it's a JSON string
    //     if (typeof rootCauseText === 'string' && rootCauseText.includes('```json')) {
    //       try {
    //         const jsonMatch = rootCauseText.match(/```json\n?([\s\S]*?)\n?```/);
    //         if (jsonMatch) {
    //           const parsed = JSON.parse(jsonMatch[1]);
    //           rootCauseText = parsed.root_cause || rootCauseText;
    //         }
    //       } catch (e) {
    //         // Keep original text if parsing fails
    //       }
    //     }
        
    //     content += `${rootCauseText}\n\n`;
    //   }
    // }
    
    // Agent findings
    if (result.agent_findings && Object.keys(result.agent_findings).length > 0) {
      // content += `## Detailed Findings\n\n`;  // Commented out per user request
      
      for (const [agent, agentData] of Object.entries(result.agent_findings)) {
        if (agentData) {
          const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
          content += `### ${agentName} Agent\n\n`;
          
          // Handle 'finding' (singular) from backend
          if (agentData.finding) {
            content += `${agentData.finding}\n\n`;
          }
          
          // Handle 'summary' if present
          if (agentData.summary) {
            content += `${agentData.summary}\n\n`;
          }
          
          // Handle 'findings' array if present
          if (agentData.findings && Array.isArray(agentData.findings)) {
            console.log('Agent Findings:', agentData.findings);
            agentData.findings.forEach(finding => {
              if (typeof finding === 'string') {
                content += `- ${finding}\n`;
              } else if (finding.description) {
                content += `- ${finding.description}\n`;
              } else if (finding.finding) {
                content += `- ${finding.finding}\n`;
              }
            });
            content += '\n';
          }
        }
      }
    }
    
    // Recommendations
    if (result.reflection?.recommendations && result.reflection.recommendations.length > 0) {
      content += `## Recommendations\n\n`;
      result.reflection.recommendations.forEach(rec => {
        content += `- ${rec}\n`;
      });
      content += '\n';
    }
    
    return content || 'Analysis completed but no detailed results available.';
  };

  /**
   * Send a message/question
   */
  const sendMessage = useCallback(async (question) => {
    if (!question.trim() || isLoading) return;

    // Add user message
    addMessage(MESSAGE_TYPES.USER, question);

    // Add placeholder assistant message
    const assistantMessage = addMessage(MESSAGE_TYPES.ASSISTANT, '', {
      status: MESSAGE_STATUS.SENDING
    });

    setIsLoading(true);

    try {
      // Submit analysis
      const response = await apiService.submitAnalysis(question);
      
      setCurrentJobId(response.job_id);
      setJobStatus(response.status);
      
      updateMessage(assistantMessage.id, {
        content: 'Query submitted. Analyzing...',
        status: MESSAGE_STATUS.PROCESSING,
        jobId: response.job_id
      });

      // Start polling for job status
      pollingRef.current = setInterval(() => {
        pollJobStatus(response.job_id, assistantMessage.id);
      }, 2000);

      // Also poll immediately
      pollJobStatus(response.job_id, assistantMessage.id);

    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      
      updateMessage(assistantMessage.id, {
        content: getRandomErrorMessage(),
        status: MESSAGE_STATUS.FAILED,
        error: error.message
      });
    }
  }, [isLoading, addMessage, updateMessage, pollJobStatus]);

  /**
   * Cancel current job
   */
  const cancelCurrentJob = useCallback(async () => {
    if (!currentJobId) return;

    try {
      await apiService.cancelJob(currentJobId);
      
      // Stop polling
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      
      setIsLoading(false);
      setJobStatus('cancelled');
      
    } catch (error) {
      console.error('Error cancelling job:', error);
    }
  }, [currentJobId]);

  const value = {
    messages,
    isLoading,
    currentJobId,
    jobStatus,
    jobProgress,
    sendMessage,
    addMessage,
    updateMessage,
    clearSession,
    cancelCurrentJob,
    MESSAGE_TYPES,
    MESSAGE_STATUS
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

/**
 * Hook to use chat context
 */
export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}

export default ChatContext;
