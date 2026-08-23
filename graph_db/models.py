"""
Pydantic Schemas for Geospatial & Graph Prediction Engine
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time

class MuleGeoEvent(BaseModel):
    """
    Standard schema for flagged suspicious transactions/accounts sent from AI Engine / Backend.
    """
    account_number: str = Field(..., description="Flagged mule account identifier")
    lat: float = Field(..., description="Latitude of the transaction or account origin")
    lon: float = Field(..., description="Longitude of the transaction or account origin")
    amount: float = Field(default=0.0, ge=0.0, description="Amount in INR involved in the suspicious flow")
    fraud_probability: float = Field(default=0.9, ge=0.0, le=1.0, description="AI fraud score (0.0 - 1.0)")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of the event")

class ATMLocation(BaseModel):
    """
    Physical ATM / AePS kiosk location model.
    """
    atm_id: str = Field(..., description="Unique ATM / Kiosk identifier")
    bank_name: str = Field(..., description="Bank or white-label operator name")
    lat: float = Field(..., description="Latitude of the ATM")
    lon: float = Field(..., description="Longitude of the ATM")
    address: Optional[str] = Field(None, description="Street / locality address")
    h3_res9: Optional[str] = Field(None, description="H3 Res 9 index of ATM location")
    distance_meters: Optional[float] = Field(None, description="Calculated distance from cluster center in meters")
    withdrawal_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Target probability score")

class GeoJSONPolygon(BaseModel):
    """
    Standard GeoJSON Polygon geometry for frontend map rendering.
    """
    type: str = "Polygon"
    coordinates: List[List[List[float]]]  # [[[lon, lat], [lon, lat], ...]]

class CashoutHotspot(BaseModel):
    """
    High-value tactical output schema sent to police command dashboard.
    """
    cluster_id: str
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, or LOW")
    center_lat: float
    center_lon: float
    h3_res8: str = Field(..., description="Neighborhood H3 cell (Res 8)")
    h3_res9: str = Field(..., description="ATM strip H3 cell (Res 9)")
    h3_boundary: GeoJSONPolygon = Field(..., description="Polygon boundary for Mapbox/Leaflet")
    mule_count: int = Field(..., ge=1, description="Number of flagged accounts in cluster")
    mule_accounts: List[str] = Field(default_factory=list)
    total_funds_at_risk: float = Field(..., ge=0.0, description="Sum of funds across accounts in INR")
    aggregate_risk_score: float = Field(..., ge=0.0, le=1.0, description="Combined risk score")
    predicted_cashout_window: str = Field(..., description="Estimated cashout time window (e.g. 'T+0 to T+45 mins')")
    nearest_atms: List[ATMLocation] = Field(default_factory=list, description="Top ranked ATMs by proximity")
    raw_geojson_feature: Optional[Dict[str, Any]] = None
