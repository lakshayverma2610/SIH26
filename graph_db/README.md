# 🗺️ Geospatial & Graph Prediction Engine (`graph_db`)

**Module Owner:** Akshansh Singh ([@akshanshuwu](https://github.com/akshanshuwu))  
**Role:** Geospatial & Graph Architect  
**SIH Problem Statement:** SIH 26184 — Cybercrime Cash Withdrawal Hotspot Forecasting

---

## 🎯 Purpose & Capabilities
Translates digital mule risk scores and fund-routing flags from the AI engine into physical, actionable cash-out predictions for law enforcement field interception:
1. **Uber H3 Discrete Global Grid (`h3_indexer.py`):** Maps spatial coordinates to Resolution 8 (neighborhood zone) and Resolution 9 (ATM kiosk strip) hexagonal cells, generating GeoJSON polygon coordinates.
2. **Spatio-Temporal Clustering (`cluster_engine.py`):** Identifies spatial and temporal convergence of multiple high-risk mule accounts using Haversine distance and rolling time-window clustering.
3. **Point-of-Egress Forecasting (`geo_predictor.py`):** Pre-indexes physical ATM kiosks, calculates nearest points of physical withdrawal, assigns interception probabilities, and estimates critical intervention SLAs.

---

## 🏗️ Architecture & Modules

```
graph_db/
├── __init__.py           # Package exports (GeospatialPredictor, H3SpatialIndexer, SpatioTemporalClusterEngine)
├── config.py             # H3 resolutions, ST-DBSCAN thresholds, Hawkes decay constants
├── models.py             # Pydantic data schemas (MuleGeoEvent, ATMLocation, CashoutHotspot)
├── h3_indexer.py         # Lat/Lon to H3 index conversion & polygon boundary generation
├── cluster_engine.py     # Spatio-Temporal clustering & aggregate risk calculator
└── geo_predictor.py      # Core prediction interface called by FastAPI Gateway
```

---

## 🔌 API & Integration Points

### 1. Ingestion by Backend (`backend/main.py`)
```python
from graph_db.geo_predictor import GeospatialPredictor

geo_predictor = GeospatialPredictor("data_engine/data/atm_locations.json")
active_hotspots = geo_predictor.aggregate_hotspots(flagged_events_buffer)
```

### 2. Output Payload for Frontend (`Sneha`) & Actions (`Aashi`)
```json
{
  "cluster_id": "CLUST_000",
  "severity": "CRITICAL",
  "center_lat": 28.6304,
  "center_lon": 77.2773,
  "h3_res8": "883da11297fffff",
  "h3_res9": "893da11297bffff",
  "h3_boundary": {
    "type": "Polygon",
    "coordinates": [[[77.276, 28.632], [77.279, 28.632], "..."]]
  },
  "mule_count": 3,
  "mule_accounts": ["ACC_9921", "ACC_9922", "ACC_9923"],
  "total_funds_at_risk": 450000.0,
  "aggregate_risk_score": 0.96,
  "predicted_cashout_window": "T+0 to T+45 mins (CRITICAL INTERCEPTION)",
  "nearest_atms": [
    {
      "atm_id": "ATM_SBI_101",
      "bank_name": "SBI ATM & Cash Point",
      "lat": 28.6304,
      "lon": 77.2773,
      "distance_meters": 47.7,
      "withdrawal_probability": 0.94
    }
  ]
}
```

---

## 🧪 Running Tests
```bash
python3 tests/test_geo_predictor.py
```
