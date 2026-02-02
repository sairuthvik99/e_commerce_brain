import { useState, useRef, useEffect } from 'react';
import { useChat } from '../../context/ChatContext';
import './ChatInput.css';

/**
 * Chat Input Component
 * Input field with send and stop buttons
 */
function ChatInput() {
  const [input, setInput] = useState('');
  const inputRef = useRef(null);
  const { sendMessage, isLoading, cancelCurrentJob } = useChat();

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      sendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleStop = () => {
    cancelCurrentJob();
  };

  return (
    <form className="chat-input-container" onSubmit={handleSubmit}>
      <div className="chat-input-wrapper">
        <textarea
          ref={inputRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your e-commerce data..."
          rows={1}
          disabled={isLoading}
        />
        
        <div className="chat-input-actions">
          {isLoading ? (
            <button 
              type="button" 
              className="stop-button"
              onClick={handleStop}
              title="Stop analysis"
            >
              <span className="stop-icon">⏹</span>
              <span className="stop-text">Stop</span>
            </button>
          ) : (
            <button 
              type="submit" 
              className="send-button"
              disabled={!input.trim()}
              title="Send message"
            >
              <span className="send-icon">➤</span>
            </button>
          )}
        </div>
      </div>
      
      <p className="chat-input-hint">
        Press Enter to send, Shift+Enter for new line
      </p>
    </form>
  );
}

export default ChatInput;
