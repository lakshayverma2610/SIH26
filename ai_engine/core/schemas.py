from typing import Optional, List
from pydantic import BaseModel, Field
import time

class TransactionEvent(BaseModel):
    """
    Strict schema representing an incoming transaction event.
    """
    tx_id: str = Field(..., description="Unique transaction identifier")
    src_acc: str = Field(..., description="Source account identifier")
    dest_acc: str = Field(..., description="Destination account identifier")
    amount: float = Field(..., ge=0, description="Transaction amount in INR")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of the transaction")
    channel: str = Field(default="UPI", description="Payment channel used")
    device_id: Optional[str] = Field(None, description="Device fingerprint ID")
    ip_address: Optional[str] = Field(None, description="Originating IP address")

class AccountMetadata(BaseModel):
    """
    Strict schema representing cached account profile data.
    """
    account_id: str = Field(..., description="Account identifier")
    dormant_days: int = Field(0, ge=0, description="Days since last activity prior to today")
    kyc_verified: bool = Field(True, description="Indicates if KYC is fully complete")

class ExtractedFeatures(BaseModel):
    """
    Strict schema representing the computed features for ML inference.
    """
    tx_id: str
    amount: float
    v1_out: int = Field(..., description="Outbound velocity in last 1 minute")
    v5_out: int = Field(..., description="Outbound velocity in last 5 minutes")
    v1_in: int = Field(..., description="Inbound velocity in last 1 minute")
    fan_out_degree: int = Field(..., description="Distinct destination accounts in last 3 minutes")
    dormancy_break: int = Field(..., description="Binary flag (1 or 0) for dormancy disruption")
    kyc_risk: int = Field(..., description="Binary flag (1 or 0) for KYC risk")
    device_reuse_count: int = Field(..., description="Number of distinct accounts using this device")
    ip_reuse_count: int = Field(..., description="Number of distinct accounts using this IP")

class InferenceResult(BaseModel):
    """
    Strict schema representing the final AI Engine output.
    """
    tx_id: str
    fraud_probability: float = Field(..., ge=0.0, le=1.0)
    is_high_risk: bool
    reasons: List[str] = Field(default_factory=list)
