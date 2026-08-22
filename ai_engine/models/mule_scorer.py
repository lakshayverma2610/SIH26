"""
LightGBM Mule Risk Scoring & Rule Boost Pipeline.
Trains quickly or performs ultra-fast in-memory inference (<10ms).
"""
import pickle
from pathlib import Path
from typing import Dict, Any

class MuleScorer:
    def __init__(self, model_path: str = None):
        self.model = None
        self.feature_names = [
            "amount", "v1_out", "v5_out", "v1_in", "fan_out_degree",
            "dormancy_break", "kyc_risk", "device_reuse_count", "ip_reuse_count"
        ]
        if model_path and Path(model_path).exists():
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)

    def score_features(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluate raw feature dictionary and output risk score (0.0 to 1.0)
        with explainability reasons.
        """
        # Rule-based heuristics (Fast inline safety guard)
        reasons = []
        rule_score = 0.0

        if features.get("dormancy_break", 0.0) == 1.0:
            rule_score += 0.35
            reasons.append("Sudden high-value activity on dormant account (>45 days)")

        if features.get("fan_out_degree", 0.0) >= 3.0:
            rule_score += 0.40
            reasons.append(f"Rapid fan-out / smurfing pattern ({int(features['fan_out_degree'])} destinations)")

        if features.get("v1_out", 0.0) >= 3.0:
            rule_score += 0.25
            reasons.append("Extreme outbound velocity in 60-second window")

        if features.get("device_reuse_count", 0.0) >= 3.0:
            rule_score += 0.20
            reasons.append("Device fingerprint linked to multiple unrelated accounts")

        # ML-based evaluation if trained model available
        ml_score = 0.0
        if self.model:
            try:
                row = [[features.get(k, 0.0) for k in self.feature_names]]
                probs = self.model.predict_proba(row)
                ml_score = float(probs[0][1])
            except Exception:
                ml_score = 0.0

        final_score = min(1.0, max(rule_score, ml_score))

        return {
            "fraud_probability": round(final_score, 4),
            "is_high_risk": final_score >= 0.70,
            "reasons": reasons if reasons else ["Normal transactional behavior"]
        }
