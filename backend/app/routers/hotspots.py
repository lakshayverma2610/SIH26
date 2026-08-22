"""
Geospatial Hotspots & ATM Cash-Out Zones Router
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.app.schemas.hotspot import HotspotsResponse, HotspotModel
from backend.app.core.stream_orchestrator import orchestrator

router = APIRouter(prefix="/api/v1/hotspots", tags=["Hotspots"])

@router.get(
    "/active",
    summary="Get Active Predicted Cash-Out Hotspots"
)
def get_active_hotspots():
    """
    Returns the current list of active geospatial H3 cash-out prediction hotspots
    aggregated from high-risk mule transactions.
    """
    hotspots = orchestrator.active_hotspots
    return {
        "status": "SUCCESS",
        "count": len(hotspots),
        "hotspots": hotspots
    }

@router.get(
    "/{h3_cell}",
    summary="Get Specific Hotspot Details"
)
def get_hotspot_by_cell(h3_cell: str):
    for hs in orchestrator.active_hotspots:
        if hs.get("h3_cell") == h3_cell:
            return {"status": "SUCCESS", "hotspot": hs}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Hotspot with H3 cell {h3_cell} not found."
    )
