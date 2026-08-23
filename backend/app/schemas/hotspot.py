"""
Hotspot Response Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Union

class CashoutTimeWindow(BaseModel):
    start_time: str
    end_time: str
    eta_minutes: int = 25

class HotspotModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    h3_cell: Optional[str] = Field(default="8860145b59fffff", description="Uber H3 Hexagonal Cell identifier")
    lat: Optional[float] = Field(default=28.6304, description="Latitude coordinate center")
    lon: Optional[float] = Field(default=77.2773, description="Longitude coordinate center")
    risk_score: Optional[float] = Field(default=0.85, description="Aggregated risk score (0.0 to 1.0)")
    event_count: Optional[int] = Field(default=1, description="Number of flagged transactions in this cluster")
    total_amount: Optional[float] = Field(default=0.0, description="Total in-flight risk amount in INR")
    polygon_coordinates: Optional[List[List[float]]] = Field(
        default_factory=list,
        description="Boundary polygon vertex coordinates [[lat, lon], ...] for Leaflet map rendering"
    )
    predicted_cashout_window: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="Predicted cash-out window"
    )
    resolution: Optional[int] = Field(default=8, description="Uber H3 resolution level")
    unique_mule_accounts: Optional[int] = Field(default=0, description="Count of converging suspect mule accounts")
    nearby_atms: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Target ATM cash-out points")

class HotspotsResponse(BaseModel):
    status: str = "SUCCESS"
    count: int
    hotspots: List[HotspotModel]
