import { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import CloseIcon from '@mui/icons-material/Close';
import InventoryIcon from '@mui/icons-material/Inventory';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CheckIcon from '@mui/icons-material/Check';
import ClearIcon from '@mui/icons-material/Clear';
import RefreshIcon from '@mui/icons-material/Refresh';
import './StockUpdateHITL.css';

/**
 * Stock Update HITL Component
 * Displays pending stock update proposals and allows approve/reject decisions
 */
function StockUpdateHITL({ onClose, autoRefresh = false }) {
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState({});
  const [results, setResults] = useState({});
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');

  /**
   * Fetch pending stock updates from the API
   */
  const fetchUpdates = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getStockUpdates('pending');
      setUpdates(response.actions || []);
    } catch (err) {
      console.error('Error fetching stock updates:', err);
      setError(err.message || 'Failed to fetch stock updates');
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch on mount
  useEffect(() => {
    fetchUpdates();
    
    // Set up auto-refresh if enabled
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchUpdates, 10000); // Refresh every 10 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  /**
   * Handle approve/reject decision
   */
  const handleDecision = (action, approved) => {
    setConfirmAction({ action, approved });
    setRejectionReason('');
    setShowConfirmModal(true);
  };

  /**
   * Confirm the decision
   */
  const confirmDecision = async () => {
    if (!confirmAction) return;
    
    const { action, approved } = confirmAction;
    const proposalId = action.action_id;
    
    setShowConfirmModal(false);
    setProcessing(prev => ({ ...prev, [proposalId]: true }));
    
    try {
      const response = await apiService.approveStockUpdate(
        proposalId,
        approved,
        'user',
        approved ? null : rejectionReason || 'Rejected by user'
      );
      
      setResults(prev => ({
        ...prev,
        [proposalId]: {
          success: true,
          approved,
          message: response.message,
          newStock: response.new_stock
        }
      }));
      
      // Remove from pending list after a delay
      setTimeout(() => {
        setUpdates(prev => prev.filter(u => u.action_id !== proposalId));
        setResults(prev => {
          const newResults = { ...prev };
          delete newResults[proposalId];
          return newResults;
        });
      }, 3000);
      
    } catch (err) {
      console.error('Error processing stock update:', err);
      setResults(prev => ({
        ...prev,
        [proposalId]: {
          success: false,
          message: err.message || 'Failed to process request'
        }
      }));
    } finally {
      setProcessing(prev => ({ ...prev, [proposalId]: false }));
      setConfirmAction(null);
    }
  };

  /**
   * Cancel the decision
   */
  const cancelDecision = () => {
    setShowConfirmModal(false);
    setConfirmAction(null);
    setRejectionReason('');
  };

  /**
   * Get risk level styling
   */
  const getRiskLevelClass = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
        return 'risk-high';
      case 'medium':
        return 'risk-medium';
      case 'low':
        return 'risk-low';
      default:
        return 'risk-unknown';
    }
  };

  // Loading state
  if (loading && updates.length === 0) {
    return (
      <div className="stock-hitl-container">
        <div className="stock-hitl-header">
          <h4><InventoryIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Stock Update Approvals</h4>
          <button className="stock-hitl-close-btn" onClick={onClose} title="Close">
            <CloseIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        <div className="stock-hitl-loading">
          <div className="stock-hitl-spinner"></div>
          <span>Loading pending stock updates...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error && updates.length === 0) {
    return (
      <div className="stock-hitl-container">
        <div className="stock-hitl-header">
          <h4><InventoryIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Stock Update Approvals</h4>
          <button className="stock-hitl-close-btn" onClick={onClose} title="Close">
            <CloseIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        <div className="stock-hitl-error">
          <span><WarningAmberIcon sx={{ fontSize: 18 }} /> {error}</span>
          <button className="stock-hitl-retry-btn" onClick={fetchUpdates}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (updates.length === 0) {
    return (
      <div className="stock-hitl-container">
        <div className="stock-hitl-header">
          <h4><InventoryIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Stock Update Approvals</h4>
          <div className="header-actions">
            <button className="stock-hitl-refresh-btn" onClick={fetchUpdates} title="Refresh">
              <RefreshIcon sx={{ fontSize: 18 }} />
            </button>
            <button className="stock-hitl-close-btn" onClick={onClose} title="Close">
              <CloseIcon sx={{ fontSize: 18 }} />
            </button>
          </div>
        </div>
        <div className="stock-hitl-empty">
          <CheckCircleIcon sx={{ fontSize: 48, color: '#22c55e' }} />
          <h5>No Pending Stock Updates</h5>
          <p>All stock update requests have been processed.</p>
        </div>
      </div>
    );
  }

  // Updates list state
  return (
    <div className="stock-hitl-container">
      <div className="stock-hitl-header">
        <h4><InventoryIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Stock Update Approvals ({updates.length})</h4>
        <div className="header-actions">
          <button className="stock-hitl-refresh-btn" onClick={fetchUpdates} title="Refresh" disabled={loading}>
            <RefreshIcon sx={{ fontSize: 18, animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          </button>
          <button className="stock-hitl-close-btn" onClick={onClose} title="Close">
            <CloseIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
      </div>
      
      {error && (
        <div className="stock-hitl-inline-error">
          <WarningAmberIcon sx={{ fontSize: 16 }} /> {error}
        </div>
      )}

      <div className="stock-hitl-updates-list">
        {updates.map((update, index) => {
          const isProcessing = processing[update.action_id];
          const result = results[update.action_id];
          const isIncrease = update.quantity_change > 0;
          
          return (
            <div 
              key={update.action_id} 
              className={`stock-update-card ${result ? (result.success ? (result.approved ? 'approved' : 'rejected') : 'error') : ''}`}
            >
              {result ? (
                <div className="update-result">
                  {result.success ? (
                    <>
                      <CheckCircleIcon sx={{ fontSize: 32, color: result.approved ? '#22c55e' : '#ef4444' }} />
                      <p>{result.message}</p>
                      {result.approved && result.newStock !== undefined && (
                        <span className="new-stock-value">New Stock: {result.newStock}</span>
                      )}
                    </>
                  ) : (
                    <>
                      <WarningAmberIcon sx={{ fontSize: 32, color: '#ef4444' }} />
                      <p>{result.message}</p>
                    </>
                  )}
                </div>
              ) : (
                <>
                  <div className="update-header">
                    <span className="update-icon">
                      {isIncrease ? 
                        <AddIcon sx={{ fontSize: 20, color: '#22c55e' }} /> : 
                        <RemoveIcon sx={{ fontSize: 20, color: '#ef4444' }} />
                      }
                    </span>
                    <span className="update-number">Update #{index + 1}</span>
                    <span className={`update-risk ${getRiskLevelClass(update.risk_level)}`}>
                      {update.risk_level} risk
                    </span>
                  </div>
                  
                  <div className="update-type-badge">
                    {isIncrease ? 'Stock Increase' : 'Stock Decrease'}
                  </div>
                  
                  <p className="update-description">{update.description}</p>
                  
                  <div className="update-details">
                    <div className="update-detail-row">
                      <span className="detail-label">Product ID:</span>
                      <span className="detail-value">{update.product_id}</span>
                    </div>
                    <div className="update-detail-row">
                      <span className="detail-label">Current Stock:</span>
                      <span className="detail-value">{update.current_stock}</span>
                    </div>
                    <div className="update-detail-row">
                      <span className="detail-label">Change:</span>
                      <span className={`detail-value ${isIncrease ? 'positive' : 'negative'}`}>
                        {isIncrease ? '+' : ''}{update.quantity_change}
                      </span>
                    </div>
                    <div className="update-detail-row">
                      <span className="detail-label">New Stock:</span>
                      <span className="detail-value highlight">{update.new_stock}</span>
                    </div>
                    {update.reason && (
                      <div className="update-detail-row">
                        <span className="detail-label">Reason:</span>
                        <span className="detail-value">{update.reason}</span>
                      </div>
                    )}
                  </div>

                  <div className="update-decision-buttons">
                    <button
                      className="decision-btn approve-btn"
                      onClick={() => handleDecision(update, true)}
                      disabled={isProcessing}
                    >
                      {isProcessing ? 'Processing...' : (
                        <>
                          <CheckIcon sx={{ fontSize: 16 }} /> Approve
                        </>
                      )}
                    </button>
                    <button
                      className="decision-btn deny-btn"
                      onClick={() => handleDecision(update, false)}
                      disabled={isProcessing}
                    >
                      <ClearIcon sx={{ fontSize: 16 }} /> Deny
                    </button>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && confirmAction && (
        <div className="stock-hitl-modal-overlay">
          <div className="stock-hitl-modal">
            <div className="modal-header">
              <h5>Confirm {confirmAction.approved ? 'Approval' : 'Rejection'}</h5>
            </div>
            <div className="modal-body">
              <p>
                Are you sure you want to <strong>{confirmAction.approved ? 'approve' : 'reject'}</strong> this stock update?
              </p>
              <p className="modal-update-desc">
                {confirmAction.action.description}
              </p>
              <div className="modal-stock-preview">
                <span>Stock Change: </span>
                <span className={confirmAction.action.quantity_change > 0 ? 'positive' : 'negative'}>
                  {confirmAction.action.current_stock} → {confirmAction.action.new_stock}
                </span>
              </div>
              
              {!confirmAction.approved && (
                <div className="rejection-reason-input">
                  <label>Reason for rejection (optional):</label>
                  <textarea
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="Enter reason for rejecting this stock update..."
                    rows={3}
                  />
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="modal-cancel-btn" onClick={cancelDecision}>
                Cancel
              </button>
              <button 
                className={`modal-confirm-btn ${confirmAction.approved ? 'confirm-approve' : 'confirm-reject'}`}
                onClick={confirmDecision}
              >
                Confirm {confirmAction.approved ? 'Approval' : 'Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StockUpdateHITL;
