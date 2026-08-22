"""
Transaction Payload & Response Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class TransactionPayload(BaseModel):
    tx_id: str = Field(..., description="Unique Transaction ID")
    src_acc: str = Field(..., description="Source Account Number / UPI ID")
    dest_acc: str = Field(..., description="Destination Account Number / Mule Target")
    amount: float = Field(..., ge=0.0, description="Transaction amount in INR")
    channel: str = Field(default="UPI", description="Payment Channel (UPI, IMPS, NEFT, RTGS, AEPS)")
    device_id: Optional[str] = Field(default="DEV_DEFAULT", description="Device Fingerprint Hash")
    ip: Optional[str] = Field(default="192.168.1.1", description="Client IP Address")
    lat: Optional[float] = Field(default=28.6304, description="Latitude of transaction origin")
    lon: Optional[float] = Field(default=77.2773, description="Longitude of transaction origin")
    timestamp: Optional[float] = Field(default=None, description="Epoch timestamp (seconds)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tx_id": "TXN_98234710",
                "src_acc": "ACC_VICTIM_001",
                "dest_acc": "ACC_MULE_999",
                "amount": 49999.0,
                "channel": "UPI",
                "device_id": "DEV_ANDROID_HASH_883",
                "ip": "103.21.14.90",
                "lat": 28.6304,
                "lon": 77.2773
            }
        }
    )

class TransactionBatchPayload(BaseModel):
    transactions: List[TransactionPayload] = Field(..., description="Batch of transactions to ingest")

class TransactionSummary(BaseModel):
    tx_id: str
    src_acc: str
    dest_acc: str
    amount: float
    channel: str
    fraud_probability: float
    is_high_risk: bool
    reasons: List[str]
    lat: Optional[float] = None
    lon: Optional[float] = None
    timestamp: Optional[float] = None

class ProcessedTransactionResponse(BaseModel):
    status: str = "PROCESSED"
    tx_id: str
    fraud_score: float
    is_high_risk: bool
    reasons: List[str]
    features: Optional[Dict[str, float]] = None
