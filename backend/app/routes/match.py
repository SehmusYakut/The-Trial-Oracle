"""POST /api/match — orchestrates trial fetch + K2 reasoning + structured response."""
from fastapi import APIRouter

from backend.app.models.patient import MatchRequest, MatchResponse, MatchResult
from backend.app.models.trial import TrialData
from backend.services.trial_service import fetch_trial
from backend.services.k2_service import match_patient_to_trial

router = APIRouter(prefix="/api", tags=["match"])


def _compute_eligibility_score(result: MatchResult) -> float:
    """
    Derive a 0.0–1.0 score from the per-criterion verdicts.

    Scoring rules:
      MET       → 1.0 per criterion
      UNCERTAIN → 0.5 per criterion
      NOT_MET   → 0.0 per criterion
    Final score is then zeroed if any disqualifying exclusion exists.
    """
    verdicts = result.criteria_verdicts
    if not verdicts:
        # No parseable criteria — fall back to label-based score
        return {"ELIGIBLE": 1.0, "UNCERTAIN": 0.5, "INELIGIBLE": 0.0}[
            result.overall_eligibility
        ]

    weight_map = {"MET": 1.0, "UNCERTAIN": 0.5, "NOT_MET": 0.0}
    raw_score = sum(weight_map.get(v.verdict, 0.0) for v in verdicts) / len(verdicts)

    if result.disqualifying_criteria:
        return 0.0

    return round(raw_score, 4)


def _build_response(result: MatchResult, trial: TrialData) -> MatchResponse:
    return MatchResponse(
        nct_id=result.nct_id,
        trial_title=trial.title,
        eligibility_score=_compute_eligibility_score(result),
        eligibility_label=result.overall_eligibility,
        confidence=result.confidence,
        summary=result.summary,
        reasoning_chain=result.criteria_verdicts,
        disqualifying_criteria=result.disqualifying_criteria,
        raw_reasoning=result.raw_reasoning,
    )


@router.post("/match", response_model=MatchResponse)
async def match_patient(body: MatchRequest):
    """
    Fetch trial data from ClinicalTrials.gov and run K2-Think-v2 eligibility analysis.

    Returns a structured response containing:
    - eligibility_score  : float 0.0–1.0
    - eligibility_label  : ELIGIBLE | INELIGIBLE | UNCERTAIN
    - confidence         : HIGH | MEDIUM | LOW
    - reasoning_chain    : per-criterion audit with patient evidence and verdict
    - raw_reasoning      : full K2 chain-of-thought
    """
    trial: TrialData = await fetch_trial(body.nct_id)
    result: MatchResult = await match_patient_to_trial(body.patient, trial)
    return _build_response(result, trial)
