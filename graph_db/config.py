"""
Geospatial & Graph Configuration Parameters for SIH 26184
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class GeoEngineConfig:
    # Uber H3 Resolutions
    # Res 8: Area ~0.74 sq km, Edge ~461m (Neighborhood / Zone level)
    # Res 9: Area ~0.10 sq km, Edge ~174m (Street / ATM Kiosk Strip level)
    DEFAULT_H3_RES_ZONE: int = 8
    DEFAULT_H3_RES_KIOSK: int = 9

    # Spatio-Temporal Clustering (ST-DBSCAN) parameters
    SPATIAL_EPS_KM: float = 1.0       # 1 km spatial radius
    TEMPORAL_EPS_SECONDS: float = 1800.0  # 30-minute rolling temporal window
    MIN_SAMPLES_CLUSTER: int = 2     # Minimum 2 events to form a multi-mule cluster

    # Cashout Prediction & Urgency Modeling
    HAWKES_LAMBDA: float = 0.05       # Exponential decay parameter for 45-min SLA
    CASHOUT_BUFFER_MINUTES: int = 25  # Estimated time buffer before physical cash-out
    MAX_NEAREST_ATMS: int = 5         # Top N nearest ATMs to rank per hotspot
    ATM_SEARCH_RADIUS_KM: float = 2.5 # Search radius around cluster center for ATMs
