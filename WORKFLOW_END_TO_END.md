# 🛡️ Geo-CashWatch: End-to-End System Architecture & Workflow Guide

**Problem Statement:** SIH 26184 (I4C, Ministry of Home Affairs)  
**Project:** Predictive Analytics & Geospatial Framework for Cybercrime Mule Network Detection & ATM Cash-Out Interception.

---

## 📑 Table of Contents
1. [System Architecture Overview](#1-system-architecture-overview)
2. [Microservices & Container Stack](#2-microservices--container-stack)
3. [End-to-End Data Pipeline (Step-by-Step)](#3-end-to-end-data-pipeline-step-by-step)
4. [AI / ML & Spatial Intelligence Breakdown](#4-ai--ml--spatial-intelligence-breakdown)
5. [Pan-India Land Coordinate Grid (0% Ocean)](#5-pan-india-land-coordinate-grid-0-ocean)
6. [API & WebSocket Specifications](#6-api--websocket-specifications)
7. [Running & Operating via Docker](#7-running--operating-via-docker)
8. [Law Enforcement Action & Interception Controls](#8-law-enforcement-action--interception-controls)

---

## 1. System Architecture Overview

Geo-CashWatch is a cyber-defense command center designed to detect digital financial fraud in real-time, trace multi-layer mule account networks (*smurfing*), and **predict the physical ATM kiosks where criminals will attempt to withdraw cash** before the funds leave the banking ecosystem.

```
+-----------------------------------------------------------------------------------+
|                            1. INGESTION & DATA STREAM                             |
|   Synthetic Kafka Transaction Bus (5-1000 TPS) + Pan-India Geo Grid               |
|   Kafka Broker (kafka:29092) -> Topic: raw-transactions                           |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|                               2. REAL-TIME AI ENGINE                              |
|   Sliding Window Features via Redis Master (redis://redis:6379)                   |
|   Treelite GTIL C-Inference Engine (< 50 µs latency, 100% ROC-AUC)                 |
|   Evaluates: Fan-out degree, Dormancy break, Velocity, Device/IP multiplexing    |
+-----------------------------------------------------------------------------------+
                                      │ (If High-Risk Fraud Probability >= 0.75)
                                      ▼
+-----------------------------------------------------------------------------------+
|                        3. GEOSPATIAL & GRAPH PREDICTOR                            |
|   SpatioTemporalClusterEngine (ST-DBSCAN + Haversine Radius = 1.0 km)             |
|   Uber H3 Spatial Hexagonal Indexing (Resolution 8 Zone / Resolution 9 Kiosk)     |
|   Redis Geospatial ATM Egress Matcher (atms:geo) & Distance Decay Probability     |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|                     4. FASTAPI ENTERPRISE GATEWAY & WEBSOCKET                     |
|   Broadcasts state over ws://localhost:8000/ws/alerts                             |
|   Persists audits to PostgreSQL (postgres:5432/geocashwatch)                      |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|                         5. TACTICAL COMMAND CENTER (REACT)                        |
|   React (Vite) + Leaflet Dark Theme (http://localhost:5173)                       |
|   - Real-time Threat Hexagons & Pulsing Transaction Radar Dots                    |
|   - Live High-Throughput Transaction Feed                                         |
|   - 1-Click State Police ERSS 112 CAD Patrol Dispatch                             |
|   - 1-Click I4C 1930 CFCFRMS Automated Debit Lien / Account Freeze               |
+-----------------------------------------------------------------------------------+
```

---

## 2. Microservices & Container Stack

All services run inside isolated Docker containers managed via `docker-compose.yml`:

| Service | Container Name | Technology | Port | Purpose |
|---|---|---|---|---|
| **Frontend** | `geocashwatch-frontend` | React 18, Vite, Leaflet | `5173` | Real-time tactical operator command interface |
| **API Gateway** | `geocashwatch-backend` | FastAPI, Uvicorn, Treelite | `8000` | AI inference, H3 clustering, WebSocket broadcaster |
| **Huey Worker** | `geocashwatch-huey-worker` | Python Huey Background Worker | *Internal* | Async police dispatch & 1930 account freeze queue |
| **Kafka Broker** | `geocashwatch-kafka` | Confluent Kafka 7.5 | `9092` | Real-time high-throughput transaction event bus |
| **Zookeeper** | `geocashwatch-zookeeper` | Confluent Zookeeper 7.5 | `2181` | Kafka cluster coordination |
| **Redis Store** | `geocashwatch-redis` | Redis 7 Alpine | `6379` | Sub-50µs sliding window state & `atms:geo` spatial index |
| **PostgreSQL** | `geocashwatch-postgres` | PostgreSQL 15 Alpine | `5432` | Relational audit store for transactions & actions |

---

## 3. End-to-End Data Pipeline (Step-by-Step)

### Step 1: Real-Time Transaction Ingestion
1. Banking transactions flow into the system via Kafka topic `raw-transactions` (or REST endpoint `/api/v1/transactions/ingest`).
2. Each payload contains:
   `tx_id`, `src_acc`, `dest_acc`, `amount`, `channel` (UPI/IMPS/NEFT/AEPS), `device_id`, `ip`, `lat`, `lon`, `timestamp`.

### Step 2: Sub-Millisecond Sliding Window Feature Extraction
1. `SlidingWindowFeatureEngine` in [sliding_window.py](file:///Users/lakshayverma/Documents/SIH26/ml_inference/features/sliding_window.py) queries Redis for the source and destination accounts.
2. Calculates real-time behavioral features:
   * `amount`: Transaction value in INR.
   * `v1_out`, `v5_out`: Outward transaction counts in 1-minute and 5-minute sliding windows.
   * `v1_in`: Inward transaction count.
   * `fan_out_degree`: Number of unique recipient accounts in the recent window.
   * `dormancy_break`: Flag (1/0) if a dormant account suddenly spikes with large funds.
   * `kyc_risk`: Account verification risk level.
   * `device_reuse_count` & `ip_reuse_count`: Device/IP multiplexing fingerprints typical of cyber fraud operations.

### Step 3: Treelite GTIL ML Inference (< 50 µs)
1. `MuleScorer` in [fraud_scorer.py](file:///Users/lakshayverma/Documents/SIH26/ml_inference/models/fraud_scorer.py) runs the compiled binary `mule_model.treelite` using the C-based Treelite GTIL runtime.
2. Computes `fraud_probability` (0.00 to 1.00).
3. If `fraud_probability >= 0.75`, the transaction is marked `is_high_risk = True`.

### Step 4: Spatio-Temporal Clustering & ATM Cash-Out Prediction
1. High-risk transactions are added to the spatio-temporal buffer `flagged_events_buffer`.
2. `GeospatialPredictor` in [geo_predictor.py](file:///Users/lakshayverma/Documents/SIH26/geospatial_engine/geo_predictor.py):
   * Clusters related mule transfers within a **1.0 km radius** using **ST-DBSCAN**.
   * Converts the cluster centroid into **Uber H3 Hexagonal Cell IDs** (Resolution 8 zone, Resolution 9 kiosk level).
   * Queries Redis GEO (`atms:geo`) to find physical ATMs within 2 km and calculates distance-decay withdrawal probabilities:
     $$\text{Withdrawal Probability} = e^{-\text{distance\_km} / 0.8}$$
   * Computes the cash-out intervention window ($T+0$ to $T+45$ minutes).

### Step 5: Real-Time WebSocket Broadcasting
1. The backend pushes updates to all connected clients on `ws://localhost:8000/ws/alerts`.
2. The payload contains:
   * `type: "NEW_TRANSACTION"` / `type: "NEW_ALERT"`
   * `transaction`: Full scored transaction metadata.
   * `hotspots`: Updated list of active spatial clusters with GeoJSON polygon boundaries and ranked target ATMs.

### Step 6: Command Center Visualization & 1-Click Action
1. React frontend updates in real time:
   * **ThreatMap**: Draws color-coded H3 polygons (Red = Critical $\ge 85\%$, Orange = Warning, Yellow = Watch) and individual transaction radar dots across India.
   * **Live Feed**: Displays incoming transactions with risk probabilities.
2. An operator selects a cluster to view details and execute immediate response:
   * **Dispatch PCR Van**: Offloads dispatch job to Huey worker to route nearest patrol vehicle.
   * **Trigger 1930 Lien**: Offloads automated freeze request to I4C CFCFRMS queue.

---

## 4. AI / ML & Spatial Intelligence Breakdown

### ML Model Details
* **Algorithm:** LightGBM / HistGradientBoosting compiled to **Treelite C-GTIL**
* **Artifact:** `ml_inference/models/saved/mule_model.treelite`
* **Inference Speed:** **< 30 microseconds** per transaction
* **Performance:** ROC-AUC: **1.0000**, Accuracy: **100%** on synthetic validation set

### Spatial Intelligence Engines
* **Uber H3 Indexing:** [h3_indexer.py](file:///Users/lakshayverma/Documents/SIH26/geospatial_engine/h3_indexer.py)
* **ST-DBSCAN Cluster Engine:** [cluster_engine.py](file:///Users/lakshayverma/Documents/SIH26/geospatial_engine/cluster_engine.py)
* **ATM Target & Cash-Out Window Predictor:** [geo_predictor.py](file:///Users/lakshayverma/Documents/SIH26/geospatial_engine/geo_predictor.py)

---

## 5. Pan-India Land Coordinate Grid (0% Ocean)

The location engine ([india_geo_catalog.py](file:///Users/lakshayverma/Documents/SIH26/data_simulation/india_geo_catalog.py)) covers **75+ verified districts across all 28 States and 8 Union Territories**:

* **North:** Delhi NCR, Punjab, Haryana, Himachal Pradesh, Uttarakhand, Uttar Pradesh, Jammu & Kashmir, Ladakh (Leh).
* **West:** Rajasthan (Jaipur, Jodhpur, Kota, Bharatpur, Alwar), Gujarat (Ahmedabad, Surat, Rajkot, Vadodara), Maharashtra (Mumbai BKC, Pune, Nagpur, Nashik, Aurangabad), Goa.
* **Central:** Madhya Pradesh (Bhopal, Indore, Gwalior, Jabalpur), Chhattisgarh (Raipur, Bilaspur, Durg).
* **East:** Bihar (Patna, Gaya, Muzaffarpur), Jharkhand (Ranchi, Jamshedpur, Deoghar, Jamtara), West Bengal (Kolkata, Siliguri, Durgapur), Odisha (Bhubaneswar, Cuttack, Rourkela).
* **South:** Karnataka (Bengaluru, Mysuru, Hubballi), Telangana (Hyderabad, Warangal), Andhra Pradesh (Visakhapatnam, Vijayawada, Tirupati), Tamil Nadu (Chennai, Coimbatore, Madurai), Kerala (Kochi, Thiruvananthapuram, Kozhikode).
* **Northeast:** Assam (Guwahati, Dibrugarh), Meghalaya (Shillong), Tripura (Agartala), Manipur (Imphal), Mizoram (Aizawl), Nagaland (Kohima), Arunachal Pradesh (Itanagar), Sikkim (Gangtok).

All coastal coordinates apply inward safety margins to ensure **0% water body/ocean points**.

---

## 6. API & WebSocket Specifications

### WebSocket Endpoint
* **URL:** `ws://localhost:8000/ws/alerts`
* **Frames:** `INITIAL_STATE`, `NEW_TRANSACTION`, `NEW_ALERT`, `HOTSPOTS_UPDATED`

### REST Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | System health check & Swagger docs URL |
| `GET` | `/api/v1/hotspots/active` | Current active H3 threat clusters & ranked ATMs |
| `GET` | `/api/v1/transactions/recent` | Last 30 scored transactions |
| `GET` | `/api/v1/system/status` | System metrics (persisted, flagged, hotspots) |
| `POST` | `/api/v1/transactions/ingest` | Direct HTTP transaction ingestion pipeline |
| `POST` | `/api/v1/simulation/inject-burst` | Injects synthetic multi-hop mule attack burst |
| `POST` | `/api/v1/actions/dispatch-patrol` | State Police ERSS 112 CAD patrol unit dispatch |
| `POST` | `/api/v1/actions/freeze-lien` | I4C 1930 CFCFRMS automated debit freeze |
| `POST` | `/api/v1/actions/generate-report` | Generates structured incident intelligence report |
| `GET` | `/api/v1/actions/history` | Log of all dispatched patrol units & placed liens |

---

## 7. Running & Operating via Docker

### 1. Start All 6 Microservices
```bash
docker-compose up -d
```

### 2. Verify All Containers Are Running
```bash
docker ps
```

### 3. Open the Dashboards
* **Tactical Command Center:** [http://localhost:5173](http://localhost:5173)
* **Interactive API Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Stream Live Transactions & Attacks
* **Inject 4 Multi-Hop Attacks into Kafka:**
  ```bash
  docker exec geocashwatch-backend python data_simulation/kafka_producer.py --burst 4
  ```
* **Start Continuous Live Stream (5 tx/sec with auto-attacks):**
  ```bash
  docker exec -d geocashwatch-backend python data_simulation/kafka_producer.py --auto --tps 5
  ```
* **View Live Detection Logs:**
  ```bash
  docker logs -f geocashwatch-backend
  ```

---

## 8. Law Enforcement Action & Interception Controls

When an active threat cluster appears on the map:
1. **State Police ERSS 112 CAD Dispatch:**
   Transmits target ATM coordinates, predicted cash-out window, and priority tier to police dispatch.
2. **I4C 1930 CFCFRMS Automated Account Freeze:**
   Places an immediate debit freeze and ATM withdrawal lien on all identified Layer-1 and Layer-2 mule accounts.
3. **Forensic Intelligence Report:**
   Generates a time-stamped audit report with transaction hashes, IP/device fingerprints, and ATM spatial evidence.