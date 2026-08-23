"""
NCRP 1930 Cyber Fraud Complaint Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class ComplaintPayload(BaseModel):
    ncrp_id: str = Field(..., description="NCRP / National Cyber Crime Reporting Portal Acknowledgement No.")
    victim_acc: str = Field(..., description="Victim Bank Account / UPI handle")
    suspect_acc: str = Field(..., description="Suspect / Immediate Layer 1 Mule Account")
    amount: float = Field(..., ge=0.0, description="Defrauded Amount in INR")
    complaint_type: str = Field(default="APK_RAT_FRAUD", description="Type of Fraud (APK_RAT_FRAUD, INVESTMENT_SCAM, DIGITAL_ARREST, SEXTORTION, KYC_FRAUD)")
    description: Optional[str] = Field(default=None, description="Complaint incident narrative")
    timestamp: Optional[float] = Field(default=None, description="Epoch timestamp when complaint was lodged")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ncrp_id": "NCRP-2026-9812450",
                "victim_acc": "ACC_VICTIM_404",
                "suspect_acc": "ACC_MULE_999",
                "amount": 150000.0,
                "complaint_type": "DIGITAL_ARREST",
                "description": "Victim coerced into transferring funds under threat of arrest."
            }
        }
    )

class ComplaintResponse(BaseModel):
    status: str = "REGISTERED"
    ncrp_id: str
    suspect_acc: str
    amount: float
    complaint_type: str
    action_recommended: str
    timestamp: float
