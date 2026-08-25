"""
Train Mule Detector Model
Ingests Gaurvi's synthetic mule chains & accounts, replays them through 
SlidingWindowFeatureEngine to extract real feature vectors, and trains ML Classifier.
"""
import sys
import time
import random
import pickle
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add root folders to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier

try:
    import lightgbm as lgb
except (ImportError, OSError):
    lgb = None

from ai_engine.features.sliding_window import SlidingWindowFeatureEngine
from ai_engine.core.schemas import TransactionEvent, AccountMetadata

def load_data_sources():
    data_dir = ROOT_DIR / "mock_data" / "data"
    acc_file = data_dir / "accounts.json"
    chain_file = data_dir / "chains.json"

    accounts = []
    chains = []

    if acc_file.exists():
        with open(acc_file, "r", encoding="utf-8") as f:
            accounts = json.load(f)

    if chain_file.exists():
        with open(chain_file, "r", encoding="utf-8") as f:
            chains = json.load(f)

    return accounts, chains

def extract_features_from_chains(accounts, chains):
    """
    Replays baseline transactions and multi-layer mule chains through SlidingWindowFeatureEngine.
    Extracts authentic 9D feature vectors for training.
    """
    print(f"Replaying {len(chains)} mule chains and baseline transactions through SlidingWindowFeatureEngine...")
    
    engine = SlidingWindowFeatureEngine()

    for acc in accounts:
        meta = AccountMetadata(
            account_id=acc["account_number"],
            dormant_days=acc.get("dormant_days", 0),
            kyc_verified=acc.get("kyc_verified", True)
        )
        engine.register_metadata(meta)

    feature_rows = []
    labels = []
    now = time.time()

    # 1. Normal Baseline Traffic Feature Extraction (Label 0)
    normal_accs = [a for a in accounts if a.get("role") == "BASELINE_NORMAL"]
    if not normal_accs:
        normal_accs = accounts[:1000]

    for i in range(12000):
        src = random.choice(normal_accs)
        dest = random.choice(normal_accs)
        while dest["account_number"] == src["account_number"]:
            dest = random.choice(normal_accs)

        tx_time = now - random.uniform(0, 3600)
        event = TransactionEvent(
            tx_id=f"TX_TRAIN_NORM_{i}",
            src_acc=src["account_number"],
            dest_acc=dest["account_number"],
            amount=round(random.uniform(200.0, 15000.0), 2),
            timestamp=tx_time,
            channel="UPI",
            device_id=src.get("device_id", "DEV_DEFAULT"),
            ip_address=src.get("ip_address", "49.36.1.1")
        )

        feats = engine.process_transaction(event)
        feature_rows.append([
            feats.amount, feats.v1_out, feats.v5_out, feats.v1_in,
            feats.fan_out_degree, feats.dormancy_break, feats.kyc_risk,
            feats.device_reuse_count, feats.ip_reuse_count
        ])
        labels.append(0)

    # 2. Fraudulent Mule Chains Feature Extraction (Label 1)
    for c_idx, chain in enumerate(chains):
        c_time = now - random.uniform(0, 1800)
        stolen = chain["total_stolen_amount"]
        victim = chain["victim_account"]
        l1 = chain["layer_1_mule"]
        l2_nodes = chain["layer_2_smurfing"]
        osint = chain.get("osint_metadata", {})

        ev1 = TransactionEvent(
            tx_id=f"TX_TRAIN_ATK_L1_{c_idx}",
            src_acc=victim,
            dest_acc=l1,
            amount=stolen,
            timestamp=c_time,
            channel="IMPS",
            device_id=f"DEV_RAT_{victim}",
            ip_address=osint.get("c2_ip", "185.220.101.4")
        )
        f1 = engine.process_transaction(ev1)
        feature_rows.append([
            f1.amount, f1.v1_out, f1.v5_out, f1.v1_in,
            f1.fan_out_degree, f1.dormancy_break, f1.kyc_risk,
            f1.device_reuse_count, f1.ip_reuse_count
        ])
        labels.append(1)

        split_amt = stolen / len(l2_nodes)
        for s_idx, l2 in enumerate(l2_nodes):
            ev2 = TransactionEvent(
                tx_id=f"TX_TRAIN_ATK_L2_{c_idx}_{s_idx}",
                src_acc=l1,
                dest_acc=l2,
                amount=split_amt,
                timestamp=c_time + (s_idx * 5),
                channel="UPI",
                device_id="DEV_SMURF_HUB_99",
                ip_address="157.33.190.12"
            )
            f2 = engine.process_transaction(ev2)
            feature_rows.append([
                f2.amount, f2.v1_out, f2.v5_out, f2.v1_in,
                f2.fan_out_degree, f2.dormancy_break, f2.kyc_risk,
                f2.device_reuse_count, f2.ip_reuse_count
            ])
            labels.append(1)

    cols = [
        "amount", "v1_out", "v5_out", "v1_in", "fan_out_degree",
        "dormancy_break", "kyc_risk", "device_reuse_count", "ip_reuse_count"
    ]
    df = pd.DataFrame(feature_rows, columns=cols)
    return df, pd.Series(labels)

def train_model():
    accounts, chains = load_data_sources()
    if not accounts or not chains:
        print("[WARN] No mock data found. Generating data first...")
        from mock_data.generate_atms import generate_atms
        from mock_data.generate_mules import generate_mules
        generate_atms(1500)
        generate_mules(250, 5000)
        accounts, chains = load_data_sources()

    X, y = extract_features_from_chains(accounts, chains)
    print(f"Extracted dataset shape: {X.shape} | Fraud instances: {sum(y)} / {len(y)}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("\nTraining Classifier...")
    if lgb is not None:
        try:
            clf = lgb.LGBMClassifier(
                n_estimators=150,
                learning_rate=0.03,
                max_depth=6,
                num_leaves=31,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
            clf.fit(X_train, y_train)
            print("Successfully trained LightGBM Classifier.")
        except Exception:
            clf = None

    if lgb is None or clf is None:
        print("Using HistGradientBoostingClassifier (LightGBM equivalent fallback)...")
        clf = HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.03,
            max_depth=6,
            random_state=42
        )
        clf.fit(X_train, y_train)

    print("\nEvaluating Model Performance:")
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    print(classification_report(y_test, y_pred))
    auc = roc_auc_score(y_test, y_prob)
    print(f"ROC-AUC Score: {auc:.4f}")

    save_dir = Path(__file__).resolve().parent / "saved"
    save_dir.mkdir(exist_ok=True)
    model_path = save_dir / "mule_model.pkl"

    with open(model_path, "wb") as f:
        pickle.dump(clf, f)

    print(f"\n[OK] Trained Mule Detector model successfully saved to {model_path}")

if __name__ == "__main__":
    train_model()
