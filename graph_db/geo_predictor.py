"""
Geospatial Predictor & ATM Point-of-Egress Forecasting Engine
"""
from typing import List, Dict, Any, Optional
import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from graph_db.config import GeoEngineConfig
from graph_db.h3_indexer import H3SpatialIndexer
from graph_db.cluster_engine import SpatioTemporalClusterEngine

class GeospatialPredictor:
    """
    Core geospatial prediction engine.
    Ingests flagged mule accounts, forms H3 spatial clusters, and predicts
    high-probability physical ATM cash-out targets for police dispatch.
    """

    def __init__(self, atms_file_path: Optional[str] = None):
        self.config = GeoEngineConfig()
        self.h3_indexer = H3SpatialIndexer(
            res_zone=self.config.DEFAULT_H3_RES_ZONE,
            res_kiosk=self.config.DEFAULT_H3_RES_KIOSK
        )
        self.cluster_engine = SpatioTemporalClusterEngine(
            spatial_eps_km=self.config.SPATIAL_EPS_KM,
            temporal_eps_sec=self.config.TEMPORAL_EPS_SECONDS,
            min_samples=self.config.MIN_SAMPLES_CLUSTER
        )
        self.atms: List[Dict[str, Any]] = []
        self._load_atms(atms_file_path)

    def _load_atms(self, file_path: Optional[str]) -> None:
        """
        Loads ATM / AePS kiosk database from file or initializes default Delhi-NCR/Metro mock dataset.
        """
        if file_path and Path(file_path).exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.atms = json.load(f)
                return
            except Exception:
                pass

        # Built-in high-density ATM dataset for Delhi NCR hubs (Laxmi Nagar, CP, Karol Bagh, Saket, Noida)
        self.atms = [
            {"atm_id": "ATM-SBI-DL-101", "bank": "State Bank of India", "bank_name": "State Bank of India", "lat": 28.6312, "lon": 77.2785, "address": "Laxmi Nagar Metro Pillar 42, Delhi", "daily_limit": 40000.0},
            {"atm_id": "ATM-HDFC-DL-104", "bank": "HDFC Bank", "bank_name": "HDFC Bank", "lat": 28.6298, "lon": 77.2755, "address": "V3S Mall Ground Floor, East Delhi", "daily_limit": 50000.0},
            {"atm_id": "AEPS-CSP-DL-202", "bank": "Paytm Payments Bank CSP", "bank_name": "Paytm Payments Bank CSP", "lat": 28.6320, "lon": 77.2801, "address": "Main Market Vikas Marg, Delhi", "daily_limit": 30000.0},
            {"atm_id": "ATM-ICICI-NOI-301", "bank": "ICICI Bank", "bank_name": "ICICI Bank", "lat": 28.5708, "lon": 77.3260, "address": "Sector 18 Market, Noida", "daily_limit": 50000.0},
            {"atm_id": "ATM-PNB-HR-402", "bank": "Punjab National Bank", "bank_name": "Punjab National Bank", "lat": 28.1402, "lon": 77.0125, "address": "Nuh Road, Mewat Region", "daily_limit": 40000.0},
            {"atm_id": "ATM-SBI-CP-501", "bank": "State Bank of India", "bank_name": "State Bank of India", "lat": 28.6328, "lon": 77.2197, "address": "Connaught Place Inner Circle, Delhi", "daily_limit": 50000.0},
            {"atm_id": "ATM-KOTAK-KB-301", "bank": "Kotak Mahindra Bank", "bank_name": "Kotak Mahindra Bank", "lat": 28.6520, "lon": 77.1905, "address": "Ajmal Khan Road, Karol Bagh, Delhi", "daily_limit": 50000.0},
            {"atm_id": "ATM-AXIS-SKT-401", "bank": "Axis Bank", "bank_name": "Axis Bank", "lat": 28.5285, "lon": 77.2195, "address": "District Centre, Saket, New Delhi", "daily_limit": 50000.0}
        ]

        # Tag ATMs with their H3 indexes
        for atm in self.atms:
            atm["h3_res9"] = self.h3_indexer.latlng_to_h3(atm["lat"], atm["lon"], resolution=self.config.DEFAULT_H3_RES_KIOSK)

    def find_nearest_atms(self, lat: float, lon: float, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Finds and ranks nearest physical ATMs from a given coordinate point.
        """
        if not self.atms:
            return []

        ranked_atms = []
        for atm in self.atms:
            dist_km = SpatioTemporalClusterEngine.haversine_distance(lat, lon, atm["lat"], atm["lon"])
            dist_meters = round(dist_km * 1000.0, 1)
            
            # Probability decreases with distance from hotspot center
            prob = max(0.1, min(0.99, math.exp(-dist_km / 0.8)))
            
            bank_title = atm.get("bank") or atm.get("bank_name", "Public Sector Bank ATM")
            ranked_atms.append({
                "atm_id": atm.get("atm_id", "ATM_GENERIC"),
                "bank": bank_title,
                "bank_name": bank_title,
                "lat": atm["lat"],
                "lon": atm["lon"],
                "address": atm.get("address", "Metro Commercial Corridor"),
                "distance_km": round(dist_km, 2),
                "distance_meters": dist_meters,
                "daily_limit": float(atm.get("daily_limit", 50000.0)),
                "withdrawal_probability": round(prob, 2),
                "h3_res9": atm.get("h3_res9")
            })

        # Sort by distance ascending
        ranked_atms.sort(key=lambda x: x["distance_km"])
        return ranked_atms[:top_k]

    def calculate_time_window_dict(self, base_timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Generates standard structured cash-out window object for backend schemas.
        """
        now = datetime.now(timezone.utc)
        eta_min = self.config.CASHOUT_BUFFER_MINUTES
        start_time = now.strftime("%H:%M UTC")
        end_time = (now + timedelta(minutes=eta_min + 20)).strftime("%H:%M UTC")
        return {
            "start_time": start_time,
            "end_time": end_time,
            "eta_minutes": eta_min
        }

    def calculate_time_window(self, base_timestamp: Optional[float] = None) -> str:
        """
        Calculates human-readable cash-out intervention window string.
        """
        start_min = 0
        end_min = self.config.CASHOUT_BUFFER_MINUTES + 20
        return f"T+{start_min} to T+{end_min} mins (CRITICAL INTERCEPTION)"

    def aggregate_hotspots(self, flagged_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main public interface called by backend/main.py and stream_orchestrator.py.
        Transforms raw flagged transaction events into actionable GeoJSON H3 hotspots.
        """
        if not flagged_events:
            return []

        # 1. Cluster events into spatio-temporal mule groups
        clusters = self.cluster_engine.cluster_events(flagged_events)

        hotspots = []
        for cluster in clusters:
            c_lat = cluster["center_lat"]
            c_lon = cluster["center_lon"]

            # 2. Get H3 Hexagon IDs
            h3_res8 = self.h3_indexer.latlng_to_h3(c_lat, c_lon, resolution=self.config.DEFAULT_H3_RES_ZONE)
            h3_res9 = self.h3_indexer.latlng_to_h3(c_lat, c_lon, resolution=self.config.DEFAULT_H3_RES_KIOSK)

            # 3. Get H3 boundary polygon coordinates for map drawing
            # GeoJSON requires [lon, lat], while Leaflet coordinates use [lat, lon]
            h3_boundary_geojson = self.h3_indexer.get_cell_boundary(h3_res8)
            # Standard Leaflet/MapLibre format [[lat, lon], ...]
            polygon_coordinates_leaflet = [[pt[1], pt[0]] for pt in h3_boundary_geojson]

            # 4. Find nearest ATM kiosks
            nearest_atms = self.find_nearest_atms(c_lat, c_lon, top_k=self.config.MAX_NEAREST_ATMS)

            # 5. Build standard structured cash-out window
            cashout_win_dict = self.calculate_time_window_dict()

            # 6. Build GeoJSON Feature
            geojson_feature = {
                "type": "Feature",
                "properties": {
                    "cluster_id": cluster["cluster_id"],
                    "severity": cluster["severity"],
                    "mule_count": cluster["mule_count"],
                    "total_funds": cluster["total_funds_at_risk"],
                    "risk_score": cluster["aggregate_risk_score"],
                    "h3_index": h3_res8
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [h3_boundary_geojson]
                }
            }

            # Harmonized dictionary compatible with both backend/app/schemas/hotspot.py and Sneha's UI
            hotspot_payload = {
                # Backend HotspotModel fields
                "h3_cell": h3_res8,
                "lat": c_lat,
                "lon": c_lon,
                "risk_score": cluster["aggregate_risk_score"],
                "event_count": cluster.get("events_count", cluster["mule_count"]),
                "total_amount": cluster["total_funds_at_risk"],
                "polygon_coordinates": polygon_coordinates_leaflet,
                "predicted_cashout_window": cashout_win_dict,
                "resolution": 8,
                "unique_mule_accounts": cluster["mule_count"],
                "nearby_atms": nearest_atms,

                # Enriched graph_db attributes
                "cluster_id": cluster["cluster_id"],
                "severity": cluster["severity"],
                "center_lat": c_lat,
                "center_lon": c_lon,
                "h3_res8": h3_res8,
                "h3_res9": h3_res9,
                "h3_boundary": {
                    "type": "Polygon",
                    "coordinates": [h3_boundary_geojson]
                },
                "mule_count": cluster["mule_count"],
                "mule_accounts": cluster["mule_accounts"],
                "total_funds_at_risk": cluster["total_funds_at_risk"],
                "aggregate_risk_score": cluster["aggregate_risk_score"],
                "nearest_atms": nearest_atms,
                "raw_geojson_feature": geojson_feature
            }
            hotspots.append(hotspot_payload)

        # Sort hotspots by descending risk and amount
        hotspots.sort(key=lambda x: (x["risk_score"], x["total_amount"]), reverse=True)
        return hotspots
