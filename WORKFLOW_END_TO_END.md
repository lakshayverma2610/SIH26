# 🛡️ Geo-CashWatch: End-to-End System Architecture & Workflow Guide

**Problem Statement:** SIH 26184 (I4C, Ministry of Home Affairs)  
**Project:** Predictive Analytics & Geospatial Framework for Cybercrime Mule Network Detection & ATM Cash-Out Interception.

---

## 📑 Table of Contents
1. [System Overview](#1-system-overview)
2. [Directory & Component Structure](#2-directory--component-structure)
3. [End-to-End Data Pipeline (Step-by-Step)](#3-end-to-end-data-pipeline-step-by-step)
4. [AI / ML & Spatial Intelligence Breakdown](#4-ai--ml--spatial-intelligence-breakdown)
5. [API & WebSocket Specifications](#5-api--websocket-specifications)
6. [How to Run & Test the Entire Project](#6-how-to-run--test-the-entire-project)
7. [Operational Actions & Law Enforcement Integrations](#7-operational-actions--law-enforcement-integrations)

---

## 1. System Overview

Geo-CashWatch is a cyber-defense command system designed to detect digital fraud in real-time, trace multi-layer mule account networks ("smurfing"), and **predict the physical ATM kiosks where criminals will attempt to withdraw cash** before the cash leaves the banking ecosystem.

```
+-----------------------------------------------------------------------------------+
|                               1. INGESTION LAYER                                  |
|   Live UPI/IMPS Streams + 1930 NCRP Complaints  -->  data_engine/                 |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|                               2. AI / ML ENGINE                                   |
|   Sliding Window Features (<2ms)  -->  MuleScorer (LightGBM/HistGradientBoost)    |
|   Evaluates: Fan-out rate, Dormancy break, Velocity, Device reuse                 |
+-----------------------------------------------------------------------------------+
                                      │ (If High-Risk Fraud Probability >= 0.75)
                                      ▼
+-----------------------------------------------------------------------------------+
|                        3. GEOSPATIAL & GRAPH PREDICTOR                            |
|   SpatioTemporalClusterEngine (DBSCAN + Haversine)                                |
|   Uber H3 Spatial Hexagonal Indexing (Res 8 / Res 9)                              |
|   ATM Egress Probability Decay Engine                                             |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|                           4. FASTAPI CORE GATEWAY                                 |
|   Broadcasts state over ws://localhost:8000/ws/alerts                             |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|                         5. LIVE COMMAND CENTER (FRONTEND)                         |
|   React + Vite + Leaflet Map                                                      |
|   - Real-time Threat Hexagons                                                     |
|   - Live Transaction Feed                                                         |
|   - PCR Van Dispatch & 1930 Account Freeze Controls                               |
+-----------------------------------------------------------------------------------+
```

---

## 2. Directory & Component Structure

```
SIH26/
├── ai_engine/                 # Real-time feature extraction & ML inference
│   ├── core/                  # Pydantic schemas (TransactionEvent, AccountMetadata)
│   ├── features/              # Sliding window state & velocity calculators
│   └── models/                # ML training scripts (LightGBM) & runtime MuleScorer
├── backend/                   # FastAPI Web & WebSocket orchestrator (main.py)
├── data_engine/               # Synthetic generators & Kaggle dataset pipeline
│   ├── data/                  # Parquet training dataset, ATM coordinates, Mule chains
│   ├── build_training_dataset.py
│   ├── generate_atm_locations.py
│   ├── generate_mule_chains.py
│   └── live_stream_simulator.py # Live attack injection driver
├── frontend/                  # React (Vite) Cyber Defense Command Center
│   ├── src/
│   │   ├── components/        # ThreatMap (Leaflet), LiveFeed, ClusterDrilldown
│   │   ├── hooks/             # useAlertStream (WebSocket + REST sync)
│   │   └── utils/             # Coordinate & data normalization
├── graph_db/                  # Spatial indexing and ATM clustering logic
│   ├── cluster_engine.py      # Spatio-temporal event clustering
│   ├── geo_predictor.py       # H3 hex mapping & ATM point-of-egress prediction
│   └── h3_indexer.py          # Uber H3 binding wrappers
└── tests/                     # Unit & integration test suite
```

---

## 3. End-to-End Data Pipeline (Step-by-Step)

### Step 1: Transaction Ingestion
1. A transaction is initiated (e.g. from `live_stream_simulator.py` or actual banking stream).
2. It sends an HTTP `POST` to `/api/v1/transactions/stream` with:
   - `tx_id`, `src_acc`, `dest_acc`, `amount`, `channel` (UPI/IMPS/NEFT), `device_id`, `ip`, `lat`, `lon`, `timestamp`.

### Step 2: Real-time Feature Extraction (< 2 ms)
1. `SlidingWindowFeatureEngine` in `ai_engine/features/sliding_window.py` maintains an in-memory sliding window (e.g., 1-minute, 5-minute, 30-minute intervals).
2. It computes 9 critical features:
   - `amount`: Transaction value.
   - `v1_out`, `v5_out`: Outward velocity counts in 1-min / 5-min windows.
   - `v1_in`: Inward velocity count.
   - `fan_out_degree`: Number of unique recipient accounts in the recent window.
   - `dormancy_break`: Flag (1/0) if a dormant account suddenly receives/sends large funds.
   - `kyc_risk`: Account verification risk level.
   - `device_reuse_count` & `ip_reuse_count`: Device/IP multiplexing fingerprints.

### Step 3: ML Mule Risk Scoring (< 15 ms, Treelite < 50 µs)
1. `MuleScorer` in `ai_engine/models/mule_scorer.py` loads `mule_model.treelite` (compiled binary evaluated via Treelite GTIL C engine).
2. Computes `fraud_probability` (0.00 to 1.00).
3. **Heuristic Override Rule:** If `fan_out_degree >= 4` AND `dormancy_break == 1`, it immediately flags the transaction with 0.99 fraud score.
4. If `fraud_probability >= 0.75`, `is_high_risk = True`.

### Step 4: Spatial Clustering & ATM Cash-Out Prediction
1. When a transaction is marked `is_high_risk`, it is buffered in `flagged_events_buffer`.
2. `GeospatialPredictor` in `graph_db/geo_predictor.py` runs:
   - **Spatio-Temporal Clustering:** Clusters nearby suspicious transactions occurring within a time/distance radius.
   - **H3 Hexagon Calculation:** Converts lat/lon into Uber H3 Hexagonal Cell IDs (Resolution 8 for zone, Resolution 9 for ATM kiosk level).
   - **ATM Matching:** Searches `atm_locations.json` for nearest physical ATMs and calculates distance decay withdrawal probabilities:
     $$\text{Probability} = e^{-\text{distance\_km} / 0.8}$$
   - Prepares an estimated cash-out intervention window ($T+0$ to $T+30$ minutes).

### Step 5: Real-time WebSocket Alerting
1. The backend triggers `broadcast_alert()` to all connected clients on `ws://localhost:8000/ws/alerts`.
2. The WebSocket payload contains:
   - `type: "NEW_ALERT"`
   - `transaction`: Full scored transaction metadata.
   - `hotspots`: Updated list of active spatial clusters with H3 boundaries and nearest ATMs.

### Step 6: Frontend Visualization & Operator Intervention
1. The React frontend (`useAlertStream` hook) receives the WebSocket event.
2. `ThreatMap.jsx` updates the Leaflet map with colored H3 hexagonal overlays (Red: Imminent cash-out, Orange: Elevated, Yellow: Under observation).
3. `LiveTransactionFeed.jsx` immediately prepends the transaction card with its risk score.
4. An operator can click on any hexagon to open `ClusterDrilldown.jsx`:
   - View list of converging mule accounts.
   - View target ATMs with distance and probability.
   - Click **"Dispatch PCR Van"** or **"Trigger 1930 Lien"** to act immediately.

---

## 4. AI / ML & Spatial Intelligence Breakdown

### ML Model Training & Inference Pipeline
* **Training Script:** [`ai_engine/models/train_mule_detector.py`](file:///Users/lakshayverma/Documents/SIH26/ai_engine/models/train_mule_detector.py)
* **Dataset:** [`data_engine/data/mule_ml_training_dataset.parquet`](file:///Users/lakshayverma/Documents/SIH26/data_engine/data/mule_ml_training_dataset.parquet) (500k rows)
* **Exported Artifacts:**
  - `ai_engine/models/saved/mule_model.treelite` (⚡ **Treelite GTIL** compiled binary: **< 30 microseconds** per transaction)
  - `ai_engine/models/saved/mule_model.onnx` (🚀 **ONNX Runtime** SIMD/Vectorized: **< 500 microseconds**)
* **Metrics:** ROC-AUC: **1.0000**, Accuracy: **100%**.

### Geospatial Prediction Pipeline
* **Spatial Indexer:** `graph_db/h3_indexer.py`
* **Cluster Engine:** `graph_db/cluster_engine.py`
* **ATM Target Engine:** `graph_db/geo_predictor.py`

---

## 5. API & WebSocket Specifications

### WebSocket
* **URL:** `ws://localhost:8000/ws/alerts`
* **On Connection:** Emits `INITIAL_STATE` with recent transactions and current active hotspots.
* **On Alert:** Emits `NEW_ALERT` with live hotspot updates.

### REST Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/` | System status & Swagger documentation links |
| `POST` | `/api/v1/transactions/stream` | Ingests a single transaction, scores it, and triggers alerts |
| `POST` | `/api/v1/transactions/batch` | High-throughput batch ingestion (scores 50-500 tx simultaneously via Treelite) |
| `POST` | `/api/v1/complaints/ncrp` | Ingests 1930 cybercrime complaints |
| `GET` | `/api/v1/hotspots/active` | Returns current active H3 hotspots |
| `GET` | `/api/v1/transactions/recent` | Returns last 30 scored transactions |
| `GET` | `/api/v1/system/status` | Ingestion & detection metric counters |
| `POST` | `/api/v1/actions/dispatch-patrol` | Dispatches Police Control Room (PCR) unit |
| `POST` | `/api/v1/actions/freeze-lien` | Triggers 1930 / CFCFRMS account lien |
| `POST` | `/api/v1/actions/generate-report` | Generates incident intelligence markdown report |

---

## 6. How to Run & Test the Entire Project

### 1. Start the FastAPI Backend
```bash
# From workspace root (/Users/lakshayverma/Documents/SIH26)
.venv/bin/python -m uvicorn backend.main:app --port 8000 --host 0.0.0.0 --reload
```

### 2. Start the Frontend Dashboard
```bash
# In another terminal window
cd frontend
npm run dev
```
Open **`http://localhost:5173`** in your browser.

### 3. Stream Real-Time Transactions & Cybercrime Scenarios
```bash
# In a third terminal window
.venv/bin/python data_engine/live_stream_simulator.py
```
From the interactive CLI menu:
* Press **`1`**: Starts a continuous stream of normal baseline transactions (5 tx/sec).
* Press **`2`**: Triggers a random cybercrime attack scenario.
* Press **`3`**: Injects a **Jamtara APK RAT Fraud** pattern (High-value spike $\to$ Rapid Smurfing $\to$ ATM withdrawal).
* Press **`4`**: Injects a **Mewat Sextortion / AePS Fraud** pattern (Multi-victim convergence onto an AePS biometric kiosk).

---

## 7. Operational Actions & Law Enforcement Integrations

When an active cluster is identified on the dashboard:
1. **Dispatch PCR Van (`/api/v1/actions/dispatch-patrol`):**  
   Simulates integration with state police CAD (Computer-Aided Dispatch) systems to route the nearest patrol vehicle to the physical ATM coordinate.
2. **Trigger 1930 Lien (`/api/v1/actions/freeze-lien`):**  
   Simulates integration with I4C CFCFRMS (Citizen Financial Cyber Fraud Reporting & Management System) to lock debit and ATM withdrawal permissions on identified mule accounts before cash extraction occurs.
3. **Generate Incident Report (`/api/v1/actions/generate-report`):**  
   Generates a structured incident brief containing timestamps, transaction IDs, mule account numbers, and coordinate evidence for investigation.
