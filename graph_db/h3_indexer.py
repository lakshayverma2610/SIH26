"""
Uber H3 Spatial Indexing & Polygon Generation Module
"""
from typing import List, Tuple, Dict, Any, Optional
import math

try:
    import h3
except ImportError:
    h3 = None

from graph_db.config import GeoEngineConfig

class H3SpatialIndexer:
    """
    High-performance wrapper for Uber H3 Discrete Global Grid System.
    Maps coordinates to hierarchical hexagonal cells and produces GeoJSON polygons.
    """

    def __init__(self, res_zone: int = GeoEngineConfig.DEFAULT_H3_RES_ZONE, res_kiosk: int = GeoEngineConfig.DEFAULT_H3_RES_KIOSK):
        self.res_zone = res_zone
        self.res_kiosk = res_kiosk

    def latlng_to_h3(self, lat: float, lon: float, resolution: Optional[int] = None) -> str:
        """
        Converts (lat, lon) to an H3 hexagon ID at the specified resolution.
        """
        res = resolution if resolution is not None else self.res_kiosk
        if h3 is None:
            return f"mock_hex_r{res}_{round(lat, 4)}_{round(lon, 4)}"

        # Compatibility with h3-py v3 and v4 APIs
        if hasattr(h3, "latlng_to_cell"):
            return h3.latlng_to_cell(lat, lon, res)
        elif hasattr(h3, "geo_to_h3"):
            return h3.geo_to_h3(lat, lon, res)
        else:
            return str(h3.latlng_to_cell(lat, lon, res))

    def get_cell_boundary(self, hex_id: str) -> List[List[float]]:
        """
        Returns the GeoJSON-compliant boundary vertices for a given H3 cell:
        [[[lon, lat], [lon, lat], ..., [lon_first, lat_first]]]
        """
        if h3 is None or hex_id.startswith("mock_hex"):
            # Synthetic hexagon coordinates around a centroid for testing/fallback
            parts = hex_id.split("_")
            try:
                lat, lon = float(parts[2]), float(parts[3])
            except Exception:
                lat, lon = 28.6139, 77.2090
            d = 0.002
            return [
                [lon, lat + d],
                [lon + d * 0.866, lat + d * 0.5],
                [lon + d * 0.866, lat - d * 0.5],
                [lon, lat - d],
                [lon - d * 0.866, lat - d * 0.5],
                [lon - d * 0.866, lat + d * 0.5],
                [lon, lat + d] # Closed loop
            ]

        try:
            if hasattr(h3, "cell_to_boundary"):
                coords = h3.cell_to_boundary(hex_id) # Returns tuple of (lat, lng)
            elif hasattr(h3, "h3_to_geo_boundary"):
                coords = h3.h3_to_geo_boundary(hex_id)
            else:
                coords = h3.cell_to_boundary(hex_id)

            # GeoJSON requires [lon, lat] order and a closed polygon ring
            polygon = [[pt[1], pt[0]] for pt in coords]
            if polygon and polygon[0] != polygon[-1]:
                polygon.append(polygon[0])
            return polygon
        except Exception:
            return []

    def get_cell_center(self, hex_id: str) -> Tuple[float, float]:
        """
        Returns the (lat, lon) centroid of an H3 cell.
        """
        if h3 is None or hex_id.startswith("mock_hex"):
            parts = hex_id.split("_")
            try:
                return float(parts[2]), float(parts[3])
            except Exception:
                return (28.6139, 77.2090)

        try:
            if hasattr(h3, "cell_to_latlng"):
                lat, lon = h3.cell_to_latlng(hex_id)
            elif hasattr(h3, "h3_to_geo"):
                lat, lon = h3.h3_to_geo(hex_id)
            else:
                lat, lon = h3.cell_to_latlng(hex_id)
            return (float(lat), float(lon))
        except Exception:
            return (28.6139, 77.2090)

    def get_k_ring(self, hex_id: str, k: int = 1) -> List[str]:
        """
        Returns all neighboring H3 cells within radius k.
        """
        if h3 is None or hex_id.startswith("mock_hex"):
            return [hex_id]
        try:
            if hasattr(h3, "grid_disk"):
                return list(h3.grid_disk(hex_id, k))
            elif hasattr(h3, "k_ring"):
                return list(h3.k_ring(hex_id, k))
            return [hex_id]
        except Exception:
            return [hex_id]

    def to_geojson_feature(self, hex_id: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Wraps an H3 cell into a standard GeoJSON Feature object.
        """
        coords = self.get_cell_boundary(hex_id)
        return {
            "type": "Feature",
            "properties": properties or {"h3_index": hex_id},
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
