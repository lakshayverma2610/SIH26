# ⚙️ Implementation Plan: Backend & Kafka/Stream Gateway

**Team Member:** Yashvi  
**Role:** Backend Core & Ingestion Engineer  
**GitHub Repository:** [lakshayverma2610/SIH26](https://github.com/lakshayverma2610/SIH26)  
**Assigned Branch:** `Backend-Kafka`  
**Working Directory:** `backend/`

## 🎯 Objective
Build the central nervous system of Geo-CashWatch. You will create a high-throughput async FastAPI gateway that ingests transaction streams, orchestrates the AI and Geo modules, and serves real-time data to the frontend via WebSockets.

## 💻 Tech Stack
* Python 3.11+
* FastAPI & Uvicorn
* Pydantic
* Asyncio (for in-memory event queues)
* WebSockets

## 🛠️ Step-by-Step GitHub Workflow

1. **Clone & Checkout:**
   ```bash
   git clone https://github.com/lakshayverma2610/SIH26.git
   cd SIH26
   git checkout Backend-Kafka
   ```
2. **Develop in `backend/` directory.**
3. **Commit & Push:**
   ```bash
   git add backend/
   git commit -m "feat(api): create async transaction ingestion endpoint"
   git push origin Backend-Kafka
   ```

## 🏗️ Programs & Modules to Build

### 1. `app/main.py`
**Purpose:** The core FastAPI application entry point.
**Details:**
* Initialize the FastAPI app with CORS middleware.
* Import and instantiate singletons for Lakshay's `MuleScorer` and Akshansh's `GeospatialPredictor`.
* **Endpoints to create:**
  * `POST /api/v1/transactions/stream`: Accepts high-speed transaction JSON payloads.
  * `POST /api/v1/complaints/ncrp`: Accepts initial 1930 victim complaints.
  * `GET /api/v1/hotspots/active`: Returns the current list of predicted cash-out zones.

### 2. `app/core/stream_orchestrator.py`
**Purpose:** Manage the pipeline flow without blocking the event loop.
**Details:**
* When a transaction hits the POST endpoint:
  1. Pass it to `feature_engine.process_and_extract()`.
  2. Pass features to `mule_scorer.score_features()`.
  3. If `is_high_risk` is True, buffer the transaction.
  4. Periodically (or upon high-risk triggers) pass the buffer to `geo_predictor.aggregate_hotspots()`.
* Keep an in-memory sliding list of the last 100 transactions and active hotspots to serve initial state to new WebSocket clients.

### 3. `app/routers/websocket_router.py` (or inside `main.py`)
**Purpose:** Push live updates to Sneha's frontend dashboard.
**Details:**
* Implement an `@app.websocket("/ws/alerts")` endpoint.
* Manage a list of `active_connections`.
* Create a `broadcast_alert(payload)` function.
* Whenever a new hotspot is synthesized or a high-risk transaction occurs, serialize the data and `await connection.send_json()` to all connected clients instantly.

## 🤝 Integration Points
* You sit in the middle: You must integrate the Python classes built by **Lakshay** (`ai_engine`) and **Akshansh** (`graph_db`).
* You are the sole data provider for **Sneha's** React dashboard.
* You receive incoming requests from **Gaurvi's** `stream_simulator`.
