"""Service for fetching and parsing clinical trial data from ClinicalTrials.gov API v2."""
import asyncio

import httpx
from fastapi import HTTPException

from backend.app.models.trial import EligibilityCriteria, TrialData

_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
_TIMEOUT = 30.0
_MAX_RETRIES = 3
_RETRY_STATUSES = {403, 429, 500, 502, 503}

# Full browser-like headers — ClinicalTrials.gov returns 403 to bare httpx/requests agents.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://clinicaltrials.gov/",
    "Origin": "https://clinicaltrials.gov",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def _parse_eligibility(raw_text: str) -> EligibilityCriteria:
    inclusion: list[str] = []
    exclusion: list[str] = []

    if not raw_text:
        return EligibilityCriteria(inclusion=inclusion, exclusion=exclusion)

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    inc_marker = "Inclusion Criteria:"
    exc_marker = "Exclusion Criteria:"
    inc_start = text.find(inc_marker)
    exc_start = text.find(exc_marker)

    if inc_start != -1:
        inc_block = text[inc_start + len(inc_marker): exc_start if exc_start != -1 else None]
        inclusion = _extract_bullets(inc_block)

    if exc_start != -1:
        exclusion = _extract_bullets(text[exc_start + len(exc_marker):])

    if inc_start == -1 and exc_start == -1:
        inclusion = _extract_bullets(text)

    return EligibilityCriteria(inclusion=inclusion, exclusion=exclusion)


def _extract_bullets(block: str) -> list[str]:
    items = []
    for line in block.splitlines():
        line = line.strip().lstrip("*-•·").strip()
        if line:
            items.append(line)
    return items


async def fetch_trial(nct_id: str) -> TrialData:
    """
    Fetch a single study from ClinicalTrials.gov API v2.

    Retries up to _MAX_RETRIES times with exponential back-off for transient
    errors (403, 429, 5xx). Raises a specific HTTP 403 exception if the server
    continues to block after all attempts so the caller can surface a clear
    "API Blocked" message rather than a generic 502.
    """
    nct_id = nct_id.strip().upper()
    url = f"{_BASE_URL}/{nct_id}"

    last_status: int | None = None

    for attempt in range(_MAX_RETRIES):
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as client:
            try:
                response = await client.get(url)
            except httpx.RequestError as exc:
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise HTTPException(
                    status_code=503,
                    detail=f"ClinicalTrials.gov API unreachable after {_MAX_RETRIES} attempts: {exc}",
                )

        last_status = response.status_code

        if last_status == 200:
            break

        if last_status == 404:
            raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found on ClinicalTrials.gov.")

        if last_status in _RETRY_STATUSES and attempt < _MAX_RETRIES - 1:
            await asyncio.sleep(2 ** attempt)
            continue

        # All retries exhausted — raise the most specific error possible.
        if last_status == 403:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"ClinicalTrials.gov blocked the request (403 Forbidden) after {_MAX_RETRIES} attempts. "
                    "The API may be rate-limiting this IP. Wait 60 seconds and retry."
                ),
            )
        raise HTTPException(
            status_code=502,
            detail=f"ClinicalTrials.gov returned HTTP {last_status} after {_MAX_RETRIES} attempts.",
        )

    data = response.json()
    protocol = data.get("protocolSection", {})

    identification = protocol.get("identificationModule", {})
    title = identification.get("briefTitle", "")

    conditions = protocol.get("conditionsModule", {}).get("conditions", [])
    status = protocol.get("statusModule", {}).get("overallStatus")
    phases = protocol.get("designModule", {}).get("phases", [])
    phase = phases[0] if phases else None

    raw_criteria = protocol.get("eligibilityModule", {}).get("eligibilityCriteria", "")
    eligibility = _parse_eligibility(raw_criteria)

    return TrialData(
        nct_id=nct_id,
        title=title,
        conditions=conditions,
        eligibility=eligibility,
        status=status,
        phase=phase,
    )
