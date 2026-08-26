# AEGIS-Geo AI Engine Architecture Blueprint

**Project:** Smart India Hackathon 2026 - PS 26184  
**Module:** AI & Geo Engine  
**Branch:** `feature/ai-engine`

This document outlines the tier-1 fintech production standard architecture for the AI Engine module responsible for real-time cybercrime mule detection and geospatial cash-out predictions.

---

## 1. End-to-End Workflow

The AI Engine operates as a high-throughput, low-latency microservice. It receives streams of transactions, computes stateful features on the fly, evaluates risk using a sub-15ms inference model, and projects the geographic cash-out zone for highly suspicious events.

### Phase A: Ingestion & Feature Engineering
*   **Module:** `features/sliding_window.py`
*   **Mechanism:** Transactions arrive as Pydantic-validated payloads. The sliding window engine maintains an in-memory, highly concurrent state (e.g., using `collections.deque`) to track:
    *   **Velocity Metrics:** Outbound and inbound transaction counts within 1-minute and 5-minute rolling windows.
    *   **Fan-out Degree:** The number of distinct destination accounts funds are sent to within a 180-second window (indicative of smurfing).
    *   **Dormancy Disruption:** Flags if an account, inactive for over 45 days, suddenly receives a high-value spike.
*   **Constraints:** Must execute in $< 2\text{ms}$. No synchronous blocking database calls in the hot path.

### Phase B: The Inference Pipeline
*   **Module:** `models/mule_scorer.py`
*   **Mechanism:** Takes the computed feature vector and evaluates it against a pre-trained ML model (conceptually LightGBM, exported to ONNX for maximum C++ execution speed).
    *   **Model Output:** A calibrated risk score between $0.0$ and $1.0$.
    *   **Heuristic Overrides:** Strict rule-based guards exist around the ML model. If specific patterns (e.g., Fan-out $> 4$ AND Dormancy Disruption) occur, the risk score is deterministically forced to $1.0$ (High Risk) regardless of the model's confidence.
*   **Constraints:** Sub-15ms latency constraint. Model loaded into memory on startup.

### Phase C: The Geospatial Predictor
*   **Module:** `geo/h3_mapper.py`
*   **Mechanism:** When a transaction is flagged as high-risk ($> 0.75$), the digital coordinates of the terminal node are resolved to an Uber H3 Hexagon at **Resolution 9** (~0.1 $\text{km}^2$, the size of a city block or ATM strip).
    *   **Hawkes Process Decay:** A self-exciting point process model is applied. The probability of a cash-out in that hexagon spikes immediately upon the funds hitting the mule account, and decays exponentially over the next 45 minutes, creating a realistic prediction window for law enforcement.

---

## 2. Directory Structure

```text
/ai_engine
├── __init__.py
├── ARCHITECTURE.md                  # This document
├── core/
│   ├── __init__.py
│   ├── config.py                    # Environment variables & constants
│   ├── schemas.py                   # Pydantic data validation models
│   └── logger.py                    # Structured JSON logging configuration
├── features/
│   ├── __init__.py
│   └── sliding_window.py            # Real-time stateful feature extractor
├── models/
│   ├── __init__.py
│   ├── mule_scorer.py               # ML/ONNX Inference wrapper
│   └── artifacts/                   # Holds the .onnx / .pkl model files
│       └── dummy_model.onnx         # Mock model for development
└── geo/
    ├── __init__.py
    └── h3_mapper.py                 # H3 Hexagon indexing and Hawkes Process logic
```

---

## 3. Industry-Grade Constraints Checklist
- [x] **Strict Type Hinting:** All functions and classes will use Python's `typing` module (`List`, `Dict`, `Optional`, etc.).
- [x] **Data Validation:** All inputs/outputs strictly typed via `pydantic.BaseModel`.
- [x] **High Performance:** No heavy ORM calls in the inference path.
- [x] **Observability:** `logging` module utilized with structured outputs (INFO, WARNING, ERROR). No `print()`.
- [x] **Clean Code:** SOLID principles, modular decoupled classes, and PEP-8 compliant docstrings.
