"""
Enterprise Redis Database Seeder (CBS & ATM Spatial Store)
Bulk loads account metadata profiles into Redis Hashes (account:<id>)
and registers ATM coordinates into Redis Geospatial Index (atms:geo).
"""
import os
import sys
import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

def seed_redis(redis_url: str = None, accounts_count: int = 5000, atms_count: int = 1500):
    target_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"Connecting to Redis Master at: {target_url}...")

    try:
        import redis
        client = redis.Redis.from_url(target_url, decode_responses=True)
        client.ping()
        print(" Connected to Redis successfully.")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Please ensure Redis is running (e.g. docker run -d -p 6379:6379 redis:7-alpine)")
        return False

    pipe = client.pipeline()

    # 1. Seed ATM Geospatial Coordinates
    print(f"\n--- 1. Seeding {atms_count} ATM Kiosks into Redis Geospatial Index (atms:geo) ---")
    from data_simulation.generate_atm_locations import generate_atm_locations
    atms = generate_atm_locations(count=atms_count)

    geo_added = 0
    for atm in atms:
        atm_id = atm["atm_id"]
        lon = float(atm["lon"])
        lat = float(atm["lat"])
        # Redis GEOADD atms:geo <lon> <lat> <member>
        pipe.geoadd("atms:geo", (lon, lat, atm_id))
        pipe.hset(f"atm:{atm_id}", mapping={
            "bank_name": atm.get("bank_name", "Public Sector Bank ATM"),
            "lat": str(lat),
            "lon": str(lon),
            "address": atm.get("address", "Commercial Corridor"),
            "ifsc_prefix": atm.get("ifsc_prefix", "SBIN000")
        })
        geo_added += 1

    pipe.execute()
    print(f"✅ Successfully indexed {geo_added} physical ATMs in Redis GEO store.")

    # 2. Seed Account Profiles (CBS Master Store)
    print(f"\n--- 2. Seeding {accounts_count} Bank Account Profiles into Redis Hashes (account:<id>) ---")
    from data_simulation.generate_mule_chains import generate_mule_chains
    accounts, chains = generate_mule_chains(num_chains=250, num_baseline_accounts=accounts_count)

    acc_added = 0
    for acc in accounts:
        acc_id = acc["account_number"]
        pipe.hset(f"account:{acc_id}", mapping={
            "dormant_days": str(acc.get("dormant_days", 0)),
            "kyc_verified": "1" if acc.get("kyc_verified", True) else "0",
            "role": str(acc.get("role", "BASELINE_NORMAL")),
            "ip_address": str(acc.get("ip_address", "49.36.1.1")),
            "device_id": str(acc.get("device_id", "DEV_DEFAULT"))
        })
        acc_added += 1
        if acc_added % 1000 == 0:
            pipe.execute()

    pipe.execute()
    print(f"✅ Successfully stored {acc_added} account master profiles in Redis.")
    print(f"\n🎉 Enterprise Redis Datastore is fully primed and ready for high-throughput sub-50µs queries!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Enterprise Redis with CBS & ATM Spatial Data")
    parser.add_argument("--url", default=None, help="Redis connection URL (default: redis://localhost:6379/0)")
    parser.add_argument("--accounts", type=int, default=5000, help="Number of account profiles to seed")
    parser.add_argument("--atms", type=int, default=1500, help="Number of ATM locations to seed")
    args = parser.parse_args()

    seed_redis(redis_url=args.url, accounts_count=args.accounts, atms_count=args.atms)
