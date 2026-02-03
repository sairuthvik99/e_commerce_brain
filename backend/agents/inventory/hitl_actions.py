"""
Inventory HITL (Human-in-the-Loop) Actions

Manages pending stock update actions that require human approval.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class PendingStockUpdate(BaseModel):
    """Model for a pending stock update action."""
    proposal_id: str = Field(..., description="Unique proposal identifier")
    product_id: int = Field(..., description="Product ID to update")
    current_stock: int = Field(..., description="Current stock level")
    quantity_change: int = Field(..., description="Amount to add/remove")
    new_stock: int = Field(..., description="Projected new stock level")
    reason: str = Field(default="", description="Reason for the update")
    status: str = Field(default="pending", description="Status: pending, approved, rejected, executed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
    approved_by: Optional[str] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    executed_at: Optional[datetime] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None)


# In-memory storage for pending stock updates
# In production, this should be stored in a database
_pending_stock_updates: Dict[str, PendingStockUpdate] = {}


def store_pending_stock_update(
    proposal_id: str,
    product_id: int,
    current_stock: int,
    quantity_change: int,
    new_stock: int,
    reason: str = ""
) -> PendingStockUpdate:
    """
    Store a pending stock update action for HITL approval.
    
    Args:
        proposal_id: Unique proposal identifier
        product_id: Product ID to update
        current_stock: Current stock level
        quantity_change: Amount to add/remove
        new_stock: Projected new stock level
        reason: Reason for the update
    
    Returns:
        PendingStockUpdate object
    """
    update = PendingStockUpdate(
        proposal_id=proposal_id,
        product_id=product_id,
        current_stock=current_stock,
        quantity_change=quantity_change,
        new_stock=new_stock,
        reason=reason,
        status="pending",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
    )
    
    _pending_stock_updates[proposal_id] = update
    logger.info(f"[HITL] Stored pending stock update {proposal_id} for product {product_id}")
    
    return update


def get_pending_stock_update(proposal_id: str) -> Optional[PendingStockUpdate]:
    """
    Get a pending stock update by proposal ID.
    
    Args:
        proposal_id: The proposal ID to look up
    
    Returns:
        PendingStockUpdate object or None if not found
    """
    return _pending_stock_updates.get(proposal_id)


def get_all_pending_stock_updates(status: Optional[str] = None) -> List[PendingStockUpdate]:
    """
    Get all pending stock updates, optionally filtered by status.
    
    Args:
        status: Filter by status (pending, approved, rejected, executed)
    
    Returns:
        List of PendingStockUpdate objects
    """
    updates = list(_pending_stock_updates.values())
    
    if status:
        updates = [u for u in updates if u.status == status]
    
    # Sort by created_at descending
    updates.sort(key=lambda x: x.created_at, reverse=True)
    
    return updates


def approve_stock_update(proposal_id: str, approver: str = None) -> Dict[str, Any]:
    """
    Approve a pending stock update.
    
    Args:
        proposal_id: The proposal ID to approve
        approver: Who approved the update
    
    Returns:
        Result dict with status and details
    """
    update = _pending_stock_updates.get(proposal_id)
    
    if not update:
        return {
            "success": False,
            "message": f"Proposal {proposal_id} not found"
        }
    
    if update.status != "pending":
        return {
            "success": False,
            "message": f"Proposal {proposal_id} already processed (status: {update.status})"
        }
    
    # Check expiry
    if update.expires_at and datetime.utcnow() > update.expires_at:
        update.status = "expired"
        return {
            "success": False,
            "message": f"Proposal {proposal_id} has expired"
        }
    
    update.status = "approved"
    update.approved_by = approver
    update.approved_at = datetime.utcnow()
    
    logger.info(f"[HITL] Approved stock update {proposal_id} by {approver}")
    
    return {
        "success": True,
        "message": f"Proposal {proposal_id} approved",
        "proposal_id": proposal_id,
        "product_id": update.product_id,
        "quantity_change": update.quantity_change,
        "status": "approved"
    }


def reject_stock_update(proposal_id: str, reason: str = None, rejector: str = None) -> Dict[str, Any]:
    """
    Reject a pending stock update.
    
    Args:
        proposal_id: The proposal ID to reject
        reason: Reason for rejection
        rejector: Who rejected the update
    
    Returns:
        Result dict with status and details
    """
    update = _pending_stock_updates.get(proposal_id)
    
    if not update:
        return {
            "success": False,
            "message": f"Proposal {proposal_id} not found"
        }
    
    if update.status != "pending":
        return {
            "success": False,
            "message": f"Proposal {proposal_id} already processed (status: {update.status})"
        }
    
    update.status = "rejected"
    update.rejection_reason = reason
    update.approved_by = rejector  # Using same field for who processed it
    update.approved_at = datetime.utcnow()
    
    logger.info(f"[HITL] Rejected stock update {proposal_id}: {reason}")
    
    return {
        "success": True,
        "message": f"Proposal {proposal_id} rejected" + (f": {reason}" if reason else ""),
        "proposal_id": proposal_id,
        "product_id": update.product_id,
        "status": "rejected"
    }


def execute_stock_update(proposal_id: str) -> Dict[str, Any]:
    """
    Execute an approved stock update.
    
    This actually updates the database after HITL approval.
    
    Args:
        proposal_id: The proposal ID to execute
    
    Returns:
        Result dict with execution status and details
    """
    update = _pending_stock_updates.get(proposal_id)
    
    if not update:
        return {
            "success": False,
            "message": f"Proposal {proposal_id} not found"
        }
    
    if update.status != "approved":
        return {
            "success": False,
            "message": f"Proposal {proposal_id} not approved (status: {update.status})"
        }
    
    try:
        # Execute the actual database update
        from backend.database.queries import update_product_stock
        
        result = update_product_stock(
            product_id=update.product_id,
            quantity_change=update.quantity_change,
            reason=update.reason
        )
        
        if result.get('success'):
            update.status = "executed"
            update.executed_at = datetime.utcnow()
            
            logger.info(f"[HITL] Executed stock update {proposal_id} for product {update.product_id}")
            
            return {
                "success": True,
                "message": f"Stock update executed successfully for Product {update.product_id}",
                "proposal_id": proposal_id,
                "product_id": update.product_id,
                "previous_stock": result.get('previous_stock'),
                "new_stock": result.get('new_stock'),
                "quantity_change": update.quantity_change,
                "status": "executed"
            }
        else:
            return {
                "success": False,
                "message": result.get('message', 'Unknown error executing stock update'),
                "proposal_id": proposal_id
            }
    
    except Exception as e:
        logger.error(f"[HITL] Failed to execute stock update {proposal_id}: {e}")
        return {
            "success": False,
            "message": f"Failed to execute stock update: {str(e)}",
            "proposal_id": proposal_id
        }


def get_pending_updates_for_display() -> List[Dict[str, Any]]:
    """
    Get all pending stock updates formatted for frontend display.
    
    Returns:
        List of action items for HITL interface
    """
    pending_updates = get_all_pending_stock_updates(status="pending")
    
    actions = []
    for update in pending_updates:
        action_type = "stock_increase" if update.quantity_change > 0 else "stock_decrease"
        
        actions.append({
            "action_id": update.proposal_id,
            "action_type": action_type,
            "description": f"{'Increase' if update.quantity_change > 0 else 'Decrease'} stock for Product {update.product_id} by {abs(update.quantity_change)} units",
            "target": f"Product {update.product_id}",
            "parameters": {
                "product_id": update.product_id,
                "current_stock": update.current_stock,
                "quantity_change": update.quantity_change,
                "new_stock": update.new_stock
            },
            "estimated_impact": f"Stock will change from {update.current_stock} to {update.new_stock}",
            "risk_level": "high" if abs(update.quantity_change) > 100 else ("medium" if abs(update.quantity_change) > 50 else "low"),
            "reason": update.reason,
            "created_at": update.created_at.isoformat(),
            "expires_at": update.expires_at.isoformat() if update.expires_at else None
        })
    
    return actions


def cleanup_expired_updates() -> int:
    """
    Clean up expired pending updates.
    
    Returns:
        Number of updates cleaned up
    """
    now = datetime.utcnow()
    expired_ids = []
    
    for proposal_id, update in _pending_stock_updates.items():
        if update.status == "pending" and update.expires_at and now > update.expires_at:
            update.status = "expired"
            expired_ids.append(proposal_id)
    
    if expired_ids:
        logger.info(f"[HITL] Cleaned up {len(expired_ids)} expired stock update proposals")
    
    return len(expired_ids)
