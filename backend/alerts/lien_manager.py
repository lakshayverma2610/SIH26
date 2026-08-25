import json
import logging
from datetime import datetime, timezone


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def trigger_account_freeze(account_numbers_list):
    """
    Simulate an emergency lien/account-freeze request.

    This is a project simulation and does not connect
    to any real banking system.
    """

    if not isinstance(account_numbers_list, list):
        raise TypeError("account_numbers_list must be a list.")

    if not account_numbers_list:
        raise ValueError("At least one account number is required.")

    payload = {
        "request_type": "EMERGENCY_LIEN",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "accounts": [
            {
                "account_number": str(account_number),
                "action": "FREEZE_WITHDRAWALS",
                "daily_atm_limit": 0
            }
            for account_number in account_numbers_list
        ]
    }

    logging.info(
        "Simulated emergency lien request created for %d account(s).",
        len(account_numbers_list)
    )

    return {
        "status": "SIMULATED_LIEN_PLACED",
        "payload": payload
    }


if __name__ == "__main__":
    sample_accounts = [
        "SIMULATED_ACCOUNT_001",
        "SIMULATED_ACCOUNT_002"
    ]

    result = trigger_account_freeze(sample_accounts)

    print("\nLien Manager Result:")
    print(json.dumps(result, indent=4))