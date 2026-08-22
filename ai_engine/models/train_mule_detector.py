"""
Train LightGBM Mule Detector Model
Generates synthetic transaction features and trains a LightGBM Classifier.
"""
import sys
import time
import random
import pickle
from pathlib import Path
import pandas as pd
import numpy as np

# Add root folders to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

try:
    import lightgbm as lgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, roc_auc_score
except ImportError:
    print("Please install lightgbm, scikit-learn, and pandas: pip install lightgbm scikit-learn pandas")
    sys.exit(1)

from ai_engine.features.sliding_window import SlidingWindowFeatureEngine

def generate_training_data(num_samples=10000):
    """
    Generate synthetic feature data for training.
    In a real scenario, this would replay historical transactions through the SlidingWindowFeatureEngine.
    Here we synthesize the extracted features directly for simplicity and speed.
    """
    print(f"Generating {num_samples} synthetic training samples...")
    data = []
    labels = []

    for _ in range(num_samples):
        is_fraud = random.random() < 0.2  # 20% fraud rate in training data

        if is_fraud:
            # Fraudulent patterns: High velocity, fan-out, dormancy break
            amount = random.uniform(10000, 100000)
            v1_out = random.randint(2, 6)
            v5_out = v1_out + random.randint(0, 5)
            v1_in = random.randint(0, 2)
            fan_out = random.randint(3, 8)
            dormancy = 1.0 if random.random() < 0.7 else 0.0
            kyc = 1.0 if random.random() < 0.5 else 0.0
            dev_reuse = random.randint(1, 5)
            ip_reuse = random.randint(1, 4)
            labels.append(1)
        else:
            # Normal patterns: Low velocity, low fan-out
            amount = random.uniform(100, 20000)
            v1_out = random.randint(0, 1)
            v5_out = random.randint(0, 3)
            v1_in = random.randint(0, 1)
            fan_out = random.randint(0, 2)
            dormancy = 0.0
            kyc = 0.0 if random.random() < 0.95 else 1.0
            dev_reuse = random.randint(1, 2)
            ip_reuse = random.randint(1, 2)
            labels.append(0)

        data.append([amount, float(v1_out), float(v5_out), float(v1_in), float(fan_out), dormancy, kyc, float(dev_reuse), float(ip_reuse)])

    columns = [
        "amount", "v1_out", "v5_out", "v1_in", "fan_out_degree",
        "dormancy_break", "kyc_risk", "device_reuse_count", "ip_reuse_count"
    ]
    df = pd.DataFrame(data, columns=columns)
    return df, pd.Series(labels)

def train_model():
    X, y = generate_training_data(15000)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Training LightGBM Classifier...")
    # Initialize the model with parameters optimizing for precision (low false positives)
    clf = lgb.LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=5,
        num_leaves=31,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    clf.fit(X_train, y_train)
    
    print("Evaluating Model...")
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_prob):.4f}")
    
    # Save the model
    save_dir = Path(__file__).resolve().parent / "saved"
    save_dir.mkdir(exist_ok=True)
    model_path = save_dir / "mule_model.pkl"
    
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
        
    print(f"\n✅ Model saved to {model_path}")

if __name__ == "__main__":
    train_model()
