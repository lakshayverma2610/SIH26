"""
Sliding-Window Feature Extractor for In-Flight Transactions.
Extracts:
- Velocity in 1 min and 5 min window (V1, V5)
- Fan-out degree (1 to N smurfing count within 180s)
- Dormancy disruption score
- Device & IP multiplexing counts
"""
import time
from collections import defaultdict, deque
from typing import Dict, Any

class SlidingWindowFeatureEngine:
    def __init__(self):
        # account -> deque of timestamps
        self.tx_history_out = defaultdict(deque)
        self.tx_history_in = defaultdict(deque)
        # account -> deque of (timestamp, dest_acc)
        self.fan_out_tracker = defaultdict(deque)
        # device_id -> set of account numbers
        self.device_accounts = defaultdict(set)
        # ip -> set of account numbers
        self.ip_accounts = defaultdict(set)
        # account metadata cache (dormancy, kyc)
        self.account_metadata = {}

    def register_account_metadata(self, account_no: str, dormant_days: int, kyc_verified: bool):
        self.account_metadata[account_no] = {
            "dormant_days": dormant_days,
            "kyc_verified": kyc_verified
        }

    def process_and_extract(self, tx: Dict[str, Any]) -> Dict[str, float]:
        raw_ts = tx.get("timestamp")
        now = float(raw_ts) if raw_ts is not None else time.time()
        src = tx.get("src_acc", "")
        dest = tx.get("dest_acc", "")
        amount = float(tx.get("amount", 0.0))
        device_id = tx.get("device_id", "UNKNOWN_DEV")
        ip = tx.get("ip", "UNKNOWN_IP")

        # Clean up timestamps older than 300s (5 mins)
        self._prune(self.tx_history_out[src], now, 300)
        self._prune(self.tx_history_in[dest], now, 300)
        self._prune_tuples(self.fan_out_tracker[src], now, 180)

        # 1. Update histories
        self.tx_history_out[src].append(now)
        self.tx_history_in[dest].append(now)
        self.fan_out_tracker[src].append((now, dest))
        if device_id != "UNKNOWN_DEV":
            self.device_accounts[device_id].add(src)
        if ip != "UNKNOWN_IP":
            self.ip_accounts[ip].add(src)

        # 2. Compute Velocity (V1: <=60s, V5: <=300s)
        v1_out = sum(1 for t in self.tx_history_out[src] if now - t <= 60)
        v5_out = len(self.tx_history_out[src])
        v1_in = sum(1 for t in self.tx_history_in[dest] if now - t <= 60)

        # 3. Compute Fan-out degree (distinct destinations within 180s)
        recent_dests = set(d for t, d in self.fan_out_tracker[src] if now - t <= 180)
        fan_out_degree = len(recent_dests)

        # 4. Dormancy Break & KYC Mismatch
        src_meta = self.account_metadata.get(src, {"dormant_days": 0, "kyc_verified": True})
        dest_meta = self.account_metadata.get(dest, {"dormant_days": 0, "kyc_verified": True})
        
        dormancy_break = 1.0 if (dest_meta["dormant_days"] > 45 and amount > 5000) else 0.0
        kyc_risk = 1.0 if not dest_meta["kyc_verified"] else 0.0

        # 5. Device & IP Multiplexing
        device_reuse_count = len(self.device_accounts.get(device_id, set()))
        ip_reuse_count = len(self.ip_accounts.get(ip, set()))

        return {
            "amount": amount,
            "v1_out": float(v1_out),
            "v5_out": float(v5_out),
            "v1_in": float(v1_in),
            "fan_out_degree": float(fan_out_degree),
            "dormancy_break": dormancy_break,
            "kyc_risk": kyc_risk,
            "device_reuse_count": float(device_reuse_count),
            "ip_reuse_count": float(ip_reuse_count)
        }

    def _prune(self, dq: deque, now: float, window: float):
        while dq and (now - dq[0] > window):
            dq.popleft()

    def _prune_tuples(self, dq: deque, now: float, window: float):
        while dq and (now - dq[0][0] > window):
            dq.popleft()
