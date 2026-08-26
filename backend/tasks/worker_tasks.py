"""
Huey Asynchronous Worker Tasks
Handles background dispatching for CAD 112, I4C CFCFRMS liens, multi-channel alerts, and DB audit logging.
"""
import os
import json
import time
import logging
from typing import List, Dict, Any, Optional

from backend.tasks.huey_app import huey
from backend.database.session import ScopedSession
from backend.database.models import (
    PoliceDispatchRecordModel,
    LienActionRecordModel,
    HotspotRecordModel,
    AccountProfileModel
)
from backend.integrations.cfcfrms_client import cfcfrms_client
from backend.integrations.erss_cad_client import erss_cad_client
from backend.integrations.npci_nfs_client import npci_nfs_client
from backend.alerts.broadcaster import broadcast_to_agencies
from backend.alerts.report_generator import generate_incident_report

logger = logging.getLogger(__name__)

def make_task_wrapper(func):
    """Wraps function with @huey.task() if Huey is active, otherwise runs synchronously."""
    if huey is not None:
        return huey.task()(func)
    return func


@make_task_wrapper
def task_async_dispatch_pcr(
    dispatch_id: str,
    h3_cell: str,
    target_atm_name: str,
    lat: float,
    lon: float,
    priority_tier: str = "CRITICAL"
) -> Dict[str, Any]:
    """
    Asynchronously triggers State Police ERSS 112 CAD patrol van routing and updates database.
    """
    logger.info(f"[HUEY WORKER] Executing async CAD dispatch for {target_atm_name} ({lat}, {lon})...")
    res = erss_cad_client.dispatch_pcr_van(
        h3_cell=h3_cell,
        target_atm_name=target_atm_name,
        lat=lat,
        lon=lon,
        priority=priority_tier
    )

    db = ScopedSession()
    try:
        dispatch_record = PoliceDispatchRecordModel(
            dispatch_id=dispatch_id,
            cad_call_id=res.get("cad_call_id", f"CAD-{int(time.time())}"),
            h3_cell=h3_cell,
            target_atm_name=target_atm_name,
            destination_lat=lat,
            destination_lon=lon,
            priority=priority_tier,
            assigned_pcr_unit=res.get("assigned_unit", "PCR_LEO_UNIT_01"),
            cad_transmission_status=res.get("status", "DISPATCHED"),
            notes=json.dumps(res)
        )
        db.merge(dispatch_record)

        # Update hotspot status to DISPATCHED
        hotspot = db.query(HotspotRecordModel).filter(HotspotRecordModel.h3_res9 == h3_cell).first()
        if hotspot:
            hotspot.status = "DISPATCHED"

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[DB ERR in async dispatch] {e}")
    finally:
        db.close()

    return res


@make_task_wrapper
def task_async_trigger_cfcfrms_lien(
    suspect_accounts: List[str],
    stolen_amount: float,
    ncrp_ack: Optional[str] = None
) -> Dict[str, Any]:
    """
    Asynchronously places 1930 CFCFRMS emergency liens across bank CBS networks and logs audit trail.
    """
    logger.info(f"[HUEY WORKER] Executing async 1930 lien for {len(suspect_accounts)} accounts...")
    res = cfcfrms_client.place_emergency_lien(
        suspect_accounts=suspect_accounts,
        stolen_amount=stolen_amount,
        ncrp_ack_number=ncrp_ack
    )

    db = ScopedSession()
    try:
        now_time = time.time()
        for idx, acc in enumerate(suspect_accounts):
            lien_id = f"LIEN_{int(now_time)}_{idx}"
            lien_record = LienActionRecordModel(
                lien_id=lien_id,
                cfcfrms_ack_ref=res.get("ncrp_ack_number", "NCRP_DIRECT"),
                account_number=acc,
                bank_code="CBS_SWITCH",
                requested_amount=stolen_amount / max(1, len(suspect_accounts)),
                actual_frozen_amount=stolen_amount / max(1, len(suspect_accounts)),
                status="LIEN_PLACED",
                response_payload=json.dumps(res)
            )
            db.merge(lien_record)

            # Update account profile active lien status
            acc_profile = db.query(AccountProfileModel).filter(AccountProfileModel.account_number == acc).first()
            if acc_profile:
                acc_profile.active_lien = True
                acc_profile.lien_amount = stolen_amount / max(1, len(suspect_accounts))

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[DB ERR in async lien] {e}")
    finally:
        db.close()

    return res


@make_task_wrapper
def task_async_broadcast_alert(alert_data: Dict[str, Any], channels: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Asynchronously broadcasts multi-channel alerts (Email, SMS, Webhook).
    """
    logger.info(f"[HUEY WORKER] Executing multi-channel broadcast for {alert_data.get('hotspot_id')}...")
    return broadcast_to_agencies(alert_data, channels=channels)


@make_task_wrapper
def task_async_compile_incident_report(incident_data: Dict[str, Any], output_filename: str) -> str:
    """
    Asynchronously generates markdown incident forensic dossier.
    """
    logger.info(f"[HUEY WORKER] Compiling forensic incident dossier to {output_filename}...")
    return generate_incident_report(incident_data, output_file=output_filename)


@make_task_wrapper
def task_async_restrict_atm(atm_id: str, duration_minutes: int = 30) -> Dict[str, Any]:
    """
    Asynchronously issues terminal-level ATM restrict order to NPCI NFS.
    """
    return npci_nfs_client.restrict_atm_dispenser(atm_id, duration_minutes=duration_minutes)
