"""
Stream Orchestrator Core Engine
Central pipeline coordinator that ingests real-time transaction streams, extracts behavioral features,
evaluates ML mule risk, updates geospatial cash-out hotspots, and broadcasts alerts.
"""
import sys
import time
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.app.config import (
    ROOT_DIR,
    MAX_RECENT_TRANSACTIONS,
    MAX_FLAGGED_EVENTS_BUFFER,
    ATMS_DATA_PATH,
    ACCOUNTS_DATA_PATH
)
from backend.app.core.connection_manager import ws_manager
from backend.app.core.fallback_geo import get_geospatial_predictor

# Import AI Engine Singletons
from ai_engine.features.sliding_window import SlidingWindowFeatureEngine
from ai_engine.models.mule_scorer import MuleScorer

logger = logging.getLogger("geo_cashwatch.orchestrator")

class StreamOrchestrator:
    def __init__(self):
        # 1. Initialize AI Feature Engine & Mule Scorer Singletons
        self.feature_engine = SlidingWindowFeatureEngine()
        self.mule_scorer = MuleScorer()

        # 2. Initialize Geospatial Predictor
        self.geo_predictor = get_geospatial_predictor(str(ATMS_DATA_PATH) if ATMS_DATA_PATH.exists() else None)

        # 3. In-memory State Buffers
        self.recent_transactions: List[Dict[str, Any]] = []
        self.flagged_events_buffer: List[Dict[str, Any]] = []
        self.active_hotspots: List[Dict[str, Any]] = []
        self.ncrp_complaints: Dict[str, Dict[str, Any]] = {}
        self.dispatched_patrols: List[Dict[str, Any]] = []
        self.placed_liens: List[Dict[str, Any]] = []

        # 4. System Metrics
        self.start_time = time.time()
        self.total_transactions_ingested = 0
        self.total_high_risk_flagged = 0
        self.total_ncrp_complaints_ingested = 0

    async def process_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest, score, buffer, and dispatch live transactions and geospatial alerts.
        """
        self.total_transactions_ingested += 1
        tx_id = tx_data.get("tx_id", f"TXN_{int(time.time()*1000)}")
        src_acc = tx_data.get("src_acc", "")
        dest_acc = tx_data.get("dest_acc", "")
        amount = float(tx_data.get("amount", 0.0))
        lat = tx_data.get("lat", 28.6304)
        lon = tx_data.get("lon", 77.2773)
        channel = tx_data.get("channel", "UPI")
        timestamp = tx_data.get("timestamp") or time.time()

        # Step 1: Extract sliding-window behavioral features
        feats = self.feature_engine.process_and_extract(tx_data)

        # Step 2: Score Mule Risk via ML & Rules
        score_res = self.mule_scorer.score_features(feats)
        fraud_prob = score_res["fraud_probability"]
        is_high_risk = score_res["is_high_risk"]
        reasons = list(score_res.get("reasons", []))

        # Check if destination or source account has an active 1930 NCRP complaint
        if dest_acc in self.ncrp_complaints:
            is_high_risk = True
            fraud_prob = max(fraud_prob, 0.95)
            complaint_info = self.ncrp_complaints[dest_acc]
            reasons.append(f"Linked to NCRP 1930 Complaint ({complaint_info.get('complaint_type', 'CYBER_FRAUD')})")
        elif src_acc in self.ncrp_complaints:
            is_high_risk = True
            fraud_prob = max(fraud_prob, 0.90)
            complaint_info = self.ncrp_complaints[src_acc]
            reasons.append(f"Source linked to NCRP 1930 Complaint ({complaint_info.get('complaint_type', 'CYBER_FRAUD')})")

        # Step 3: Record transaction in sliding buffer (last 100)
        tx_summary = {
            "tx_id": tx_id,
            "src_acc": src_acc,
            "dest_acc": dest_acc,
            "amount": amount,
            "channel": channel,
            "fraud_probability": round(fraud_prob, 4),
            "is_high_risk": is_high_risk,
            "reasons": reasons,
            "lat": lat,
            "lon": lon,
            "timestamp": timestamp
        }

        self.recent_transactions.append(tx_summary)
        if len(self.recent_transactions) > MAX_RECENT_TRANSACTIONS:
            self.recent_transactions.pop(0)

        # Step 4: Broadcast every transaction to live feed for Sneha's dashboard
        asyncio.create_task(ws_manager.broadcast({
            "type": "NEW_TRANSACTION",
            "transaction": tx_summary,
            "timestamp": time.time()
        }))

        # Step 5: If High Risk, buffer for geospatial cash-out clustering & trigger alerts
        if is_high_risk:
            self.total_high_risk_flagged += 1
            self.flagged_events_buffer.append({
                "account_number": dest_acc,
                "lat": lat,
                "lon": lon,
                "amount": amount,
                "fraud_probability": fraud_prob
            })
            if len(self.flagged_events_buffer) > MAX_FLAGGED_EVENTS_BUFFER:
                self.flagged_events_buffer.pop(0)

            # Recalculate active H3 hotspots
            self.active_hotspots = self.geo_predictor.aggregate_hotspots(self.flagged_events_buffer)

            # Broadcast instant alert to all connected dashboards (preserves NEW_ALERT schema)
            alert_payload = {
                "type": "NEW_ALERT",
                "transaction": tx_summary,
                "hotspots": self.active_hotspots,
                "timestamp": time.time()
            }
            asyncio.create_task(ws_manager.broadcast(alert_payload))

            # Broadcast dedicated hotspots update event for map layer refresh
            hotspots_payload = {
                "type": "HOTSPOTS_UPDATED",
                "hotspots": self.active_hotspots,
                "count": len(self.active_hotspots),
                "timestamp": time.time()
            }
            asyncio.create_task(ws_manager.broadcast(hotspots_payload))

        return {
            "status": "PROCESSED",
            "tx_id": tx_id,
            "fraud_score": round(fraud_prob, 4),
            "is_high_risk": is_high_risk,
            "reasons": reasons,
            "features": feats
        }

    async def process_batch(self, tx_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of incoming transactions.
        """
        results = []
        for tx in tx_list:
            res = await self.process_transaction(tx)
            results.append(res)
        return results

    async def register_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new 1930 NCRP victim complaint and cross-reference with suspect accounts.
        """
        self.total_ncrp_complaints_ingested += 1
        ncrp_id = complaint_data.get("ncrp_id")
        suspect_acc = complaint_data.get("suspect_acc")
        amount = float(complaint_data.get("amount", 0.0))
        complaint_type = complaint_data.get("complaint_type", "APK_RAT_FRAUD")
        now = time.time()

        record = {
            "ncrp_id": ncrp_id,
            "victim_acc": complaint_data.get("victim_acc"),
            "suspect_acc": suspect_acc,
            "amount": amount,
            "complaint_type": complaint_type,
            "description": complaint_data.get("description"),
            "timestamp": complaint_data.get("timestamp") or now
        }

        self.ncrp_complaints[suspect_acc] = record

        # Broadcast complaint event to live dashboard
        asyncio.create_task(ws_manager.broadcast({
            "type": "COMPLAINT_REGISTERED",
            "complaint": record,
            "timestamp": now
        }))

        return {
            "status": "REGISTERED",
            "ncrp_id": ncrp_id,
            "suspect_acc": suspect_acc,
            "amount": amount,
            "complaint_type": complaint_type,
            "action_recommended": "TRIGGER_IMMEDIATE_DEBIT_FREEZE",
            "timestamp": now
        }

    async def dispatch_patrol(
        self,
        h3_cell: str,
        unit_id: Optional[str] = None,
        priority: str = "HIGH",
        notes: str = "",
        destination_lat: Optional[float] = None,
        destination_lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Dispatch a PCR / Cyber Patrol Unit to an active H3 cash-out hotspot with Google Maps CAD route.
        """
        call_id = f"PCR-DISPATCH-{int(time.time() * 1000)}"
        assigned_unit = unit_id or f"PCR-UNIT-{(hash(h3_cell) % 90 + 10)}"
        now = time.time()

        # Resolve destination coordinates from payload or active hotspots
        target_lat = destination_lat
        target_lon = destination_lon
        if target_lat is None or target_lon is None:
            for hs in self.active_hotspots:
                if hs.get("h3_cell") == h3_cell:
                    target_lat = hs.get("lat")
                    target_lon = hs.get("lon")
                    break
        if target_lat is None or target_lon is None:
            target_lat = 28.6304
            target_lon = 77.2773

        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={target_lat:.6f},{target_lon:.6f}"

        record = {
            "status": "DISPATCHED",
            "h3_cell": h3_cell,
            "cad_call_id": call_id,
            "patrol_unit_id": assigned_unit,
            "priority": priority,
            "destination": {"lat": round(target_lat, 6), "lon": round(target_lon, 6)},
            "google_maps_url": maps_url,
            "notes": notes,
            "message": f"Tactical intercept dispatched to H3 Hex {h3_cell} for Unit {assigned_unit}.",
            "timestamp": now
        }

        self.dispatched_patrols.append(record)

        # Broadcast dispatch event to dashboard
        asyncio.create_task(ws_manager.broadcast({
            "type": "PATROL_DISPATCHED",
            "dispatch": record,
            "timestamp": now
        }))

        return record

    async def freeze_lien(
        self,
        account_no: Optional[str] = None,
        account_numbers: Optional[List[str]] = None,
        system: str = "CFCFRMS-1930",
        reason: str = "",
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Trigger an automated 1930 CFCFRMS debit freeze / lien on suspect mule accounts (single or batch).
        """
        lien_id = f"LIEN-1930-{int(time.time() * 1000)}"
        now = time.time()

        # Build list of affected accounts
        accounts_list = []
        if account_numbers:
            accounts_list.extend(account_numbers)
        if account_no and account_no not in accounts_list:
            accounts_list.insert(0, account_no)
        if not accounts_list:
            accounts_list = ["UNKNOWN_ACCOUNT"]

        primary_account = accounts_list[0]

        record = {
            "status": "LIEN_PLACED",
            "account_number": primary_account,
            "accounts_affected": accounts_list,
            "system": system,
            "lien_id": lien_id,
            "freeze_amount": amount,
            "atm_daily_limit": "₹0.00",
            "reason": reason or "Automated ML Mule Risk Threshold Exceeded (>0.70)",
            "message": f"Debit & ATM withdrawal permissions locked for {len(accounts_list)} accounts ({', '.join(accounts_list)}).",
            "timestamp": now
        }

        self.placed_liens.append(record)

        # Broadcast freeze event to dashboard
        asyncio.create_task(ws_manager.broadcast({
            "type": "LIEN_PLACED",
            "lien": record,
            "timestamp": now
        }))

        return record

    def get_initial_state(self) -> Dict[str, Any]:
        """
        Construct initial state payload for newly connected WebSocket clients.
        """
        return {
            "type": "INITIAL_STATE",
            "hotspots": self.active_hotspots,
            "recent_txs": self.recent_transactions[-50:],
            "system_metrics": self.get_system_metrics()
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Telemetry and operational statistics.
        """
        uptime_seconds = round(time.time() - self.start_time, 2)
        return {
            "uptime_seconds": uptime_seconds,
            "total_transactions_ingested": self.total_transactions_ingested,
            "total_high_risk_flagged": self.total_high_risk_flagged,
            "total_ncrp_complaints": self.total_ncrp_complaints_ingested,
            "active_hotspots_count": len(self.active_hotspots),
            "active_websocket_clients": ws_manager.client_count
        }

orchestrator = StreamOrchestrator()
