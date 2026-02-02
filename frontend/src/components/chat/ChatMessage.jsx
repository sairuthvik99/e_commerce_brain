import { useState } from 'react';
import { MESSAGE_TYPES, MESSAGE_STATUS } from '../../context/ChatContext';
import HITLActions from './HITLActions';
import './ChatMessage.css';

/**
 * Chat Message Component
 * Renders a single chat message
 */
function ChatMessage({ message }) {
  const { type, content, status, timestamp, jobId, result } = message;
  const [showHITL, setShowHITL] = useState(false);

  const isUser = type === MESSAGE_TYPES.USER;
  const isLoading = status === MESSAGE_STATUS.SENDING || status === MESSAGE_STATUS.PROCESSING;
  const isError = status === MESSAGE_STATUS.FAILED;
  const isCancelled = status === MESSAGE_STATUS.CANCELLED;

  const formatTimestamp = (ts) => {
    return new Date(ts).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="message-loading">
          <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span className="loading-text">
            {status === MESSAGE_STATUS.SENDING ? 'Submitting...' : 'Analyzing...'}
          </span>
          {jobId && (
            <span className="job-badge">Query Submitted</span>
          )}
        </div>
      );
    }

    // Simple markdown-like rendering
    return (
      <div className="message-content" dangerouslySetInnerHTML={{ 
        __html: formatContent(content) 
      }} />
    );
  };

  const formatContent = (text) => {
    if (!text) return '';
    
    // Basic markdown parsing
    let formatted = text
      // Headers
      .replace(/^## (.+)$/gm, '<h3>$1</h3>')
      .replace(/^### (.+)$/gm, '<h4>$1</h4>')
      // Bold
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Lists
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      // Paragraphs
      .replace(/\n\n/g, '</p><p>')
      // Line breaks
      .replace(/\n/g, '<br>');
    
    // Wrap lists
    formatted = formatted.replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');
    
    return `<p>${formatted}</p>`;
  };

  // Check if HITL recommendations button should be shown
  const showRecommendationsButton = !isUser && 
    status === MESSAGE_STATUS.COMPLETED && 
    jobId;

  return (
    <div className={`chat-message ${isUser ? 'message-user' : 'message-assistant'} ${isError ? 'message-error' : ''} ${isCancelled ? 'message-cancelled' : ''}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🧠'}
      </div>
      <div className="message-bubble">
        {renderContent()}
        
        {/* HITL Recommendations Button */}
        {showRecommendationsButton && !showHITL && (
          <button 
            className="recommendations-btn"
            onClick={() => setShowHITL(true)}
          >
            💡 View Recommendations
          </button>
        )}
        
        {/* HITL Actions Panel */}
        {showHITL && jobId && (
          <HITLActions 
            jobId={jobId} 
            onClose={() => setShowHITL(false)} 
          />
        )}
        
        <div className="message-meta">
          <span className="message-time">{formatTimestamp(timestamp)}</span>
          {status === MESSAGE_STATUS.FAILED && (
            <span className="message-status error">Failed</span>
          )}
          {status === MESSAGE_STATUS.CANCELLED && (
            <span className="message-status cancelled">Cancelled</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
