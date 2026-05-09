"""Routes for clinical trial data retrieval."""
from fastapi import APIRouter

from backend.app.models.trial import TrialData, TrialRequest
from backend.services.trial_service import fetch_trial

router = APIRouter(prefix="/trials", tags=["trials"])


@router.get("/{nct_id}", response_model=TrialData)
async def get_trial(nct_id: str):
    """Fetch and return structured data for a trial by its NCT ID."""
    return await fetch_trial(nct_id)


@router.post("/lookup", response_model=TrialData)
async def lookup_trial(body: TrialRequest):
    """Fetch trial data using a JSON body (useful for frontend forms)."""
    return await fetch_trial(body.nct_id)
