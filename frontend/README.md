# Geo-CashWatch Frontend

React command dashboard for SIH 26184. It visualizes predicted H3 cash-out hotspots, scored transactions, nearby ATM/AePS terminals, and simulated law-enforcement actions.

## Run locally

```bash
npm install
copy .env.example .env
npm run dev
```

The default `.env.example` enables demo mode, so the UI works without the backend. Set `VITE_USE_MOCK_STREAM=false` to consume the FastAPI WebSocket at `ws://localhost:8000/ws/alerts`.

## Backend integration

- WebSocket: `GET /ws/alerts`
- Patrol dispatch: `POST /api/v1/actions/dispatch-patrol`
- Debit freeze: `POST /api/v1/actions/freeze-lien`

Supported WebSocket events: `INITIAL_STATE`, `NEW_TRANSACTION`, `NEW_ALERT`, and `HOTSPOTS_UPDATED`.

The dashboard also responds to `COMPLAINT_REGISTERED`, `PATROL_DISPATCHED`, and `LIEN_PLACED` operational events. Hotspots accept both the harmonized backend fields and the enriched Graph-DB fields, including GeoJSON boundaries, Res-9 cells, mule account lists, and ranked ATM metadata.

## Checks

```bash
npm run lint
npm run build
```
