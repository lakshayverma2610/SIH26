"""
Law Enforcement & Automated Intercept Actions Router
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.app.schemas.action import (
    PatrolDispatchPayload,
    PatrolDispatchResponse,
    FreezeLienPayload,
    FreezeLienResponse
)
from backend.app.core.stream_orchestrator import orchestrator

router = APIRouter(prefix="/api/v1/actions", tags=["Actions"])

@router.post(
    "/dispatch-patrol",
    response_model=PatrolDispatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispatch PCR / Cyber Patrol to H3 Hotspot"
)
async def dispatch_patrol(payload: PatrolDispatchPayload):
    """
    Triggers automated Computer-Aided Dispatch (CAD) alert to the nearest
    Cyber Patrol Unit for tactical ATM interception.
    """
    try:
        record = await orchestrator.dispatch_patrol(
            h3_cell=payload.h3_cell,
            unit_id=payload.patrol_unit_id,
            priority=payload.priority or "HIGH",
            notes=payload.notes or ""
        )
        return record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patrol dispatch failed: {str(e)}"
        )

@router.post(
    "/freeze-lien",
    response_model=FreezeLienResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Automated CFCFRMS 1930 Debit Freeze / Lien"
)
async def freeze_lien(payload: FreezeLienPayload):
    """
    Places an automated debit freeze and lien across banking switches for a suspect mule account.
    """
    try:
        record = await orchestrator.freeze_lien(
            account_no=payload.account_number,
            system=payload.system or "CFCFRMS-1930",
            reason=payload.reason or "",
            amount=payload.freeze_amount
        )
        return record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lien placement failed: {str(e)}"
        )

@router.get(
    "/history",
    summary="Fetch Action Audit History"
)
def get_action_history():
    """
    Returns audit log of all patrol dispatches and lien freezes placed.
    """
    return {
        "status": "SUCCESS",
        "total_dispatches": len(orchestrator.dispatched_patrols),
        "total_liens": len(orchestrator.placed_liens),
        "dispatches": orchestrator.dispatched_patrols,
        "liens": orchestrator.placed_liens
    }
