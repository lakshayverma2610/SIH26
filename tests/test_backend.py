"""
End-to-End Test Suite for Geo-CashWatch Backend Gateway & Stream Orchestrator
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "metrics" in data
    assert "total_transactions_ingested" in data["metrics"]

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert data["websocket_alerts"] == "/ws/alerts"

def test_ingest_normal_transaction():
    payload = {
        "tx_id": "TX_TEST_001",
        "src_acc": "ACC_USER_101",
        "dest_acc": "ACC_MERCHANT_201",
        "amount": 250.0,
        "channel": "UPI",
        "device_id": "DEV_USER_101",
        "ip": "192.168.1.50",
        "lat": 28.6304,
        "lon": 77.2773
    }
    response = client.post("/api/v1/transactions/stream", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PROCESSED"
    assert data["tx_id"] == "TX_TEST_001"
    assert "fraud_score" in data
    assert "is_high_risk" in data
    assert "features" in data

def test_ingest_high_risk_smurfing_transaction():
    # Register dormant account metadata for destinations
    from backend.app.core.stream_orchestrator import orchestrator
    for i in range(4):
        orchestrator.feature_engine.register_account_metadata(f"ACC_DORMANT_{i}", dormant_days=90, kyc_verified=False)

    # Inject rapid fan-out smurfing transactions
    src = "ACC_SUSPECT_MULE_1"
    for i in range(4):
        payload = {
            "tx_id": f"TX_SMURF_{i}",
            "src_acc": src,
            "dest_acc": f"ACC_DORMANT_{i}",
            "amount": 80000.0,
            "channel": "IMPS",
            "device_id": "DEV_SUSPECT_SHARED",
            "ip": "103.45.12.9",
            "lat": 28.6304,
            "lon": 77.2773
        }
        response = client.post("/api/v1/transactions/stream", json=payload)
        assert response.status_code == 200

    last_data = response.json()
    assert last_data["is_high_risk"] is True
    assert last_data["fraud_score"] >= 0.70

def test_ingest_batch_transactions():
    batch = {
        "transactions": [
            {
                "tx_id": f"TX_BATCH_{i}",
                "src_acc": f"ACC_SRC_{i}",
                "dest_acc": f"ACC_DST_{i}",
                "amount": 1000.0 * (i + 1),
                "channel": "UPI",
                "lat": 28.6139,
                "lon": 77.2090
            }
            for i in range(3)
        ]
    }
    response = client.post("/api/v1/transactions/batch", json=batch)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 3
    assert all(r["status"] == "PROCESSED" for r in results)

def test_get_recent_transactions():
    response = client.get("/api/v1/transactions/recent?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "transactions" in data
    assert len(data["transactions"]) > 0

def test_ncrp_complaint_ingestion():
    complaint = {
        "ncrp_id": "NCRP-2026-TEST-999",
        "victim_acc": "ACC_VICTIM_888",
        "suspect_acc": "ACC_SUSPECT_999",
        "amount": 120000.0,
        "complaint_type": "APK_RAT_FRAUD",
        "description": "Victim downloaded malicious APK, unauthorized IMPS transfers made."
    }
    response = client.post("/api/v1/complaints/ncrp", json=complaint)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "REGISTERED"
    assert data["suspect_acc"] == "ACC_SUSPECT_999"
    assert data["action_recommended"] == "TRIGGER_IMMEDIATE_DEBIT_FREEZE"

def test_active_hotspots_endpoint():
    response = client.get("/api/v1/hotspots/active")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "hotspots" in data
    assert isinstance(data["hotspots"], list)

def test_dispatch_patrol_action():
    payload = {
        "h3_cell": "8860145b59fffff",
        "patrol_unit_id": "PCR-NORTH-04",
        "priority": "CRITICAL",
        "notes": "Suspect mule cash withdrawal activity reported near Connaught Place ATM cluster."
    }
    response = client.post("/api/v1/actions/dispatch-patrol", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DISPATCHED"
    assert data["h3_cell"] == "8860145b59fffff"
    assert data["patrol_unit_id"] == "PCR-NORTH-04"
    assert "cad_call_id" in data

def test_freeze_lien_action():
    payload = {
        "account_number": "ACC_SUSPECT_999",
        "system": "CFCFRMS-1930",
        "reason": "1930 NCRP Cyber Complaint Linkage",
        "freeze_amount": 120000.0
    }
    response = client.post("/api/v1/actions/freeze-lien", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "LIEN_PLACED"
    assert data["account_number"] == "ACC_SUSPECT_999"
    assert "lien_id" in data

def test_action_history():
    response = client.get("/api/v1/actions/history")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["total_dispatches"] >= 1
    assert data["total_liens"] >= 1

def test_websocket_alerts_connection():
    with client.websocket_connect("/ws/alerts") as ws:
        # Initial state message must be received on connect
        data = ws.receive_json()
        assert data["type"] == "INITIAL_STATE"
        assert "hotspots" in data
        assert "recent_txs" in data
        assert "system_metrics" in data

        # Send ping, expect pong
        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"
