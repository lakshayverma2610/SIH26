"""
Unit and Integration Tests for Geospatial & Graph Engine
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from graph_db.h3_indexer import H3SpatialIndexer
from graph_db.cluster_engine import SpatioTemporalClusterEngine
from graph_db.geo_predictor import GeospatialPredictor


def test_h3_indexer():
    print("[TEST] Testing H3SpatialIndexer...")
    indexer = H3SpatialIndexer()
    lat, lon = 28.6304, 77.2773

    hex_res8 = indexer.latlng_to_h3(lat, lon, resolution=8)
    hex_res9 = indexer.latlng_to_h3(lat, lon, resolution=9)
    assert hex_res8 is not None, "Failed to generate Res 8 H3 index"
    assert hex_res9 is not None, "Failed to generate Res 9 H3 index"

    boundary = indexer.get_cell_boundary(hex_res9)
    assert len(boundary) >= 6, "Boundary polygon must have at least 6 vertices"
    assert boundary[0] == boundary[-1], "Boundary polygon must form a closed loop"

    feature = indexer.to_geojson_feature(hex_res9, {"name": "Laxmi Nagar Hub"})
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Polygon"
    print(f"  ✓ Hex Res 8: {hex_res8}, Hex Res 9: {hex_res9}")
    print("  ✓ H3SpatialIndexer passed!")


def test_cluster_engine():
    print("[TEST] Testing SpatioTemporalClusterEngine...")
    engine = SpatioTemporalClusterEngine(spatial_eps_km=1.5, temporal_eps_sec=1800)

    # Test single-point fallback (should not crash or drop alert)
    single_event = [{"account_number": "ACC_001", "lat": 28.6304, "lon": 77.2773, "amount": 100000, "fraud_probability": 0.95}]
    res_single = engine.cluster_events(single_event)
    assert len(res_single) == 1
    assert res_single[0]["mule_count"] == 1

    # Test multi-point convergence
    events = [
        {"account_number": "ACC_MULE_1", "lat": 28.6304, "lon": 77.2773, "amount": 150000, "fraud_probability": 0.96},
        {"account_number": "ACC_MULE_2", "lat": 28.6315, "lon": 77.2785, "amount": 120000, "fraud_probability": 0.93},
        {"account_number": "ACC_MULE_3", "lat": 28.6290, "lon": 77.2760, "amount": 80000, "fraud_probability": 0.89},
        # Distant outlier point (Connaught Place ~10km away)
        {"account_number": "ACC_MULE_OUTLIER", "lat": 28.5285, "lon": 77.2195, "amount": 50000, "fraud_probability": 0.85}
    ]

    clusters = engine.cluster_events(events)
    assert len(clusters) >= 2, "Expected at least 2 distinct clusters (Laxmi Nagar and Saket)"
    main_cluster = clusters[0]
    assert main_cluster["mule_count"] >= 2
    assert main_cluster["severity"] in ["CRITICAL", "HIGH"]
    print(f"  ✓ Formed {len(clusters)} clusters. Top cluster severity: {main_cluster['severity']}")
    print("  ✓ SpatioTemporalClusterEngine passed!")


def test_geo_predictor():
    print("[TEST] Testing GeospatialPredictor...")
    predictor = GeospatialPredictor()

    sample_flagged_stream = [
        {"account_number": "ACC_9921", "lat": 28.6304, "lon": 77.2773, "amount": 250000, "fraud_probability": 0.97},
        {"account_number": "ACC_9922", "lat": 28.6310, "lon": 77.2780, "amount": 180000, "fraud_probability": 0.94}
    ]

    hotspots = predictor.aggregate_hotspots(sample_flagged_stream)
    assert len(hotspots) >= 1, "Should produce at least 1 active cash-out hotspot"

    top_hotspot = hotspots[0]
    assert "h3_boundary" in top_hotspot
    assert "nearest_atms" in top_hotspot
    assert len(top_hotspot["nearest_atms"]) > 0, "Should identify nearest physical ATMs"

    closest_atm = top_hotspot["nearest_atms"][0]
    print(f"  ✓ Hotspot ID: {top_hotspot['cluster_id']}")
    print(f"  ✓ Target ATM: {closest_atm['bank_name']} ({closest_atm['distance_meters']}m away)")
    print(f"  ✓ Intervention SLA: {top_hotspot['predicted_cashout_window']}")
    print("  ✓ GeospatialPredictor passed!")


if __name__ == "__main__":
    print("=" * 60)
    print(" RUNNING GEOSPATIAL & GRAPH ENGINE INTEGRATION TESTS")
    print("=" * 60)
    test_h3_indexer()
    test_cluster_engine()
    test_geo_predictor()
    print("=" * 60)
    print(" ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
