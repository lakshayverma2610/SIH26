"""
Hotspot Response Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CashoutTimeWindow(BaseModel):
    start_time: str
    end_time: str
    eta_minutes: int = 25

class HotspotModel(BaseModel):
    h3_cell: str = Field(..., description="Uber H3 Hexagonal Cell identifier")
    lat: float = Field(..., description="Latitude coordinate center")
    lon: float = Field(..., description="Longitude coordinate center")
    risk_score: float = Field(..., description="Aggregated risk score (0.0 to 1.0)")
    event_count: int = Field(..., description="Number of flagged transactions in this cluster")
    total_amount: float = Field(..., description="Total in-flight risk amount in INR")
    polygon_coordinates: Optional[List[List[float]]] = Field(
        default_factory=list,
        description="Boundary polygon vertex coordinates [[lat, lon], ...] for Leaflet map rendering"
    )
    predicted_cashout_window: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Predicted cash-out window {'start_time': str, 'end_time': str, 'eta_minutes': int}"
    )
    resolution: Optional[int] = Field(default=8, description="Uber H3 resolution level")
    unique_mule_accounts: Optional[int] = Field(default=0, description="Count of converging suspect mule accounts")
    nearby_atms: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Target ATM cash-out points")

class HotspotsResponse(BaseModel):
    status: str = "SUCCESS"
    count: int
    hotspots: List[HotspotModel]
