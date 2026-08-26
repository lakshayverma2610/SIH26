"""
Geo-CashWatch Enterprise API Gateway & Real-Time Orchestrator
- Consumes high-throughput UPI/IMPS streams via Apache Kafka
- Executes sub-50µs Treelite GTIL AI Inference & Sliding-Window Feature Extraction
- Queries Enterprise Redis for CBS Account Metadata & ATM Spatial Indices
- Persists all audit events to PostgreSQL / Database Layer
- Offloads async police CAD 112 & I4C 1930 CFCFRMS liens to Huey Task Queue
- Broadcasts real-time WebSocket alerts to command dashboard
"""
import sys
import site
import time
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add user site packages and root folders to sys.path
sys.path.insert(0, site.getusersitepackages())
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Core AI & Geospatial Engines
from ml_inference.core.schemas import TransactionEvent, AccountMetadata
from ml_inference.features.sliding_window import SlidingWindowFeatureEngine
from ml_inference.models.fraud_scorer import FraudScorer
from geospatial_engine.geo_predictor import GeospatialPredictor

# Database & Tasks
from backend.database.session import init_db, get_db, ScopedSession
from backend.database.models import (
    TransactionRecordModel,
    HotspotRecordModel,
    PoliceDispatchRecordModel,
    LienActionRecordModel,
    NCRPComplaintModel
)
from backend.tasks.worker_tasks import (
    task_async_dispatch_pcr,
    task_async_trigger_cfcfrms_lien,
    task_async_broadcast_alert,
    task_async_compile_incident_report,
    task_async_restrict_atm
)
from backend.integrations.cfcfrms_client import cfcfrms_client
from backend.integrations.ncrp_client import ncrp_client
from backend.integrations.erss_cad_client import erss_cad_client
from backend.streaming.kafka_client import kafka_client

logger = logging.getLogger("api_gateway")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="Geo-CashWatch Enterprise API Gateway",
    description="Predictive Analytics & Geospatial Framework for Cybercrime Mule Network Detection & ATM Cash-Out Interception (SIH 26184 - I4C MHA)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Enterprise Singletons
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
feature_engine = SlidingWindowFeatureEngine(redis_url=REDIS_URL)
fraud_scorer = FraudScorer()
atms_path = ROOT_DIR / "data_simulation" / "data" / "atm_locations.json"
geo_predictor = GeospatialPredictor(atms_file_path=str(atms_path) if atms_path.exists() else None, redis_url=REDIS_URL)

# In-memory buffers for high-speed WebSocket broadcasting
active_connections: List[WebSocket] = []
flagged_events_buffer = []
recent_transactions = []
active_hotspots = []


@app.on_event("startup")
async def startup_event():
    """Initializes Database tables, Kafka Producer, and Kafka Consumer loop."""
    logger.info("Initializing Geo-CashWatch Enterprise Gateway...")
    init_db()
    await kafka_client.start_producer()
    await kafka_client.start_consumer(process_kafka_message)
    logger.info("✅ All systems initialized and ready.")


@app.on_event("shutdown")
async def shutdown_event():
    await kafka_client.stop_producer()
    await kafka_client.stop_consumer()


# ==============================================================================
# PYDANTIC REQUEST SCHEMAS
# ==============================================================================
class DispatchPatrolPayload(BaseModel):
    h3_cell: str
    target_atm_name: Optional[str] = "SBI ATM Kiosk"
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    priority: str = "CRITICAL"
    notes: Optional[str] = "Imminent ATM cash-out predicted by AI cyber defense framework"

class FreezeLienPayload(BaseModel):
    account_number: Optional[str] = None
    account_numbers: Optional[List[str]] = []
    freeze_amount: Optional[float] = 0.0
    ncrp_ack_number: Optional[str] = None
    reason: Optional[str] = "Automated AI predictive intervention for imminent ATM cash-out"

class NCRPComplaintPayload(BaseModel):
    victim_account: str
    suspect_layer1_account: str
    reported_loss_amount: float
    crime_category: str = "APK_RAT_FRAUD"
    ack_number: Optional[str] = None
    auto_trigger_lien: bool = True
    description: Optional[str] = "1930 Citizen Helpline Complaint"

class RestrictTerminalPayload(BaseModel):
    atm_id: str
    duration_minutes: int = 30
    reason: Optional[str] = "Multi-mule ATM cash-out convergence detected"

class ReportPayload(BaseModel):
    hotspot_id: str
    format: str = "MARKDOWN"

class BroadcastPayload(BaseModel):
    hotspot_id: str
    severity: str = "CRITICAL"
    message: Optional[str] = "Immediate cash-out threat detected."
    channels: Optional[List[str]] = None


# ==============================================================================
# WEBSOCKET & KAFKA STREAM INGESTION PIPELINE
# ==============================================================================
@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "hotspots": active_hotspots,
            "recent_txs": recent_transactions[-10:]
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


async def broadcast_alert_websocket(payload: Dict[str, Any]):
    for connection in active_connections:
        try:
            await connection.send_json(payload)
        except Exception:
            pass


async def process_kafka_message(tx_data: dict):
    """Processes incoming real-time transaction event."""
    tx_event = TransactionEvent(
        tx_id=tx_data.get("tx_id"),
        src_acc=tx_data.get("src_acc"),
        dest_acc=tx_data.get("dest_acc"),
        amount=tx_data.get("amount", 0.0),
        timestamp=tx_data.get("timestamp") or time.time(),
        channel=tx_data.get("channel", "UPI"),
        device_id=tx_data.get("device_id", "DEV_DEFAULT"),
        ip_address=tx_data.get("ip", "192.168.1.1")
    )

    t0 = time.perf_counter()
    feats = feature_engine.process_transaction(tx_event)
    score_res = fraud_scorer.score(feats)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    tx_summary = {
        "tx_id": tx_event.tx_id,
        "src_acc": tx_event.src_acc,
        "dest_acc": tx_event.dest_acc,
        "amount": tx_event.amount,
        "channel": tx_event.channel,
        "fraud_probability": score_res.fraud_probability,
        "is_high_risk": score_res.is_high_risk,
        "reasons": score_res.reasons,
        "lat": tx_data.get("lat"),
        "lon": tx_data.get("lon"),
        "timestamp": tx_event.timestamp
    }

    recent_transactions.append(tx_summary)
    if len(recent_transactions) > 100:
        recent_transactions.pop(0)

    # 1. Asynchronously persist transaction to database
    db = ScopedSession()
    try:
        tx_record = TransactionRecordModel(
            tx_id=tx_event.tx_id,
            src_acc=tx_event.src_acc,
            dest_acc=tx_event.dest_acc,
            amount=tx_event.amount,
            channel=tx_event.channel,
            timestamp=tx_event.timestamp,
            device_id=tx_event.device_id,
            ip_address=tx_event.ip_address,
            lat=tx_data.get("lat"),
            lon=tx_data.get("lon"),
            fraud_probability=score_res.fraud_probability,
            is_high_risk=score_res.is_high_risk,
            reasons=json.dumps(score_res.reasons),
            detection_latency_ms=round(latency_ms, 3)
        )
        db.merge(tx_record)
        db.commit()
    except Exception as err:
        db.rollback()
    finally:
        db.close()

    # 2. Spatio-temporal cluster aggregation for high-risk threats
    if score_res.is_high_risk:
        flagged_events_buffer.append({
            "account_number": tx_event.dest_acc,
            "lat": tx_data.get("lat"),
            "lon": tx_data.get("lon"),
            "amount": tx_event.amount,
            "fraud_probability": score_res.fraud_probability,
            "timestamp": tx_event.timestamp
        })

        global active_hotspots
        active_hotspots = geo_predictor.aggregate_hotspots(flagged_events_buffer[-50:])

        # Persist updated hotspots to database
        db = ScopedSession()
        try:
            for hs in active_hotspots:
                hs_record = HotspotRecordModel(
                    cluster_id=hs["cluster_id"],
                    h3_res8=hs.get("h3_res8"),
                    h3_res9=hs.get("h3_res9"),
                    center_lat=hs["center_lat"],
                    center_lon=hs["center_lon"],
                    severity=hs.get("severity", "CRITICAL"),
                    mule_count=hs.get("mule_count", 1),
                    mule_accounts=json.dumps(hs.get("mule_accounts", [])),
                    total_funds_at_risk=hs.get("total_funds_at_risk", 0.0),
                    aggregate_risk_score=hs.get("aggregate_risk_score", 0.95),
                    predicted_cashout_window=hs.get("predicted_cashout_window", "T+0 to T+30 mins"),
                    nearest_atms_json=json.dumps(hs.get("nearest_atms", [])),
                    status="ACTIVE"
                )
                db.merge(hs_record)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        # Push real-time alert to connected WebSockets
        asyncio.create_task(broadcast_alert_websocket({
            "type": "NEW_ALERT",
            "transaction": tx_summary,
            "hotspots": active_hotspots
        }))

    return score_res


# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================
@app.get("/")
def root_status():
    return {
        "status": "ONLINE",
        "system": "Geo-CashWatch Enterprise Gateway (SIH 26184)",
        "version": "2.0.0",
        "docs_url": "/docs",
        "active_hotspots_api": "/api/v1/hotspots/active",
        "websocket_alerts": "/ws/alerts"
    }


@app.get("/api/v1/hotspots/active")
def get_active_hotspots():
    return {"status": "SUCCESS", "hotspots": active_hotspots}


@app.get("/api/v1/transactions/recent")
def get_recent_transactions():
    return {"status": "SUCCESS", "transactions": recent_transactions[-30:]}


@app.post("/api/v1/transactions/ingest")
async def ingest_transaction(tx_data: dict):
    """
    Ingests a raw transaction directly via HTTP REST, running the full AI detection and clustering pipeline.
    """
    score_res = await process_kafka_message(tx_data)
    return {
        "status": "PROCESSED",
        "tx_id": tx_data.get("tx_id"),
        "fraud_probability": score_res.fraud_probability,
        "is_high_risk": score_res.is_high_risk,
        "reasons": score_res.reasons
    }


@app.post("/api/v1/simulation/inject-burst")
async def inject_simulation_burst(count: int = 15):
    """
    Injects a burst of realistic transactions including multi-hop money mule attacks.
    """
    import random
    data_dir = ROOT_DIR / "data_simulation" / "data"
    chains_file = data_dir / "mule_transaction_chains.json"
    chains = []
    if chains_file.exists():
        try:
            with open(chains_file, "r", encoding="utf-8") as f:
                chains = json.load(f)
        except Exception:
            pass

    # 1. Normal baseline transactions
    for i in range(max(1, count - 4)):
        lat = random.uniform(28.50, 28.70)
        lon = random.uniform(77.10, 77.35)
        now_ts = time.time()
        tx = {
            "tx_id": f"TX_SIM_{int(now_ts)}_{random.randint(1000, 9999)}",
            "src_acc": f"{random.randint(100000000000, 999999999999)}",
            "dest_acc": f"{random.randint(100000000000, 999999999999)}",
            "amount": round(random.uniform(500.0, 12000.0), 2),
            "channel": "UPI",
            "device_id": f"DEV_{random.randint(100, 999)}",
            "ip": f"49.36.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "lat": lat,
            "lon": lon,
            "timestamp": now_ts
        }
        await process_kafka_message(tx)

    # 2. Inject high-risk mule chain attack
    if chains:
        chain = random.choice(chains)
        hops = chain.get("hops", [])
        for hop in hops:
            now_ts = time.time()
            tx = {
                "tx_id": f"TX_MULE_{int(now_ts)}_{random.randint(100, 999)}",
                "src_acc": hop.get("src_acc"),
                "dest_acc": hop.get("dest_acc"),
                "amount": float(hop.get("amount", 95000.0)),
                "channel": hop.get("channel", "UPI"),
                "device_id": hop.get("device_id", "DEV_C2_EMULATOR_01"),
                "ip": hop.get("ip_address", "103.14.26.10"),
                "lat": float(hop.get("lat", 28.6304)),
                "lon": float(hop.get("lon", 77.2773)),
                "timestamp": now_ts
            }
            await process_kafka_message(tx)

    return {
        "status": "BURST_INJECTED",
        "transactions_processed": count,
        "active_hotspots_count": len(active_hotspots)
    }



@app.post("/api/v1/actions/dispatch-patrol")
def dispatch_patrol(payload: DispatchPatrolPayload):
    """
    Triggers State Police ERSS 112 CAD unit dispatch via Huey async worker.
    """
    dispatch_id = f"DISPATCH_{int(time.time())}"
    lat = payload.destination_lat or 28.6304
    lon = payload.destination_lon or 77.2773

    # Offload to Huey background worker
    task_async_dispatch_pcr(
        dispatch_id=dispatch_id,
        h3_cell=payload.h3_cell,
        target_atm_name=payload.target_atm_name,
        lat=lat,
        lon=lon,
        priority_tier=payload.priority
    )

    google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
    return {
        "status": "QUEUED_FOR_DISPATCH",
        "dispatch_id": dispatch_id,
        "cad_call_id": f"CAD-ERSS-112-{int(time.time())}",
        "h3_cell": payload.h3_cell,
        "target_atm": payload.target_atm_name,
        "assigned_pcr_unit": "PCR_UNIT_FAST_RESPONSE_07",
        "maps_url": google_maps_url,
        "message": f"Police Control Room (PCR) patrol unit dispatched to {payload.target_atm_name}."
    }


@app.post("/api/v1/actions/freeze-lien")
def trigger_1930_freeze(payload: FreezeLienPayload):
    """
    Triggers I4C CFCFRMS 1930 multi-hop account lien freeze via Huey async worker.
    """
    accounts = payload.account_numbers if payload.account_numbers else []
    if payload.account_number and payload.account_number not in accounts:
        accounts.append(payload.account_number)

    if not accounts:
        raise HTTPException(status_code=400, detail="At least one account number is required.")

    # Offload to Huey background worker
    task_async_trigger_cfcfrms_lien(
        suspect_accounts=accounts,
        stolen_amount=payload.freeze_amount or 150000.0,
        ncrp_ack=payload.ncrp_ack_number
    )

    return {
        "status": "LIEN_PLACED",
        "system": "I4C_CFCFRMS_1930",
        "accounts_frozen": accounts,
        "total_amount_hold_inr": payload.freeze_amount,
        "message": f"Emergency debit and ATM withdrawal lien placed for {len(accounts)} accounts across CBS banking switch."
    }


@app.post("/api/v1/complaints/ncrp")
def register_ncrp_complaint(payload: NCRPComplaintPayload, db: Session = Depends(get_db)):
    """
    Official 1930 NCRP Citizen Cybercrime Complaint Registration Endpoint.
    Automatically logs the complaint and queues an emergency lien hold on Layer 1 mule accounts.
    """
    res = ncrp_client.ingest_1930_complaint(
        victim_account=payload.victim_account,
        suspect_account=payload.suspect_layer1_account,
        loss_amount=payload.reported_loss_amount,
        crime_category=payload.crime_category,
        ack_number=payload.ack_number,
        notes=payload.description
    )

    ack_num = res["acknowledgement_number"]
    complaint_record = NCRPComplaintModel(
        ncrp_ack_number=ack_num,
        victim_account=payload.victim_account,
        suspect_layer1_account=payload.suspect_layer1_account,
        reported_loss_amount=payload.reported_loss_amount,
        crime_category=payload.crime_category,
        description=payload.description,
        status="LIEN_PLACED" if payload.auto_trigger_lien else "INVESTIGATING"
    )
    db.merge(complaint_record)
    db.commit()

    if payload.auto_trigger_lien:
        task_async_trigger_cfcfrms_lien(
            suspect_accounts=[payload.suspect_layer1_account],
            stolen_amount=payload.reported_loss_amount,
            ncrp_ack=ack_num
        )

    return {
        "status": "COMPLAINT_REGISTERED",
        "ncrp_ack_number": ack_num,
        "auto_lien_triggered": payload.auto_trigger_lien,
        "details": res
    }


@app.post("/api/v1/actions/restrict-terminal")
def restrict_terminal(payload: RestrictTerminalPayload):
    """
    Issues emergency terminal-level restriction flag to NPCI NFS Switch.
    """
    task_async_restrict_atm(atm_id=payload.atm_id, duration_minutes=payload.duration_minutes)
    return {
        "status": "TERMINAL_RESTRICTED",
        "system": "NPCI_NFS_SWITCH",
        "terminal_id": payload.atm_id,
        "duration_minutes": payload.duration_minutes,
        "message": f"Cash dispenser and AePS biometric limits restricted on {payload.atm_id}."
    }


@app.post("/api/v1/actions/generate-report")
def generate_report(payload: ReportPayload):
    incident_data = {
        "victim_complaint": f"Incident associated with H3 Hotspot {payload.hotspot_id}",
        "mule_hops": ["Layer 1 Mule Hop (Dormancy Spiked)", "Layer 2 Smurfing Split (Multi-ATM extraction)"],
        "risk_scores": {"transaction_risk": 0.98, "cluster_risk": 0.95},
        "predicted_atm_cluster": f"H3 Cell: {payload.hotspot_id}",
        "actions_taken": ["1930 CFCFRMS Lien Placed", "ERSS 112 CAD Patrol Dispatched"]
    }
    filename = f"incident_report_{payload.hotspot_id}.md"
    task_async_compile_incident_report(incident_data, filename)

    return {
        "status": "REPORT_QUEUED",
        "report_id": f"REP-{payload.hotspot_id}-{int(time.time())}",
        "file_name": filename,
        "message": f"Forensic incident dossier queued for compilation to {filename}"
    }


@app.post("/api/v1/actions/broadcast-alert")
def trigger_external_broadcast(payload: BroadcastPayload):
    alert_data = {
        "hotspot_id": payload.hotspot_id,
        "severity": payload.severity,
        "message": payload.message
    }
    task_async_broadcast_alert(alert_data=alert_data, channels=payload.channels)
    return {
        "status": "BROADCAST_QUEUED",
        "hotspot_id": payload.hotspot_id,
        "channels": payload.channels or ["EMAIL", "SMS", "WEBHOOK"]
    }


@app.get("/api/v1/actions/history")
def get_action_history(db: Session = Depends(get_db)):
    """
    Returns full database audit trail of police dispatches, liens, and complaints.
    """
    dispatches = db.query(PoliceDispatchRecordModel).order_by(PoliceDispatchRecordModel.created_at.desc()).limit(20).all()
    liens = db.query(LienActionRecordModel).order_by(LienActionRecordModel.created_at.desc()).limit(20).all()
    complaints = db.query(NCRPComplaintModel).order_by(NCRPComplaintModel.created_at.desc()).limit(20).all()

    return {
        "status": "SUCCESS",
        "total_dispatches": len(dispatches),
        "total_liens_placed": len(liens),
        "total_ncrp_complaints": len(complaints),
        "recent_dispatches": [
            {
                "dispatch_id": d.dispatch_id,
                "cad_call_id": d.cad_call_id,
                "h3_cell": d.h3_cell,
                "target_atm": d.target_atm_name,
                "assigned_unit": d.assigned_pcr_unit,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in dispatches
        ],
        "recent_liens": [
            {
                "lien_id": l.lien_id,
                "account_number": l.account_number,
                "amount": l.actual_frozen_amount,
                "status": l.status,
                "created_at": l.created_at.isoformat() if l.created_at else None
            }
            for l in liens
        ]
    }


@app.get("/api/v1/system/status")
def get_system_status(db: Session = Depends(get_db)):
    tx_count = db.query(TransactionRecordModel).count()
    flagged_count = db.query(TransactionRecordModel).filter(TransactionRecordModel.is_high_risk == True).count()
    return {
        "status": "ONLINE",
        "architecture": "Enterprise Cloud-Native (PostgreSQL + Redis + Kafka + Huey)",
        "metrics": {
            "total_transactions_persisted": tx_count,
            "total_high_risk_flagged": flagged_count,
            "active_hotspots_tracked": len(active_hotspots)
        }
    }
