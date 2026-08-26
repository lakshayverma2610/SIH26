"""
Multi-Channel Alert Broadcaster
Dispatches urgent cash-out hotspot alerts to law enforcement nodal officers
and cyber defense command centers.
"""
import os
import json
import logging
import urllib.request
import urllib.parse
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==============================================================================
# CONFIGURATION & ENVIRONMENT VARIABLES
# ==============================================================================
env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
if os.path.exists(env_file_path):
    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# 1. Primary Live Alert Channel: Email via Resend API
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
ALERT_RECIPIENT_EMAIL = os.getenv("ALERT_RECIPIENT_EMAIL", "")

# 2. Placeholders for Future Production Integrations
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")
ALERT_RECIPIENT_PHONE = os.getenv("ALERT_RECIPIENT_PHONE", "")
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")


def send_email_alert(subject: str, body: str) -> Dict[str, Any]:
    """Sends real-time email alert to nodal officers via Resend API."""
    if not RESEND_API_KEY or not ALERT_RECIPIENT_EMAIL:
        return {"status": "SKIPPED", "channel": "EMAIL", "reason": "RESEND_API_KEY or ALERT_RECIPIENT_EMAIL not configured"}

    url = "https://api.resend.com/emails"
    payload = json.dumps({
        "from": "Geo-CashWatch <onboarding@resend.dev>",
        "to": [ALERT_RECIPIENT_EMAIL],
        "subject": subject,
        "text": body
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            logging.info(f"✅ [EMAIL ALERT DELIVERED] Recipient: {ALERT_RECIPIENT_EMAIL} | ID: {res_data.get('id')}")
            return {"status": "DELIVERED", "channel": "EMAIL", "id": res_data.get("id")}
    except Exception as e:
        logging.error(f"[EMAIL ALERT ERR] {e}")
        return {"status": "FAILED", "channel": "EMAIL", "error": str(e)}


def send_sms_alert(message: str) -> Dict[str, Any]:
    """Sends SMS alert via Fast2SMS (placeholder for production with funded balance)."""
    if not FAST2SMS_API_KEY or not ALERT_RECIPIENT_PHONE:
        return {"status": "SKIPPED", "channel": "SMS", "reason": "Fast2SMS credentials not configured"}

    phone_clean = ALERT_RECIPIENT_PHONE.replace("+91", "").replace("-", "").strip()
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = json.dumps({
        "route": "q",
        "message": message,
        "language": "english",
        "numbers": phone_clean
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "authorization": FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            status = "DELIVERED" if res_data.get("return") is True else "FAILED"
            return {"status": status, "channel": "SMS", "recipient": phone_clean}
    except Exception as e:
        logging.error(f"[SMS ALERT ERR] {e}")
        return {"status": "FAILED", "channel": "SMS", "error": str(e)}


def send_webhook_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sends structured JSON alert to external CAD or SIEM platform (placeholder)."""
    if not ALERT_WEBHOOK_URL:
        return {"status": "SKIPPED", "channel": "WEBHOOK", "reason": "ALERT_WEBHOOK_URL not configured"}

    try:
        payload = json.dumps(alert_data).encode("utf-8")
        req = urllib.request.Request(
            ALERT_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return {"status": "DELIVERED", "channel": "WEBHOOK", "http_status": response.status}
    except Exception as e:
        logging.error(f"[WEBHOOK ERR] {e}")
        return {"status": "FAILED", "channel": "WEBHOOK", "error": str(e)}


def broadcast_to_agencies(alert_data: Dict[str, Any], channels: List[str] = None) -> Dict[str, Any]:
    """
    Broadcasts critical cash-out alerts to law enforcement agencies and nodal officers.
    Defaults to active Email notifications, with optional SMS/Webhook dispatch.
    """
    if channels is None:
        channels = ["EMAIL", "SMS", "WEBHOOK"]

    hotspot_id = alert_data.get("hotspot_id", "UNKNOWN_HOTSPOT")
    severity = alert_data.get("severity", "CRITICAL")
    message_text = alert_data.get("message", "Immediate cash-out threat detected.")

    formatted_msg = (
        f"[GEO-CASHWATCH CYBER DEFENSE ALERT]\n"
        f"Severity: {severity}\n"
        f"H3 Hotspot Cell: {hotspot_id}\n"
        f"Threat Details: {message_text}\n"
        f"Action Required: Dispatch PCR patrol & place 1930 account lien."
    )

    logging.info(f"Initiating {severity} broadcast for hotspot {hotspot_id}")
    delivery_reports = {}

    for channel in channels:
        ch_upper = channel.upper()
        if ch_upper == "EMAIL":
            subject = f"[{severity} ALERT] Geo-CashWatch ATM Egress Hotspot: {hotspot_id}"
            delivery_reports["EMAIL"] = send_email_alert(subject, formatted_msg)
        elif ch_upper == "SMS":
            delivery_reports["SMS"] = send_sms_alert(f"[CYBER ALERT] Hotspot {hotspot_id}: {message_text}")
        elif ch_upper == "WEBHOOK":
            delivery_reports["WEBHOOK"] = send_webhook_alert(alert_data)

    return {
        "status": "BROADCAST_COMPLETE",
        "hotspot_id": hotspot_id,
        "delivery_reports": delivery_reports
    }


if __name__ == "__main__":
    sample_alert = {
        "hotspot_id": "8828308281fffff",
        "severity": "CRITICAL",
        "message": "Convergence of 4 mule accounts detected near SBI ATM Kiosk (Deoghar)."
    }

    result = broadcast_to_agencies(sample_alert)
    print("\nBroadcaster Output:")
    print(json.dumps(result, indent=2))
