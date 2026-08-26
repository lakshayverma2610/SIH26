# Geo-CashWatch: Complete Codebase File-by-File Guide

> **Predictive Analytics & Geospatial Framework for Cybercrime Mule Network Detection & ATM Cash-Out Interception**  
> *Target Problem: SIH 26184 — I4C Ministry of Home Affairs (MHA), Government of India*

---

## 📑 Table of Contents

1. [Architectural Overview](#architectural-overview)
2. [Backend & API Layer (`backend/`)](#1-backend--api-layer-backend)
   - [backend/api_gateway.py](#backendapi_gatewaypy)
   - [backend/database/models.py](#backenddatabasemodelspy)
   - [backend/database/session.py](#backenddatabasesessionpy)
   - [backend/database/__init__.py](#backenddatabase__init__py)
   - [backend/streaming/kafka_client.py](#backendstreamingkafka_clientpy)
   - [backend/tasks/huey_app.py](#backendtaskshuey_apppy)
   - [backend/tasks/worker.py](#backendtasksworkerpy)
   - [backend/tasks/worker_tasks.py](#backendtasksworker_taskspy)
   - [backend/tasks/__init__.py](#backendtasks__init__py)
   - [backend/alerts/broadcaster.py](#backendalertsbroadcasterpy)
   - [backend/alerts/report_generator.py](#backendalertsreport_generatorpy)
   - [backend/alerts/__init__.py](#backendalerts__init__py)
   - [backend/integrations/cfcfrms_client.py](#backendintegrationscfcfrms_clientpy)
   - [backend/integrations/erss_cad_client.py](#backendintegrationserss_cad_clientpy)
   - [backend/integrations/ncrp_client.py](#backendintegrationsncrp_clientpy)
   - [backend/integrations/npci_nfs_client.py](#backendintegrationsnpci_nfs_clientpy)
   - [backend/integrations/__init__.py](#backendintegrations__init__py)
   - [backend/Dockerfile](#backenddockerfile)
   - [backend/requirements.txt](#backendrequirementstxt)
3. [Geospatial Engine (`geospatial_engine/`)](#2-geospatial-engine-geospatial_engine)
   - [geospatial_engine/geo_predictor.py](#geospatial_enginegeo_predictorpy)
   - [geospatial_engine/cluster_engine.py](#geospatial_enginecluster_enginepy)
   - [geospatial_engine/h3_indexer.py](#geospatial_engineh3_indexerpy)
   - [geospatial_engine/models.py](#geospatial_enginemodelspy)
   - [geospatial_engine/config.py](#geospatial_engineconfigpy)
   - [geospatial_engine/__init__.py](#geospatial_engine__init__py)
   - [geospatial_engine/README.md](#geospatial_enginereadmemd)
4. [Machine Learning & Real-Time Inference (`ml_inference/`)](#3-machine-learning--real-time-inference-ml_inference)
   - [ml_inference/models/fraud_scorer.py](#ml_inferencemodelsfraud_scorerpy)
   - [ml_inference/features/sliding_window.py](#ml_inferencefeaturessliding_windowpy)
   - [ml_inference/geo/h3_mapper.py](#ml_inferencegeoh3_mapperpy)
   - [ml_inference/core/schemas.py](#ml_inferencecoreschemaspy)
   - [ml_inference/core/config.py](#ml_inferencecoreconfigpy)
   - [ml_inference/core/logger.py](#ml_inferencecoreloggerpy)
   - [ml_inference/models/train_mule_detector.py](#ml_inferencemodelstrain_mule_detectorpy)
   - [ml_inference/ARCHITECTURE.md](#ml_inferencearchitecturemd)
5. [Data Simulation & Synthetic Generator (`data_simulation/`)](#4-data-simulation--synthetic-generator-data_simulation)
   - [data_simulation/kafka_producer.py](#data_simulationkafka_producerpy)
   - [data_simulation/generate_mule_chains.py](#data_simulationgenerate_mule_chainspy)
   - [data_simulation/generate_atm_locations.py](#data_simulationgenerate_atm_locationspy)
   - [data_simulation/build_training_dataset.py](#data_simulationbuild_training_datasetpy)
   - [data_simulation/seed_redis.py](#data_simulationseed_redispy)
   - [data_simulation/simulation_config.json](#data_simulationsimulation_configjson)
   - [data_simulation/requirements.txt](#data_simulationrequirementstxt)
   - [data_simulation/pitch_deck_strategy.md](#data_simulationpitch_deck_strategymd)
   - [data_simulation/__init__.py](#data_simulation__init__py)
   - [data_simulation/data/ (JSON, Parquet, and DB assets)](#data_simulationdata-datasets--databases)
6. [Frontend Dashboard (`frontend/`)](#5-frontend-dashboard-frontend)
   - [frontend/src/App.jsx](#frontendsrcappjsx)
   - [frontend/src/main.jsx](#frontendsrcmainjsx)
   - [frontend/src/index.css](#frontendsrcindexcss)
   - [frontend/src/components/ThreatMap.jsx](#frontendsrccomponentsthreatmapjsx)
   - [frontend/src/components/ClusterDrilldown.jsx](#frontendsrccomponentsclusterdrilldownjsx)
   - [frontend/src/components/LiveTransactionFeed.jsx](#frontendsrccomponentslivetransactionfeedjsx)
   - [frontend/src/hooks/useAlertStream.js](#frontendsrchooksusealertstreamjs)
   - [frontend/src/utils/normalize.js](#frontendsrcutilsnormalizejs)
   - [frontend/vite.config.js](#frontendviteconfigjs)
   - [frontend/package.json](#frontendpackagejson)
   - [frontend/Dockerfile](#frontenddockerfile)
   - [frontend/index.html](#frontendindexhtml)
   - [frontend/README.md](#frontendreadmemd)
7. [Infrastructure & Orchestration (`k8s/`)](#6-infrastructure--orchestration-k8s)
   - [k8s/backend-deployment.yaml](#k8sbackend-deploymentyaml)
   - [k8s/frontend-deployment.yaml](#k8sfrontend-deploymentyaml)
   - [k8s/huey-worker-deployment.yaml](#k8shuey-worker-deploymentyaml)
   - [k8s/kafka-cluster.yaml](#k8skafka-clusteryaml)
   - [k8s/postgres-deployment.yaml](#k8spostgres-deploymentyaml)
   - [k8s/redis-deployment.yaml](#k8sredis-deploymentyaml)
8. [Automated Verification & Tests (`tests/`)](#7-automated-verification--tests-tests)
   - [tests/test_end_to_end_stream.py](#teststest_end_to_end_streampy)
   - [tests/test_geo_predictor.py](#teststest_geo_predictorpy)
9. [Root Project Configuration & Docs](#8-root-project-configuration--docs)
   - [README.md](#readmemd)
   - [WORKFLOW_END_TO_END.md](#workflow_end_to_endmd)
   - [.env.example](#envexample)
   - [.gitignore](#gitignore)

---

# 1. Backend & API Layer (`backend/`)

---

### `backend/api_gateway.py`
* **1. One–Two Line Summary:**  
  The central FastAPI orchestrator that ingests live transactions from Kafka, runs instant AI fraud detection and geospatial clustering, and broadcasts live WebSocket alerts to the dashboard.
* **2. How It Works:**  
  When a transaction arrives (via HTTP or Kafka), it extracts live features using `SlidingWindowFeatureEngine`, predicts fraud using `FraudScorer`, and if high-risk, passes coordinates to `GeospatialPredictor` to identify nearby ATM targets. It stores records in the database, pushes alerts over WebSockets, and offloads heavy police/bank actions to background worker queues.
* **3. Tech Stack Used:**  
  Python, FastAPI, Starlette WebSockets, SQLAlchemy, Pydantic, asyncio, aiokafka, Redis.
* **4. Where It Is Used / Connected:**  
  Connected to `frontend/src/hooks/useAlertStream.js` (WebSockets & REST API), `backend/streaming/kafka_client.py`, `backend/tasks/worker_tasks.py`, and `backend/database/models.py`.
* **5. Key Concepts:**  
  * **API Gateway:** A single entry point that manages all incoming requests and routes them to internal services.  
  * **WebSocket:** A continuous, two-way communication channel that sends instant updates to the browser without refreshing.  
  * **Orchestrator:** A master controller coordinating multiple smaller tools (ML model, spatial index, database, tasks).

---

### `backend/database/models.py`
* **1. One–Two Line Summary:**  
  Defines the database schema and table structures for bank accounts, live transactions, predicted ATM hotspots, police dispatches, and I4C 1930 bank liens.
* **2. How It Works:**  
  Uses SQLAlchemy ORM classes to map Python objects to relational database tables (`banking_transactions`, `cbs_account_profiles`, `mule_hotspots`, `police_dispatches`, `cfcfrms_lien_actions`, `ncrp_complaints`). It sets up primary keys, indexes, and relationships for fast query retrieval.
* **3. Tech Stack Used:**  
  Python, SQLAlchemy ORM, PostgreSQL / SQLite.
* **4. Where It Is Used / Connected:**  
  Used by `backend/api_gateway.py`, `backend/tasks/worker_tasks.py`, and `backend/database/session.py` to read and write all persistent records.
* **5. Key Concepts:**  
  * **ORM (Object-Relational Mapping):** A library technique that lets developers manipulate a SQL database using clean Python code instead of raw SQL strings.  
  * **Database Index:** A data structure that allows database queries to find specific records in microseconds.

---

### `backend/database/session.py`
* **1. One–Two Line Summary:**  
  Creates and manages database connections, thread-safe session pools, and automatically creates tables on startup.
* **2. How It Works:**  
  Reads the `DATABASE_URL` environment variable (supporting PostgreSQL in production or SQLite in local mode). Creates a SQLAlchemy `engine` and `sessionmaker`, and provides a `get_db()` dependency generator for FastAPI endpoints.
* **3. Tech Stack Used:**  
  Python, SQLAlchemy, SQLite, PostgreSQL.
* **4. Where It Is Used / Connected:**  
  Imported by `backend/api_gateway.py` during app startup and REST requests, and by `backend/tasks/worker_tasks.py` to persist async background task updates.
* **5. Key Concepts:**  
  * **Session Pool:** A pool of pre-opened database connections shared among requests for high efficiency.  
  * **Thread-Local Scoped Session:** Ensures each background task or thread gets its own isolated database transaction without race conditions.

---

### `backend/database/__init__.py`
* **1. One–Two Line Summary:**  
  Package initialization file that exposes the database models and session helpers cleanly to other modules.
* **2. How It Works:**  
  Re-exports `Base`, `init_db`, `get_db`, and all ORM models so external files can import them cleanly with `from backend.database import ...`.
* **3. Tech Stack Used:**  
  Python.
* **4. Where It Is Used / Connected:**  
  Used across `backend/` and test suites for convenient package-level imports.
* **5. Key Concepts:**  
  * **Python Package `__init__`:** A special file that turns a directory into an importable Python module.

---

### `backend/streaming/kafka_client.py`
* **1. One–Two Line Summary:**  
  Asynchronous Apache Kafka producer and consumer client for high-throughput streaming of raw banking transactions.
* **2. How It Works:**  
  Uses `aiokafka` to asynchronously connect to the Kafka broker. Listens to the `raw-transactions` topic in an event loop and feeds each incoming transaction message to the API Gateway's real-time detection pipeline.
* **3. Tech Stack Used:**  
  Python, `aiokafka`, `asyncio`, Apache Kafka.
* **4. Where It Is Used / Connected:**  
  Started inside `backend/api_gateway.py` startup event; receives messages emitted by `data_simulation/kafka_producer.py`.
* **5. Key Concepts:**  
  * **Message Queue / Kafka:** A high-speed pipeline for streaming millions of events between independent computer programs without dropping data.  
  * **Consumer Group:** A coordinated group of workers sharing the work of reading messages from a queue.

---

### `backend/tasks/huey_app.py`
* **1. One–Two Line Summary:**  
  Configures the lightweight Huey background task queue backed by SQLite or Redis.
* **2. How It Works:**  
  Initializes a `SqliteHuey` or `RedisHuey` instance depending on environment settings. It gives workers a fast queue to run non-blocking asynchronous jobs.
* **3. Tech Stack Used:**  
  Python, Huey (Python Task Queue), SQLite / Redis.
* **4. Where It Is Used / Connected:**  
  Imported by `backend/tasks/worker_tasks.py` and `backend/tasks/worker.py` to register and execute background tasks.
* **5. Key Concepts:**  
  * **Task Queue:** A background processing system where long-running jobs wait their turn to execute without making the user wait.

---

### `backend/tasks/worker.py`
* **1. One–Two Line Summary:**  
  The entry point script to run the standalone Huey background worker process.
* **2. How It Works:**  
  When run from the command line (`python -m backend.tasks.worker`), it boots the Huey consumer process, continuously pulling queued tasks and executing them in the background.
* **3. Tech Stack Used:**  
  Python, Huey consumer.
* **4. Where It Is Used / Connected:**  
  Run in Docker/Kubernetes (`k8s/huey-worker-deployment.yaml`) as an independent background worker container.
* **5. Key Concepts:**  
  * **Worker Process:** A background program running in the background that performs heavy lifting like sending emails or calling slow external APIs.

---

### `backend/tasks/worker_tasks.py`
* **1. One–Two Line Summary:**  
  Contains the background worker functions for dispatching police (ERSS 112), freezing bank accounts (CFCFRMS 1930), sending emails, and locking ATM dispensers.
* **2. How It Works:**  
  Defines decorated async tasks (`task_async_dispatch_pcr`, `task_async_trigger_cfcfrms_lien`, `task_async_broadcast_alert`, `task_async_restrict_atm`, `task_async_compile_incident_report`). When called, they run outside the main HTTP thread, contact external APIs, and record results in the database.
* **3. Tech Stack Used:**  
  Python, Huey, SQLAlchemy, JSON, Time.
* **4. Where It Is Used / Connected:**  
  Called by `backend/api_gateway.py` whenever a fraud alert is confirmed or an operator clicks an action button on the dashboard.
* **5. Key Concepts:**  
  * **Asynchronous Task Execution:** Running a task in the background so the main application stays fast and responsive.

---

### `backend/tasks/__init__.py`
* **1. One–Two Line Summary:**  
  Package initialization file for background tasks.
* **2. How It Works:**  
  Exposes Huey worker task functions for clean importing across the backend.
* **3. Tech Stack Used:**  
  Python.
* **4. Where It Is Used / Connected:**  
  Imported by `backend/api_gateway.py`.
* **5. Key Concepts:**  
  * **Module Export:** Re-exporting functions for cleaner code organization.

---

### `backend/alerts/broadcaster.py`
* **1. One–Two Line Summary:**  
  Dispatches multi-channel urgent alerts (Email via Resend API, SMS, Webhooks) to police nodal officers and cyber defense centers.
* **2. How It Works:**  
  Takes high-risk hotspot data, formats human-readable threat notifications, and sends emails through the Resend REST API to designated nodal officers. It also includes hooks for SMS and webhook gateways.
* **3. Tech Stack Used:**  
  Python, `urllib.request`, Resend Email API, JSON.
* **4. Where It Is Used / Connected:**  
  Called by `backend/tasks/worker_tasks.py` during `task_async_broadcast_alert` when a critical mule cluster is formed.
* **5. Key Concepts:**  
  * **Multi-Channel Alerting:** Sending emergency messages across multiple platforms (email, SMS, webhooks) simultaneously to ensure quick response.

---

### `backend/alerts/report_generator.py`
* **1. One–Two Line Summary:**  
  Generates standardized Law Enforcement Incident Reports and Evidence Briefs in Markdown and PDF/Text formats.
* **2. How It Works:**  
  Compiles hotspot details, target ATM locations, involved mule bank accounts, total funds at risk, and timestamps into a formal evidence dossier ready to be submitted to court or senior police officials.
* **3. Tech Stack Used:**  
  Python, String formatting, JSON, Datetime.
* **4. Where It Is Used / Connected:**  
  Triggered by `backend/api_gateway.py` (`/api/v1/actions/generate-report`) and `backend/tasks/worker_tasks.py`.
* **5. Key Concepts:**  
  * **Incident Report / Evidence Dossier:** A formal, audit-ready summary of cybercrime facts used by police officers for legal and operational actions.

---

### `backend/alerts/__init__.py`
* **1. One–Two Line Summary:**  
  Package initialization for alerts and reporting tools.
* **2. How It Works:**  
  Exposes `broadcast_to_agencies` and `generate_incident_report`.
* **3. Tech Stack Used:**  
  Python.
* **4. Where It Is Used / Connected:**  
  Imported in `backend/tasks/worker_tasks.py`.
* **5. Key Concepts:**  
  * **Package Initializer:** Defines public exports for the alerts module.

---

### `backend/integrations/cfcfrms_client.py`
* **1. One–Two Line Summary:**  
  Integration client for the Indian Cyber Crime Coordination Centre (I4C) **CFCFRMS / 1930 Cyber Fraud Helpline** to place emergency bank account liens.
* **2. How It Works:**  
  Formats and sends bank freeze requests (locking ATM cards, UPI, net banking) to Core Banking Systems. Uses real HTTPS requests if production keys are set, or generates realistic mock reference IDs for testing and simulations.
* **3. Tech Stack Used:**  
  Python, `urllib.request`, JSON, Logging.
* **4. Where It Is Used / Connected:**  
  Called by `backend/tasks/worker_tasks.py` (`task_async_trigger_cfcfrms_lien`) and `backend/api_gateway.py`.
* **5. Key Concepts:**  
  * **Account Lien / Debit Freeze:** A legal lock that prevents suspects from withdrawing stolen money.  
  * **CFCFRMS (1930):** The central Indian government platform coordinating cybercrime bank freezes.

---

### `backend/integrations/erss_cad_client.py`
* **1. One–Two Line Summary:**  
  Integration client for State Police Emergency Response Support System (**ERSS 112 CAD**) to dispatch patrol vans to target ATMs.
* **2. How It Works:**  
  Packages GPS coordinates, target ATM kiosk names, priority tiers, and Google Maps routing URLs, transmitting an emergency dispatch call to State Police Control Rooms (PSAP).
* **3. Tech Stack Used:**  
  Python, `urllib.request`, JSON, Logging.
* **4. Where It Is Used / Connected:**  
  Called by `backend/tasks/worker_tasks.py` during `task_async_dispatch_pcr` when an imminent ATM cash-out is detected.
* **5. Key Concepts:**  
  * **CAD (Computer-Aided Dispatch):** Software used by 112/911 police operators to track and send police vehicles to incident locations.  
  * **PSAP (Public Safety Answering Point):** The centralized emergency call center for police.

---

### `backend/integrations/ncrp_client.py`
* **1. One–Two Line Summary:**  
  Adapter for ingesting citizen fraud complaints from the National Cyber Crime Reporting Portal (**NCRP / 1930**).
* **2. How It Works:**  
  Takes 14-digit citizen complaint acknowledgment numbers, victim details, and suspect accounts, standardizing them into the internal threat graph to trigger predictive tracking.
* **3. Tech Stack Used:**  
  Python, `urllib.request`, JSON.
* **4. Where It Is Used / Connected:**  
  Invoked in `backend/api_gateway.py` (`/api/v1/complaints/ingest-1930`) when a new victim report arrives.
* **5. Key Concepts:**  
  * **NCRP:** The official online portal (cybercrime.gov.in) where Indian citizens report cyber frauds.  
  * **Money Restoration Module (MRM):** The backend process that traces and recovers stolen money back to victims.

---

### `backend/integrations/npci_nfs_client.py`
* **1. One–Two Line Summary:**  
  Adapter for the NPCI **National Financial Switch (NFS)** to temporarily restrict ATM cash dispensers or enforce extra biometric challenges.
* **2. How It Works:**  
  Transmits an emergency lock instruction for specific physical ATM terminal IDs during high-risk mule convergence, stopping fraudsters from pulling out cash at the machine.
* **3. Tech Stack Used:**  
  Python, JSON, Logging.
* **4. Where It Is Used / Connected:**  
  Called by `backend/tasks/worker_tasks.py` (`task_async_restrict_atm`) and `backend/api_gateway.py`.
* **5. Key Concepts:**  
  * **NFS (National Financial Switch):** The backbone network in India that connects all bank ATMs and cash dispensers.  
  * **Terminal Restriction:** Programmatically disabling cash dispensing at a specific ATM machine during an active cyber attack.

---

### `backend/integrations/__init__.py`
* **1. One–Two Line Summary:**  
  Re-exports all integration clients for law enforcement and banking networks.
* **2. How It Works:**  
  Aggregates `cfcfrms_client`, `erss_cad_client`, `ncrp_client`, and `npci_nfs_client` for clean imports.
* **3. Tech Stack Used:**  
  Python.
* **4. Where It Is Used / Connected:**  
  Imported across the backend.
* **5. Key Concepts:**  
  * **Facade / Module Aggregator:** Grouping related external clients in one clean package.

---

### `backend/Dockerfile`
* **1. One–Two Line Summary:**  
  Containerization recipe to package the Python backend into a production-ready Docker container.
* **2. How It Works:**  
  Uses a lightweight Python base image, installs system libraries (like OpenMP for AI inference), installs Python dependencies from `requirements.txt`, and configures the default startup command using `uvicorn`.
* **3. Tech Stack Used:**  
  Docker, Linux, Uvicorn, Python.
* **4. Where It Is Used / Connected:**  
  Used in Kubernetes (`k8s/backend-deployment.yaml`) and Docker builds to deploy the backend microservice.
* **5. Key Concepts:**  
  * **Docker Container:** A lightweight, self-contained software package that runs reliably on any computer or cloud server.

---

### `backend/requirements.txt`
* **1. One–Two Line Summary:**  
  Lists all third-party Python packages required to run the backend API and worker processes.
* **2. How It Works:**  
  Read by `pip install -r requirements.txt` during setup or Docker builds to install dependencies like FastAPI, Uvicorn, SQLAlchemy, aiokafka, redis, huey, and scikit-learn.
* **3. Tech Stack Used:**  
  Pip package management.
* **4. Where It Is Used / Connected:**  
  Referenced during environment setup and inside `backend/Dockerfile`.
* **5. Key Concepts:**  
  * **Dependency Management:** Specifying exact library versions required for a program to function without version conflicts.

---

# 2. Geospatial Engine (`geospatial_engine/`)

---

### `geospatial_engine/geo_predictor.py`
* **1. One–Two Line Summary:**  
  The core geospatial prediction engine that groups flagged transactions into geographical clusters and predicts exact ATM cash-out targets.
* **2. How It Works:**  
  Takes flagged high-risk transactions, maps them to Uber H3 hexagons, runs spatio-temporal clustering (`SpatioTemporalClusterEngine`), queries Redis GEO (or in-memory spatial indexes) for nearest ATMs, and calculates cash-out ETA windows.
* **3. Tech Stack Used:**  
  Python, Uber H3 Spatial Index, Redis Geospatial, Haversine Math.
* **4. Where It Is Used / Connected:**  
  Instantiated in `backend/api_gateway.py` and tested in `tests/test_geo_predictor.py`.
* **5. Key Concepts:**  
  * **Geospatial Prediction:** Estimating physical real-world locations where criminals will act based on digital footprints.  
  * **ETA Cash-Out Window:** The estimated 15–30 minute countdown before a mule physically arrives at an ATM.

---

### `geospatial_engine/cluster_engine.py`
* **1. One–Two Line Summary:**  
  Implements Spatio-Temporal Clustering (ST-DBSCAN) to group suspicious transactions occurring close in both distance and time.
* **2. How It Works:**  
  Calculates the physical distance (using Haversine spherical math) and time gap between transactions. Transactions occurring within 1.0 km and 30 minutes of each other are grouped into a single high-priority threat cluster.
* **3. Tech Stack Used:**  
  Python, Scikit-learn DBSCAN (with pure-Python fallback algorithm), NumPy, Math.
* **4. Where It Is Used / Connected:**  
  Called internally by `geospatial_engine/geo_predictor.py`.
* **5. Key Concepts:**  
  * **Spatio-Temporal Clustering:** Finding groups of events that happen close together in both space (geography) and time (minutes).  
  * **Haversine Formula:** A mathematical formula to calculate the distance between two GPS points on Earth.

---

### `geospatial_engine/h3_indexer.py`
* **1. One–Two Line Summary:**  
  Wrapper for Uber’s H3 Discrete Global Grid System, converting GPS coordinates into hexagonal spatial cells and GeoJSON boundary polygons.
* **2. How It Works:**  
  Converts `(latitude, longitude)` into an H3 hexagonal index at Resolution 8 (city neighborhood ~700m) or Resolution 9 (street/kiosk ~100m) and generates GeoJSON polygon boundary rings for rendering on interactive maps.
* **3. Tech Stack Used:**  
  Python, `h3-py` (Uber H3 Discrete Global Grid).
* **4. Where It Is Used / Connected:**  
  Used by `geospatial_engine/geo_predictor.py` and `ml_inference/geo/h3_mapper.py`.
* **5. Key Concepts:**  
  * **Uber H3:** A global hexagonal spatial grid system developed by Uber to divide the world into equal-sized hexagons for fast geospatial lookups.  
  * **GeoJSON Polygon:** A standardized web format for representing geographic shapes and borders on maps.

---

### `geospatial_engine/models.py`
* **1. One–Two Line Summary:**  
  Pydantic data schemas representing geospatial entities, ATM points of interest, clusters, and prediction results.
* **2. How It Works:**  
  Defines strict data models (`ATMPointOfInterest`, `SpatialCluster`, `CashoutPredictionResult`, `HotspotSummary`) with type validation for clean data flow between the AI engine and the frontend.
* **3. Tech Stack Used:**  
  Python, Pydantic.
* **4. Where It Is Used / Connected:**  
  Imported across `geospatial_engine/` and `backend/api_gateway.py`.
* **5. Key Concepts:**  
  * **Data Schema:** A blueprint defining the exact fields, types, and constraints required for a piece of data.

---

### `geospatial_engine/config.py`
* **1. One–Two Line Summary:**  
  Holds default geospatial configuration constants like spatial radius, temporal windows, and H3 resolutions.
* **2. How It Works:**  
  Defines `GeoEngineConfig` class containing parameters such as `SPATIAL_EPS_KM = 1.0`, `TEMPORAL_EPS_SECONDS = 1800` (30 mins), and H3 resolution levels.
* **3. Tech Stack Used:**  
  Python dataclasses / constants.
* **4. Where It Is Used / Connected:**  
  Imported by `cluster_engine.py`, `geo_predictor.py`, and `h3_indexer.py`.
* **5. Key Concepts:**  
  * **Configuration Module:** Storing system settings in a single place to make tuning easy without changing core logic.

---

### `geospatial_engine/__init__.py`
* **1. One–Two Line Summary:**  
  Package initialization file for the geospatial engine.
* **2. How It Works:**  
  Exposes `GeospatialPredictor`, `H3SpatialIndexer`, and `SpatioTemporalClusterEngine` for clean importing.
* **3. Tech Stack Used:**  
  Python.
* **4. Where It Is Used / Connected:**  
  Imported by `backend/api_gateway.py` and test suites.
* **5. Key Concepts:**  
  * **Package Entry Point:** Exposing primary classes at the top module level.

---

### `geospatial_engine/README.md`
* **1. One–Two Line Summary:**  
  Technical documentation explaining the mathematical and spatial concepts behind the geospatial prediction engine.
* **2. How It Works:**  
  Provides developers with architectural overviews of H3 indexing, ST-DBSCAN clustering, and Redis GEO algorithms.
* **3. Tech Stack Used:**  
  Markdown.
* **4. Where It Is Used / Connected:**  
  Reference document for developers and evaluators.
* **5. Key Concepts:**  
  * **Documentation:** Clear guides explaining how the math and code work together.

---

# 3. Machine Learning & Real-Time Inference (`ml_inference/`)

---

### `ml_inference/models/fraud_scorer.py`
* **1. One–Two Line Summary:**  
  Ultra-fast ML inference engine using compiled Treelite GTIL decision trees (<50 microseconds) and heuristic overrides to score transaction fraud probabilities.
* **2. How It Works:**  
  Converts extracted feature objects into a numeric matrix, passes them to a pre-compiled Treelite decision tree model, applies rule-based heuristic overrides (such as sudden dormancy breaks and high fan-out degrees), and returns a risk score from 0.0 to 1.0.
* **3. Tech Stack Used:**  
  Python, Treelite GTIL, NumPy, Scikit-Learn.
* **4. Where It Is Used / Connected:**  
  Used in `backend/api_gateway.py` on every live incoming transaction.
* **5. Key Concepts:**  
  * **Treelite GTIL:** A compiler that converts trained machine learning decision tree models into super-fast native C code for microsecond execution.  
  * **Heuristic Override:** A strict safety rule (like "if account was dormant 90 days and suddenly receives ₹5 lakh, flag immediately") that guarantees detection even if ML is uncertain.

---

### `ml_inference/features/sliding_window.py`
* **1. One–Two Line Summary:**  
  High-speed feature extraction engine that tracks velocity, fan-out degrees, and dormancy breaks using Redis in-memory storage.
* **2. How It Works:**  
  Maintains rolling transaction histories for each bank account in Redis (using sorted sets and hashes). Computes incoming/outgoing transaction counts in the last 1 minute (`v1`) and 5 minutes (`v5`), checks account dormancy, and tracks device/IP reuse.
* **3. Tech Stack Used:**  
  Python, Redis (Sorted Sets, Hashes, Pipelines), Dataclasses.
* **4. Where It Is Used / Connected:**  
  Called in `backend/api_gateway.py` right before passing transactions to `FraudScorer`.
* **5. Key Concepts:**  
  * **Sliding Window:** Looking back over a fixed time period (e.g., last 5 minutes) to count how fast money is moving.  
  * **Velocity (v1 / v5):** The speed and count of transactions passing through an account in 1 or 5 minutes.  
  * **Fan-Out Degree:** When one bank account suddenly sends money to many different accounts at once (classic smurfing behavior).

---

### `ml_inference/geo/h3_mapper.py`
* **1. One–Two Line Summary:**  
  Lightweight utility inside the ML pipeline for fast spatial mapping of coordinates to H3 hex IDs.
* **2. How It Works:**  
  Wraps H3 conversion functions specifically formatted for ML feature vectors and batch processing.
* **3. Tech Stack Used:**  
  Python, Uber H3.
* **4. Where It Is Used / Connected:**  
  Used during ML feature preparation and batch training data creation.
* **5. Key Concepts:**  
  * **Spatial Feature:** Turning geographic coordinates into discrete category codes that machine learning models can learn from.

---

### `ml_inference/core/schemas.py`
* **1. One–Two Line Summary:**  
  Pydantic data models for transaction events, account metadata, extracted features, and inference results.
* **2. How It Works:**  
  Enforces strict data types for `TransactionEvent`, `AccountMetadata`, `ExtractedFeatures`, and `InferenceResult`, ensuring data integrity across the machine learning pipeline.
* **3. Tech Stack Used:**  
  Python, Pydantic.
* **4. Where It Is Used / Connected:**  
  Imported across `ml_inference/` and by `backend/api_gateway.py`.
* **5. Key Concepts:**  
  * **Data Validation:** Automatic checking that all incoming transaction fields have the right format (e.g., positive numbers, valid strings).

---

### `ml_inference/core/config.py`
* **1. One–Two Line Summary:**  
  Configuration parameters for the ML inference service, such as threshold cutoffs and feature names.
* **2. How It Works:**  
  Defines thresholds (e.g., high-risk cutoff = 0.70, critical cutoff = 0.85) and path references to saved models.
* **3. Tech Stack Used:**  
  Python.
* **4. Where It Is Used / Connected:**  
  Used by `FraudScorer` and `sliding_window.py`.
* **5. Key Concepts:**  
  * **Threshold:** A cutoff number used to decide whether an account is classified as suspicious or safe.

---

### `ml_inference/core/logger.py`
* **1. One–Two Line Summary:**  
  Standardized JSON and structured logging configuration for the ML inference subsystem.
* **2. How It Works:**  
  Sets up Python logging with uniform timestamps and log formatting for easy debugging and log aggregation.
* **3. Tech Stack Used:**  
  Python `logging`.
* **4. Where It Is Used / Connected:**  
  Imported across `ml_inference/` modules.
* **5. Key Concepts:**  
  * **Structured Logging:** Writing logs in a clean, predictable format so humans and log monitoring tools can easily analyze errors.

---

### `ml_inference/models/train_mule_detector.py`
* **1. One–Two Line Summary:**  
  Offline training script that trains an XGBoost / LightGBM decision tree model on synthetic mule datasets and compiles it into Treelite GTIL binary format.
* **2. How It Works:**  
  Loads `mule_ml_training_dataset.parquet`, splits data into train/test sets, trains an XGBoost classifier, evaluates precision/recall/ROC-AUC, and exports `mule_model.treelite` for microsecond production inference.
* **3. Tech Stack Used:**  
  Python, XGBoost, Treelite, Pandas, Scikit-Learn, Parquet.
* **4. Where It Is Used / Connected:**  
  Run during model development to output `ml_inference/models/saved/mule_model.treelite`.
* **5. Key Concepts:**  
  * **Model Training:** Teaching an AI algorithm to recognize patterns of cybercrime using historical or simulated examples.  
  * **Model Serialization / Compilation:** Saving a trained AI brain into a fast binary file that can be loaded instantly in production.

---

### `ml_inference/ARCHITECTURE.md`
* **1. One–Two Line Summary:**  
  Comprehensive architecture design document detailing the sub-millisecond AI inference pipeline.
* **2. How It Works:**  
  Explains the mathematical theory, feature engineering formulas, and Treelite GTIL compilation pipeline to engineers and auditors.
* **3. Tech Stack Used:**  
  Markdown.
* **4. Where It Is Used / Connected:**  
  Architectural reference for developers and technical evaluators.
* **5. Key Concepts:**  
  * **System Architecture:** High-level blueprint showing how hardware and software components connect.

---

# 4. Data Simulation & Synthetic Generator (`data_simulation/`)

---

### `data_simulation/kafka_producer.py`
* **1. One–Two Line Summary:**  
  High-speed transaction traffic generator that simulates normal banking streams and injects coordinated cybercrime mule attacks into Kafka.
* **2. How It Works:**  
  Generates transactions at configurable transactions-per-second (TPS). In background threads, it injects multi-hop smurfing attacks across money mule chains and pushes them directly to the `raw-transactions` Kafka topic.
* **3. Tech Stack Used:**  
  Python, `kafka-python`, threading, JSON, random.
* **4. Where It Is Used / Connected:**  
  Sends messages consumed by `backend/streaming/kafka_client.py` and `backend/api_gateway.py`.
* **5. Key Concepts:**  
  * **Traffic Generator:** A tool that mimics real-world user activity by creating thousands of realistic simulated transactions.  
  * **TPS (Transactions Per Second):** A metric measuring how many transactions a system handles every second.

---

### `data_simulation/generate_mule_chains.py`
* **1. One–Two Line Summary:**  
  Generates realistic multi-layer money mule networks (Layer 1 Smurfing $\rightarrow$ Layer 2 Aggregation $\rightarrow$ Layer 3 ATM Cash-Out) and simulated NCRP 1930 complaints.
* **2. How It Works:**  
  Creates synthetic bank account profiles with varying KYC risk, device IDs, and dormancy statuses. Builds complex money laundering topologies (APK RAT frauds, investment scams, digital arrest scams) and outputs JSON datasets.
* **3. Tech Stack Used:**  
  Python, JSON, Random.
* **4. Where It Is Used / Connected:**  
  Generates data files used by `seed_redis.py`, `build_training_dataset.py`, and `kafka_producer.py`.
* **5. Key Concepts:**  
  * **Money Mule Chain:** A network of compromised accounts through which stolen money is split and bounced to evade detection before being withdrawn as cash.  
  * **Multi-Layer Smurfing:** Breaking large stolen amounts into small sums and transferring them through several intermediate accounts.

---

### `data_simulation/generate_atm_locations.py`
* **1. One–Two Line Summary:**  
  Generates realistic high-density ATM and AePS cash kiosk location datasets across key metro hubs (Delhi-NCR, Mumbai, Bangalore).
* **2. How It Works:**  
  Synthesizes realistic GPS coordinates, bank names (SBI, HDFC, ICICI, PNB), IFSC prefixes, and commercial street addresses around major market hubs and metro stations.
* **3. Tech Stack Used:**  
  Python, JSON, Random.
* **4. Where It Is Used / Connected:**  
  Outputs `data_simulation/data/atm_locations.json`, used by `geospatial_engine/geo_predictor.py` and `seed_redis.py`.
* **5. Key Concepts:**  
  * **Synthetic Geodata:** Artificial but mathematically realistic geographic coordinates used to test spatial algorithms without privacy restrictions.

---

### `data_simulation/build_training_dataset.py`
* **1. One–Two Line Summary:**  
  Builds balanced, feature-engineered datasets (Parquet format) containing millions of simulated normal and fraud transactions for ML model training.
* **2. How It Works:**  
  Extracts sliding window features (velocities, fan-out degrees, dormancy breaks, KYC risk) for both legitimate and mule transactions, labels them (`is_mule = 0 or 1`), and exports a compressed Apache Parquet file.
* **3. Tech Stack Used:**  
  Python, Pandas, PyArrow / FastParquet, NumPy.
* **4. Where It Is Used / Connected:**  
  Outputs `mule_ml_training_dataset.parquet`, which is consumed by `train_mule_detector.py`.
* **5. Key Concepts:**  
  * **Apache Parquet:** A high-performance, compressed columnar data storage format ideal for machine learning datasets.

---

### `data_simulation/seed_redis.py`
* **1. One–Two Line Summary:**  
  Initializes and bulk-loads Redis with account profiles (CBS master store) and ATM coordinates (Redis Geospatial index).
* **2. How It Works:**  
  Uses fast Redis pipelining to load thousands of bank account metadata records into `account:<id>` hashes and registers all ATM coordinates into the `atms:geo` geospatial index for sub-millisecond radius lookups.
* **3. Tech Stack Used:**  
  Python, `redis-py` (GEOADD, HSET, Pipelines).
* **4. Where It Is Used / Connected:**  
  Run during system setup to prepare Redis for `backend/api_gateway.py` and `geospatial_engine/geo_predictor.py`.
* **5. Key Concepts:**  
  * **Redis Pipeline:** Sending multiple commands to Redis in a single network batch to drastically speed up data loading.  
  * **Redis GEO Index:** Built-in Redis capability to store GPS coordinates and find points within a given kilometer radius in microseconds.

---

### `data_simulation/simulation_config.json`
* **1. One–Two Line Summary:**  
  Configuration file containing parameters for attack scenarios, crime categories, C2 IP ranges, and mule generation rules.
* **2. How It Works:**  
  Provides standardized definitions of fraud categories (e.g., `APK_RAT_FRAUD`, `DIGITAL_ARREST_SCAM`, `TASK_INVESTMENT_FRAUD`) and simulation parameters used across generators.
* **3. Tech Stack Used:**  
  JSON.
* **4. Where It Is Used / Connected:**  
  Read by `generate_mule_chains.py` and `kafka_producer.py`.
* **5. Key Concepts:**  
  * **Simulation Configuration:** Central file defining all fraud patterns and rules used by test generators.

---

### `data_simulation/requirements.txt`
* **1. One–Two Line Summary:**  
  Lists dependencies required specifically for data generation, Kafka publishing, and dataset building.
* **2. How It Works:**  
  Installs packages like `kafka-python`, `pandas`, `pyarrow`, `faker`, and `redis`.
* **3. Tech Stack Used:**  
  Pip package management.
* **4. Where It Is Used / Connected:**  
  Used during setup of the simulation environment.
* **5. Key Concepts:**  
  * **Subsystem Dependencies:** Modular requirement list for running generator scripts independently.

---

### `data_simulation/pitch_deck_strategy.md`
* **1. One–Two Line Summary:**  
  Strategic presentation brief outlining the project's value proposition, government impact (I4C MHA), and system architecture for hackathon judging.
* **2. How It Works:**  
  Contains pitch narrative, executive summaries, operational workflows, and competitive differentiators for SIH evaluation.
* **3. Tech Stack Used:**  
  Markdown.
* **4. Where It Is Used / Connected:**  
  Pitching, presentation, and evaluation reference.
* **5. Key Concepts:**  
  * **Pitch Deck Strategy:** High-level summary connecting technical achievements with real-world law enforcement impact.

---

### `data_simulation/__init__.py`
* **1. One–Two Line Summary:**  
  Package initialization file for data simulation tools.
* **2. How It Works:**  
  Allows scripts in `data_simulation` to be imported as Python modules.
* **3. Tech Stack Used:**  
  Python.
* **4. Where It Is Used / Connected:**  
  Used when importing generator functions across tools.
* **5. Key Concepts:**  
  * **Python Module Namespace:** Organizing standalone scripts into an importable library.

---

### `data_simulation/data/` (Datasets & Databases)
* **1. `account_profiles.json`:** JSON list of simulated legitimate and mule bank accounts with KYC and dormancy statuses.
* **2. `atm_locations.json`:** JSON list of physical ATM locations in Delhi-NCR with GPS coordinates, bank names, and addresses.
* **3. `mule_transaction_chains.json`:** Simulated multi-hop money laundering transaction graphs.
* **4. `ncrp_crime_distribution.json`:** Statistical distribution of cybercrime types based on national NCRP 1930 trends.
* **5. `mule_ml_training_dataset.parquet`:** Compressed ML training dataset with extracted feature vectors and fraud labels.
* **6. `geocashwatch.db` & `huey_tasks.db`:** SQLite local database files used during offline local development for relational data and background queues.

---

# 5. Frontend Dashboard (`frontend/`)

---

### `frontend/src/App.jsx`
* **1. One–Two Line Summary:**  
  Main React UI component orchestrating the cybercrime command dashboard layout, real-time KPI metrics, and drilldown modals.
* **2. How It Works:**  
  Uses the custom `useAlertStream` hook to listen to live backend events. Displays the top navigation bar, KPI summary cards (Active Hotspots, Funds at Risk, Flagged Events, Stream Volume), interactive `ThreatMap`, `LiveTransactionFeed`, and opens `ClusterDrilldown` when a hotspot is clicked.
* **3. Tech Stack Used:**  
  React, JSX, Lucide-React Icons, CSS Modules.
* **4. Where It Is Used / Connected:**  
  Rendered by `frontend/src/main.jsx`; connects `ThreatMap`, `LiveTransactionFeed`, and `ClusterDrilldown`.
* **5. Key Concepts:**  
  * **Command Center Dashboard:** A unified, real-time visual interface displaying live intelligence, active threats, and response actions.  
  * **State Management:** Tracking current alerts, selected hotspots, and system health in React memory.

---

### `frontend/src/main.jsx`
* **1. One–Two Line Summary:**  
  The JavaScript entry point that bootstraps the React application and mounts it into the browser DOM.
* **2. How It Works:**  
  Imports React, ReactDOM, `index.css`, and `App.jsx`, rendering the root `<App />` component inside the `<div id="root">` element in `index.html`.
* **3. Tech Stack Used:**  
  React 18, ReactDOM, JavaScript (ES Modules).
* **4. Where It Is Used / Connected:**  
  Loaded by `frontend/index.html`.
* **5. Key Concepts:**  
  * **DOM Mounting:** Attaching a dynamic React component tree to a static HTML page in the web browser.

---

### `frontend/src/index.css`
* **1. One–Two Line Summary:**  
  The complete design system stylesheet featuring a sleek dark-mode aesthetic, radar glowing animations, and responsive grid layouts.
* **2. How It Works:**  
  Defines CSS variables for tactical dark color palettes (cyan, amber, critical red), typography (Inter/JetBrains Mono), glassmorphic panels, scrollbars, and pulsing radar animations for live map markers.
* **3. Tech Stack Used:**  
  Vanilla CSS3, Flexbox, CSS Grid, Keyframe Animations.
* **4. Where It Is Used / Connected:**  
  Imported globally in `frontend/src/main.jsx`.
* **5. Key Concepts:**  
  * **Dark Mode Tactical UI:** A high-contrast dark theme designed for emergency operations centers and cyber monitoring rooms.  
  * **Micro-Animations:** Subtle visual glowing and pulsing effects that draw immediate attention to critical threats.

---

### `frontend/src/components/ThreatMap.jsx`
* **1. One–Two Line Summary:**  
  Interactive Leaflet geospatial map displaying real-time H3 hexagonal threat zones and nearby ATM dispenser markers.
* **2. How It Works:**  
  Uses React-Leaflet on top of Dark Matter CartoDB tiles. Renders color-coded polygons for H3 cells based on risk score (Critical Red $\ge 85\%$, Warning Orange $\ge 65\%$, Watch Yellow) and displays clickable ATM pins.
* **3. Tech Stack Used:**  
  React-Leaflet, Leaflet, CartoDB Dark Tiles, GeoJSON.
* **4. Where It Is Used / Connected:**  
  Embedded inside `frontend/src/App.jsx`.
* **5. Key Concepts:**  
  * **Tile Layer:** Map imagery served in small square image tiles.  
  * **Vector Polygons:** Drawing geometric shapes (like H3 hexagons) directly on top of the map using GPS coordinates.

---

### `frontend/src/components/ClusterDrilldown.jsx`
* **1. One–Two Line Summary:**  
  Modal overlay that opens when an officer clicks a hotspot, allowing them to inspect converging mule accounts and trigger 1-click police dispatch, 1930 liens, or incident reports.
* **2. How It Works:**  
  Displays aggregate risk, funds at risk, estimated cash-out ETA countdown, converging mule account numbers, and ranked target ATMs. Contains action buttons that send POST requests to the backend API (`/dispatch-patrol`, `/freeze-lien`, `/generate-report`).
* **3. Tech Stack Used:**  
  React, Lucide-React, Fetch API, CSS.
* **4. Where It Is Used / Connected:**  
  Rendered conditionally inside `frontend/src/App.jsx` when a user selects a hotspot.
* **5. Key Concepts:**  
  * **Drilldown Modal:** A detailed popup window that allows users to investigate a specific alert in depth and take action.  
  * **1-Click Interception:** Giving operators quick action buttons to instantly freeze accounts or dispatch police without manual paperwork.

---

### `frontend/src/components/LiveTransactionFeed.jsx`
* **1. One–Two Line Summary:**  
  Real-time scrolling ticker showing incoming transactions, fraud risk badges, account transfers, and detection reasons.
* **2. How It Works:**  
  Renders a vertical list of buffered transactions. High-risk transactions are highlighted in red with fraud reasons (e.g., "Rapid velocity + Dormancy break") and formatted currency amounts.
* **3. Tech Stack Used:**  
  React, Lucide-React, CSS.
* **4. Where It Is Used / Connected:**  
  Rendered on the right sidebar of `frontend/src/App.jsx`.
* **5. Key Concepts:**  
  * **Live Activity Feed:** A continuously updating list showing the latest system events in real time.

---

### `frontend/src/hooks/useAlertStream.js`
* **1. One–Two Line Summary:**  
  Custom React hook managing WebSocket connections, auto-reconnection, and high-throughput batching to prevent browser lag.
* **2. How It Works:**  
  Connects to `ws://localhost:8000/ws/alerts`. It buffers high-speed incoming transaction and hotspot messages in memory and flushes them to React state at a smooth 10 FPS interval, preventing UI freezing during heavy transaction spikes.
* **3. Tech Stack Used:**  
  React (`useEffect`, `useState`, `useRef`, `useCallback`), WebSocket API.
* **4. Where It Is Used / Connected:**  
  Imported by `frontend/src/App.jsx`.
* **5. Key Concepts:**  
  * **Custom React Hook:** A reusable function that encapsulates complex stateful logic (like WebSocket networking) cleanly.  
  * **Batching / Throttling:** Collecting multiple rapid events into batches so the browser doesn't slow down re-rendering too often.

---

### `frontend/src/utils/normalize.js`
* **1. One–Two Line Summary:**  
  Data normalization helper that standardizes different payload formats from REST APIs, WebSockets, and mock engines into uniform frontend objects.
* **2. How It Works:**  
  Provides functions (`normalizeHotspot`, `normalizeTransaction`, `normalizeAtm`, `formatCashoutTime`) that extract latitude, longitude, boundary coordinates, and currency values safely even if backend field names vary slightly.
* **3. Tech Stack Used:**  
  JavaScript (ES6).
* **4. Where It Is Used / Connected:**  
  Used across `frontend/src/hooks/useAlertStream.js`, `ThreatMap.jsx`, and `ClusterDrilldown.jsx`.
* **5. Key Concepts:**  
  * **Data Normalization:** Cleaning and formatting varying data shapes into a consistent structure before the UI uses them.

---

### `frontend/vite.config.js`
* **1. One–Two Line Summary:**  
  Vite build configuration file configuring React plugins, local development server ports, and proxy settings.
* **2. How It Works:**  
  Configures `@vitejs/plugin-react` and sets development server defaults for fast hot-module reloading (HMR).
* **3. Tech Stack Used:**  
  Vite, Node.js.
* **4. Where It Is Used / Connected:**  
  Used by Vite when running `npm run dev` or `npm run build`.
* **5. Key Concepts:**  
  * **Vite:** A modern, extremely fast frontend build tool and development server.  
  * **Hot Module Replacement (HMR):** Updating modified code in the browser instantly without requiring a full page refresh.

---

### `frontend/package.json`
* **1. One–Two Line Summary:**  
  Node.js project manifest defining frontend dependencies, scripts, and build tools.
* **2. How It Works:**  
  Declares dependencies (React, Leaflet, Lucide-React) and developer tools (Vite, ESLint). Defines scripts like `npm run dev` and `npm run build`.
* **3. Tech Stack Used:**  
  npm / Node.js.
* **4. Where It Is Used / Connected:**  
  Used by `npm install` and inside `frontend/Dockerfile`.
* **5. Key Concepts:**  
  * **Package Manifest:** A configuration file declaring all JavaScript libraries and project metadata.

---

### `frontend/Dockerfile`
* **1. One–Two Line Summary:**  
  Multi-stage Dockerfile that builds the React application and serves the static production bundle using an ultra-lightweight Nginx web server.
* **2. How It Works:**  
  Stage 1 uses Node.js to run `npm run build`. Stage 2 copies the compiled static HTML/CSS/JS files into an `nginx:alpine` image for high-speed production serving.
* **3. Tech Stack Used:**  
  Docker, Node.js, Nginx Alpine.
* **4. Where It Is Used / Connected:**  
  Used to deploy the dashboard in Kubernetes (`k8s/frontend-deployment.yaml`).
* **5. Key Concepts:**  
  * **Multi-Stage Build:** A Docker best practice that separates the heavy building tools from the tiny production server, creating tiny, secure Docker images.

---

### `frontend/index.html`
* **1. One–Two Line Summary:**  
  The main HTML entry document for the single-page application (SPA).
* **2. How It Works:**  
  Sets up HTML meta tags, loads Google Fonts (Inter, JetBrains Mono), includes Leaflet CSS stylesheets, and hosts the root `<div id="root"></div>` where React renders.
* **3. Tech Stack Used:**  
  HTML5.
* **4. Where It Is Used / Connected:**  
  Served by Vite or Nginx to the user's web browser.
* **5. Key Concepts:**  
  * **Single Page Application (SPA):** A web application that loads a single HTML page and dynamically updates content without reloading.

---

### `frontend/README.md`
* **1. One–Two Line Summary:**  
  Developer instructions for running, building, and configuring the frontend dashboard locally.
* **2. How It Works:**  
  Explains environment variables (`VITE_WS_URL`, `VITE_API_BASE_URL`) and step-by-step setup commands.
* **3. Tech Stack Used:**  
  Markdown.
* **4. Where It Is Used / Connected:**  
  Frontend developer reference.
* **5. Key Concepts:**  
  * **Developer Guide:** Practical instructions for setting up and running software locally.

---

# 6. Infrastructure & Orchestration (`k8s/`)

---

### `k8s/backend-deployment.yaml`
* **1. One–Two Line Summary:**  
  Kubernetes manifest deploying the Geo-CashWatch FastAPI backend with replication, environment configurations, and cluster services.
* **2. How It Works:**  
  Creates a Kubernetes `Deployment` running the backend container and a `Service` exposing port 8000 internally within the cluster.
* **3. Tech Stack Used:**  
  Kubernetes (YAML), Docker.
* **4. Where It Is Used / Connected:**  
  Applied to Kubernetes clusters via `kubectl apply -f k8s/backend-deployment.yaml`.
* **5. Key Concepts:**  
  * **Kubernetes Deployment:** A declarative definition ensuring a specific number of container replicas are always running and healthy.

---

### `k8s/frontend-deployment.yaml`
* **1. One–Two Line Summary:**  
  Kubernetes manifest deploying the Nginx-hosted frontend dashboard container and exposing it to external users.
* **2. How It Works:**  
  Defines a `Deployment` for the React dashboard and a `Service` (LoadBalancer or NodePort) exposing port 80 to web browsers.
* **3. Tech Stack Used:**  
  Kubernetes (YAML).
* **4. Where It Is Used / Connected:**  
  Applied via `kubectl apply -f k8s/frontend-deployment.yaml`.
* **5. Key Concepts:**  
  * **Kubernetes Service:** An abstraction that defines a network endpoint to access a group of running pods.

---

### `k8s/huey-worker-deployment.yaml`
* **1. One–Two Line Summary:**  
  Kubernetes manifest running dedicated background worker containers to process async police dispatches and bank liens.
* **2. How It Works:**  
  Deploys pods that execute `python -m backend.tasks.worker`, continuously consuming and executing jobs from the shared task queue.
* **3. Tech Stack Used:**  
  Kubernetes (YAML).
* **4. Where It Is Used / Connected:**  
  Works alongside `backend-deployment.yaml` in Kubernetes.
* **5. Key Concepts:**  
  * **Background Worker Pod:** An isolated compute pod dedicated to executing async background jobs.

---

### `k8s/kafka-cluster.yaml`
* **1. One–Two Line Summary:**  
  Kubernetes manifest deploying the Apache Kafka event streaming broker and Zookeeper cluster.
* **2. How It Works:**  
  Creates persistent stateful services for Kafka and Zookeeper with internal cluster ports (`9092`) for stream ingestion.
* **3. Tech Stack Used:**  
  Kubernetes, Apache Kafka, Zookeeper.
* **4. Where It Is Used / Connected:**  
  Used as the central message bus for all microservices in Kubernetes.
* **5. Key Concepts:**  
  * **Event Bus:** Central nervous system of a distributed architecture where all events are published and received.

---

### `k8s/postgres-deployment.yaml`
* **1. One–Two Line Summary:**  
  Kubernetes manifest deploying the PostgreSQL relational database with persistent storage volumes.
* **2. How It Works:**  
  Deploys a `postgres:15` container with a `PersistentVolumeClaim` to ensure transaction audit logs and dispatch records are saved permanently.
* **3. Tech Stack Used:**  
  Kubernetes, PostgreSQL.
* **4. Where It Is Used / Connected:**  
  Connected to `backend-deployment.yaml` via `DATABASE_URL`.
* **5. Key Concepts:**  
  * **Persistent Volume:** Storage on a server that survives even if a container restarts or crashes.

---

### `k8s/redis-deployment.yaml`
* **1. One–Two Line Summary:**  
  Kubernetes manifest deploying Redis in-memory database for sub-millisecond feature extraction and geospatial ATM lookups.
* **2. How It Works:**  
  Deploys a `redis:7-alpine` container exposing port 6379 for instant in-memory key-value and geospatial queries.
* **3. Tech Stack Used:**  
  Kubernetes, Redis.
* **4. Where It Is Used / Connected:**  
  Connected to the backend API, feature engine, and geospatial predictor.
* **5. Key Concepts:**  
  * **In-Memory Cache:** Storing data in RAM instead of disk for ultra-fast (sub-millisecond) read and write speeds.

---

# 7. Automated Verification & Tests (`tests/`)

---

### `tests/test_end_to_end_stream.py`
* **1. One–Two Line Summary:**  
  End-to-end integration test validating the entire pipeline from transaction ingestion to AI fraud scoring, spatial clustering, and WebSocket alert generation.
* **2. How It Works:**  
  Synthesizes a burst of smurfing transactions, feeds them through `api_gateway.py` / `SlidingWindowFeatureEngine` / `FraudScorer`, and asserts that high-risk transactions are detected with valid fraud probabilities and correct reasons.
* **3. Tech Stack Used:**  
  Python, Pytest, FastAPI TestClient, Unittest.
* **4. Where It Is Used / Connected:**  
  Executed via `pytest tests/test_end_to_end_stream.py` in automated test suites and CI/CD pipelines.
* **5. Key Concepts:**  
  * **End-to-End (E2E) Test:** Testing the entire software journey from input to final output to ensure all components work together seamlessly.

---

### `tests/test_geo_predictor.py`
* **1. One–Two Line Summary:**  
  Unit and integration test verifying H3 hexagonal indexing, spatial clustering, ATM distance calculations, and cash-out window estimation.
* **2. How It Works:**  
  Passes sample coordinates into `GeospatialPredictor` and `H3SpatialIndexer`, asserting that generated H3 cells, nearest ATM rankings, and Haversine distances are mathematically accurate.
* **3. Tech Stack Used:**  
  Python, Pytest, Math.
* **4. Where It Is Used / Connected:**  
  Executed via `pytest tests/test_geo_predictor.py`.
* **5. Key Concepts:**  
  * **Unit Test:** Testing an isolated function or class to verify that its logic produces exact mathematical results.

---

# 8. Root Project Configuration & Docs

---

### `README.md`
* **1. One–Two Line Summary:**  
  The main project landing page providing high-level problem statements, feature highlights, architecture diagrams, and quickstart commands.
* **2. How It Works:**  
  Gives judges, evaluators, and engineers a comprehensive overview of the Geo-CashWatch system, showing how it solves SIH 26184 for the Ministry of Home Affairs.
* **3. Tech Stack Used:**  
  Markdown.
* **4. Where It Is Used / Connected:**  
  Root workspace repository homepage.
* **5. Key Concepts:**  
  * **Project Overview:** High-level executive summary of the entire repository.

---

### `WORKFLOW_END_TO_END.md`
* **1. One–Two Line Summary:**  
  Step-by-step end-to-end operational guide explaining the full lifecycle of a cyber fraud attack from victim complaint to ATM interception.
* **2. How It Works:**  
  Details the 6 operational phases: Victim reporting (1930) $\rightarrow$ Real-time stream ingestion $\rightarrow$ Sub-50µs AI scoring $\rightarrow$ H3 Spatial Clustering $\rightarrow$ 1-Click Bank Liens $\rightarrow$ ERSS 112 Police Dispatch.
* **3. Tech Stack Used:**  
  Markdown.
* **4. Where It Is Used / Connected:**  
  Standard operating procedure (SOP) guide for operators and technical reviewers.
* **5. Key Concepts:**  
  * **Operational Workflow:** Step-by-step description of how humans and machines collaborate during an emergency incident.

---

### `.env.example`
* **1. One–Two Line Summary:**  
  Template file documenting all required environment variables and configuration keys.
* **2. How It Works:**  
  Lists sample keys for `KAFKA_BOOTSTRAP_SERVERS`, `REDIS_URL`, `DATABASE_URL`, `RESEND_API_KEY`, `CFCFRMS_API_KEY`, and `ERSS_CAD_TOKEN` so developers know what settings to provide.
* **3. Tech Stack Used:**  
  Environment file syntax.
* **4. Where It Is Used / Connected:**  
  Copied to `.env` during local installation and referenced across all backend services.
* **5. Key Concepts:**  
  * **Environment Variables:** External settings passed into an application at runtime so secret keys are never hardcoded in source code.

---

### `.gitignore`
* **1. One–Two Line Summary:**  
  Specifies files and folders that Git should ignore and not track in source control.
* **2. How It Works:**  
  Prevents temporary files (`__pycache__`, `.pytest_cache`, `.venv`, `node_modules`, `.env`, build artifacts) from polluting the Git repository.
* **3. Tech Stack Used:**  
  Git configuration.
* **4. Where It Is Used / Connected:**  
  Used automatically by Git during version control operations.
* **5. Key Concepts:**  
  * **Source Control Filter:** Protecting repositories from committing sensitive secrets or bulky auto-generated temporary files.
