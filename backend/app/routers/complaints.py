"""
NCRP 1930 Cybercrime Complaints Router
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.app.schemas.complaint import ComplaintPayload, ComplaintResponse
from backend.app.core.stream_orchestrator import orchestrator

router = APIRouter(prefix="/api/v1/complaints", tags=["Complaints"])

@router.post(
    "/ncrp",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest NCRP 1930 Cyber Fraud Complaint"
)
async def ingest_ncrp_complaint(complaint: ComplaintPayload):
    """
    Ingest a 1930 cyber fraud complaint, register the suspect mule account,
    and cross-reference immediately against in-flight transactions.
    """
    try:
        complaint_dict = complaint.model_dump()
        res = await orchestrator.register_complaint(complaint_dict)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register NCRP complaint: {str(e)}"
        )

@router.get(
    "/list",
    summary="List Registered NCRP Complaints"
)
def list_complaints():
    return {
        "status": "SUCCESS",
        "count": len(orchestrator.ncrp_complaints),
        "complaints": list(orchestrator.ncrp_complaints.values())
    }
