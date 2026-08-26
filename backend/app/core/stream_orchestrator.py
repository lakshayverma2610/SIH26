"""
Stream Orchestrator Core Engine
Central pipeline coordinator that ingests real-time transaction streams, extracts behavioral features,
evaluates ML mule risk, updates geospatial cash-out hotspots, and broadcasts alerts.
"""
import sys
import time
import json
import uuid
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from backend.app.config import (
    ROOT_DIR,
    MAX_RECENT_TRANSACTIONS,
    MAX_FLAGGED_EVENTS_BUFFER,
    ATMS_DATA_PATH,
    ACCOUNTS_DATA_PATH
)
from backend.app.core.connection_manager import ws_manager
from graph_db.geo_predictor import GeospatialPredictor

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
        self.geo_predictor = GeospatialPredictor(str(ATMS_DATA_PATH) if ATMS_DATA_PATH.exists() else None)

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
        if hasattr(feats, "model_dump"):
            feats_dict = feats.model_dump()
        elif hasattr(feats, "__dict__"):
            feats_dict = dict(feats.__dict__)
        elif isinstance(feats, dict):
            feats_dict = dict(feats)
        else:
            feats_dict = {}

        # Step 2: Score Mule Risk via ML & Rules
        score_res = self.mule_scorer.score_features(feats)
        if isinstance(score_res, dict):
            fraud_prob = score_res.get("fraud_probability", 0.0)
            is_high_risk = score_res.get("is_high_risk", False)
            reasons = list(score_res.get("reasons", []))
        else:
            fraud_prob = getattr(score_res, "fraud_probability", 0.0)
            is_high_risk = getattr(score_res, "is_high_risk", False)
            reasons = list(getattr(score_res, "reasons", []))

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

            # Recalculate active H3 hotspots and normalize schema
            raw_hotspots = self.geo_predictor.aggregate_hotspots(self.flagged_events_buffer)
            normalized_hotspots = []
            for hs in raw_hotspots:
                h3_cell = hs.get("h3_cell") or hs.get("h3_res9") or hs.get("h3_res8") or hs.get("cluster_id", "8860145b59fffff")
                hs_lat = hs.get("lat") if hs.get("lat") is not None else hs.get("center_lat", 28.6304)
                hs_lon = hs.get("lon") if hs.get("lon") is not None else hs.get("center_lon", 77.2773)
                hs_risk = hs.get("risk_score") if hs.get("risk_score") is not None else hs.get("aggregate_risk_score", 0.85)
                hs_amt = hs.get("total_amount") if hs.get("total_amount") is not None else hs.get("total_funds_at_risk", 0.0)
                hs_mules = hs.get("unique_mule_accounts") if hs.get("unique_mule_accounts") is not None else hs.get("mule_count", 1)
                hs_atms = hs.get("nearby_atms") or hs.get("nearest_atms") or []

                poly_coords = hs.get("polygon_coordinates")
                if not poly_coords and "h3_boundary" in hs and isinstance(hs["h3_boundary"], dict):
                    coords_list = hs["h3_boundary"].get("coordinates", [])
                    if coords_list:
                        poly_coords = coords_list[0]
                if not poly_coords:
                    poly_coords = []

                norm_hs = dict(hs)
                norm_hs.update({
                    "h3_cell": h3_cell,
                    "lat": round(float(hs_lat), 6),
                    "lon": round(float(hs_lon), 6),
                    "risk_score": round(min(1.0, float(hs_risk)), 4),
                    "event_count": hs.get("event_count") or hs_mules,
                    "total_amount": round(float(hs_amt), 2),
                    "unique_mule_accounts": hs_mules,
                    "polygon_coordinates": poly_coords,
                    "nearby_atms": hs_atms,
                    "predicted_cashout_window": hs.get("predicted_cashout_window") or {"start_time": "12:00:00 UTC", "end_time": "12:35:00 UTC", "eta_minutes": 25}
                })
                normalized_hotspots.append(norm_hs)

            self.active_hotspots = normalized_hotspots

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
            "features": feats_dict
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
            "atm_daily_limit": "INR 0.00",
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

    def generate_incident_report(
        self,
        hotspot_id: Optional[str] = None,
        complaint_id: Optional[str] = None,
        format_type: str = "MARKDOWN",
        include_map_coordinates: bool = True
    ) -> Dict[str, Any]:
        """
        Compile active in-memory complaints, suspect transactions, geospatial clusters,
        and executed CAD patrol/lien actions into a structured Markdown incident action report.
        """
        now = datetime.now(timezone.utc)
        report_id = f"IAR-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        now_str = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. Resolve Complaint Data
        complaint = None
        complaint_match_type = "EXACT_MATCH"
        if complaint_id:
            for rec in self.ncrp_complaints.values():
                if rec.get("ncrp_id") == complaint_id:
                    complaint = rec
                    break
        if not complaint and self.ncrp_complaints:
            complaint = list(self.ncrp_complaints.values())[-1]
            complaint_match_type = "LATEST_ACTIVE_BUFFER"

        # 2. Resolve Hotspot Data
        hotspot = None
        hotspot_match_type = "EXACT_MATCH"
        if hotspot_id:
            for hs in self.active_hotspots:
                if hs.get("h3_cell") == hotspot_id or hs.get("h3_res9") == hotspot_id or hs.get("cluster_id") == hotspot_id:
                    hotspot = hs
                    break
        if not hotspot and self.active_hotspots:
            hotspot = self.active_hotspots[0]
            hotspot_match_type = "PRIMARY_ACTIVE_BUFFER"

        # 3. Correlate Relevant Transactions
        suspect_acc = complaint.get("suspect_acc") if complaint else None
        related_txs = []
        if suspect_acc:
            related_txs = [
                tx for tx in self.recent_transactions
                if tx.get("src_acc") == suspect_acc or tx.get("dest_acc") == suspect_acc
            ]
        if not related_txs:
            related_txs = [tx for tx in self.recent_transactions if tx.get("is_high_risk")][-5:]
        if not related_txs:
            related_txs = self.recent_transactions[-5:]

        # 4. Correlate Actions
        dispatches = list(self.dispatched_patrols)
        liens = list(self.placed_liens)

        # 5. Build Markdown Content
        title = f"Incident Action Report - {complaint.get('ncrp_id') if complaint else (hotspot.get('h3_cell') if hotspot else report_id)}"
        
        md_lines = [
            "# 🚨 CYBER CRIME INCIDENT ACTION REPORT (IAR)",
            f"**Report Reference:** `{report_id}`  ",
            f"**Generated At:** {now_str}  ",
            f"**System Source:** Geo-CashWatch Backend Stream Orchestrator  ",
            f"**Operational Scope:** Law Enforcement & 1930 CFCFRMS Incident Response  ",
            "",
            "---",
            "",
            "## 1. Incident Overview",
        ]

        if complaint:
            md_lines.extend([
                f"- **1930 NCRP Reference:** `{complaint.get('ncrp_id')}` ({complaint_match_type})",
                f"- **Victim Account:** `{complaint.get('victim_acc', 'N/A')}`",
                f"- **Tagged Layer-1 Suspect Account:** `{complaint.get('suspect_acc', 'N/A')}`",
                f"- **Reported Defrauded Amount:** INR {complaint.get('amount', 0.0):,.2f}",
                f"- **Modus Operandi:** {complaint.get('complaint_type', 'CYBER_FRAUD')}",
                f"- **Incident Narrative:** {complaint.get('description', 'N/A')}",
            ])
        else:
            md_lines.append("- **NCRP Complaint Status:** No matching NCRP complaint registered in current memory buffer.")

        md_lines.extend([
            "",
            "---",
            "",
            "## 2. In-Flight Transaction & AI Mule Evaluation",
        ])

        if related_txs:
            md_lines.append("| Tx ID | Source | Destination | Amount (INR) | Risk Score | High Risk | Reasons |")
            md_lines.append("|---|---|---|---|---|---|---|")
            for tx in related_txs:
                reasons_str = "; ".join(tx.get("reasons", [])) or "Normal"
                md_lines.append(
                    f"| `{tx.get('tx_id')}` | `{tx.get('src_acc')}` | `{tx.get('dest_acc')}` | "
                    f"INR {tx.get('amount', 0.0):,.2f} | {tx.get('fraud_probability', 0.0):.2f} | "
                    f"{'YES' if tx.get('is_high_risk') else 'NO'} | {reasons_str} |"
                )
        else:
            md_lines.append("- *No transaction flow recorded in in-memory sliding window.*")

        md_lines.extend([
            "",
            "---",
            "",
            "## 3. Geospatial Threat & ATM Cash-Out Prediction",
        ])

        if hotspot:
            win = hotspot.get("predicted_cashout_window") or {}
            if isinstance(win, dict):
                win_str = f"{win.get('start_time', 'N/A')} - {win.get('end_time', 'N/A')} (ETA {win.get('eta_minutes', 25)}m)"
            else:
                win_str = str(win)
            
            hs_cell = hotspot.get("h3_cell") or hotspot.get("h3_res9") or hotspot.get("cluster_id") or "8860145b59fffff"
            hs_lat = hotspot.get("lat") or hotspot.get("center_lat") or 28.6304
            hs_lon = hotspot.get("lon") or hotspot.get("center_lon") or 77.2773
            hs_risk = hotspot.get("risk_score") or hotspot.get("aggregate_risk_score") or 0.85
            hs_amt = hotspot.get("total_amount") or hotspot.get("total_funds_at_risk") or 0.0
            hs_mules = hotspot.get("unique_mule_accounts") or hotspot.get("mule_count") or 1
            
            coords_str = f"{hs_lat}, {hs_lon}" if include_map_coordinates else "Coordinates suppressed"
            
            md_lines.extend([
                f"- **Target H3 Cell:** `{hs_cell}` ({hotspot_match_type})",
                f"- **Cluster Center:** {coords_str}",
                f"- **Aggregated Risk Score:** {float(hs_risk):.2f}",
                f"- **Total Funds at Risk:** INR {float(hs_amt):,.2f}",
                f"- **Predicted Cash-Out Window:** {win_str}",
                f"- **Unique Suspect Accounts in Cluster:** {hs_mules}",
                "",
                "### Targeted Physical ATM / AePS Terminals:",
            ])
            nearby_atms = hotspot.get("nearby_atms") or hotspot.get("nearest_atms") or []
            if nearby_atms:
                for idx, atm in enumerate(nearby_atms, 1):
                    bank_name = atm.get("bank") or atm.get("bank_name") or "Public Sector Bank ATM"
                    atm_id = atm.get("atm_id", "ATM")
                    dist_km = atm.get("distance_km") or (round(atm.get("distance_meters", 0.0)/1000.0, 2)) or 0.0
                    limit = atm.get("daily_limit", 50000.0)
                    loc = f" (Lat: {atm.get('lat')}, Lon: {atm.get('lon')})" if include_map_coordinates and atm.get('lat') else ""
                    md_lines.append(
                        f"{idx}. **{bank_name}** (`{atm_id}`) - "
                        f"Distance: {dist_km} km{loc} | Limit: INR {limit:,.2f}"
                    )
            else:
                md_lines.append("- *No specific ATM points associated with this cluster.*")
        else:
            md_lines.append("- **Hotspot Status:** No active spatial cash-out hotspots aggregated in memory.")

        md_lines.extend([
            "",
            "---",
            "",
            "## 4. Tactical Interception & Enforcement Log",
        ])

        if dispatches:
            md_lines.append("### Computer-Aided Dispatches (CAD):")
            for d in dispatches:
                maps_info = f" [CAD Navigation Route]({d.get('google_maps_url')})" if d.get("google_maps_url") else ""
                md_lines.append(
                    f"- **{d.get('cad_call_id')}** -> Unit `{d.get('patrol_unit_id')}` | "
                    f"Priority: `{d.get('priority')}` | Target: `{d.get('h3_cell')}`{maps_info}"
                )
        else:
            md_lines.append("- *No PCR patrol dispatches triggered.*")

        if liens:
            md_lines.append("\n### 1930 / NPCI Banking Liens Placed:")
            for l in liens:
                accs = ", ".join(l.get("accounts_affected", [l.get("account_number", "N/A")]))
                md_lines.append(
                    f"- **{l.get('lien_id')}** -> Accounts: `{accs}` | "
                    f"ATM Daily Limit: `{l.get('atm_daily_limit', 'INR 0.00')}` | Reason: {l.get('reason')}"
                )
        else:
            md_lines.append("- *No emergency debit/ATM liens recorded in active session.*")

        md_lines.extend([
            "",
            "---",
            "",
            "## 5. System Metadata & Statutory References",
            "- **Processing Gateway:** FastAPI Async Stream Orchestrator",
            "- **Statutory References:** Reference metadata for emergency requests under Section 91 CrPC and digital log trail under Section 65B Indian Evidence Act.",
            "- **Notice:** Generated automatically from real-time operational memory buffers for investigative assistance."
        ])

        content = "\n".join(md_lines)

        target_cell = (hotspot.get("h3_cell") or hotspot.get("h3_res9") or hotspot.get("cluster_id")) if hotspot else None
        atms_count = len(hotspot.get("nearby_atms") or hotspot.get("nearest_atms") or []) if hotspot else 0
        total_risk_val = (hotspot.get("total_amount") or hotspot.get("total_funds_at_risk") or 0.0) if hotspot else 0.0

        summary_stats = {
            "report_id": report_id,
            "complaint_id": complaint.get("ncrp_id") if complaint else None,
            "hotspot_cell": target_cell,
            "total_stolen_amount": complaint.get("amount", 0.0) if complaint else 0.0,
            "total_funds_at_risk": total_risk_val,
            "related_txs_count": len(related_txs),
            "dispatches_count": len(dispatches),
            "liens_count": len(liens),
            "atms_targeted_count": atms_count
        }

        return {
            "status": "GENERATED",
            "report_id": report_id,
            "format": format_type.upper(),
            "title": title,
            "content": content,
            "summary_stats": summary_stats,
            "timestamp": time.time()
        }

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
