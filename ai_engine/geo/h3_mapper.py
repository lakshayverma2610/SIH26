import math
try:
    import h3
except ImportError:
    h3 = None

from ai_engine.core.logger import get_logger
from ai_engine.core.schemas import CashoutPrediction

logger = get_logger(__name__)

class SpatioTemporalPredictor:
    """
    Production-ready geospatial predictor for cybercrime mule cash-outs.
    Converts digital transaction footprints into physical Uber H3 hexagons
    and applies Hawkes Process decay to model the urgency of the threat.
    """

    def __init__(self) -> None:
        if h3 is None:
            logger.warning("h3 library is not installed. SpatioTemporalPredictor will use mock Hex IDs.")
        logger.info("SpatioTemporalPredictor initialized successfully.")

    def get_h3_index(self, lat: float, lon: float, resolution: int = 9) -> str:
        """
        Converts a physical (latitude, longitude) coordinate into a deterministic
        Uber H3 Hexagon string ID.
        Resolution 9 represents an area of ~0.1 sq km (a neighborhood block).
        """
        if h3 is None:
            # Fallback for local development if h3 is missing
            return f"mock_hex_r{resolution}_{round(lat, 2)}_{round(lon, 2)}"
        
        # Depending on the h3-py version, the function might be latlng_to_cell or geo_to_h3.
        # We will attempt the modern latlng_to_cell first.
        try:
            return h3.latlng_to_cell(lat, lon, resolution)
        except AttributeError:
            return h3.geo_to_h3(lat, lon, resolution)

    def calculate_hawkes_decay(self, base_risk: float, time_elapsed_minutes: float) -> float:
        """
        Applies a Hawkes Process exponential decay function.
        In financial cybercrime, the probability of a physical cash-out spikes 
        immediately after the digital transfer occurs, and decays exponentially 
        as time passes (since mules try to withdraw instantly to avoid liens).
        
        Math: decayed_risk = base_risk * e^(-lambda * t)
        We use a lambda of 0.05 so the risk drops significantly (~10% of base) after 45 mins.
        """
        # Lambda decay constant. Higher = faster decay. 0.05 targets a 45-min critical window.
        decay_constant = 0.05 
        
        # e^(-lambda * t)
        decay_multiplier = math.exp(-decay_constant * time_elapsed_minutes)
        
        decayed_risk = base_risk * decay_multiplier
        
        # Ensure it stays within bounds
        return max(0.0, min(1.0, decayed_risk))

    def predict_cashout_zone(self, lat: float, lon: float, fraud_probability: float) -> CashoutPrediction:
        """
        Orchestrates the geospatial prediction.
        Takes the suspected terminal node's coordinates and the ML fraud probability,
        and outputs a strictly typed cash-out prediction zone for law enforcement.
        """
        # 1. Get the spatial boundary (Resolution 9 is optimal for ATM clusters)
        hex_id = self.get_h3_index(lat, lon, resolution=9)
        
        # 2. Assume T=0 for the initial alert generation
        time_elapsed = 0.0
        decayed_risk = self.calculate_hawkes_decay(base_risk=fraud_probability, time_elapsed_minutes=time_elapsed)
        
        # 3. Generate the temporal window (Standard SLA is 45 minutes for PCR dispatch)
        time_window = "T+0 to T+45 mins"
        
        # 4. Compile the strict Pydantic prediction schema
        prediction = CashoutPrediction(
            h3_hex_id=hex_id,
            decayed_risk_score=round(decayed_risk, 4),
            predicted_time_window=time_window
        )
        
        # 5. Observability: Structured logging of the geospatial conversion
        logger.info(
            "Geospatial cash-out zone predicted",
            extra={
                "lat": lat,
                "lon": lon,
                "h3_hex_id": prediction.h3_hex_id,
                "base_fraud_prob": fraud_probability,
                "decayed_risk": prediction.decayed_risk_score,
                "temporal_window": prediction.predicted_time_window
            }
        )
        
        return prediction
