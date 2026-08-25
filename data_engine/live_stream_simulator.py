"""
Real-Time Transaction Stream Simulator & Attack Injection Driver
Targets FastAPI Backend at http://localhost:8000/api/v1/transactions/stream
"""
import sys
import time
import json
import random
import requests
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

API_URL = "http://localhost:8000/api/v1/transactions/stream"
COMPLAINT_API_URL = "http://localhost:8000/api/v1/complaints/ncrp"

def load_simulation_data():
    data_dir = Path(__file__).resolve().parent / "data"
    acc_file = data_dir / "account_profiles.json"
    chain_file = data_dir / "mule_transaction_chains.json"

    accounts = []
    chains = []

    if acc_file.exists():
        with open(acc_file, "r", encoding="utf-8") as f:
            accounts = json.load(f)

    if chain_file.exists():
        with open(chain_file, "r", encoding="utf-8") as f:
            chains = json.load(f)

    return accounts, chains

def send_transaction(tx_payload):
    try:
        res = requests.post(API_URL, json=tx_payload, timeout=2.0)
        if res.status_code == 200:
            data = res.json()
            score = data.get("fraud_score", 0.0)
            high_risk = data.get("is_high_risk", False)
            tag = "[CRITICAL ALERT]" if high_risk else "[NORMAL]"
            print(f"{tag} TX {tx_payload['tx_id']}: {tx_payload['src_acc']} -> {tx_payload['dest_acc']} | Amount: INR {tx_payload['amount']} | Score: {score}")
        else:
            print(f"[ERR] Status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[ERR] API Connection Failed: {e}")

def run_continuous_background_stream(accounts, rate_per_sec=5):
    print(f"\n--- Starting Background Baseline Stream ({rate_per_sec} tx/sec) ---")
    tx_counter = 1
    normal_accounts = [a for a in accounts if a.get("role") == "BASELINE_NORMAL"]
    if not normal_accounts:
        normal_accounts = accounts

    try:
        while True:
            src = random.choice(normal_accounts)
            dest = random.choice(normal_accounts)
            while dest["account_number"] == src["account_number"]:
                dest = random.choice(normal_accounts)

            amount = round(random.uniform(200.0, 15000.0), 2)
            tx_id = f"TX_NORM_{int(time.time())}_{tx_counter:04d}"

            payload = {
                "tx_id": tx_id,
                "src_acc": src["account_number"],
                "dest_acc": dest["account_number"],
                "amount": amount,
                "channel": "UPI",
                "device_id": src.get("device_id", "DEV_DEFAULT"),
                "ip": src.get("ip_address", "49.36.10.10"),
                "lat": 28.6304 + random.uniform(-0.02, 0.02),
                "lon": 77.2773 + random.uniform(-0.02, 0.02),
                "timestamp": time.time()
            }

            send_transaction(payload)
            tx_counter += 1
            time.sleep(1.0 / rate_per_sec)
    except KeyboardInterrupt:
        print("\nBackground stream paused.")

def trigger_attack_scenario(chain):
    print(f"\n=======================================================")
    print(f"🚨 TRIGGERING NCRP SCENARIO: {chain['ncrp_complaint_id']}")
    print(f"   Category: {chain['crime_category']} | Stolen Amount: INR {chain['total_stolen_amount']}")
    print(f"=======================================================")

    now = time.time()
    victim = chain["victim_account"]
    l1 = chain["layer_1_mule"]
    l2_nodes = chain["layer_2_smurfing"]
    terminal = chain["layer_3_terminal"]
    osint = chain.get("osint_metadata", {})

    # Step 1: Ingest 1930 NCRP Complaint
    try:
        complaint_payload = {
            "ncrp_id": chain["ncrp_complaint_id"],
            "victim_acc": victim,
            "suspect_acc": l1,
            "amount": chain["total_stolen_amount"],
            "complaint_type": chain["crime_category"]
        }
        res = requests.post(COMPLAINT_API_URL, json=complaint_payload, timeout=2.0)
        print(f"[NCRP 1930 INGESTION] Res: {res.json()}")
    except Exception as e:
        print(f"[NCRP 1930 INGESTION ERR] {e}")

    # Step 2: Layer 0 -> Layer 1 (Spike into Dormant Receiver)
    tx1_id = f"TX_ATK_L1_{int(now)}"
    payload1 = {
        "tx_id": tx1_id,
        "src_acc": victim,
        "dest_acc": l1,
        "amount": chain["total_stolen_amount"],
        "channel": "IMPS",
        "device_id": f"DEV_RAT_{victim}",
        "ip": osint.get("c2_ip", "185.220.101.4"),
        "lat": terminal.get("lat", 28.6304),
        "lon": terminal.get("lon", 77.2773),
        "timestamp": now
    }
    print("\n--> Step A: Victim -> L1 Receiver Mule (High-Value Spiking)")
    send_transaction(payload1)
    time.sleep(0.5)

    # Step 3: Layer 1 -> Layer 2 Smurfing Splits (Rapid Fan-Out within 180s)
    split_amount = round(chain["total_stolen_amount"] / len(l2_nodes), 2)
    print(f"\n--> Step B: L1 -> L2 Smurfing Nodes ({len(l2_nodes)} Rapid Split Transfers)")

    for idx, l2 in enumerate(l2_nodes, 1):
        tx2_id = f"TX_ATK_L2_{int(now)}_{idx}"
        payload2 = {
            "tx_id": tx2_id,
            "src_acc": l1,
            "dest_acc": l2,
            "amount": split_amount,
            "channel": "UPI",
            "device_id": "DEV_SMURF_HUB_99",
            "ip": "157.33.190.12",
            "lat": terminal.get("lat", 28.6304) + (idx * 0.0005),
            "lon": terminal.get("lon", 77.2773) + (idx * 0.0005),
            "timestamp": now + (idx * 2)
        }
        send_transaction(payload2)
        time.sleep(0.2)

    print(f"\n🎯 Target Physical Cash Withdrawal Hotspot: {terminal.get('bank_name')} ({terminal.get('h3_res9')})")
    print("=======================================================\n")

BATCH_API_URL = "http://localhost:8000/api/v1/transactions/batch"

def send_batch_transactions(accounts, batch_size=50):
    print(f"\n🚀 Sending High-Speed Batch Burst ({batch_size} transactions) to FastAPI Treelite Engine...")
    tx_list = []
    now = time.time()
    normal_accounts = [a for a in accounts if a.get("role") == "BASELINE_NORMAL"] or accounts

    for i in range(batch_size):
        src = random.choice(normal_accounts)
        dest = random.choice(normal_accounts)
        while dest["account_number"] == src["account_number"]:
            dest = random.choice(normal_accounts)

        tx_list.append({
            "tx_id": f"TX_BATCH_{int(now)}_{i:03d}",
            "src_acc": src["account_number"],
            "dest_acc": dest["account_number"],
            "amount": round(random.uniform(500.0, 45000.0), 2),
            "channel": random.choice(["UPI", "IMPS", "NEFT"]),
            "device_id": src.get("device_id", "DEV_DEFAULT"),
            "ip": src.get("ip_address", "49.36.1.1"),
            "lat": 28.6304 + random.uniform(-0.03, 0.03),
            "lon": 77.2773 + random.uniform(-0.03, 0.03),
            "timestamp": now + (i * 0.1)
        })

    try:
        t0 = time.perf_counter()
        res = requests.post(BATCH_API_URL, json={"transactions": tx_list}, timeout=5.0)
        t1 = time.perf_counter()
        if res.status_code == 200:
            data = res.json()
            print(f"[OK] Batch Ingested! Engine: {data.get('engine')} | Processed: {data.get('total_ingested')} tx | Server Latency: {data.get('latency_ms')} ms | Client Roundtrip: {(t1-t0)*1000:.2f} ms")
        else:
            print(f"[ERR] Batch failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[ERR] Batch connection failed: {e}")

def interactive_cli_menu(accounts, chains):
    while True:
        print("\n=======================================================")
        print("      AEGIS-Geo Cybercrime Stream Simulator (SIH 26184) ")
        print("=======================================================")
        print("  [1] Start Continuous Background Baseline Stream (5 tx/sec)")
        print("  [2] Trigger Random Cybercrime Attack Scenario")
        print("  [3] Trigger Jamtara APK RAT Fraud Scenario")
        print("  [4] Trigger Mewat Sextortion / AePS Scenario")
        print("  [5] Trigger High-Throughput Batch Burst (50 tx via Treelite)")
        print("  [6] Exit Simulator")
        print("=======================================================")
        choice = input("Enter option (1-6): ").strip()

        if choice == "1":
            run_continuous_background_stream(accounts, rate_per_sec=5)
        elif choice == "2":
            if chains:
                trigger_attack_scenario(random.choice(chains))
            else:
                print("No chains found in data/mule_transaction_chains.json. Run generate_mule_chains.py first.")
        elif choice == "3":
            apk_chains = [c for c in chains if c.get("crime_category") == "APK_RAT_FRAUD"]
            if apk_chains:
                trigger_attack_scenario(apk_chains[0])
            elif chains:
                trigger_attack_scenario(chains[0])
        elif choice == "4":
            mewat_chains = [c for c in chains if c.get("crime_category") in ["SEXTORTION_VISHING", "AEPS_BIOMETRIC_FRAUD"]]
            if mewat_chains:
                trigger_attack_scenario(mewat_chains[0])
            elif chains:
                trigger_attack_scenario(chains[0])
        elif choice == "5":
            send_batch_transactions(accounts, batch_size=50)
        elif choice == "6":
            print("Exiting simulator. Good luck with SIH demo!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AEGIS-Geo Real-Time Stream Simulator")
    parser.add_argument("--mode", choices=["interactive", "background", "attack"], default="interactive")
    args = parser.parse_args()

    accs, chs = load_simulation_data()
    if not accs or not chs:
        print("No simulation data found. Generating now...")
        from data_engine.generate_atm_locations import generate_atm_locations
        from data_engine.generate_mule_chains import generate_mule_chains
        generate_atm_locations(1500)
        generate_mule_chains(250, 5000)
        accs, chs = load_simulation_data()

    if args.mode == "background":
        run_continuous_background_stream(accs, 5)
    elif args.mode == "attack":
        if chs:
            trigger_attack_scenario(chs[0])
    else:
        interactive_cli_menu(accs, chs)
