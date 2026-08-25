"""
Real-Time Transaction Stream Simulator & Attack Injection Driver
Pushing directly to Kafka (Producer)
"""
import sys
import time
import json
import random
import requests
import argparse
import os
import threading
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
RAW_TX_TOPIC = "raw-transactions"
producer = None

if KAFKA_ENABLED:
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print(f"✅ Kafka Producer Connected: {KAFKA_BOOTSTRAP_SERVERS}")
    except ImportError:
        print("⚠️ 'kafka-python' not installed. Running in REST API mode. (pip install kafka-python)")
        KAFKA_ENABLED = False

API_URL = "http://localhost:8000/api/v1/transactions/stream"
COMPLAINT_API_URL = "http://localhost:8000/api/v1/complaints/ncrp"

# Global variables for multithreaded continuous streaming
STREAMING_ACTIVE = False
CURRENT_TPS = 5
tx_counter = 1

def generate_random_location():
    # 90% chance of being inside India, 10% chance of International
    if random.random() < 0.90:
        # Approximate bounding box for India
        lat = random.uniform(8.0, 37.0)
        lon = random.uniform(68.0, 97.0)
    else:
        # Global bounds (excluding poles)
        lat = random.uniform(-60.0, 70.0)
        lon = random.uniform(-180.0, 180.0)
    return lat, lon

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

def send_transaction(tx_payload, silent=False):
    if KAFKA_ENABLED and producer:
        try:
            producer.send(RAW_TX_TOPIC, tx_payload)
            # We don't flush on every single tx during high-volume background stream to maximize throughput
            if not silent:
                producer.flush()
                print(f"[KAFKA PUBLISH] TX {tx_payload['tx_id']}: {tx_payload['src_acc']} -> {tx_payload['dest_acc']} | Amount: INR {tx_payload['amount']}")
        except Exception as e:
            if not silent: print(f"[KAFKA ERR] {e}")
        return

    try:
        res = requests.post(API_URL, json=tx_payload, timeout=2.0)
        if not silent:
            if res.status_code == 200:
                data = res.json()
                score = data.get("fraud_score", 0.0)
                high_risk = data.get("is_high_risk", False)
                tag = "[CRITICAL ALERT]" if high_risk else "[NORMAL]"
                print(f"{tag} TX {tx_payload['tx_id']}: {tx_payload['src_acc']} -> {tx_payload['dest_acc']} | Amount: INR {tx_payload['amount']} | Score: {score}")
            else:
                print(f"[ERR] Status {res.status_code}: {res.text}")
    except Exception as e:
        if not silent: print(f"[ERR] API Connection Failed: {e}")

def continuous_background_worker(accounts, chains):
    """Runs on a separate thread, endlessly pumping normal transactions and rare unique attacks."""
    global tx_counter, STREAMING_ACTIVE, CURRENT_TPS
    
    normal_accounts = [a for a in accounts if a.get("role") == "BASELINE_NORMAL"]
    if not normal_accounts:
        normal_accounts = accounts

    while True:
        if STREAMING_ACTIVE and CURRENT_TPS > 0:
            # Generate random 12-digit account numbers to prevent artificial velocity/smurfing flags
            # on the backend sliding window engine, making high-TPS completely realistic baseline noise.
            src_acc = f"{random.randint(100000000000, 999999999999)}"
            dest_acc = f"{random.randint(100000000000, 999999999999)}"

            amount = round(random.uniform(200.0, 15000.0), 2)
            tx_id = f"TX_NORM_{int(time.time())}_{tx_counter:04d}"
            
            rand_lat, rand_lon = generate_random_location()

            payload = {
                "tx_id": tx_id,
                "src_acc": src_acc,
                "dest_acc": dest_acc,
                "amount": amount,
                "channel": "UPI",
                "device_id": f"DEV_{random.randint(1000, 9999)}",
                "ip": f"49.36.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "lat": rand_lat,
                "lon": rand_lon,
                "timestamp": time.time()
            }

            # Silent=True to not spam the terminal menu, just pump to Kafka
            send_transaction(payload, silent=True)
            tx_counter += 1
            
            # Periodically flush if using Kafka to clear the buffer
            if KAFKA_ENABLED and producer and tx_counter % 50 == 0:
                producer.flush()
                
            # Randomly inject a completely unique, fresh cybercrime attack into the background stream
            # Probability scaled inversely with TPS so we don't spam thousands of attacks
            prob = min(0.01 / CURRENT_TPS, 0.005)
            if chains and random.random() < prob:
                threading.Thread(target=trigger_attack_scenario, args=(random.choice(chains), True), daemon=True).start()
                
            time.sleep(1.0 / CURRENT_TPS)
        else:
            time.sleep(0.5)

def trigger_attack_scenario(chain, silent=False):
    now = time.time()
    
    # ALWAYS generate completely fresh, random, unique mule accounts for every attack
    # This ensures the AI model is tested on unseen accounts every single time
    victim = f"{random.randint(100000000000, 999999999999)}"
    l1 = f"{random.randint(100000000000, 999999999999)}"
    l2_count = len(chain.get("layer_2_smurfing", [1,2,3]))
    l2_nodes = [f"{random.randint(100000000000, 999999999999)}" for _ in range(l2_count)]
    
    atk_lat, atk_lon = generate_random_location()
    terminal_name = chain.get("layer_3_terminal", {}).get("bank_name", "Random Branch")
    osint = chain.get("osint_metadata", {})
    
    if not silent:
        print(f"\n=======================================================")
        print(f"🚨 INJECTING UNIQUE RANDOM ATTACK INTO STREAM")
        print(f"   Category: {chain['crime_category']} | Stolen Amount: INR {chain['total_stolen_amount']}")
        print(f"   Fresh Mule L1 Account Generated: {l1}")
        print(f"=======================================================")

    # Step 1: Ingest 1930 NCRP Complaint
    try:
        complaint_payload = {
            "ncrp_id": f"NCRP_{int(now)}",
            "victim_acc": victim,
            "suspect_acc": l1,
            "amount": chain["total_stolen_amount"],
            "complaint_type": chain["crime_category"]
        }
        requests.post(COMPLAINT_API_URL, json=complaint_payload, timeout=2.0)
    except:
        pass

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
        "lat": atk_lat,
        "lon": atk_lon,
        "timestamp": now
    }
    if not silent: print("\n--> Step A: Victim -> L1 Receiver Mule (High-Value Spiking)")
    send_transaction(payload1, silent=silent)
    time.sleep(0.5)

    # Step 3: Layer 1 -> Layer 2 Smurfing Splits (Rapid Fan-Out)
    split_amount = round(chain["total_stolen_amount"] / len(l2_nodes), 2)
    if not silent: print(f"\n--> Step B: L1 -> L2 Smurfing Nodes ({len(l2_nodes)} Rapid Split Transfers to Unique Accounts)")

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
            "lat": atk_lat + (idx * 0.0005),
            "lon": atk_lon + (idx * 0.0005),
            "timestamp": now + (idx * 2)
        }
        send_transaction(payload2, silent=silent)
        time.sleep(0.1)
        
    if KAFKA_ENABLED and producer:
        producer.flush()

    if not silent:
        print(f"\n🎯 Attack Injected! Model should detect physical target at: {terminal_name}")
        print("=======================================================\n")

def attack_submenu(chains):
    while True:
        print("\n--- INJECT SPECIFIC ATTACK ---")
        print("  [1] Jamtara APK RAT Fraud")
        print("  [2] Mewat Sextortion/AePS Attack")
        print("  [3] Back to Main Menu")
        choice = input("Select attack: ").strip()
        if choice == "1":
            apk_chains = [c for c in chains if c.get("crime_category") == "APK_RAT_FRAUD"]
            if apk_chains:
                trigger_attack_scenario(random.choice(apk_chains))
        elif choice == "2":
            mewat_chains = [c for c in chains if c.get("crime_category") in ["SEXTORTION_VISHING", "AEPS_BIOMETRIC_FRAUD"]]
            if mewat_chains:
                trigger_attack_scenario(random.choice(mewat_chains))
        elif choice == "3":
            break
        else:
            print("Invalid choice.")

def interactive_cli_menu(accounts, chains):
    global STREAMING_ACTIVE, CURRENT_TPS
    
    # Start the continuous background worker thread
    bg_thread = threading.Thread(target=continuous_background_worker, args=(accounts, chains), daemon=True)
    bg_thread.start()
    
    while True:
        status = "🟢 ACTIVE" if STREAMING_ACTIVE else "🔴 PAUSED"
        print("\n=======================================================")
        print("      Geo-CashWatch: Live Stream & Attack Controller   ")
        print("=======================================================")
        print(f"  Background Stream: {status} | Rate: {CURRENT_TPS} tx/sec")
        print("=======================================================")
        print("  [1] Toggle Continuous Background Stream")
        print("  [2] Change Stream Volume (TPS)")
        print("  [3] Inject Random Unique Cybercrime Attack")
        print("  [4] Specific Attack Submenu")
        print("  [5] Exit")
        print("=======================================================")
        choice = input("Enter command: ").strip()

        if choice == "1":
            STREAMING_ACTIVE = not STREAMING_ACTIVE
            print(f"Stream is now {'ACTIVE' if STREAMING_ACTIVE else 'PAUSED'}")
        elif choice == "2":
            try:
                new_tps = int(input("Enter new Transactions Per Second (e.g. 50, 1000): "))
                if new_tps > 0:
                    CURRENT_TPS = new_tps
                    print(f"Volume increased to {CURRENT_TPS} tx/sec!")
            except ValueError:
                print("Invalid input.")
        elif choice == "3":
            if chains:
                trigger_attack_scenario(random.choice(chains))
        elif choice == "4":
            attack_submenu(chains)
        elif choice == "5":
            print("Shutting down simulator...")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Geo-CashWatch Stream Simulator")
    args = parser.parse_args()

    accs, chs = load_simulation_data()
    if not accs or not chs:
        print("No simulation data found. Generating now...")
        from data_engine.generate_atm_locations import generate_atm_locations
        from data_engine.generate_mule_chains import generate_mule_chains
        generate_atm_locations(1500)
        generate_mule_chains(250, 5000)
        accs, chs = load_simulation_data()

    interactive_cli_menu(accs, chs)
