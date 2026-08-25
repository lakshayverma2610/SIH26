# 🛡️ Geo-CashWatch (SIH 26184)
> **Predictive Analytics & Geospatial Framework for Cybercrime Mule Network Detection & ATM Cash-Out Interception**

Developed for **Smart India Hackathon (SIH 26184)** — Ministry of Home Affairs (I4C).

---

## 📖 Complete Documentation
For the full end-to-end architecture, data flow pipeline, and testing instructions, read the comprehensive guide:
👉 **[WORKFLOW_END_TO_END.md](WORKFLOW_END_TO_END.md)**

---

## 🚀 Quick Start

### 1. Start the Backend (FastAPI + WebSockets)
```bash
.venv/bin/python -m uvicorn backend.main:app --port 8000 --host 0.0.0.0 --reload
```

### 2. Start the Frontend Dashboard (React + Leaflet)
```bash
cd frontend
npm run dev
```
Access the dashboard at `http://localhost:5173`.

### 3. Launch Live Real-Time Simulator & Inject Attacks
```bash
.venv/bin/python data_engine/live_stream_simulator.py
```
Use the interactive CLI menu:
- `1`: Normal baseline transaction stream
- `2`: Random cybercrime attack scenario
- `3`: Jamtara APK RAT fraud
- `4`: Mewat Sextortion / AePS biometric fraud
