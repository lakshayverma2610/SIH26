"""
Law Enforcement & Automated Response Action Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PatrolDispatchPayload(BaseModel):
    h3_cell: str = Field(..., description="Target Uber H3 Hexagonal Cell Identifier (e.g. 8860145b59fffff)")
    patrol_unit_id: Optional[str] = Field(default=None, description="Assigned PCR / Cyber Patrol Unit ID")
    destination_lat: Optional[float] = Field(default=None, description="Target destination latitude")
    destination_lon: Optional[float] = Field(default=None, description="Target destination longitude")
    priority: Optional[str] = Field(default="HIGH", description="Dispatch Priority (HIGH, CRITICAL, MEDIUM)")
    notes: Optional[str] = Field(default="Automated tactical intercept near flagged ATM hotspot.", description="Dispatch notes")

class PatrolDispatchResponse(BaseModel):
    status: str = "DISPATCHED"
    h3_cell: str
    cad_call_id: str
    patrol_unit_id: str
    priority: str
    destination: Optional[Dict[str, float]] = Field(default=None, description="Target destination coordinates")
    google_maps_url: Optional[str] = Field(default=None, description="Dynamic Google Maps navigation link for CAD patrol dispatch")
    message: str
    timestamp: float

class FreezeLienPayload(BaseModel):
    account_number: Optional[str] = Field(default=None, description="Target Suspect Mule Account Number")
    account_numbers: Optional[List[str]] = Field(default=None, description="List of suspect mule accounts for batch freeze")
    system: Optional[str] = Field(default="CFCFRMS-1930", description="Reporting / Lien Freeze System")
    reason: Optional[str] = Field(default="Automated AI Mule Risk Threshold Exceeded (>0.70) / NCRP 1930 Match", description="Legal/Analytical justification")
    freeze_amount: Optional[float] = Field(default=None, description="Amount to freeze/lien (INR), or full debit lock if null")

class FreezeLienResponse(BaseModel):
    status: str = "LIEN_PLACED"
    account_number: Optional[str] = Field(default=None, description="Primary frozen account")
    accounts_affected: Optional[List[str]] = Field(default_factory=list, description="List of all accounts frozen in batch")
    atm_daily_limit: Optional[str] = Field(default="₹0.00", description="Reduced ATM daily limit")
    system: str
    lien_id: str
    message: str
    timestamp: float

class IncidentReportPayload(BaseModel):
    hotspot_id: Optional[str] = Field(default=None, description="Associated Hotspot / H3 Cell ID")
    complaint_id: Optional[str] = Field(default=None, description="Associated 1930 NCRP Complaint ID")
    format: str = Field(default="MARKDOWN", description="Output format: MARKDOWN or PDF")
    include_map_coordinates: bool = Field(default=True, description="Include ATM/cluster geo coordinates")

class IncidentReportResponse(BaseModel):
    status: str = "GENERATED"
    report_id: str
    format: str
    title: str
    content: str
    summary_stats: Optional[Dict[str, Any]] = None
    timestamp: float
