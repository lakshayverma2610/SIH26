"""
Geospatial Predictor Loader & Fallback Engine
Dynamically loads Akshansh's `graph_db.geo_predictor.GeospatialPredictor` when available,
or provides a standalone spatial clustering fallback for ATM cash-out zone forecasting.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import math

logger = logging.getLogger("geo_cashwatch.geo")

# Default realistic ATM points for Delhi NCR / Jamtara / Mewat corridors
DEFAULT_FALLBACK_ATMS = [
    {"atm_id": "ATM-SBI-DL-101", "bank": "State Bank of India", "lat": 28.6312, "lon": 77.2785, "address": "Laxmi Nagar Metro Pillar 42, Delhi", "daily_limit": 40000.0},
    {"atm_id": "ATM-HDFC-DL-104", "bank": "HDFC Bank", "lat": 28.6298, "lon": 77.2755, "address": "V3S Mall Ground Floor, East Delhi", "daily_limit": 50000.0},
    {"atm_id": "AEPS-CSP-DL-202", "bank": "Paytm Payments Bank CSP", "lat": 28.6320, "lon": 77.2801, "address": "Main Market Vikas Marg, Delhi", "daily_limit": 30000.0},
    {"atm_id": "ATM-ICICI-NOI-301", "bank": "ICICI Bank", "lat": 28.5708, "lon": 77.3260, "address": "Sector 18 Market, Noida", "daily_limit": 50000.0},
    {"atm_id": "ATM-PNB-HR-402", "bank": "Punjab National Bank", "lat": 28.1402, "lon": 77.0125, "address": "Nuh Road, Mewat Region", "daily_limit": 40000.0},
    {"atm_id": "ATM-SBI-CP-501", "bank": "State Bank of India", "lat": 28.6328, "lon": 77.2197, "address": "Connaught Place Inner Circle, Delhi", "daily_limit": 50000.0},
]


class FallbackGeospatialPredictor:
    """
    In-memory geospatial clustering engine that computes H3-like spatial grids,
    exact 6-vertex polygon boundaries for map visualization, estimated cash-out
    time windows, and associations with nearby physical ATM infrastructure.
    """
    def __init__(self, atms_path: str = None):
        self.atms = list(DEFAULT_FALLBACK_ATMS)
        if atms_path and Path(atms_path).exists():
            try:
                with open(atms_path, "r", encoding="utf-8") as f:
                    loaded_atms = json.load(f)
                    if isinstance(loaded_atms, list) and loaded_atms:
                        self.atms = loaded_atms
                logger.info(f"Loaded {len(self.atms)} ATM points from {atms_path}")
            except Exception as e:
                logger.warning(f"Could not load ATMs file ({e}), using default reference ATMs")

    def _approx_h3_index(self, lat: float, lon: float, precision: int = 7) -> str:
        """
        Deterministic spatial cell identifier based on rounded coordinates.
        Generates standard H3-like 15-character hex identifiers.
        """
        lat_grid = round(lat * 100)
        lon_grid = round(lon * 100)
        hash_val = abs(hash((lat_grid, lon_grid, precision))) % (16 ** 12)
        return f"88{hash_val:013x}"[:15]

    def _compute_h3_boundary(self, center_lat: float, center_lon: float, radius_km: float = 0.6) -> List[List[float]]:
        """
        Compute standard 6-vertex hexagonal boundary coordinates [[lat, lon], ...]
        closed polygon format for Sneha's Leaflet / MapLibre visualization.
        """
        # Try native Uber H3 if installed in python environment
        try:
            import h3
            h3_cell = h3.latlng_to_cell(center_lat, center_lon, 8) if hasattr(h3, 'latlng_to_cell') else h3.geo_to_h3(center_lat, center_lon, 8)
            boundary = h3.cell_to_boundary(h3_cell) if hasattr(h3, 'cell_to_boundary') else h3.h3_to_geo_boundary(h3_cell)
            return [[round(pt[0], 6), round(pt[1], 6)] for pt in boundary]
        except Exception:
            pass

        # Fallback geodesic regular hexagon math (Resolution 8 ~ 0.6km radius)
        coords = []
        d_lat = radius_km / 110.574
        cos_lat = math.cos(math.radians(center_lat))
        d_lon = radius_km / (111.320 * cos_lat) if abs(cos_lat) > 1e-6 else radius_km / 111.320

        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.radians(angle_deg)
            vertex_lat = center_lat + d_lat * math.sin(angle_rad)
            vertex_lon = center_lon + d_lon * math.cos(angle_rad)
            coords.append([round(vertex_lat, 6), round(vertex_lon, 6)])

        # Close polygon
        coords.append(coords[0])
        return coords

    def _compute_cashout_window(self, eta_minutes: int = 25) -> Dict[str, Any]:
        """
        Compute estimated time-to-cashout prediction window for law enforcement intercept.
        """
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(minutes=max(5, eta_minutes - 15))
        end_time = now + timedelta(minutes=eta_minutes + 10)
        return {
            "start_time": start_time.strftime("%H:%M:%S UTC"),
            "end_time": end_time.strftime("%H:%M:%S UTC"),
            "eta_minutes": eta_minutes
        }

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance formula in kilometers between two GPS coordinates."""
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def aggregate_hotspots(self, flagged_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregates flagged high-risk transactions into geospatial cash-out hotspots
        enriched with H3 hexagon boundaries, time windows, and target ATM kiosks.
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
                            "lon": atm_lon,
                            "address": atm.get("address", "Main Market Road"),
                            "daily_limit": atm.get("daily_limit", 50000.0)
                        })

            # If no ATMs within 3.0km, associate the closest fallback ATMs
            if not nearby_atms and self.atms:
                sorted_atms = sorted(
                    self.atms,
                    key=lambda a: self._haversine_km(avg_lat, avg_lon, a.get("lat", avg_lat), a.get("lon", avg_lon))
                )
                for atm in sorted_atms[:3]:
                    dist = self._haversine_km(avg_lat, avg_lon, atm["lat"], atm["lon"])
                    nearby_atms.append({
                        "atm_id": atm.get("atm_id", "ATM_DEFAULT"),
                        "bank": atm.get("bank", "Bank"),
                        "distance_km": round(dist, 2),
                        "lat": atm["lat"],
                        "lon": atm["lon"],
                        "address": atm.get("address", "Main Market Road"),
                        "daily_limit": atm.get("daily_limit", 50000.0)
                    })

            # Compute polygon boundary coordinates
            polygon_coords = self._compute_h3_boundary(avg_lat, avg_lon, radius_km=0.6)

            # Compute cash-out prediction time window
            cashout_window = self._compute_cashout_window(eta_minutes=25)

            hotspots.append({
                "h3_cell": cell,
                "lat": round(avg_lat, 6),
                "lon": round(avg_lon, 6),
                "risk_score": round(min(1.0, avg_score), 4),
                "event_count": len(data["scores"]),
                "total_amount": round(total_amt, 2),
                "unique_mule_accounts": len(data["accounts"]),
                "polygon_coordinates": polygon_coords,
                "predicted_cashout_window": cashout_window,
                "resolution": 8,
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
