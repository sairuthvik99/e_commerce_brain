"""
Human-in-the-Loop (HITL) Endpoints

Endpoints for action proposals, approval, and rejection.
"""

from typing import Optional, Any, Dict, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from backend.api.schemas import JobStatus, MessageResponse
from backend.api.services.job_manager import JobManager, get_job_manager


# ============================================================
# HITL Request/Response Schemas
# ============================================================

class ActionItem(BaseModel):
    """Individual action item in a proposal."""
    action_id: str = Field(..., description="Unique action identifier")
    action_type: str = Field(..., description="Type of action (restock, discount, pause_campaign, etc.)")
    description: str = Field(..., description="Human-readable description")
    target: Optional[str] = Field(None, description="Target entity (product SKU, campaign ID, etc.)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    estimated_impact: Optional[str] = Field(None, description="Expected outcome")
    risk_level: str = Field(default="medium", description="Risk level: low, medium, high")
    

class ActionProposalResponse(BaseModel):
    """Response containing proposed actions for approval."""
    job_id: str = Field(..., description="Associated job ID")
    proposal_id: str = Field(..., description="Unique proposal identifier")
    status: str = Field(..., description="Proposal status: pending, approved, rejected, partial")
    actions: List[ActionItem] = Field(default_factory=list, description="Proposed actions")
    root_cause_summary: Optional[str] = Field(None, description="Summary of root cause")
    confidence_score: float = Field(default=0.0, description="Analysis confidence")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Proposal expiration time")


class ApprovalRequest(BaseModel):
    """Request to approve/reject actions."""
    approved_action_ids: List[str] = Field(default_factory=list, description="IDs of approved actions")
    rejected_action_ids: List[str] = Field(default_factory=list, description="IDs of rejected actions")
    approver: Optional[str] = Field(None, description="Who approved (ops_manager, marketing_lead, founder)")
    notes: Optional[str] = Field(None, description="Approval notes or reason for rejection")


class ApprovalResponse(BaseModel):
    """Response after processing approval."""
    job_id: str
    proposal_id: str
    status: str = Field(..., description="Updated status: approved, rejected, partial")
    approved_actions: List[str] = Field(default_factory=list)
    rejected_actions: List[str] = Field(default_factory=list)
    message: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class ExecutionResult(BaseModel):
    """Result of executing an approved action."""
    action_id: str
    status: str = Field(..., description="execution status: success, failed, pending")
    message: str
    executed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None


router = APIRouter()


# ============================================================
# In-memory storage for proposals (replace with DB in production)
# ============================================================

_proposals: Dict[str, Dict[str, Any]] = {}


def _generate_proposal_id() -> str:
    """Generate a unique proposal ID."""
    import uuid
    return f"proposal_{uuid.uuid4().hex[:12]}"


def _generate_actions_from_llm(job_id: str, root_cause: Dict[str, Any], agent_findings: Dict[str, Any]) -> List[ActionItem]:
    """
    Generate action proposals using LLM based on root cause analysis.
    
    Args:
        job_id: The job identifier
        root_cause: Root cause analysis result
        agent_findings: Findings from all agents
        
    Returns:
        List of ActionItem proposals
    """
    import json
    from langchain_openai import AzureChatOpenAI
    from backend.settings import Settings
    
    try:
        llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("supervisor", "gpt-4"),
        )
        
        # Build context from root cause and findings
        context = {
            "root_cause": root_cause,
            "agent_findings": agent_findings
        }
        
        system_prompt = """You are an AI operations advisor for an e-commerce business.
Based on the analysis results, propose specific corrective actions.

For each action, provide:
- action_type: One of [restock, discount, pause_campaign, resume_campaign, create_support_ticket, contact_supplier, update_product_page, other]
- description: Clear description of what to do
- target: Specific entity (product SKU, campaign ID, etc.) if applicable
- parameters: Relevant parameters as JSON object
- estimated_impact: Expected outcome
- risk_level: One of [low, medium, high]

Return a JSON array of actions. Example:
[
  {
    "action_type": "restock",
    "description": "Expedite restock for product X",
    "target": "SKU-123",
    "parameters": {"quantity": 500, "priority": "urgent"},
    "estimated_impact": "Restore availability in 2-3 days",
    "risk_level": "low"
  }
]

Only return the JSON array, no other text."""

        user_prompt = f"""Based on this analysis, propose corrective actions:

Root Cause Analysis:
{json.dumps(root_cause, indent=2)}

Agent Findings Summary:
{json.dumps(agent_findings, indent=2)}

Propose 2-4 specific, actionable corrective actions."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        
        # Parse LLM response
        content = response.content.strip()
        # Clean up potential markdown formatting
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        actions_data = json.loads(content)
        
        actions = []
        for i, action_data in enumerate(actions_data):
            actions.append(ActionItem(
                action_id=f"{job_id}_act_{i+1}",
                action_type=action_data.get("action_type", "other"),
                description=action_data.get("description", ""),
                target=action_data.get("target"),
                parameters=action_data.get("parameters"),
                estimated_impact=action_data.get("estimated_impact"),
                risk_level=action_data.get("risk_level", "medium")
            ))
        
        logger.info(f"Generated {len(actions)} actions from LLM for job {job_id}")
        return actions
        
    except Exception as e:
        logger.error(f"Failed to generate actions from LLM: {e}")
        # Return a basic action if LLM fails
        return [ActionItem(
            action_id=f"{job_id}_act_1",
            action_type="other",
            description="Review the analysis and determine appropriate action manually",
            target=None,
            parameters=None,
            estimated_impact="Manual review required",
            risk_level="low"
        )]


# ============================================================
# HITL Endpoints
# ============================================================

@router.get(
    "/jobs/{job_id}/actions",
    response_model=ActionProposalResponse,
    summary="Get Action Proposals",
    description="Get proposed actions for a completed analysis job",
    responses={
        200: {"description": "Action proposals retrieved"},
        404: {"description": "Job not found"},
        409: {"description": "Job not completed yet"}
    }
)
async def get_action_proposals(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
) -> ActionProposalResponse:
    """
    Get proposed actions for a completed job.
    
    Returns a list of recommended actions based on the root cause analysis.
    Each action requires human approval before execution.
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job not completed. Current status: '{job.status.value}'"
        )
    
    # Check if proposal already exists
    if job_id in _proposals:
        proposal = _proposals[job_id]
        return ActionProposalResponse(**proposal)
    
    # Generate new proposal using LLM
    proposal_id = _generate_proposal_id()
    actions = _generate_actions_from_llm(job_id, job.root_cause or {}, job.agent_findings or {})
    
    root_cause_summary = None
    confidence = 0.0
    if job.root_cause:
        root_cause_summary = job.root_cause.get("primary_cause", "Unknown")
        confidence = job.root_cause.get("confidence_score", 0.0)
    
    proposal = {
        "job_id": job_id,
        "proposal_id": proposal_id,
        "status": "pending",
        "actions": [a.model_dump() for a in actions],
        "root_cause_summary": root_cause_summary,
        "confidence_score": confidence,
        "created_at": datetime.utcnow(),
        "expires_at": None
    }
    
    _proposals[job_id] = proposal
    logger.info(f"Created action proposal {proposal_id} for job {job_id}")
    
    return ActionProposalResponse(**proposal)


@router.post(
    "/jobs/{job_id}/actions/approve",
    response_model=ApprovalResponse,
    summary="Approve/Reject Actions",
    description="Submit approval or rejection for proposed actions",
    responses={
        200: {"description": "Approval processed"},
        404: {"description": "Job or proposal not found"},
        400: {"description": "Invalid approval request"}
    }
)
async def approve_actions(
    job_id: str,
    request: ApprovalRequest,
    job_manager: JobManager = Depends(get_job_manager)
) -> ApprovalResponse:
    """
    Approve or reject proposed actions.
    
    The approver can:
    - Approve all actions
    - Reject all actions
    - Partially approve (approve some, reject others)
    
    Approved actions will be queued for execution.
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    if job_id not in _proposals:
        raise HTTPException(
            status_code=404,
            detail=f"No action proposal found for job '{job_id}'. Call GET /jobs/{job_id}/actions first."
        )
    
    proposal = _proposals[job_id]
    
    if proposal["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Proposal already processed. Status: '{proposal['status']}'"
        )
    
    # Validate action IDs
    valid_action_ids = {a["action_id"] for a in proposal["actions"]}
    all_requested = set(request.approved_action_ids) | set(request.rejected_action_ids)
    
    invalid_ids = all_requested - valid_action_ids
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action IDs: {list(invalid_ids)}"
        )
    
    # Process approval
    approved = list(request.approved_action_ids)
    rejected = list(request.rejected_action_ids)
    
    # Update proposal status
    if len(approved) == len(proposal["actions"]):
        new_status = "approved"
    elif len(rejected) == len(proposal["actions"]):
        new_status = "rejected"
    elif approved:
        new_status = "partial"
    else:
        new_status = "rejected"
    
    proposal["status"] = new_status
    proposal["approved_at"] = datetime.utcnow()
    proposal["approved_by"] = request.approver
    proposal["approval_notes"] = request.notes
    
    logger.info(
        f"Proposal {proposal['proposal_id']} for job {job_id}: "
        f"status={new_status}, approved={len(approved)}, rejected={len(rejected)}"
    )
    
    return ApprovalResponse(
        job_id=job_id,
        proposal_id=proposal["proposal_id"],
        status=new_status,
        approved_actions=approved,
        rejected_actions=rejected,
        message=f"Processed {len(approved)} approved and {len(rejected)} rejected actions",
        approved_by=request.approver,
        approved_at=proposal["approved_at"]
    )


@router.post(
    "/jobs/{job_id}/actions/execute",
    summary="Execute Approved Actions",
    description="Execute all approved actions for a job",
    responses={
        200: {"description": "Actions executed"},
        404: {"description": "Job or proposal not found"},
        400: {"description": "No approved actions to execute"}
    }
)
async def execute_actions(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
) -> Dict[str, Any]:
    """
    Execute all approved actions.
    
    This endpoint triggers the execution of actions that have been approved.
    Actions are executed sequentially and results are returned.
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    if job_id not in _proposals:
        raise HTTPException(
            status_code=404,
            detail=f"No action proposal found for job '{job_id}'"
        )
    
    proposal = _proposals[job_id]
    
    if proposal["status"] not in ["approved", "partial"]:
        raise HTTPException(
            status_code=400,
            detail=f"No approved actions. Proposal status: '{proposal['status']}'"
        )
    
    # Get approved action IDs
    approved_ids = proposal.get("approved_actions", [])
    if not approved_ids:
        # If status is approved but no specific IDs, all are approved
        approved_ids = [a["action_id"] for a in proposal["actions"]]
    
    # Execute actions (mock implementation)
    results = []
    for action in proposal["actions"]:
        if action["action_id"] in approved_ids:
            # Mock execution
            result = ExecutionResult(
                action_id=action["action_id"],
                status="success",
                message=f"Action '{action['action_type']}' executed successfully",
                executed_at=datetime.utcnow(),
                result_data={"target": action.get("target"), "parameters": action.get("parameters")}
            )
            results.append(result.model_dump())
            logger.info(f"Executed action {action['action_id']}: {action['action_type']}")
    
    return {
        "job_id": job_id,
        "proposal_id": proposal["proposal_id"],
        "executed_count": len(results),
        "results": results,
        "message": f"Successfully executed {len(results)} actions"
    }


@router.get(
    "/proposals",
    summary="List All Proposals",
    description="List all action proposals with optional status filter",
    responses={
        200: {"description": "Proposals retrieved"}
    }
)
async def list_proposals(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100)
) -> Dict[str, Any]:
    """List all action proposals."""
    proposals = list(_proposals.values())
    
    if status:
        proposals = [p for p in proposals if p["status"] == status]
    
    # Sort by created_at descending
    proposals.sort(key=lambda p: p.get("created_at", datetime.min), reverse=True)
    
    return {
        "proposals": proposals[:limit],
        "total": len(proposals)
    }
