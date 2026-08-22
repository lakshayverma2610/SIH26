"""
Geospatial Predictor Loader & Fallback Engine
Dynamically loads Akshansh's `graph_db.geo_predictor.GeospatialPredictor` when available,
or provides a spatial clustering fallback for ATM cash-out zone forecasting.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import math

logger = logging.getLogger("geo_cashwatch.geo")

class FallbackGeospatialPredictor:
    """
    In-memory geospatial clustering engine that computes H3-like spatial grids
    and associates flagged mule cash flow with nearby ATM infrastructure.
    """
    def __init__(self, atms_path: str = None):
        self.atms = []
        if atms_path and Path(atms_path).exists():
            try:
                with open(atms_path, "r", encoding="utf-8") as f:
                    self.atms = json.load(f)
                logger.info(f"Loaded {len(self.atms)} ATM points from {atms_path}")
            except Exception as e:
                logger.warning(f"Could not load ATMs file: {e}")

    def _approx_h3_index(self, lat: float, lon: float, precision: int = 7) -> str:
        """
        Deterministic spatial cell identifier based on rounded coordinates.
        Generates standard H3-like 15-character hex identifiers.
        """
        lat_grid = round(lat * 100)
        lon_grid = round(lon * 100)
        hash_val = abs(hash((lat_grid, lon_grid, precision))) % (16 ** 12)
        return f"88{hash_val:013x}"[:15]

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def aggregate_hotspots(self, flagged_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregates flagged high-risk transactions into geospatial cash-out hotspots.
        """
        if not flagged_events:
            return []

        clusters = defaultdict(lambda: {
            "lats": [],
            "lons": [],
            "scores": [],
            "amounts": [],
            "accounts": set()
        })

        for ev in flagged_events:
            lat = ev.get("lat", 28.6304)
            lon = ev.get("lon", 77.2773)
            cell = self._approx_h3_index(lat, lon)
            clusters[cell]["lats"].append(lat)
            clusters[cell]["lons"].append(lon)
            clusters[cell]["scores"].append(ev.get("fraud_probability", 0.8))
            clusters[cell]["amounts"].append(ev.get("amount", 0.0))
            clusters[cell]["accounts"].add(ev.get("account_number", "UNKNOWN"))

        hotspots = []
        for cell, data in clusters.items():
            avg_lat = sum(data["lats"]) / len(data["lats"])
            avg_lon = sum(data["lons"]) / len(data["lons"])
            avg_score = sum(data["scores"]) / len(data["scores"])
            total_amt = sum(data["amounts"])

            # Find nearby ATMs within 3.0 km
            nearby_atms = []
            for atm in self.atms:
                atm_lat = atm.get("lat")
                atm_lon = atm.get("lon")
                if atm_lat and atm_lon:
                    dist = self._haversine_km(avg_lat, avg_lon, atm_lat, atm_lon)
                    if dist <= 3.0:
                        nearby_atms.append({
                            "atm_id": atm.get("atm_id", "ATM_DEFAULT"),
                            "bank": atm.get("bank", "Bank"),
                            "distance_km": round(dist, 2),
                            "lat": atm_lat,
                            "lon": atm_lon
                        })

            hotspots.append({
                "h3_cell": cell,
                "lat": round(avg_lat, 6),
                "lon": round(avg_lon, 6),
                "risk_score": round(min(1.0, avg_score), 4),
                "event_count": len(data["scores"]),
                "total_amount": round(total_amt, 2),
                "unique_mule_accounts": len(data["accounts"]),
                "nearby_atms": nearby_atms[:5]
            })

        # Sort hotspots by descending risk and amount
        hotspots.sort(key=lambda x: (x["risk_score"], x["total_amount"]), reverse=True)
        return hotspots


def get_geospatial_predictor(atms_path: str = None):
    """
    Factory function: Attempts to load Graph-DB team's GeospatialPredictor,
    or falls back to FallbackGeospatialPredictor.
    """
    try:
        from graph_db.geo_predictor import GeospatialPredictor
        logger.info("Successfully loaded graph_db.geo_predictor.GeospatialPredictor")
        return GeospatialPredictor(atms_path)
    except (ImportError, ModuleNotFoundError, AttributeError) as e:
        logger.info(f"Using FallbackGeospatialPredictor (graph_db module pending: {e})")
        return FallbackGeospatialPredictor(atms_path)
