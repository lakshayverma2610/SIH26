"""
Spatio-Temporal Cluster Engine (ST-DBSCAN & Rolling Convergence)
"""
from typing import List, Dict, Any, Tuple
import math
import time

try:
    from sklearn.cluster import DBSCAN
    import numpy as np
except ImportError:
    DBSCAN = None
    np = None

from geospatial_engine.config import GeoEngineConfig

class SpatioTemporalClusterEngine:
    """
    Groups flagged mule accounts converging in space (km) and time (minutes).
    """

    def __init__(
        self,
        spatial_eps_km: float = GeoEngineConfig.SPATIAL_EPS_KM,
        temporal_eps_sec: float = GeoEngineConfig.TEMPORAL_EPS_SECONDS,
        min_samples: int = GeoEngineConfig.MIN_SAMPLES_CLUSTER
    ):
        self.spatial_eps_km = spatial_eps_km
        self.temporal_eps_sec = temporal_eps_sec
        self.min_samples = min_samples

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates great-circle distance between two points in kilometers.
        """
        r = 6371.0 # Earth radius in km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    def cluster_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clusters a list of flagged mule events into spatio-temporal groups.
        Each event dict: {account_number, lat, lon, amount, fraud_probability, timestamp}
        """
        if not events:
            return []

        now = time.time()
        # Normalize timestamps if missing
        for ev in events:
            if "timestamp" not in ev or ev["timestamp"] is None:
                ev["timestamp"] = now

        n = len(events)
        if n < self.min_samples:
            # For 1 event, create a single isolated cluster so critical single-account alerts are never missed
            return [self._format_cluster(events, cluster_id=0)]

        # Custom distance matrix calculation for ST-DBSCAN
        # If distance_km <= spatial_eps AND abs(delta_t) <= temporal_eps -> reachable
        # We construct an adjacency graph / connected components or use DBSCAN
        clusters_map: Dict[int, List[Dict[str, Any]]] = {}
        
        # Build adjacency matrix
        visited = [False] * n
        cluster_id = 0

        for i in range(n):
            if visited[i]:
                continue
            
            # Find all neighbors satisfying both spatial and temporal eps
            queue = [i]
            visited[i] = True
            current_cluster = [events[i]]

            while queue:
                curr = queue.pop(0)
                curr_ev = events[curr]
                for j in range(n):
                    if not visited[j]:
                        target_ev = events[j]
                        dist_km = self.haversine_distance(
                            curr_ev["lat"], curr_ev["lon"],
                            target_ev["lat"], target_ev["lon"]
                        )
                        time_diff = abs(curr_ev["timestamp"] - target_ev["timestamp"])

                        if dist_km <= self.spatial_eps_km and time_diff <= self.temporal_eps_sec:
                            visited[j] = True
                            queue.append(j)
                            current_cluster.append(target_ev)

            clusters_map[cluster_id] = current_cluster
            cluster_id += 1

        result = []
        for cid, cluster_events_list in clusters_map.items():
            result.append(self._format_cluster(cluster_events_list, cluster_id=cid))

        # Sort clusters by aggregate risk descending (highest risk first)
        result.sort(key=lambda x: x["aggregate_risk_score"], reverse=True)
        return result

    def _format_cluster(self, cluster_events: List[Dict[str, Any]], cluster_id: int) -> Dict[str, Any]:
        """
        Aggregates risk, calculates centroid, and determines threat severity.
        """
        total_funds = sum(e.get("amount", 0.0) for e in cluster_events)
        avg_prob = sum(e.get("fraud_probability", 0.9) for e in cluster_events) / len(cluster_events)
        
        # Weighted centroid by amount (or simple mean)
        center_lat = sum(e["lat"] for e in cluster_events) / len(cluster_events)
        center_lon = sum(e["lon"] for e in cluster_events) / len(cluster_events)

        mule_accounts = list({str(e.get("account_number", "UNKNOWN")) for e in cluster_events})

        # Calculate aggregate severity
        # High funds (> 200k) or multiple mules (> 2) = CRITICAL
        if total_funds >= 200000 or len(mule_accounts) >= 3 or avg_prob >= 0.95:
            severity = "CRITICAL"
        elif total_funds >= 50000 or len(mule_accounts) >= 2 or avg_prob >= 0.80:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        # Aggregate risk score (0.0 - 1.0)
        risk_score = min(1.0, avg_prob * (0.8 + 0.1 * min(len(mule_accounts), 3)))

        return {
            "cluster_id": f"CLUST_{cluster_id:03d}",
            "center_lat": round(center_lat, 6),
            "center_lon": round(center_lon, 6),
            "mule_count": len(mule_accounts),
            "mule_accounts": mule_accounts,
            "total_funds_at_risk": round(total_funds, 2),
            "average_fraud_probability": round(avg_prob, 4),
            "aggregate_risk_score": round(risk_score, 4),
            "severity": severity,
            "events_count": len(cluster_events)
        }
