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

## Checks

```bash
npm run lint
npm run build
```
