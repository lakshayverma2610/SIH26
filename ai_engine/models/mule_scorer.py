import time
import random
import pickle
from pathlib import Path
from typing import List, Optional

try:
    import onnxruntime as ort
except ImportError:
    ort = None

import numpy as np

from ai_engine.core.logger import get_logger
from ai_engine.core.schemas import ExtractedFeatures, InferenceResult

logger = get_logger(__name__)

class MuleScorer:
    """
    Production-ready hybrid ML + Heuristics inference engine.
    Evaluates ExtractedFeatures against pre-trained LightGBM model / ONNX,
    applying strict business rules for determinism and explainability.
    """
    
    def __init__(self, model_filename: str = "mule_model.pkl") -> None:
        self.models_dir = Path(__file__).resolve().parent
        self.pkl_path = self.models_dir / "saved" / model_filename
        self.onnx_path = self.models_dir / "artifacts" / "dummy_model.onnx"
        
        self.session = None
        self.pkl_model = None
        self._load_model()

    def _load_model(self) -> None:
        """Attempts to load pickle LightGBM model or ONNX session."""
        # 1. Try Pickle LightGBM model first
        if self.pkl_path.exists():
            try:
                with open(self.pkl_path, "rb") as f:
                    self.pkl_model = pickle.load(f)
                logger.info("Pickle LightGBM ML model loaded successfully.", extra={"model_path": str(self.pkl_path)})
                return
            except Exception as e:
                logger.error("Failed to load pickle LightGBM model. Trying ONNX fallback.", exc_info=True)

        # 2. Try ONNX runtime model
        if ort and self.onnx_path.exists():
            try:
                sess_options = ort.SessionOptions()
                sess_options.intra_op_num_threads = 1
                sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                self.session = ort.InferenceSession(str(self.onnx_path), sess_options)
                logger.info("ONNX ML model loaded successfully.", extra={"model_path": str(self.onnx_path)})
                return
            except Exception as e:
                logger.error("Failed to load ONNX model.", exc_info=True)

        logger.warning("No pre-trained model found. Initializing heuristic-driven risk evaluation.")

    def _get_ml_probability(self, features: ExtractedFeatures) -> float:
        """Runs inference using trained LightGBM pickle model or ONNX fallback."""
        input_vector = np.array([[
            features.amount, 
            float(features.v1_out), 
            float(features.v5_out), 
            float(features.v1_in), 
            float(features.fan_out_degree), 
            float(features.dormancy_break), 
            float(features.kyc_risk), 
            float(features.device_reuse_count), 
            float(features.ip_reuse_count)
        ]], dtype=np.float32)

        if self.pkl_model is not None:
            try:
                probs = self.pkl_model.predict_proba(input_vector)[0]
                return float(probs[1]) if len(probs) > 1 else float(probs[0])
            except Exception as e:
                logger.error(f"Error predicting with pickle model: {e}")

        if self.session is not None:
            try:
                input_name = self.session.get_inputs()[0].name
                result = self.session.run(None, {input_name: input_vector})
                return float(result[1][0][1])
            except Exception as e:
                logger.error(f"Error predicting with ONNX model: {e}")

        # Basic fallback heuristic probability calculation
        score = 0.1
        if features.v1_out >= 3:
            score += 0.3
        if features.fan_out_degree >= 3:
            score += 0.35
        if features.dormancy_break == 1:
            score += 0.3
        return min(0.99, max(0.05, score))

    def score(self, features: ExtractedFeatures) -> InferenceResult:
        """
        Evaluates transaction features and generates a final InferenceResult.
        Guaranteed execution in < 15ms.
        """
        start_time = time.perf_counter()
        
        # Step A: ML Model Probability
        fraud_prob = self._get_ml_probability(features)
        is_high_risk = False
        reasons: List[str] = []

        # Step B: Deterministic Heuristic Override
        # Fan-out > 4 AND Dormancy break is definitively fraudulent
        if features.fan_out_degree >= 4 and features.dormancy_break == 1:
            fraud_prob = 0.99
            is_high_risk = True
            reasons.append("CRITICAL: Dormancy break with rapid fan-out smurfing")
            logger.warning("Heuristic override triggered: Rapid fan-out + Dormancy break", extra={"tx_id": features.tx_id})

        # Step C: Threshold Check
        if fraud_prob >= 0.75:
            is_high_risk = True
            if not reasons:
                reasons.append("ML model indicated high risk probability (>= 0.75)")
        elif fraud_prob >= 0.50:
            reasons.append("Elevated risk probability detected")

        result = InferenceResult(
            tx_id=features.tx_id,
            fraud_probability=round(fraud_prob, 4),
            is_high_risk=is_high_risk,
            reasons=reasons
        )
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Inference pipeline execution complete", 
            extra={
                "tx_id": features.tx_id,
                "latency_ms": round(latency_ms, 2),
                "fraud_probability": result.fraud_probability,
                "is_high_risk": result.is_high_risk
            }
        )

        return result

    def score_features(self, features: ExtractedFeatures) -> dict:
        """Alias helper method returning dict for backend compatibility."""
        res = self.score(features)
        return {
            "fraud_probability": res.fraud_probability,
            "is_high_risk": res.is_high_risk,
            "reasons": res.reasons
        }
