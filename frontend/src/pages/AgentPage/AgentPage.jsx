import { useRef, useEffect } from 'react';
import { useChat } from '../../context/ChatContext';
import { ChatMessage, ChatInput, QuestionCards } from '../../components/chat';
import './AgentPage.css';

/**
 * Agent Page - Chat Interface
 * Displays chat with AI agent
 */
function AgentPage() {
  const { messages, sendMessage, isLoading, jobProgress } = useChat();
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const hasMessages = messages.length > 0;

  const handleQuestionSelect = (question) => {
    sendMessage(question);
  };

  return (
    <div className="agent-page">
      <div className="agent-container">
        {/* Chat Area */}
        <div className="chat-area">
          {!hasMessages ? (
            <div className="chat-welcome">
              <div className="welcome-header">
                <span className="welcome-icon">🧠</span>
                <h1>STEB's AI Agent</h1>
                <p>Your intelligent e-commerce operations assistant</p>
              </div>
              <QuestionCards onSelectQuestion={handleQuestionSelect} />
            </div>
          ) : (
            <div className="messages-container">
              <div className="messages-list">
                {messages.map(message => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Progress Indicator */}
              {isLoading && jobProgress && (
                <div className="progress-indicator">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${jobProgress.percentage || 0}%` }}
                    />
                  </div>
                  <span className="progress-text">
                    {jobProgress.current_agent 
                      ? `Processing: ${jobProgress.current_agent}`
                      : 'Analyzing...'}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="input-area">
          <ChatInput />
        </div>
      </div>
    </div>
  );
}

export default AgentPage;
