import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.main import app

client = TestClient(app)

def test_transaction_stream_ingestion():
    payload = {
        "tx_id": "TX_TEST_001",
        "src_acc": "ACC_VICTIM_9012",
        "dest_acc": "ACC_MULE_L1_4011",
        "amount": 250000.0,
        "channel": "IMPS",
        "device_id": "DEV_RAT_VICTIM_9012",
        "ip": "185.220.101.4",
        "lat": 24.2185,
        "lon": 86.6492,
        "timestamp": time.time()
    }
    response = client.post("/api/v1/transactions/stream", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PROCESSED"
    assert "fraud_score" in data
    assert "is_high_risk" in data

def test_ncrp_complaint_ingestion():
    complaint = {
        "ncrp_id": "NCRP-1930-TEST-999",
        "victim_acc": "ACC_VICTIM_9012",
        "suspect_acc": "ACC_MULE_L1_4011",
        "amount": 250000.0,
        "complaint_type": "APK_RAT_FRAUD"
    }
    response = client.post("/api/v1/complaints/ncrp", json=complaint)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INGESTED"
    assert data["ncrp_id"] == "NCRP-1930-TEST-999"

def test_get_active_hotspots():
    response = client.get("/api/v1/hotspots/active")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "hotspots" in data
