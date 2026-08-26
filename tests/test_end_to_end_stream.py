"""
End-to-End System Tests for Geo-CashWatch Enterprise Architecture
"""
import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.api_gateway import app

client = TestClient(app)

def test_root_status():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert data["version"] == "2.0.0"

def test_get_active_hotspots():
    response = client.get("/api/v1/hotspots/active")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "hotspots" in data

def test_ncrp_complaint_ingestion():
    complaint = {
        "victim_account": "ACC_VICTIM_9012",
        "suspect_layer1_account": "ACC_MULE_L1_4011",
        "reported_loss_amount": 250000.0,
        "crime_category": "APK_RAT_FRAUD",
        "auto_trigger_lien": True,
        "description": "Victim reported remote APK access fraud."
    }
    response = client.post("/api/v1/complaints/ncrp", json=complaint)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLAINT_REGISTERED"
    assert "ncrp_ack_number" in data
    assert data["auto_lien_triggered"] is True

def test_dispatch_patrol_endpoint():
    payload = {
        "h3_cell": "8928308280fffff",
        "target_atm_name": "SBI ATM Kiosk Vikas Marg",
        "destination_lat": 28.6304,
        "destination_lon": 77.2773,
        "priority": "CRITICAL"
    }
    response = client.post("/api/v1/actions/dispatch-patrol", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUEUED_FOR_DISPATCH"
    assert "maps_url" in data

def test_action_history_endpoint():
    response = client.get("/api/v1/actions/history")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "total_dispatches" in data
    assert "total_liens_placed" in data
