import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np

# Ensure Homebrew OpenMP library path is accessible on macOS if needed
if sys.platform == "darwin" and os.path.exists("/opt/homebrew/opt/libomp/lib"):
    current_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
    if "/opt/homebrew/opt/libomp/lib" not in current_dyld:
        os.environ["DYLD_LIBRARY_PATH"] = f"/opt/homebrew/opt/libomp/lib:{current_dyld}".rstrip(":")

try:
    import treelite
    import treelite.gtil
except (ImportError, OSError):
    treelite = None

try:
    import onnxruntime as ort
except (ImportError, OSError):
    ort = None

from ai_engine.core.logger import get_logger
from ai_engine.core.schemas import ExtractedFeatures, InferenceResult

logger = get_logger(__name__)

class MuleScorer:
    """
    High-throughput hybrid inference engine supporting:
    1. Treelite GTIL (Ultra-low microsecond tree inference)
    2. ONNX Runtime (Vectorized SIMD inference)
    3. Deterministic Smurfing / Dormancy-Break heuristic overrides
    """

    def __init__(self, model_filename: str = "mule_model.treelite") -> None:
        self.models_dir = Path(__file__).resolve().parent / "saved"
        self.treelite_path = self.models_dir / model_filename
        self.onnx_path = self.models_dir / "mule_model.onnx"

        self.treelite_model = None
        self.onnx_session = None
        self.active_engine = "HEURISTIC"

        self._load_model()

    def _load_model(self) -> None:
        """Attempts to load the highest-performance runtime engine available."""
        # 1. Primary: Treelite GTIL (< 50 microseconds)
        if treelite and self.treelite_path.exists():
            try:
                self.treelite_model = treelite.Model.deserialize(str(self.treelite_path))
                self.active_engine = "TREELITE_GTIL"
                logger.info("⚡ Treelite GTIL Engine initialized (< 50µs inference).", extra={"path": str(self.treelite_path)})
                return
            except Exception as e:
                logger.warning(f"Treelite loading failed ({e}). Falling back to ONNX.")

        # 2. Secondary: ONNX Runtime (< 0.5 ms)
        if ort and self.onnx_path.exists():
            try:
                sess_options = ort.SessionOptions()
                sess_options.intra_op_num_threads = 2
                sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                self.onnx_session = ort.InferenceSession(str(self.onnx_path), sess_options)
                self.active_engine = "ONNX_RUNTIME"
                logger.info("🚀 ONNX Runtime initialized (Vectorized AVX inference).", extra={"path": str(self.onnx_path)})
                return
            except Exception as e:
                logger.warning(f"ONNX loading failed ({e}). Falling back to Heuristics.")

        logger.warning("No pre-trained model file found. Falling back to rule-based heuristics.")
        self.active_engine = "HEURISTIC_ONLY"

    def _features_to_matrix(self, features_list: List[ExtractedFeatures]) -> np.ndarray:
        return np.array([
            [
                f.amount,
                float(f.v1_out),
                float(f.v5_out),
                float(f.v1_in),
                float(f.fan_out_degree),
                float(f.dormancy_break),
                float(f.kyc_risk),
                float(f.device_reuse_count),
                float(f.ip_reuse_count)
            ]
            for f in features_list
        ], dtype=np.float32)

    def _predict_probabilities(self, X: np.ndarray) -> np.ndarray:
        """Runs batch inference using active high-performance engine."""
        n_samples = len(X)
        if n_samples == 0:
            return np.array([], dtype=np.float32)

        # 1. Treelite GTIL Engine
        if self.treelite_model is not None and treelite is not None:
            try:
                pred = treelite.gtil.predict(self.treelite_model, X)
                pred = np.squeeze(pred)
                if pred.ndim == 0:
                    pred = np.array([pred])
                if pred.ndim == 2 and pred.shape[1] > 1:
                    return pred[:, 1]
                return pred
            except Exception as e:
                logger.error(f"Treelite prediction error: {e}")

        # 2. ONNX Runtime Engine
        if self.onnx_session is not None:
            try:
                input_name = self.onnx_session.get_inputs()[0].name
                raw_out = self.onnx_session.run(None, {input_name: X})
                # Check for LightGBM ONNX outputs: [probabilities_tensor] or [labels, probabilities_maps]
                if len(raw_out) > 1 and isinstance(raw_out[1], list):
                    return np.array([d.get(1, 0.0) for d in raw_out[1]], dtype=np.float32)
                elif len(raw_out) > 1 and isinstance(raw_out[1], np.ndarray):
                    return raw_out[1][:, 1] if raw_out[1].shape[1] > 1 else raw_out[1][:, 0]
                elif len(raw_out) == 1 and isinstance(raw_out[0], np.ndarray):
                    return raw_out[0][:, 1] if raw_out[0].shape[1] > 1 else raw_out[0][:, 0]
            except Exception as e:
                logger.error(f"ONNX prediction error: {e}")

        # 3. Fallback Heuristics
        results = []
        for row in X:
            v1_out = row[1]
            fan_out = row[4]
            dormancy = row[5]
            score = 0.1
            if v1_out >= 3:
                score += 0.3
            if fan_out >= 3:
                score += 0.35
            if dormancy == 1:
                score += 0.3
            results.append(min(0.99, max(0.05, score)))
        return np.array(results, dtype=np.float32)

    def score(self, features: ExtractedFeatures) -> InferenceResult:
        """Scores a single transaction event in < 15ms (Treelite < 50µs)."""
        return self.score_batch([features])[0]

    def score_batch(self, features_list: List[ExtractedFeatures]) -> List[InferenceResult]:
        """
        High-speed batch inference method.
        Evaluates N transactions simultaneously using vectorized CPU matrix execution.
        """
        if not features_list:
            return []

        start_time = time.perf_counter()
        X = self._features_to_matrix(features_list)
        probs = self._predict_probabilities(X)

        results: List[InferenceResult] = []
        for idx, features in enumerate(features_list):
            fraud_prob = float(probs[idx]) if idx < len(probs) else 0.1
            is_high_risk = False
            reasons: List[str] = []

            # Step B: Deterministic Heuristic Override Rule
            # Rapid smurfing fan-out + Dormancy break is 100% fraud
            if features.fan_out_degree >= 4 and features.dormancy_break == 1:
                fraud_prob = 0.99
                is_high_risk = True
                reasons.append("CRITICAL: Dormancy break with rapid fan-out smurfing")

            # Step C: Confidence Threshold Checks
            if fraud_prob >= 0.75:
                is_high_risk = True
                if not reasons:
                    reasons.append(f"ML ({self.active_engine}) high risk probability (>= 0.75)")
            elif fraud_prob >= 0.50:
                reasons.append("Elevated risk probability detected")

            results.append(InferenceResult(
                tx_id=features.tx_id,
                fraud_probability=round(fraud_prob, 4),
                is_high_risk=is_high_risk,
                reasons=reasons
            ))

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Batch inference complete [{self.active_engine}]",
            extra={
                "batch_size": len(features_list),
                "total_latency_ms": round(latency_ms, 3),
                "avg_per_tx_us": round((latency_ms / len(features_list)) * 1000, 1)
            }
        )

        return results

    def score_features(self, features: ExtractedFeatures) -> dict:
        """Alias helper method returning dict for backend compatibility."""
        res = self.score(features)
        return {
            "fraud_probability": res.fraud_probability,
            "is_high_risk": res.is_high_risk,
            "reasons": res.reasons
        }
