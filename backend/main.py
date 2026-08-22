"""
Geo-CashWatch FastAPI Core Gateway
- Ingests real-time transaction streams & 1930 NCRP complaints
- Invokes Feature Engine & ML Mule Scorer
- Invokes Geospatial H3 Predictor
- Exposes WebSocket for live dashboard & alert broadcasting
"""
import sys
import site
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

from ai_engine.features.sliding_window import SlidingWindowFeatureEngine
from ai_engine.models.mule_scorer import MuleScorer
from graph_db.geo_predictor import GeospatialPredictor

app = FastAPI(
    title="Geo-CashWatch API Gateway",
    description="Predictive Analytics Framework for Cybercrime Cash Withdrawal Forecasting (SIH 26184)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
feature_engine = SlidingWindowFeatureEngine()
mule_scorer = MuleScorer()
atms_path = ROOT_DIR / "mock_data" / "data" / "atms.json"
geo_predictor = GeospatialPredictor(str(atms_path))

# In-memory alert state & active websocket connections
active_connections: List[WebSocket] = []
flagged_events_buffer = []
recent_transactions = []
active_hotspots = []

# Load synthetic accounts metadata if available
accounts_path = ROOT_DIR / "mock_data" / "data" / "accounts.json"
if accounts_path.exists():
    with open(accounts_path, "r", encoding="utf-8") as f:
        acc_list = json.load(f)
        for acc in acc_list:
            feature_engine.register_account_metadata(
                acc["account_number"],
                acc.get("dormant_days", 0),
                acc.get("kyc_verified", True)
            )

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

class ComplaintPayload(BaseModel):
    ncrp_id: str
    victim_acc: str
    suspect_acc: str
    amount: float
    complaint_type: str = "APK_RAT_FRAUD"

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
    tx_dict = tx.dict()
    # 1. Extract sliding-window behavioral features
    feats = feature_engine.process_and_extract(tx_dict)
    
    # 2. Score Mule Risk via ML / Heuristics
    score_res = mule_scorer.score_features(feats)
    
    tx_summary = {
        "tx_id": tx.tx_id,
        "src_acc": tx.src_acc,
        "dest_acc": tx.dest_acc,
        "amount": tx.amount,
        "channel": tx.channel,
        "fraud_probability": score_res["fraud_probability"],
        "is_high_risk": score_res["is_high_risk"],
        "reasons": score_res["reasons"],
        "lat": tx.lat,
        "lon": tx.lon
    }
    recent_transactions.append(tx_summary)
    if len(recent_transactions) > 100:
        recent_transactions.pop(0)

    # 3. If high risk, buffer for geospatial cash-out clustering
    if score_res["is_high_risk"]:
        flagged_events_buffer.append({
            "account_number": tx.dest_acc,
            "lat": tx.lat,
            "lon": tx.lon,
            "amount": tx.amount,
            "fraud_probability": score_res["fraud_probability"]
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
        "fraud_score": score_res["fraud_probability"],
        "is_high_risk": score_res["is_high_risk"]
    }

@app.get("/api/v1/hotspots/active")
def get_active_hotspots():
    return {"status": "SUCCESS", "hotspots": active_hotspots}

@app.get("/api/v1/transactions/recent")
def get_recent_transactions():
    return {"status": "SUCCESS", "transactions": recent_transactions[-30:]}

@app.post("/api/v1/actions/dispatch-patrol")
def dispatch_patrol(h3_cell: str):
    return {
        "status": "DISPATCHED",
        "h3_cell": h3_cell,
        "cad_call_id": f"PCR-DISPATCH-{int(asyncio.get_event_loop().time())}",
        "message": "Automated alert broadcasted to nearest Cyber Patrol Unit with GPS navigation."
    }

@app.post("/api/v1/actions/freeze-lien")
def trigger_1930_freeze(account_number: str):
    return {
        "status": "LIEN_PLACED",
        "account_number": account_number,
        "system": "CFCFRMS-1930",
        "message": f"Debit & ATM withdrawal permissions locked for account {account_number}."
    }
