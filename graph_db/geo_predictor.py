"""
Geospatial Predictor & ATM Point-of-Egress Forecasting Engine
"""
from typing import List, Dict, Any, Optional
import json
import math
import time
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
            {"atm_id": "ATM_SBI_101", "bank_name": "SBI ATM & Cash Point", "lat": 28.6304, "lon": 77.2773, "address": "Main Vikas Marg, Laxmi Nagar, Delhi"},
            {"atm_id": "ATM_HDFC_102", "bank_name": "HDFC Bank ATM Kiosk", "lat": 28.6315, "lon": 77.2785, "address": "Near Metro Gate 2, Laxmi Nagar, Delhi"},
            {"atm_id": "ATM_ICICI_103", "bank_name": "ICICI Bank 24/7 ATM", "lat": 28.6292, "lon": 77.2760, "address": "Guru Ram Dass Nagar, Laxmi Nagar, Delhi"},
            {"atm_id": "ATM_PNB_104", "bank_name": "Punjab National Bank ATM", "lat": 28.6328, "lon": 77.2801, "address": "Shakarpur Commercial Complex, Delhi"},
            {"atm_id": "ATM_AXIS_105", "bank_name": "Axis Bank ATM", "lat": 28.6335, "lon": 77.2765, "address": "Panchsheel Enclave, Shakarpur, Delhi"},

            {"atm_id": "ATM_SBI_201", "bank_name": "State Bank of India", "lat": 28.6320, "lon": 77.2185, "address": "Block B, Connaught Place, New Delhi"},
            {"atm_id": "ATM_HDFC_202", "bank_name": "HDFC Bank Cash Deposit", "lat": 28.6340, "lon": 77.2205, "address": "Radial Road 4, Connaught Place, New Delhi"},
            {"atm_id": "ATM_ICICI_203", "bank_name": "ICICI Bank Express ATM", "lat": 28.6295, "lon": 77.2160, "address": "Inner Circle, Connaught Place, New Delhi"},
            {"atm_id": "ATM_BOB_204", "bank_name": "Bank of Baroda e-Lobby", "lat": 28.6355, "lon": 77.2230, "address": "Barakhamba Road, New Delhi"},

            {"atm_id": "ATM_KOTAK_301", "bank_name": "Kotak Mahindra Bank ATM", "lat": 28.6520, "lon": 77.1905, "address": "Ajmal Khan Road, Karol Bagh, Delhi"},
            {"atm_id": "ATM_SBI_302", "bank_name": "SBI ATM Kiosk", "lat": 28.6508, "lon": 77.1880, "address": "Pusa Road, Karol Bagh, Delhi"},

            {"atm_id": "ATM_AXIS_401", "bank_name": "Axis Bank 24h ATM", "lat": 28.5285, "lon": 77.2195, "address": "District Centre, Saket, New Delhi"},
            {"atm_id": "ATM_HDFC_402", "bank_name": "HDFC Bank ATM", "lat": 28.5270, "lon": 77.2210, "address": "Select Citywalk Corridor, Saket, New Delhi"},

            {"atm_id": "ATM_SBI_501", "bank_name": "SBI ATM Sector 18", "lat": 28.5708, "lon": 77.3255, "address": "Atta Market, Sector 18, Noida"},
            {"atm_id": "ATM_ICICI_502", "bank_name": "ICICI Bank ATM Hub", "lat": 28.5720, "lon": 77.3270, "address": "Wave Mall Commercial, Sector 18, Noida"}
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
            # Decay score = e^(-dist_km / 0.8)
            prob = max(0.1, min(0.99, math.exp(-dist_km / 0.8)))
            
            ranked_atms.append({
                "atm_id": atm.get("atm_id", "ATM_GENERIC"),
                "bank_name": atm.get("bank_name", "Public Sector Bank ATM"),
                "lat": atm["lat"],
                "lon": atm["lon"],
                "address": atm.get("address", "Metro Commercial Corridor"),
                "distance_meters": dist_meters,
                "withdrawal_probability": round(prob, 2),
                "h3_res9": atm.get("h3_res9")
            })

        # Sort by distance ascending
        ranked_atms.sort(key=lambda x: x["distance_meters"])
        return ranked_atms[:top_k]

    def calculate_time_window(self, base_timestamp: float) -> str:
        """
        Calculates expected cash-out intervention window.
        """
        start_min = 0
        end_min = self.config.CASHOUT_BUFFER_MINUTES + 20
        return f"T+{start_min} to T+{end_min} mins (CRITICAL INTERCEPTION)"

    def aggregate_hotspots(self, flagged_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main public interface called by backend/main.py.
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
            h3_boundary = self.h3_indexer.get_cell_boundary(h3_res9)

            # 4. Find nearest ATM kiosks
            nearest_atms = self.find_nearest_atms(c_lat, c_lon, top_k=self.config.MAX_NEAREST_ATMS)

            # 5. Build GeoJSON Feature for Sneha's dashboard
            geojson_feature = {
                "type": "Feature",
                "properties": {
                    "cluster_id": cluster["cluster_id"],
                    "severity": cluster["severity"],
                    "mule_count": cluster["mule_count"],
                    "total_funds": cluster["total_funds_at_risk"],
                    "risk_score": cluster["aggregate_risk_score"],
                    "h3_index": h3_res9
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [h3_boundary]
                }
            }

            hotspot_payload = {
                "cluster_id": cluster["cluster_id"],
                "severity": cluster["severity"],
                "center_lat": c_lat,
                "center_lon": c_lon,
                "h3_res8": h3_res8,
                "h3_res9": h3_res9,
                "h3_boundary": {
                    "type": "Polygon",
                    "coordinates": [h3_boundary]
                },
                "mule_count": cluster["mule_count"],
                "mule_accounts": cluster["mule_accounts"],
                "total_funds_at_risk": cluster["total_funds_at_risk"],
                "aggregate_risk_score": cluster["aggregate_risk_score"],
                "predicted_cashout_window": self.calculate_time_window(time.time()),
                "nearest_atms": nearest_atms,
                "raw_geojson_feature": geojson_feature
            }
            hotspots.append(hotspot_payload)

        return hotspots


if __name__ == "__main__":
    # Self-test script
    predictor = GeospatialPredictor()
    sample_events = [
        {"account_number": "ACC_MULE_01", "lat": 28.6304, "lon": 77.2773, "amount": 150000, "fraud_probability": 0.96},
        {"account_number": "ACC_MULE_02", "lat": 28.6312, "lon": 77.2780, "amount": 120000, "fraud_probability": 0.92},
        {"account_number": "ACC_MULE_03", "lat": 28.6298, "lon": 77.2765, "amount": 90000, "fraud_probability": 0.88}
    ]
    results = predictor.aggregate_hotspots(sample_events)
    print("Self-Test Hotspots Output:")
    print(json.dumps(results, indent=2))
