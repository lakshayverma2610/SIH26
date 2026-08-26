import os
import time
from collections import defaultdict, deque
from typing import Dict, Set, Tuple, Optional

from ml_inference.core.config import settings
from ml_inference.core.logger import get_logger
from ml_inference.core.schemas import TransactionEvent, AccountMetadata, ExtractedFeatures

logger = get_logger(__name__)

class SlidingWindowFeatureEngine:
    """
    Stateful feature extractor for high-frequency transactions.
    Supports in-memory cache and enterprise Redis O(1) account metadata lookups.
    """
    
    def __init__(self, redis_url: Optional[str] = None) -> None:
        # account_id -> deque of timestamps
        self._tx_history_out: Dict[str, deque[float]] = defaultdict(deque)
        self._tx_history_in: Dict[str, deque[float]] = defaultdict(deque)
        
        # account_id -> deque of (timestamp, dest_acc_id)
        self._fan_out_tracker: Dict[str, deque[Tuple[float, str]]] = defaultdict(deque)
        
        # Hardware/Network -> set of account_ids
        self._device_accounts: Dict[str, Set[str]] = defaultdict(set)
        self._ip_accounts: Dict[str, Set[str]] = defaultdict(set)
        
        # In-memory fast cache: account_id -> AccountMetadata
        self._account_metadata: Dict[str, AccountMetadata] = {}

        # Redis connection for enterprise distributed account lookup
        self.redis_client = None
        target_redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis
            self.redis_client = redis.Redis.from_url(target_redis_url, decode_responses=True, socket_timeout=1.0)
            self.redis_client.ping()
            logger.info("⚡ SlidingWindowFeatureEngine connected to Redis Master.", extra={"url": target_redis_url})
        except Exception as e:
            self.redis_client = None
            logger.info(f"SlidingWindowFeatureEngine running in local in-memory cache mode ({e}).")

    def register_metadata(self, metadata: AccountMetadata) -> None:
        """Cache account metadata for quick access during feature extraction."""
        self._account_metadata[metadata.account_id] = metadata

    def get_account_metadata(self, account_id: str) -> AccountMetadata:
        """Retrieves account metadata from in-memory cache or Redis Hash store."""
        if account_id in self._account_metadata:
            return self._account_metadata[account_id]

        if self.redis_client:
            try:
                acc_data = self.redis_client.hgetall(f"account:{account_id}")
                if acc_data:
                    meta = AccountMetadata(
                        account_id=account_id,
                        dormant_days=int(acc_data.get("dormant_days", 0)),
                        kyc_verified=str(acc_data.get("kyc_verified", "true")).lower() in ("true", "1")
                    )
                    self._account_metadata[account_id] = meta
                    return meta
            except Exception:
                pass

        default_meta = AccountMetadata(account_id=account_id, dormant_days=0, kyc_verified=True)
        return default_meta

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
        dest_meta = self.get_account_metadata(dest)
        
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
