"""
Generate Synthetic Fraud Network Topologies & NCRP 1930 Cybercrime Complaints
Outputs to data_simulation/data/account_profiles.json and data_simulation/data/mule_transaction_chains.json
"""
import sys
import json
import random
import time
from pathlib import Path

# Add root folder to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

def generate_mule_chains(num_chains: int = 250, num_baseline_accounts: int = 5000):
    print(f"Generating {num_baseline_accounts} baseline accounts & {num_chains} multi-layer mule chains...")

    accounts = []
    chains = []

    # Load generated ATMs to link Layer 3 terminal nodes
    atms_file = Path(__file__).resolve().parent / "data" / "atm_locations.json"
    atms = []
    if atms_file.exists():
        with open(atms_file, "r", encoding="utf-8") as f:
            atms = json.load(f)

    # 1. Generate Baseline Legitimate Accounts
    for i in range(1, num_baseline_accounts + 1):
        acc_num = f"ACC_BASE_{i:05d}"
        accounts.append({
            "account_number": acc_num,
            "dormant_days": 0,
            "kyc_verified": True,
            "role": "BASELINE_NORMAL",
            "ip_address": f"49.36.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "device_id": f"DEV_BASE_{random.randint(100, 999)}"
        })

    config_path = Path(__file__).resolve().parent / "simulation_config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    crime_categories = config["crime_categories"]
    c2_ips = config["c2_ips"]
    telegram_channels = config["telegram_channels"]

    # 2. Generate 3-to-4 Layer Mule Chains
    for c in range(1, num_chains + 1):
        chain_id = f"CHAIN_NCRP_2026_{c:04d}"
        category = random.choice(crime_categories)

        stolen_amount = float(random.choice([
            random.randint(25000, 85000),
            random.randint(100000, 350000),
            random.randint(450000, 1500000)
        ]))

        # Victim Node
        victim_acc = f"ACC_VICTIM_{c:04d}"
        victim_ip = f"106.213.{random.randint(1, 255)}.{random.randint(1, 255)}"
        victim_device = f"DEV_VICTIM_{random.randint(1000, 9999)}"
        accounts.append({
            "account_number": victim_acc,
            "dormant_days": 0,
            "kyc_verified": True,
            "role": "VICTIM",
            "ip_address": victim_ip,
            "device_id": victim_device
        })

        # Layer 1 Receiver Mule Node (Dormant Account Spiking)
        l1_mule = f"ACC_MULE_L1_{c:04d}"
        dormant_days = random.randint(46, 180)
        l1_ip = random.choice(c2_ips)
        accounts.append({
            "account_number": l1_mule,
            "dormant_days": dormant_days,
            "kyc_verified": False,
            "role": "LAYER_1_RECEIVER",
            "ip_address": l1_ip,
            "device_id": f"DEV_MULE_L1_{random.randint(1000, 9999)}"
        })

        # Layer 2 Smurfing Mules (3 to 6 split nodes)
        num_l2 = random.randint(3, 6)
        l2_mules = []
        l2_share = stolen_amount / num_l2

        # Shared device/IP multiplexing typical of cyber fraud hubs
        shared_l2_ip = f"157.33.{random.randint(1, 255)}.{random.randint(1, 255)}"
        shared_l2_device = f"DEV_MULE_HUB_{random.randint(10, 99)}"

        for s in range(1, num_l2 + 1):
            l2_acc = f"ACC_MULE_L2_{c:04d}_{s}"
            l2_mules.append(l2_acc)
            accounts.append({
                "account_number": l2_acc,
                "dormant_days": random.randint(10, 60),
                "kyc_verified": random.choice([True, False]),
                "role": "LAYER_2_SMURFING",
                "ip_address": shared_l2_ip,
                "device_id": shared_l2_device
            })

        # Layer 3 Physical Terminal ATM
        target_atm = random.choice(atms) if atms else {
            "atm_id": config["anchor_atms"][0]["atm_id"],
            "bank_name": config["anchor_atms"][0]["bank_name"],
            "lat": config["anchor_atms"][0]["lat"],
            "lon": config["anchor_atms"][0]["lon"],
            "h3_res9": "89618c0e667ffff" # Mocked fallback
        }

        # Threat OSINT Metadata
        osint = {
            "c2_ip": random.choice(c2_ips),
            "apk_package_name": "com.sbi.rewards.update.apk" if category == "APK_RAT_FRAUD" else None,
            "telegram_channel": random.choice(telegram_channels),
            "victim_imei": f"86420104{random.randint(1000000, 9999999)}",
            "target_h3_res9": target_atm.get("h3_res9")
        }

        chain_obj = {
            "chain_id": chain_id,
            "ncrp_complaint_id": f"NCRP-1930-2026-{random.randint(100000, 999999)}",
            "crime_category": category,
            "total_stolen_amount": stolen_amount,
            "victim_account": victim_acc,
            "layer_1_mule": l1_mule,
            "layer_2_smurfing": l2_mules,
            "layer_3_terminal": {
                "atm_id": target_atm.get("atm_id"),
                "bank_name": target_atm.get("bank_name"),
                "lat": target_atm.get("lat"),
                "lon": target_atm.get("lon"),
                "h3_res9": target_atm.get("h3_res9")
            },
            "time_delta_seconds": random.randint(15, 60),
            "osint_metadata": osint
        }

        chains.append(chain_obj)

    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    acc_file = out_dir / "account_profiles.json"
    chain_file = out_dir / "mule_transaction_chains.json"

    with open(acc_file, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)

    with open(chain_file, "w", encoding="utf-8") as f:
        json.dump(chains, f, indent=2)

    print(f"[OK] Generated {len(accounts)} accounts saved to {acc_file}")
    print(f"[OK] Generated {len(chains)} 3-layer mule chains saved to {chain_file}")
    return accounts, chains

if __name__ == "__main__":
    generate_mule_chains(250, 5000)

