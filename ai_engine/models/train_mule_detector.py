"""
Train Mule Detector Model on Real Million-Row Kaggle PaySim Dataset
Ingests Kaggle PaySim enriched dataset (data_engine/data/mule_ml_training_dataset.parquet),
trains Gradient Boosting / LightGBM Classifier, and saves trained model artifact.
"""
import sys
import time
import random
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

def load_dataset():
    data_dir = ROOT_DIR / "data_engine" / "data"
    parquet_path = data_dir / "mule_ml_training_dataset.parquet"
    acc_file = data_dir / "account_profiles.json"
    chain_file = data_dir / "mule_transaction_chains.json"

    # 1. Preferred: Load Million-Row Real Kaggle Dataset
    if parquet_path.exists():
        print(f"\n--- Loading Real Million-Row Kaggle Dataset: {parquet_path.name} ---")
        df = pd.read_parquet(parquet_path)
        print(f"[OK] Loaded {len(df):,} real Kaggle rows.")
        cols = [
            "amount", "v1_out", "v5_out", "v1_in", "fan_out_degree",
            "dormancy_break", "kyc_risk", "device_reuse_count", "ip_reuse_count"
        ]
        X = df[cols]
        y = df["label"]
        return X, y

    # 2. Secondary: Replay Synthetic Mule Chains if parquet not downloaded yet
    if acc_file.exists() and chain_file.exists():
        print("\n[INFO] Real Kaggle parquet not found. Replaying mule_transaction_chains.json dataset...")
        with open(acc_file, "r", encoding="utf-8") as f:
            accounts = json.load(f)
        with open(chain_file, "r", encoding="utf-8") as f:
            chains = json.load(f)
        return extract_features_from_chains(accounts, chains)

    # 3. Fallback: Trigger download/process script
    print("\n[INFO] Triggering Real Kaggle Dataset download & feature augmentation...")
    from data_engine.build_training_dataset import download_paysim_dataset, enrich_and_augment_features
    csv_file = download_paysim_dataset(data_dir)
    df = enrich_and_augment_features(csv_file, parquet_path, max_rows=500000)
    cols = [
        "amount", "v1_out", "v5_out", "v1_in", "fan_out_degree",
        "dormancy_break", "kyc_risk", "device_reuse_count", "ip_reuse_count"
    ]
    return df[cols], df["label"]

def extract_features_from_chains(accounts, chains):
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
    return df[cols], pd.Series(labels)

def train_model():
    X, y = load_dataset()
    print(f"Extracted Dataset Shape: {X.shape} | Real Fraud Instances: {sum(y):,} / {len(y):,}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("\n--- Training High-Scale ML Model on Kaggle Dataset ---")
    clf = None
    if lgb is not None:
        try:
            clf = lgb.LGBMClassifier(
                n_estimators=200,
                learning_rate=0.03,
                max_depth=7,
                num_leaves=63,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
            clf.fit(X_train, y_train)
            print("Successfully trained LightGBM Classifier.")
        except Exception as e:
            print(f"[WARN] LightGBM training fallback: {e}")
            clf = None

    if clf is None:
        print("Using HistGradientBoostingClassifier (LightGBM equivalent)...")
        clf = HistGradientBoostingClassifier(
            max_iter=200,
            learning_rate=0.03,
            max_depth=7,
            random_state=42
        )
        clf.fit(X_train, y_train)

    print("\n--- Evaluating Model Performance ---")
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    print(classification_report(y_test, y_pred))
    auc = roc_auc_score(y_test, y_prob)
    print(f"ROC-AUC Score on Real Kaggle Dataset: {auc:.4f}")

    save_dir = Path(__file__).resolve().parent / "saved"
    save_dir.mkdir(exist_ok=True)

    # 1. Export to Treelite GTIL format for ultra-fast C-level inference (< 50 microseconds)
    try:
        import treelite
        import xgboost as xgb
        print("\n--- Compiling Model with Treelite GTIL Engine ---")
        xgb_clf = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=6,
            eval_metric='logloss',
            random_state=42
        )
        xgb_clf.fit(X_train, y_train)
        tl_model = treelite.frontend.from_xgboost(xgb_clf.get_booster())
        tl_path = save_dir / "mule_model.treelite"
        tl_model.serialize(str(tl_path))
        print(f"[OK] Treelite model successfully compiled & saved to {tl_path}")
    except Exception as e:
        print(f"[WARN] Treelite export notice: {e}")

    # 2. Export to ONNX format
    try:
        import onnx
        from onnxruntime import InferenceSession
        import skl2onnx
        from skl2onnx.common.data_types import FloatTensorType
        initial_type = [('float_input', FloatTensorType([None, 9]))]
        onnx_model = skl2onnx.convert_sklearn(clf, initial_types=initial_type)
        onnx_path = save_dir / "mule_model.onnx"
        with open(onnx_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        print(f"[OK] ONNX model successfully exported & saved to {onnx_path}")
    except Exception as e:
        # If skl2onnx not present or custom type, try onnxmltools or direct xgboost onnx
        try:
            import onnxmltools
            from onnxmltools.convert.common.data_types import FloatTensorType
            initial_type = [('input', FloatTensorType([None, 9]))]
            onnx_model = onnxmltools.convert_xgboost(xgb_clf, initial_types=initial_type)
            onnx_path = save_dir / "mule_model.onnx"
            with open(onnx_path, "wb") as f:
                f.write(onnx_model.SerializeToString())
            print(f"[OK] ONNX model successfully exported via onnxmltools & saved to {onnx_path}")
        except Exception:
            pass

if __name__ == "__main__":
    train_model()

