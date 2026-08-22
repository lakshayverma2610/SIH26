"""
Law Enforcement & Automated Response Action Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional

class PatrolDispatchPayload(BaseModel):
    h3_cell: str = Field(..., description="Target Uber H3 Hexagonal Cell Identifier (e.g. 8860145b59fffff)")
    patrol_unit_id: Optional[str] = Field(default=None, description="Assigned PCR / Cyber Patrol Unit ID")
    priority: Optional[str] = Field(default="HIGH", description="Dispatch Priority (HIGH, CRITICAL, MEDIUM)")
    notes: Optional[str] = Field(default="Automated tactical intercept near flagged ATM hotspot.", description="Dispatch notes")

class PatrolDispatchResponse(BaseModel):
    status: str = "DISPATCHED"
    h3_cell: str
    cad_call_id: str
    patrol_unit_id: str
    priority: str
    message: str
    timestamp: float

class FreezeLienPayload(BaseModel):
    account_number: str = Field(..., description="Target Suspect Mule Account Number")
    system: Optional[str] = Field(default="CFCFRMS-1930", description="Reporting / Lien Freeze System")
    reason: Optional[str] = Field(default="Automated AI Mule Risk Threshold Exceeded (>0.70) / NCRP 1930 Match", description="Legal/Analytical justification")
    freeze_amount: Optional[float] = Field(default=None, description="Amount to freeze/lien (INR), or full debit lock if null")

class FreezeLienResponse(BaseModel):
    status: str = "LIEN_PLACED"
    account_number: str
    system: str
    lien_id: str
    message: str
    timestamp: float
