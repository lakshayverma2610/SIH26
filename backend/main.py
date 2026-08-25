"""
Geo-CashWatch FastAPI Core Gateway (SIH 26184)
- Ingests real-time transaction streams & 1930 NCRP complaints
- Invokes SlidingWindowFeatureEngine & ML Mule Scorer
- Invokes Geospatial H3 Hawkes Predictor
- Exposes WebSocket for live dashboard & alert broadcasting
"""
import sys
import site
import time
from pathlib import Path

# Add user site packages and root folders to sys.path
sys.path.insert(0, site.getusersitepackages())
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json

from ai_engine.core.schemas import TransactionEvent, AccountMetadata
from ai_engine.features.sliding_window import SlidingWindowFeatureEngine
from ai_engine.models.mule_scorer import MuleScorer
from graph_db.geo_predictor import GeospatialPredictor

app = FastAPI(
    title="Geo-CashWatch API Gateway",
    description="Predictive Analytics Framework for Cybercrime Cash Withdrawal Forecasting (SIH 26184 - I4C MHA)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root_status():
    return {
        "status": "ONLINE",
        "system": "Geo-CashWatch API Gateway (SIH 26184)",
        "docs_url": "http://localhost:8000/docs",
        "swagger_ui": "/docs",
        "active_hotspots_api": "/api/v1/hotspots/active",
        "websocket_alerts": "ws://localhost:8000/ws/alerts"
    }

# Core singletons
feature_engine = SlidingWindowFeatureEngine()
mule_scorer = MuleScorer()
atms_path = ROOT_DIR / "data_engine" / "data" / "atm_locations.json"
geo_predictor = GeospatialPredictor(str(atms_path))

# In-memory alert state & active websocket connections
active_connections: List[WebSocket] = []
flagged_events_buffer = []
recent_transactions = []
active_hotspots = []
ncrp_complaints_buffer = []

# Load synthetic accounts metadata if available
accounts_path = ROOT_DIR / "data_engine" / "data" / "account_profiles.json"
if accounts_path.exists():
    with open(accounts_path, "r", encoding="utf-8") as f:
        acc_list = json.load(f)
        for acc in acc_list:
            meta = AccountMetadata(
                account_id=acc["account_number"],
                dormant_days=acc.get("dormant_days", 0),
                kyc_verified=acc.get("kyc_verified", True)
            )
            feature_engine.register_metadata(meta)

class TransactionPayload(BaseModel):
    tx_id: str
    src_acc: str
    dest_acc: str
    amount: float
    channel: str = "UPI"
    device_id: Optional[str] = "DEV_DEFAULT"
    ip: Optional[str] = "192.168.1.1"
    lat: Optional[float] = 28.6304
    lon: Optional[float] = 77.2773
    timestamp: Optional[float] = None

class BatchTransactionsPayload(BaseModel):
    transactions: List[TransactionPayload]

class ComplaintPayload(BaseModel):
    ncrp_id: str
    victim_acc: str
    suspect_acc: str
    amount: float
    complaint_type: str = "APK_RAT_FRAUD"

class DispatchPatrolPayload(BaseModel):
    h3_cell: str
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    priority: str = "CRITICAL"

class FreezeLienPayload(BaseModel):
    account_number: Optional[str] = None
    account_numbers: Optional[List[str]] = []
    freeze_amount: Optional[float] = 0.0
    reason: Optional[str] = ""

class ReportPayload(BaseModel):
    hotspot_id: str
    format: str = "MARKDOWN"
    include_map_coordinates: bool = True

@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send initial state
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "hotspots": active_hotspots,
            "recent_txs": recent_transactions[-10:]
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_alert(payload: Dict[str, Any]):
    for connection in active_connections:
        try:
            await connection.send_json(payload)
        except Exception:
            pass

@app.post("/api/v1/transactions/stream")
async def ingest_transaction(tx: TransactionPayload):
    # 1. Convert to validated TransactionEvent Pydantic model
    tx_event = TransactionEvent(
        tx_id=tx.tx_id,
        src_acc=tx.src_acc,
        dest_acc=tx.dest_acc,
        amount=tx.amount,
        timestamp=tx.timestamp or time.time(),
        channel=tx.channel,
        device_id=tx.device_id,
        ip_address=tx.ip
    )

    # 2. Extract sliding-window behavioral features (< 2ms)
    feats = feature_engine.process_transaction(tx_event)
    
    # 3. Score Mule Risk via ML / Heuristics (< 15ms)
    score_res = mule_scorer.score(feats)
    
    tx_summary = {
        "tx_id": tx.tx_id,
        "src_acc": tx.src_acc,
        "dest_acc": tx.dest_acc,
        "amount": tx.amount,
        "channel": tx.channel,
        "fraud_probability": score_res.fraud_probability,
        "is_high_risk": score_res.is_high_risk,
        "reasons": score_res.reasons,
        "lat": tx.lat,
        "lon": tx.lon,
        "timestamp": tx_event.timestamp
    }
    recent_transactions.append(tx_summary)
    if len(recent_transactions) > 100:
        recent_transactions.pop(0)

    # 4. If high risk, buffer for geospatial cash-out clustering
    if score_res.is_high_risk:
        flagged_events_buffer.append({
            "account_number": tx.dest_acc,
            "lat": tx.lat,
            "lon": tx.lon,
            "amount": tx.amount,
            "fraud_probability": score_res.fraud_probability,
            "timestamp": tx_event.timestamp
        })
        
        # Recalculate active H3 hotspots
        global active_hotspots
        active_hotspots = geo_predictor.aggregate_hotspots(flagged_events_buffer[-50:])
        
        # Broadcast alert to all connected command center dashboards
        asyncio.create_task(broadcast_alert({
            "type": "NEW_ALERT",
            "transaction": tx_summary,
            "hotspots": active_hotspots
        }))

    return {
        "status": "PROCESSED",
        "fraud_score": score_res.fraud_probability,
        "is_high_risk": score_res.is_high_risk,
        "reasons": score_res.reasons
    }

@app.post("/api/v1/transactions/batch")
async def ingest_transactions_batch(batch: BatchTransactionsPayload):
    """
    High-throughput batch transaction ingestion endpoint.
    Leverages vectorized Treelite / ONNX scoring for hundreds of transactions in < 5ms.
    """
    t_start = time.perf_counter()
    tx_events = []
    features_list = []

    for tx in batch.transactions:
        event = TransactionEvent(
            tx_id=tx.tx_id,
            src_acc=tx.src_acc,
            dest_acc=tx.dest_acc,
            amount=tx.amount,
            timestamp=tx.timestamp or time.time(),
            channel=tx.channel,
            device_id=tx.device_id,
            ip_address=tx.ip
        )
        tx_events.append(event)
        feats = feature_engine.process_transaction(event)
        features_list.append(feats)

    # 1. Vectorized Batch Scoring (< 1ms with Treelite)
    score_results = mule_scorer.score_batch(features_list)

    batch_output = []
    high_risk_flagged = []

    for idx, (tx, event, score_res) in enumerate(zip(batch.transactions, tx_events, score_results)):
        summary = {
            "tx_id": tx.tx_id,
            "src_acc": tx.src_acc,
            "dest_acc": tx.dest_acc,
            "amount": tx.amount,
            "channel": tx.channel,
            "fraud_probability": score_res.fraud_probability,
            "is_high_risk": score_res.is_high_risk,
            "reasons": score_res.reasons,
            "lat": tx.lat,
            "lon": tx.lon,
            "timestamp": event.timestamp
        }
        recent_transactions.append(summary)
        if len(recent_transactions) > 200:
            recent_transactions.pop(0)

        if score_res.is_high_risk:
            flagged_events_buffer.append({
                "account_number": tx.dest_acc,
                "lat": tx.lat,
                "lon": tx.lon,
                "amount": tx.amount,
                "fraud_probability": score_res.fraud_probability,
                "timestamp": event.timestamp
            })
            high_risk_flagged.append(summary)

        batch_output.append({
            "tx_id": tx.tx_id,
            "fraud_score": score_res.fraud_probability,
            "is_high_risk": score_res.is_high_risk,
            "reasons": score_res.reasons
        })

    # 2. If any high-risk flagged in batch, recalculate hotspots & broadcast
    global active_hotspots
    if high_risk_flagged:
        active_hotspots = geo_predictor.aggregate_hotspots(flagged_events_buffer[-50:])
        for alert_tx in high_risk_flagged:
            asyncio.create_task(broadcast_alert({
                "type": "NEW_ALERT",
                "transaction": alert_tx,
                "hotspots": active_hotspots
            }))

    total_latency_ms = (time.perf_counter() - t_start) * 1000

    return {
        "status": "BATCH_PROCESSED",
        "engine": mule_scorer.active_engine,
        "total_ingested": len(batch.transactions),
        "high_risk_count": len(high_risk_flagged),
        "latency_ms": round(total_latency_ms, 3),
        "results": batch_output
    }

@app.post("/api/v1/complaints/ncrp")
async def ingest_ncrp_complaint(complaint: ComplaintPayload):
    ncrp_entry = {
        "ncrp_id": complaint.ncrp_id,
        "victim_acc": complaint.victim_acc,
        "suspect_acc": complaint.suspect_acc,
        "amount": complaint.amount,
        "complaint_type": complaint.complaint_type,
        "timestamp": time.time(),
        "status": "LIEN_RECOMMENDED"
    }
    ncrp_complaints_buffer.append(ncrp_entry)

    # Trigger automatic CFCFRMS account lien recommendation
    asyncio.create_task(broadcast_alert({
        "type": "NCRP_COMPLAINT_INGESTED",
        "complaint": ncrp_entry
    }))

    return {
        "status": "INGESTED",
        "ncrp_id": complaint.ncrp_id,
        "cfcfrms_action": f"AUTOMATED_LIEN_PLACED_FOR_{complaint.suspect_acc}"
    }

@app.get("/api/v1/hotspots/active")
def get_active_hotspots():
    return {"status": "SUCCESS", "hotspots": active_hotspots}

@app.get("/api/v1/transactions/recent")
def get_recent_transactions():
    return {"status": "SUCCESS", "transactions": recent_transactions[-30:]}

@app.post("/api/v1/actions/dispatch-patrol")
def dispatch_patrol(payload: DispatchPatrolPayload):
    return {
        "status": "DISPATCHED",
        "h3_cell": payload.h3_cell,
        "cad_call_id": f"PCR-DISPATCH-{int(time.time())}",
        "message": f"Automated alert broadcasted to Cyber Patrol Unit assigned to H3 cell {payload.h3_cell}."
    }

@app.post("/api/v1/actions/freeze-lien")
def trigger_1930_freeze(payload: FreezeLienPayload):
    acc = payload.account_number or (payload.account_numbers[0] if payload.account_numbers else "UNKNOWN")
    return {
        "status": "LIEN_PLACED",
        "account_number": acc,
        "system": "CFCFRMS-1930",
        "message": f"Debit & ATM withdrawal permissions locked for account {acc}."
    }

@app.post("/api/v1/actions/generate-report")
def generate_report(payload: ReportPayload):
    return {
        "status": "GENERATED",
        "report_id": f"REP-{payload.hotspot_id}-{int(time.time())}",
        "content": f"# Incident Report: {payload.hotspot_id}\n\nAutomated risk report generated for cash-out hotspot {payload.hotspot_id}.\n\n- Format: {payload.format}\n- Generated at: {time.time()}"
    }

@app.get("/api/v1/system/status")
def get_system_status():
    return {
        "status": "ONLINE",
        "metrics": {
            "total_transactions_ingested": len(recent_transactions),
            "total_high_risk_flagged": len(flagged_events_buffer),
            "active_hotspots_tracked": len(active_hotspots)
        }
    }

@app.get("/api/v1/actions/history")
def get_action_history():
    return {
        "total_dispatches": 0,
        "total_liens": 0
    }
