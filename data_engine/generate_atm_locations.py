"""
Generate Physical Cash Withdrawal Infrastructure Data (ATMs, AePS Micro-Merchants, Bank Branches)
Outputs to data_engine/data/atm_locations.json
"""
import sys
import json
import random
from pathlib import Path

# Add root folder to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    import h3
except ImportError:
    h3 = None

def get_h3_index(lat: float, lon: float, res: int = 9) -> str:
    if h3 is not None:
        try:
            return h3.latlng_to_cell(lat, lon, res)
        except AttributeError:
            return h3.geo_to_h3(lat, lon, res)
    # Deterministic fallback format matching H3 string pattern
    lat_int = int((lat + 90) * 10000)
    lon_int = int((lon + 180) * 10000)
    return f"8961{lat_int:06x}{lon_int:05x}"[:15]

def generate_atm_locations(count: int = 1500):
    print(f"Generating {count} realistic physical cash withdrawal kiosks across Indian cybercrime corridors...")
    
    corridors = [
        {"name": "Jamtara", "state": "Jharkhand", "lat_center": 24.2185, "lon_center": 86.6492, "weight": 0.20},
        {"name": "Deoghar", "state": "Jharkhand", "lat_center": 24.4826, "lon_center": 86.6994, "weight": 0.15},
        {"name": "Nuh/Mewat", "state": "Haryana", "lat_center": 28.1025, "lon_center": 77.0145, "weight": 0.20},
        {"name": "Bharatpur", "state": "Rajasthan", "lat_center": 27.2170, "lon_center": 77.4895, "weight": 0.15},
        {"name": "Delhi NCR", "state": "Delhi/UP", "lat_center": 28.6304, "lon_center": 77.2773, "weight": 0.15},
        {"name": "Mumbai Metro", "state": "Maharashtra", "lat_center": 19.0760, "lon_center": 72.8777, "weight": 0.15}
    ]

    banks = [
        {"code": "SBI", "name": "State Bank of India", "ifsc_prefix": "SBIN000"},
        {"code": "HDFC", "name": "HDFC Bank", "ifsc_prefix": "HDFC000"},
        {"code": "ICICI", "name": "ICICI Bank", "ifsc_prefix": "ICIC000"},
        {"code": "PNB", "name": "Punjab National Bank", "ifsc_prefix": "PUNB000"},
        {"code": "BOB", "name": "Bank of Baroda", "ifsc_prefix": "BARB000"},
        {"code": "AXIS", "name": "Axis Bank", "ifsc_prefix": "UTIB000"},
        {"code": "IPPB", "name": "India Post Payments Bank (AePS Point)", "ifsc_prefix": "IPOS000"},
        {"code": "PAYTM", "name": "Paytm Payments Bank AePS Micro-Merchant", "ifsc_prefix": "PYTM000"}
    ]

    terminal_types = ["ATM_STANDALONE", "E_LOBBY", "AEPS_MICRO_MERCHANT", "BANK_BRANCH_CASH_COUNTER"]

    atms = []
    
    # Priority high-density anchor ATMs for Delhi NCR (to align with graph_db built-in defaults)
    anchor_atms = [
        {"atm_id": "ATM_SBI_101", "bank_name": "SBI ATM & Cash Point", "lat": 28.6304, "lon": 77.2773, "address": "Main Vikas Marg, Laxmi Nagar, Delhi", "city": "Delhi"},
        {"atm_id": "ATM_HDFC_102", "bank_name": "HDFC Bank ATM Kiosk", "lat": 28.6315, "lon": 77.2785, "address": "Near Metro Gate 2, Laxmi Nagar, Delhi", "city": "Delhi"},
        {"atm_id": "ATM_ICICI_103", "bank_name": "ICICI Bank 24/7 ATM", "lat": 28.6292, "lon": 77.2760, "address": "Guru Ram Dass Nagar, Laxmi Nagar, Delhi", "city": "Delhi"},
        {"atm_id": "ATM_PNB_104", "bank_name": "Punjab National Bank ATM", "lat": 28.6328, "lon": 77.2801, "address": "Shakarpur Commercial Complex, Delhi", "city": "Delhi"},
        {"atm_id": "ATM_AXIS_105", "bank_name": "Axis Bank ATM", "lat": 28.6335, "lon": 77.2765, "address": "Panchsheel Enclave, Shakarpur, Delhi", "city": "Delhi"},
        {"atm_id": "ATM_SBI_201", "bank_name": "State Bank of India", "lat": 28.6320, "lon": 77.2185, "address": "Block B, Connaught Place, New Delhi", "city": "Delhi"},
        {"atm_id": "ATM_HDFC_202", "bank_name": "HDFC Bank Cash Deposit", "lat": 28.6340, "lon": 77.2205, "address": "Radial Road 4, Connaught Place, New Delhi", "city": "Delhi"}
    ]

    for anchor in anchor_atms:
        anchor["daily_limit_inr"] = 500000.0
        anchor["terminal_type"] = "E_LOBBY"
        anchor["h3_res9"] = get_h3_index(anchor["lat"], anchor["lon"], 9)
        anchor["is_active"] = True
        atms.append(anchor)

    # Generate remaining ATMs
    remaining_count = count - len(anchor_atms)
    for i in range(1, remaining_count + 1):
        corridor = random.choices(corridors, weights=[c["weight"] for c in corridors])[0]
        bank = random.choice(banks)
        term_type = random.choice(terminal_types)

        # Offset within ~15km radius of corridor center
        lat_offset = random.gauss(0, 0.08)
        lon_offset = random.gauss(0, 0.08)
        lat = round(corridor["lat_center"] + lat_offset, 5)
        lon = round(corridor["lon_center"] + lon_offset, 5)

        atm_id = f"ATM_{bank['code']}_{corridor['name'][:3].upper()}_{i:04d}"
        address = f"Kiosk #{i}, Main Road, {corridor['name']}, {corridor['state']}"
        daily_limit = float(random.choice([100000, 200000, 400000, 500000]))
        h3_res9 = get_h3_index(lat, lon, 9)

        atms.append({
            "atm_id": atm_id,
            "bank_name": f"{bank['name']} - {term_type.replace('_', ' ')}",
            "lat": lat,
            "lon": lon,
            "address": address,
            "city": corridor["name"],
            "state": corridor["state"],
            "daily_limit_inr": daily_limit,
            "terminal_type": term_type,
            "h3_res9": h3_res9,
            "is_active": True
        })

    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "atm_locations.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(atms, f, indent=2)

    print(f"[OK] Generated {len(atms)} ATM & AePS locations saved to {out_file}")
    return atms

if __name__ == "__main__":
    generate_atm_locations(1500)
