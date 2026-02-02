import { useState, useRef, useEffect, createElement } from 'react';
import { useChat } from '../../context/ChatContext';
import { QUESTION_CATEGORIES } from '../../constants/questions';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import StopIcon from '@mui/icons-material/Stop';
import SendIcon from '@mui/icons-material/Send';
import './ChatInput.css';

/**
 * Chat Input Component
 * Input field with send and stop buttons and slash command support
 */
function ChatInput() {
  const [input, setInput] = useState('');
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [menuPosition, setMenuPosition] = useState({ bottom: 0 });
  const inputRef = useRef(null);
  const menuRef = useRef(null);
  const { sendMessage, isLoading, cancelCurrentJob } = useChat();

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target) && 
          inputRef.current && !inputRef.current.contains(e.target)) {
        setShowSlashMenu(false);
        setSelectedCategory(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      sendMessage(input.trim());
      setInput('');
      setShowSlashMenu(false);
      setSelectedCategory(null);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setInput(value);

    // Show slash menu when user types '/'
    if (value === '/') {
      setShowSlashMenu(true);
      setSelectedCategory(null);
    } else if (!value.startsWith('/')) {
      setShowSlashMenu(false);
      setSelectedCategory(null);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!showSlashMenu) {
        handleSubmit(e);
      }
    } else if (e.key === 'Escape') {
      setShowSlashMenu(false);
      setSelectedCategory(null);
      setInput('');
    }
  };

  const handleCategorySelect = (categoryKey) => {
    setSelectedCategory(categoryKey);
  };

  const handleQuestionSelect = (question) => {
    setInput('');
    setShowSlashMenu(false);
    setSelectedCategory(null);
    sendMessage(question);
  };

  const handleBackToCategories = () => {
    setSelectedCategory(null);
  };

  const handleStop = () => {
    cancelCurrentJob();
  };

  return (
    <form className="chat-input-container" onSubmit={handleSubmit}>
      {/* Slash Command Menu */}
      {showSlashMenu && (
        <div className="slash-menu" ref={menuRef}>
          {!selectedCategory ? (
            // Show agent categories
            <div className="slash-menu-categories">
              <div className="slash-menu-header">
                <span className="slash-menu-title">Select an Agent</span>
                <span className="slash-menu-hint">Choose a category to see questions</span>
              </div>
              <div className="slash-menu-list">
                {Object.entries(QUESTION_CATEGORIES).map(([key, category]) => {
                  const IconComponent = category.iconComponent;
                  return (
                    <button
                      key={key}
                      type="button"
                      className="slash-menu-item category-item"
                      onClick={() => handleCategorySelect(key)}
                    >
                      <span className="item-icon">
                        {IconComponent && <IconComponent sx={{ fontSize: 24 }} />}
                      </span>
                      <div className="item-content">
                        <span className="item-title">{category.title}</span>
                        <span className="item-description">{category.description}</span>
                      </div>
                      <span className="item-arrow"><ArrowForwardIcon sx={{ fontSize: 18 }} /></span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            // Show questions for selected category
            <div className="slash-menu-questions">
              <div className="slash-menu-header">
                <button 
                  type="button" 
                  className="back-button"
                  onClick={handleBackToCategories}
                >
                  <ArrowBackIcon sx={{ fontSize: 18 }} /> Back
                </button>
                <span className="slash-menu-title">
                  {QUESTION_CATEGORIES[selectedCategory].iconComponent && 
                    createElement(QUESTION_CATEGORIES[selectedCategory].iconComponent, { sx: { fontSize: 20 } })}
                  {' '}{QUESTION_CATEGORIES[selectedCategory].title}
                </span>
              </div>
              <div className="slash-menu-list">
                {QUESTION_CATEGORIES[selectedCategory].questions.map((question, index) => (
                  <button
                    key={index}
                    type="button"
                    className="slash-menu-item question-item"
                    onClick={() => handleQuestionSelect(question)}
                  >
                    <span className="question-number">{index + 1}</span>
                    <span className="question-text">{question}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="chat-input-wrapper">
        <textarea
          ref={inputRef}
          className="chat-input"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question or type / for quick commands..."
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
              <StopIcon className="stop-icon" sx={{ fontSize: 18 }} />
              <span className="stop-text">Stop</span>
            </button>
          ) : (
            <button 
              type="submit" 
              className="send-button"
              disabled={!input.trim() || showSlashMenu}
              title="Send message"
            >
              <SendIcon className="send-icon" sx={{ fontSize: 20 }} />
            </button>
          )}
        </div>
      </div>
      
      <p className="chat-input-hint">
        Press Enter to send, Shift+Enter for new line, <strong>/</strong> for quick commands
      </p>
    </form>
  );
}

export default ChatInput;
