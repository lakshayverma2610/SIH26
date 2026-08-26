"""
SQLAlchemy ORM Models for Geo-CashWatch Enterprise Architecture
Persists Bank Accounts, Transactions, H3 Mule Clusters, Dispatches, Liens, and NCRP Complaints.
"""
from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class AccountProfileModel(Base):
    """
    Core Banking System (CBS) Customer & Account Master Record.
    """
    __tablename__ = "cbs_account_profiles"

    account_number = Column(String(64), primary_key=True, index=True)
    bank_code = Column(String(32), default="SBI", index=True)
    ifsc_prefix = Column(String(16), default="SBIN000")
    kyc_verified = Column(Boolean, default=True)
    dormant_days = Column(Integer, default=0)
    risk_rating = Column(String(32), default="LOW")
    active_lien = Column(Boolean, default=False)
    lien_amount = Column(Float, default=0.0)
    device_id = Column(String(128), nullable=True, index=True)
    ip_address = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class TransactionRecordModel(Base):
    """
    Real-Time Ingested Banking Transaction Record with AI Fraud Scoring Metadata.
    """
    __tablename__ = "banking_transactions"

    tx_id = Column(String(128), primary_key=True, index=True)
    src_acc = Column(String(64), index=True, nullable=False)
    dest_acc = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    channel = Column(String(32), default="UPI", index=True)
    timestamp = Column(Float, nullable=False, index=True)
    device_id = Column(String(128), nullable=True)
    ip_address = Column(String(64), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)

    # ML & Risk Evaluation Fields
    fraud_probability = Column(Float, default=0.0)
    is_high_risk = Column(Boolean, default=False, index=True)
    reasons = Column(Text, default="[]")  # JSON encoded list of strings
    detection_latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_tx_src_dest", "src_acc", "dest_acc"),
        Index("idx_tx_time_risk", "timestamp", "is_high_risk"),
    )


class HotspotRecordModel(Base):
    """
    Spatio-Temporal Mule Cluster & Predicted ATM Egress Hotspot.
    """
    __tablename__ = "mule_hotspots"

    cluster_id = Column(String(128), primary_key=True, index=True)
    h3_res8 = Column(String(32), index=True)
    h3_res9 = Column(String(32), index=True)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    severity = Column(String(32), default="CRITICAL", index=True)
    mule_count = Column(Integer, default=1)
    mule_accounts = Column(Text, default="[]")  # JSON encoded list of account numbers
    total_funds_at_risk = Column(Float, default=0.0)
    aggregate_risk_score = Column(Float, default=0.95)
    predicted_cashout_window = Column(String(128), default="T+0 to T+30 mins")
    nearest_atms_json = Column(Text, default="[]")  # JSON encoded list of target ATMs
    status = Column(String(32), default="ACTIVE", index=True)  # ACTIVE, DISPATCHED, RESOLVED, LIENED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PoliceDispatchRecordModel(Base):
    """
    Law Enforcement Police Control Room (PCR) / ERSS 112 CAD Dispatch Log.
    """
    __tablename__ = "police_dispatches"

    dispatch_id = Column(String(128), primary_key=True, index=True)
    cad_call_id = Column(String(128), unique=True, index=True)
    h3_cell = Column(String(32), index=True)
    target_atm_name = Column(String(256), nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lon = Column(Float, nullable=True)
    priority = Column(String(32), default="CRITICAL")
    assigned_pcr_unit = Column(String(64), default="PCR_PATROL_LEO_01")
    cad_transmission_status = Column(String(32), default="DISPATCHED")  # DISPATCHED, ACKNOWLEDGED, ARRIVED, RESOLVED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class LienActionRecordModel(Base):
    """
    I4C CFCFRMS 1930 Account Lien / Freeze Action Audit Trail.
    """
    __tablename__ = "cfcfrms_lien_actions"

    lien_id = Column(String(128), primary_key=True, index=True)
    cfcfrms_ack_ref = Column(String(128), index=True)
    account_number = Column(String(64), index=True, nullable=False)
    bank_code = Column(String(32), default="SBI")
    requested_amount = Column(Float, default=0.0)
    actual_frozen_amount = Column(Float, default=0.0)
    status = Column(String(32), default="LIEN_PLACED")  # PENDING, LIEN_PLACED, FAILED, RELEASED
    response_payload = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class NCRPComplaintModel(Base):
    """
    National Cyber Crime Reporting Portal (NCRP) 1930 Citizen Incident Complaint.
    """
    __tablename__ = "ncrp_citizen_complaints"

    ncrp_ack_number = Column(String(64), primary_key=True, index=True)
    victim_account = Column(String(64), index=True, nullable=False)
    suspect_layer1_account = Column(String(64), index=True, nullable=False)
    reported_loss_amount = Column(Float, nullable=False)
    crime_category = Column(String(64), default="APK_RAT_FRAUD", index=True)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="INVESTIGATING")  # INVESTIGATING, LIEN_PLACED, RECOVERED, CLOSED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
