import time
from collections import defaultdict, deque
from typing import Dict, Set, Tuple, Any

from ai_engine.core.config import settings
from ai_engine.core.logger import get_logger
from ai_engine.core.schemas import TransactionEvent, AccountMetadata, ExtractedFeatures

logger = get_logger(__name__)

class SlidingWindowFeatureEngine:
    """
    Stateful, in-memory feature extractor for high-frequency transactions.
    Calculates velocity, fan-out degree, and dormancy disruptions in real-time.
    """
    
    def __init__(self) -> None:
        # account_id -> deque of timestamps
        self._tx_history_out: Dict[str, deque[float]] = defaultdict(deque)
        self._tx_history_in: Dict[str, deque[float]] = defaultdict(deque)
        
        # account_id -> deque of (timestamp, dest_acc_id)
        self._fan_out_tracker: Dict[str, deque[Tuple[float, str]]] = defaultdict(deque)
        
        # Hardware/Network -> set of account_ids
        self._device_accounts: Dict[str, Set[str]] = defaultdict(set)
        self._ip_accounts: Dict[str, Set[str]] = defaultdict(set)
        
        # account_id -> AccountMetadata
        self._account_metadata: Dict[str, AccountMetadata] = {}
        
        logger.info("SlidingWindowFeatureEngine initialized successfully.")

    def register_metadata(self, metadata: AccountMetadata) -> None:
        """Cache account metadata for quick access during feature extraction."""
        self._account_metadata[metadata.account_id] = metadata

    def register_account_metadata(self, account_id: str, dormant_days: int = 0, kyc_verified: bool = True) -> None:
        """Convenience method to cache account metadata using raw primitives."""
        self.register_metadata(AccountMetadata(account_id=account_id, dormant_days=dormant_days, kyc_verified=kyc_verified))

    def process_and_extract(self, tx_data: Dict[str, Any] | TransactionEvent) -> ExtractedFeatures:
        """
        Convenience adapter that accepts either a dict or a TransactionEvent.
        """
        if isinstance(tx_data, dict):
            raw_ts = tx_data.get("timestamp")
            ts = float(raw_ts) if raw_ts is not None else time.time()
            event = TransactionEvent(
                tx_id=str(tx_data.get("tx_id", f"TX_{int(time.time()*1000)}")),
                src_acc=str(tx_data.get("src_acc", "")),
                dest_acc=str(tx_data.get("dest_acc", "")),
                amount=float(tx_data.get("amount", 0.0)),
                timestamp=ts,
                channel=str(tx_data.get("channel", "UPI")),
                device_id=tx_data.get("device_id"),
                ip_address=tx_data.get("ip") or tx_data.get("ip_address")
            )
        else:
            event = tx_data
        return self.process_transaction(event)

    def process_transaction(self, event: TransactionEvent) -> ExtractedFeatures:
        """
        Ingests a new transaction, updates the sliding window state, 
        and extracts behavioral features for ML inference.
        
        Must execute in < 2ms.
        """
        now = event.timestamp
        src = event.src_acc
        dest = event.dest_acc

        # 1. Prune expired events to maintain memory efficiency and valid window state
        self._prune_history(self._tx_history_out[src], now, settings.WINDOW_5M_SECONDS)
        self._prune_history(self._tx_history_in[dest], now, settings.WINDOW_5M_SECONDS)
        self._prune_fan_out(self._fan_out_tracker[src], now, settings.FAN_OUT_WINDOW_SECONDS)

        # 2. Update state with current event
        self._tx_history_out[src].append(now)
        self._tx_history_in[dest].append(now)
        self._fan_out_tracker[src].append((now, dest))
        
        if event.device_id:
            self._device_accounts[event.device_id].add(src)
        if event.ip_address:
            self._ip_accounts[event.ip_address].add(src)

        # 3. Compute Velocity Metrics
        v1_out = sum(1 for t in self._tx_history_out[src] if now - t <= settings.WINDOW_1M_SECONDS)
        v5_out = len(self._tx_history_out[src])
        v1_in = sum(1 for t in self._tx_history_in[dest] if now - t <= settings.WINDOW_1M_SECONDS)

        # 4. Compute Fan-out Degree
        recent_dests = {d for t, d in self._fan_out_tracker[src] if now - t <= settings.FAN_OUT_WINDOW_SECONDS}
        fan_out_degree = len(recent_dests)

        # 5. Compute Heuristic Flags (Dormancy & KYC)
        dest_meta = self._account_metadata.get(
            dest, 
            AccountMetadata(account_id=dest, dormant_days=0, kyc_verified=True)
        )
        
        dormancy_break = 1 if (
            dest_meta.dormant_days > settings.DORMANCY_DAYS_THRESHOLD 
            and event.amount > settings.HIGH_VALUE_THRESHOLD_INR
        ) else 0
        
        kyc_risk = 1 if not dest_meta.kyc_verified else 0

        # 6. Compute Device/IP Multiplexing
        device_reuse = len(self._device_accounts.get(event.device_id, set())) if event.device_id else 0
        ip_reuse = len(self._ip_accounts.get(event.ip_address, set())) if event.ip_address else 0

        # Construct and return validated feature payload
        features = ExtractedFeatures(
            tx_id=event.tx_id,
            amount=event.amount,
            v1_out=v1_out,
            v5_out=v5_out,
            v1_in=v1_in,
            fan_out_degree=fan_out_degree,
            dormancy_break=dormancy_break,
            kyc_risk=kyc_risk,
            device_reuse_count=device_reuse,
            ip_reuse_count=ip_reuse
        )
        
        # Log heavy anomalies for observability
        if fan_out_degree >= 4 or dormancy_break:
            logger.warning(
                "Anomaly detected in sliding window extraction.", 
                extra={"tx_id": event.tx_id, "fan_out": fan_out_degree, "dormancy_break": dormancy_break}
            )

        return features

    @staticmethod
    def _prune_history(history: deque[float], current_time: float, max_age: int) -> None:
        """Removes timestamps older than max_age from the left of the deque."""
        while history and (current_time - history[0] > max_age):
            history.popleft()

    @staticmethod
    def _prune_fan_out(history: deque[Tuple[float, str]], current_time: float, max_age: int) -> None:
        """Removes fan-out tuples older than max_age from the left of the deque."""
        while history and (current_time - history[0][0] > max_age):
            history.popleft()
