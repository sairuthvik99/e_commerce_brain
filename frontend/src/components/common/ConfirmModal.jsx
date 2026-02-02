import { useState } from 'react';
import { getProviderColor } from '../../constants/agentModels';
import './ConfirmModal.css';

/**
 * Confirmation Modal Component
 * Shows a modal dialog to confirm model change
 */
function ConfirmModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  currentModel, 
  newModel,
  isLoading 
}) {
  if (!isOpen) return null;

  const handleConfirm = async () => {
    await onConfirm();
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget && !isLoading) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-container">
        <div className="modal-header">
          <h3 className="modal-title">Change AI Model</h3>
        </div>
        
        <div className="modal-body">
          <p className="modal-message">
            Are you sure you want to change the AI model for all agents?
          </p>
          
          <div className="model-change-preview">
            <div className="model-item current">
              <span className="model-label-text">Current:</span>
              <span 
                className="model-badge"
                style={{ '--provider-color': getProviderColor(currentModel?.provider) }}
              >
                {currentModel?.label || 'Unknown'}
              </span>
            </div>
            
            <div className="model-arrow">→</div>
            
            <div className="model-item new">
              <span className="model-label-text">New:</span>
              <span 
                className="model-badge highlight"
                style={{ '--provider-color': getProviderColor(newModel?.provider) }}
              >
                {newModel?.label || 'Unknown'}
              </span>
            </div>
          </div>
          
          <p className="modal-note">
            This will update the model used by all agents (Sales, Inventory, Marketing, Support, etc.)
          </p>
        </div>
        
        <div className="modal-footer">
          <button 
            className="modal-btn cancel"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </button>
          <button 
            className="modal-btn confirm"
            onClick={handleConfirm}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="btn-spinner"></span>
                Changing...
              </>
            ) : (
              'Confirm Change'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;
