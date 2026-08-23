"""
Law Enforcement & Automated Intercept Actions Router
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.app.schemas.action import (
    PatrolDispatchPayload,
    PatrolDispatchResponse,
    FreezeLienPayload,
    FreezeLienResponse,
    IncidentReportPayload,
    IncidentReportResponse
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
            notes=payload.notes or "",
            destination_lat=payload.destination_lat,
            destination_lon=payload.destination_lon
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
            account_numbers=payload.account_numbers,
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

@router.post(
    "/generate-report",
    response_model=IncidentReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Incident Action Report (Evidence Summary)"
)
def generate_incident_report(payload: IncidentReportPayload):
    """
    Compiles active victim complaints, suspect transactions, geospatial ATM clusters,
    and executed CAD patrols/banking liens into a structured incident report.
    """
    try:
        report = orchestrator.generate_incident_report(
            hotspot_id=payload.hotspot_id,
            complaint_id=payload.complaint_id,
            format_type=payload.format,
            include_map_coordinates=payload.include_map_coordinates
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
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

@router.get(
    "/trace/{account_no}",
    summary="Multi-Hop Money Mule Flow Trace"
)
def get_graph_trace(account_no: str):
    """
    Returns a multi-hop money flow tree (Layer 1 -> Layer 2 -> Terminal ATM).
    """
    # Placeholder for actual Neo4j / NetworkX graph traversal
    import random
    return {
        "status": "SUCCESS",
        "account_no": account_no,
        "trace": [
            {
                "hop": 1,
                "layer": "Victim / Source",
                "account": f"ACC_VICTIM_{random.randint(100, 999)}",
                "amount_transferred": random.randint(50000, 200000)
            },
            {
                "hop": 2,
                "layer": "Layer-1 Mule",
                "account": account_no,
                "amount_transferred": random.randint(50000, 200000)
            },
            {
                "hop": 3,
                "layer": "Terminal Egress / ATM",
                "account": f"ATM_{random.randint(100, 999)}",
                "cashout_location": {
                    "lat": 28.6304,
                    "lon": 77.2773
                }
            }
        ]
    }

