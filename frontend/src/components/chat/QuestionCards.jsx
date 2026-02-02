import { useState } from 'react';
import { QUESTION_CATEGORIES } from '../../constants/questions';
import Card from '../common/Card';
import './QuestionCards.css';

/**
 * Question Cards Component
 * Shows category cards and question modal when clicked
 */
function QuestionCards({ onSelectQuestion }) {
  const [selectedCategory, setSelectedCategory] = useState(null);

  const handleCategoryClick = (categoryKey) => {
    setSelectedCategory(categoryKey);
  };

  const handleQuestionSelect = (question) => {
    onSelectQuestion(question);
    setSelectedCategory(null);
  };

  const handleCloseModal = () => {
    setSelectedCategory(null);
  };

  const handleModalBackdropClick = (e) => {
    if (e.target.classList.contains('question-modal-backdrop')) {
      handleCloseModal();
    }
  };

  return (
    <div className="question-cards-container">
      <div className="question-cards-header">
        <h2>What would you like to analyze?</h2>
        <p>Select a category to get started with predefined questions</p>
      </div>

      <div className="question-cards-grid">
        {Object.entries(QUESTION_CATEGORIES).map(([key, category]) => (
          <Card 
            key={key} 
            className="question-category-card"
            hoverable
            onClick={() => handleCategoryClick(key)}
          >
            <span className="category-icon">{category.icon}</span>
            <h3 className="category-title">{category.title}</h3>
            <p className="category-description">{category.description}</p>
            <span className="category-count">
              {category.questions.length} questions
            </span>
          </Card>
        ))}
      </div>

      {/* Question Selection Modal */}
      {selectedCategory && (
        <div 
          className="question-modal-backdrop"
          onClick={handleModalBackdropClick}
        >
          <div className="question-modal">
            <div className="question-modal-header">
              <span className="modal-icon">
                {QUESTION_CATEGORIES[selectedCategory].icon}
              </span>
              <h3>{QUESTION_CATEGORIES[selectedCategory].title}</h3>
              <button 
                className="modal-close"
                onClick={handleCloseModal}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>
            
            <div className="question-modal-body">
              <p className="modal-description">
                Select a question to analyze:
              </p>
              <ul className="question-list">
                {QUESTION_CATEGORIES[selectedCategory].questions.map((question, index) => (
                  <li key={index}>
                    <button
                      className="question-item"
                      onClick={() => handleQuestionSelect(question)}
                    >
                      {question}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default QuestionCards;
