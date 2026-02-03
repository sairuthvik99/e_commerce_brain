import { useState } from 'react';
import { apiService } from '../../services/api';
import CloseIcon from '@mui/icons-material/Close';
import TrackChangesIcon from '@mui/icons-material/TrackChanges';
import PhoneIcon from '@mui/icons-material/Phone';
import ConfirmationNumberIcon from '@mui/icons-material/ConfirmationNumber';
import EditNoteIcon from '@mui/icons-material/EditNote';
import InventoryIcon from '@mui/icons-material/Inventory';
import EmailIcon from '@mui/icons-material/Email';
import BoltIcon from '@mui/icons-material/Bolt';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CheckIcon from '@mui/icons-material/Check';
import ClearIcon from '@mui/icons-material/Clear';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import './HITLActions.css';

/**
 * HITL Actions Component
 * Displays recommended actions for a job and allows accept/reject decisions
 */
function HITLActions({ jobId, onClose }) {
  const [actions, setActions] = useState([]);
  const [proposalId, setProposalId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [actionDecisions, setActionDecisions] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);

  /**
   * Fetch actions from the API
   */
  const fetchActions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getJobActions(jobId);
      setActions(response.actions || []);
      setProposalId(response.proposal_id);
      
      // Initialize all actions as undecided
      const initialDecisions = {};
      (response.actions || []).forEach(action => {
        initialDecisions[action.action_id] = null;
      });
      setActionDecisions(initialDecisions);
    } catch (err) {
      console.error('Error fetching actions:', err);
      setError(err.message || 'Failed to fetch recommendations');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle decision change for an action
   */
  const handleDecision = (actionId, decision) => {
    setConfirmAction({ actionId, decision });
    setShowConfirmModal(true);
  };

  /**
   * Confirm the decision
   */
  const confirmDecision = () => {
    if (confirmAction) {
      setActionDecisions(prev => ({
        ...prev,
        [confirmAction.actionId]: confirmAction.decision
      }));
    }
    setShowConfirmModal(false);
    setConfirmAction(null);
  };

  /**
   * Cancel the decision
   */
  const cancelDecision = () => {
    setShowConfirmModal(false);
    setConfirmAction(null);
  };

  /**
   * Submit all decisions
   */
  const submitDecisions = async () => {
    const approvedIds = Object.entries(actionDecisions)
      .filter(([_, decision]) => decision === 'accept')
      .map(([id]) => id);
    
    const rejectedIds = Object.entries(actionDecisions)
      .filter(([_, decision]) => decision === 'reject')
      .map(([id]) => id);

    // Check if all actions have been decided
    const undecidedCount = Object.values(actionDecisions).filter(d => d === null).length;
    if (undecidedCount > 0) {
      setError(`Please decide on all ${undecidedCount} remaining action(s) before submitting.`);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await apiService.approveProposal(
        jobId,
        approvedIds,
        rejectedIds,
        'user', // approver
        'Decisions submitted from chat interface' // notes
      );
      setSubmitted(true);
    } catch (err) {
      console.error('Error submitting decisions:', err);
      setError(err.message || 'Failed to submit decisions');
    } finally {
      setSubmitting(false);
    }
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

  /**
   * Get action type icon
   */
  const getActionTypeIcon = (actionType) => {
    switch (actionType) {
      case 'contact_supplier':
        return <PhoneIcon sx={{ fontSize: 20 }} />;
      case 'create_support_ticket':
        return <ConfirmationNumberIcon sx={{ fontSize: 20 }} />;
      case 'update_product_page':
        return <EditNoteIcon sx={{ fontSize: 20 }} />;
      case 'adjust_inventory':
        return <InventoryIcon sx={{ fontSize: 20 }} />;
      case 'send_notification':
        return <EmailIcon sx={{ fontSize: 20 }} />;
      default:
        return <BoltIcon sx={{ fontSize: 20 }} />;
    }
  };

  // Initial state - show load button
  if (actions.length === 0 && !loading && !error) {
    return (
      <div className="hitl-actions-container">
        <div className="hitl-header">
          <h4><TrackChangesIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Recommended Actions</h4>
          <button className="hitl-close-btn" onClick={onClose} title="Close">
            <CloseIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        <div className="hitl-load-section">
          <p>Click below to view AI-generated action recommendations for this analysis.</p>
          <button className="hitl-load-btn" onClick={fetchActions}>
            Load Recommendations
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="hitl-actions-container">
        <div className="hitl-header">
          <h4><TrackChangesIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Recommended Actions</h4>
          <button className="hitl-close-btn" onClick={onClose} title="Close">
            <CloseIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        <div className="hitl-loading">
          <div className="hitl-spinner"></div>
          <span>Loading recommendations...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error && actions.length === 0) {
    return (
      <div className="hitl-actions-container">
        <div className="hitl-header">
          <h4><TrackChangesIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Recommended Actions</h4>
          <button className="hitl-close-btn" onClick={onClose} title="Close">
            <CloseIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        <div className="hitl-error">
          <span><WarningAmberIcon sx={{ fontSize: 18 }} /> {error}</span>
          <button className="hitl-retry-btn" onClick={fetchActions}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Submitted state
  if (submitted) {
    return (
      <div className="hitl-actions-container">
        <div className="hitl-header">
          <h4><TrackChangesIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Recommended Actions</h4>
          <button className="hitl-close-btn" onClick={onClose} title="Close">
            <CloseIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        <div className="hitl-submitted">
          <div className="hitl-success-icon"><CheckCircleIcon sx={{ fontSize: 48, color: '#22c55e' }} /></div>
          <h5>Decisions Submitted Successfully!</h5>
          <p>
            Approved: {Object.values(actionDecisions).filter(d => d === 'accept').length} actions<br/>
            Rejected: {Object.values(actionDecisions).filter(d => d === 'reject').length} actions
          </p>
          <button className="hitl-done-btn" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    );
  }

  // Actions list state
  return (
    <div className="hitl-actions-container">
      <div className="hitl-header">
        <h4><TrackChangesIcon sx={{ fontSize: 20, marginRight: '6px' }} /> Recommended Actions ({actions.length})</h4>
        <button className="hitl-close-btn" onClick={onClose} title="Close">
          <CloseIcon sx={{ fontSize: 18 }} />
        </button>
      </div>
      
      {error && (
        <div className="hitl-inline-error">
          <WarningAmberIcon sx={{ fontSize: 16 }} /> {error}
        </div>
      )}

      <div className="hitl-actions-list">
        {actions.map((action, index) => (
          <div 
            key={action.action_id} 
            className={`hitl-action-card ${actionDecisions[action.action_id] ? `decision-${actionDecisions[action.action_id]}` : ''}`}
          >
            <div className="action-header">
              <span className="action-icon">{getActionTypeIcon(action.action_type)}</span>
              <span className="action-number">Action {index + 1}</span>
              <span className={`action-risk ${getRiskLevelClass(action.risk_level)}`}>
                {action.risk_level} risk
              </span>
            </div>
            
            <div className="action-type-badge">
              {action.action_type.replace(/_/g, ' ')}
            </div>
            
            <p className="action-description">{action.description}</p>
            
            <div className="action-details">
              <div className="action-detail-row">
                <span className="detail-label">Target:</span>
                <span className="detail-value">{action.target}</span>
              </div>
              <div className="action-detail-row">
                <span className="detail-label">Impact:</span>
                <span className="detail-value">{action.estimated_impact}</span>
              </div>
            </div>

            <div className="action-decision-buttons">
              <button
                className={`decision-btn accept-btn ${actionDecisions[action.action_id] === 'accept' ? 'selected' : ''}`}
                onClick={() => handleDecision(action.action_id, 'accept')}
                disabled={submitting}
              >
                <CheckIcon sx={{ fontSize: 16 }} /> Accept
              </button>
              <button
                className={`decision-btn reject-btn ${actionDecisions[action.action_id] === 'reject' ? 'selected' : ''}`}
                onClick={() => handleDecision(action.action_id, 'reject')}
                disabled={submitting}
              >
                <ClearIcon sx={{ fontSize: 16 }} /> Reject
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="hitl-footer">
        <div className="decision-summary">
          <span className="accepted-count">
            <CheckIcon sx={{ fontSize: 14 }} /> {Object.values(actionDecisions).filter(d => d === 'accept').length} Accepted
          </span>
          <span className="rejected-count">
            <ClearIcon sx={{ fontSize: 14 }} /> {Object.values(actionDecisions).filter(d => d === 'reject').length} Rejected
          </span>
          <span className="pending-count">
            <RadioButtonUncheckedIcon sx={{ fontSize: 14 }} /> {Object.values(actionDecisions).filter(d => d === null).length} Pending
          </span>
        </div>
        <button 
          className="hitl-submit-btn" 
          onClick={submitDecisions}
          disabled={submitting || Object.values(actionDecisions).some(d => d === null)}
        >
          {submitting ? 'Submitting...' : 'Submit All Decisions'}
        </button>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && confirmAction && (
        <div className="hitl-modal-overlay">
          <div className="hitl-modal">
            <div className="modal-header">
              <h5>Confirm {confirmAction.decision === 'accept' ? 'Acceptance' : 'Rejection'}</h5>
            </div>
            <div className="modal-body">
              <p>
                Are you sure you want to <strong>{confirmAction.decision}</strong> this action?
              </p>
              <p className="modal-action-desc">
                {actions.find(a => a.action_id === confirmAction.actionId)?.description}
              </p>
            </div>
            <div className="modal-footer">
              <button className="modal-cancel-btn" onClick={cancelDecision}>
                Cancel
              </button>
              <button 
                className={`modal-confirm-btn ${confirmAction.decision === 'accept' ? 'confirm-accept' : 'confirm-reject'}`}
                onClick={confirmDecision}
              >
                Confirm {confirmAction.decision === 'accept' ? 'Accept' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HITLActions;
