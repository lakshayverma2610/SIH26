"""
Transaction Ingestion Stream Router
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.app.schemas.transaction import (
    TransactionPayload,
    TransactionBatchPayload,
    ProcessedTransactionResponse
)
from backend.app.core.stream_orchestrator import orchestrator

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])

@router.post(
    "/stream",
    response_model=ProcessedTransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest Real-time Banking / UPI Transaction"
)
async def ingest_transaction(tx: TransactionPayload):
    """
    Ingest a single transaction, extract sliding-window velocity & multiplexing features,
    score mule probability, and trigger hotspot alerts if high risk.
    """
    try:
        tx_dict = tx.model_dump()
        result = await orchestrator.process_transaction(tx_dict)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction processing failed: {str(e)}"
        )

@router.post(
    "/batch",
    response_model=List[ProcessedTransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Batch Ingest High-Speed Transaction Stream"
)
async def ingest_transaction_batch(batch: TransactionBatchPayload):
    """
    Ingest multiple transactions in batch mode for high-throughput stream simulators.
    """
    try:
        tx_dicts = [tx.model_dump() for tx in batch.transactions]
        results = await orchestrator.process_batch(tx_dicts)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )

@router.get(
    "/recent",
    summary="Fetch Recent Ingested Transactions"
)
def get_recent_transactions(limit: int = 30):
    """
    Fetch the latest transactions buffer with computed fraud scores and flags.
    """
    return {
        "status": "SUCCESS",
        "count": len(orchestrator.recent_transactions[-limit:]),
        "transactions": orchestrator.recent_transactions[-limit:]
    }
