"""Service for fetching and parsing clinical trial data from ClinicalTrials.gov API v2."""
import json
import logging
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import HTTPException
from tenacity import (
    AsyncRetrying,
    RetryError,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from backend.app.models.trial import EligibilityCriteria, TrialData

_log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

_BASE_URL  = "https://clinicaltrials.gov/api/v2/studies"
_WARMUP_URL = "https://clinicaltrials.gov/"
_TIMEOUT   = 30.0
_CACHE_TTL = 600  # 10 minutes

# ── User-Agent pool ─────────────────────────────────────────────────────────────
_USER_AGENTS: list[dict[str, str]] = [
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "ch_ua": '"Chromium";v="124","Google Chrome";v="124","Not-A.Brand";v="99"',
        "ch_platform": '"Windows"',
        "ch_mobile": "?0",
    },
    {
        "ua": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "ch_ua": '"Chromium";v="123","Google Chrome";v="123","Not-A.Brand";v="99"',
        "ch_platform": '"macOS"',
        "ch_mobile": "?0",
    },
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
            "Gecko/20100101 Firefox/125.0"
        ),
        "ch_ua": None,   # Firefox does not send Sec-Ch-Ua
        "ch_platform": None,
        "ch_mobile": None,
    },
    {
        "ua": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.4.1 Safari/605.1.15"
        ),
        "ch_ua": None,   # Safari does not send Sec-Ch-Ua
        "ch_platform": None,
        "ch_mobile": None,
    },
]

# Realistic referers — cycling through search/browse pages looks more human
_REFERERS = [
    "https://clinicaltrials.gov/",
    "https://clinicaltrials.gov/search?term=lung+cancer&recrs=a",
    "https://clinicaltrials.gov/search?cond=Non-small+cell+lung+cancer&term=EGFR",
    "https://clinicaltrials.gov/search?term=osimertinib&recrs=b",
    "https://clinicaltrials.gov/search?cond=cancer&age_v=18%2B&phase=2",
]


def _make_headers() -> dict[str, str]:
    """Build a full nuclear browser header suite for one request attempt."""
    profile = random.choice(_USER_AGENTS)
    referer  = random.choice(_REFERERS)

    headers: dict[str, str] = {
        "User-Agent":      profile["ua"],
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control":   "no-cache",
        "Pragma":          "no-cache",
        "Connection":      "keep-alive",
        "DNT":             "1",
        "Referer":         referer,
        "Origin":          "https://clinicaltrials.gov",
        "Sec-Fetch-Dest":  "empty",
        "Sec-Fetch-Mode":  "cors",
        "Sec-Fetch-Site":  "same-origin",
    }

    # Chrome client-hints — only genuine Chrome sends these;
    # sending them with a Firefox UA would be a contradiction.
    if profile["ch_ua"] is not None:
        headers["Sec-Ch-Ua"]          = profile["ch_ua"]
        headers["Sec-Ch-Ua-Mobile"]   = profile["ch_mobile"]
        headers["Sec-Ch-Ua-Platform"] = profile["ch_platform"]

    _log.debug(
        "Headers built — UA=…%s  Referer=%s",
        profile["ua"][-35:], referer,
    )
    return headers


# ── In-memory TTL cache ─────────────────────────────────────────────────────────
@dataclass
class _CacheEntry:
    data: TrialData
    expires_at: float  # monotonic timestamp


class _TTLCache:
    def __init__(self, ttl: int = _CACHE_TTL) -> None:
        self._store: dict[str, _CacheEntry] = {}
        self._ttl = ttl

    def get(self, key: str) -> TrialData | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[key]
            _log.info("Cache EXPIRED — %s", key)
            return None
        remaining = int(entry.expires_at - time.monotonic())
        _log.info("Cache HIT — %s  (%d s remaining)", key, remaining)
        return entry.data

    def set(self, key: str, value: TrialData) -> None:
        self._store[key] = _CacheEntry(
            data=value,
            expires_at=time.monotonic() + self._ttl,
        )
        _log.info("Cache SET — %s  (TTL %d s)", key, self._ttl)


_cache = _TTLCache()


# ── Retry sentinel ──────────────────────────────────────────────────────────────
class _RetryableError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__(f"Retryable HTTP {status}")


# ── Graceful fallback for demo resilience ───────────────────────────────────────
# Embedded minimal data for NCT04280706 — used only when the live API is
# unreachable after all retries, so a live demo never crashes on a 403.
_FALLBACK_TRIALS: dict[str, TrialData] = {
    "NCT04280706": TrialData(
        nct_id="NCT04280706",
        title=(
            "Osimertinib With or Without Bevacizumab in Treating Patients With "
            "EGFR-Mutant Non-Small Cell Lung Cancer and Brain Metastases"
        ),
        conditions=["Non-Small Cell Lung Cancer", "Brain Metastases"],
        eligibility=EligibilityCriteria(
            inclusion=[
                "Histologically or cytologically confirmed non-small cell lung cancer",
                "EGFR sensitizing mutation confirmed: exon 19 deletion or exon 21 L858R substitution",
                "Age >= 18 years at the time of study entry",
                "ECOG Performance Status 0, 1, or 2",
                "At least one measurable lesion per RECIST v1.1",
                "Adequate bone marrow: ANC >= 1.5 × 10⁹/L; Platelets >= 100 × 10⁹/L",
                "Adequate renal function: eGFR >= 45 mL/min/1.73 m²",
                "Adequate hepatic function: ALT and AST <= 2.5 × ULN; total bilirubin <= 1.5 × ULN",
                "No prior exposure to osimertinib or any third-generation EGFR TKI",
            ],
            exclusion=[
                "Prior treatment with any third-generation EGFR inhibitor (e.g., osimertinib, rociletinib, nazartinib)",
                "Active autoimmune disease requiring systemic treatment within the past 2 years",
                "Uncontrolled or symptomatic brain metastases requiring urgent radiation or steroids",
                "QTc interval > 470 ms (females) or > 450 ms (males) on screening ECG",
                "Pregnancy or active breastfeeding",
                "Active systemic infection requiring IV antibiotics",
                "History of interstitial lung disease or drug-induced interstitial lung disease",
            ],
        ),
        status="RECRUITING",
        phase="PHASE2",
    ),
}


# ── JSON-file fallback loader ───────────────────────────────────────────────────
_MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock_trials.json"


def _load_json_fallback(nct_id: str) -> TrialData | None:
    """Load a trial from data/mock_trials.json if the live API is unavailable."""
    try:
        raw = json.loads(_MOCK_PATH.read_text(encoding="utf-8"))
        entry = raw.get(nct_id)
        if entry is None:
            return None
        return TrialData(
            nct_id=entry["nct_id"],
            title=entry["title"],
            conditions=entry.get("conditions", []),
            eligibility=EligibilityCriteria(
                inclusion=entry["eligibility"]["inclusion"],
                exclusion=entry["eligibility"]["exclusion"],
            ),
            status=entry.get("status"),
            phase=entry.get("phase"),
        )
    except Exception as exc:
        _log.warning("Could not load mock_trials.json: %s", exc)
        return None


# ── Parse helpers ───────────────────────────────────────────────────────────────
def _parse_eligibility(raw_text: str) -> EligibilityCriteria:
    inclusion: list[str] = []
    exclusion: list[str] = []

    if not raw_text:
        return EligibilityCriteria(inclusion=inclusion, exclusion=exclusion)

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    inc_marker, exc_marker = "Inclusion Criteria:", "Exclusion Criteria:"
    inc_start = text.find(inc_marker)
    exc_start = text.find(exc_marker)

    if inc_start != -1:
        inclusion = _extract_bullets(
            text[inc_start + len(inc_marker): exc_start if exc_start != -1 else None]
        )
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


def _parse_trial(data: dict, nct_id: str) -> TrialData:
    protocol = data.get("protocolSection", {})
    title      = protocol.get("identificationModule", {}).get("briefTitle", "")
    conditions = protocol.get("conditionsModule",    {}).get("conditions", [])
    status     = protocol.get("statusModule",        {}).get("overallStatus")
    phases     = protocol.get("designModule",        {}).get("phases", [])
    phase      = phases[0] if phases else None
    raw        = protocol.get("eligibilityModule",   {}).get("eligibilityCriteria", "")
    return TrialData(
        nct_id=nct_id,
        title=title,
        conditions=conditions,
        eligibility=_parse_eligibility(raw),
        status=status,
        phase=phase,
    )


# ── Session-persistent fetch with jittered retry ────────────────────────────────
async def _fetch_with_session(url: str) -> dict:
    """
    Open a single httpx session for the full retry cycle so cookies acquired
    during the warm-up GET persist across all retry attempts.

    Retry policy: exponential back-off 2 → 4 → 8 s PLUS uniform jitter
    [1.5, 3.0] s — human-like cadence that avoids synchronised retry storms.
    """
    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Referer": "https://clinicaltrials.gov/",
            "Origin": "https://clinicaltrials.gov",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Ch-Ua": '"Chromium";v="124","Google Chrome";v="124","Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Cookie": "cookieconsent_status=dismiss; _ga=GA1.1.000000001.1700000000",
        },
    ) as client:
        last_status = 0
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(_RetryableError),
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=2, min=2, max=8) + wait_random(1.5, 3.0),
            before_sleep=before_sleep_log(_log, logging.WARNING),
            reraise=True,
        ):
            with attempt:
                headers = _make_headers()
                _log.info(
                    "Attempt %d → GET %s  UA=…%s",
                    attempt.retry_state.attempt_number,
                    url,
                    headers["User-Agent"][-35:],
                )

                try:
                    response = await client.get(url, headers=headers)
                except httpx.RequestError as exc:
                    _log.warning("Network error on attempt %d: %s", attempt.retry_state.attempt_number, exc)
                    raise _RetryableError(0) from exc

                last_status = response.status_code
                _log.info("HTTP %d on attempt %d", last_status, attempt.retry_state.attempt_number)

                if last_status == 200:
                    return response.json()

                if last_status == 404:
                    raise HTTPException(status_code=404, detail=f"Trial not found: {url}")

                if last_status in {403, 429, 500, 502, 503}:
                    raise _RetryableError(last_status)

                raise HTTPException(
                    status_code=502,
                    detail=f"ClinicalTrials.gov returned unexpected HTTP {last_status}.",
                )

    # Unreachable — AsyncRetrying either returns or raises RetryError
    raise HTTPException(status_code=503, detail="Fetch loop exited without result.")  # pragma: no cover


# ── Public API ──────────────────────────────────────────────────────────────────
async def fetch_trial(nct_id: str) -> TrialData:
    """
    Return TrialData for the given NCT ID.

    Resolution order:
      1. TTL cache        — no network call if a fresh entry exists (10-min window).
      2. mock_trials.json — local file checked before any network activity.
      3. Embedded dict    — in-process fallback for known demo IDs.
      4. Live fetch       — session-persistent httpx client with browser headers
                            and jittered exponential back-off (4 attempts total).

    Raises HTTP 404 for unknown trials after all sources are exhausted.
    """
    nct_id = nct_id.strip().upper()

    # 1 — TTL cache
    cached = _cache.get(nct_id)
    if cached is not None:
        return cached

    # 2 — JSON file (checked BEFORE any network call)
    json_fallback = _load_json_fallback(nct_id)
    if json_fallback is not None:
        _log.info("[LOCAL] Serving %s from mock_trials.json — no network call made.", nct_id)
        _cache.set(nct_id, json_fallback)
        return json_fallback

    # 3 — Embedded Python dict
    embedded = _FALLBACK_TRIALS.get(nct_id)
    if embedded is not None:
        _log.info("[LOCAL] Serving %s from embedded fallback dict — no network call made.", nct_id)
        _cache.set(nct_id, embedded)
        return embedded

    # 4 — Live fetch
    url = f"{_BASE_URL}/{nct_id}"
    last_retryable_status = 0

    try:
        raw = await _fetch_with_session(url)
    except HTTPException:
        raise  # 404 / 502 — propagate directly
    except RetryError as exc:
        cause = exc.last_attempt.exception()
        if isinstance(cause, _RetryableError):
            last_retryable_status = cause.status
        _log.error(
            "All retry attempts exhausted for %s (last HTTP %d)",
            nct_id, last_retryable_status,
        )
        raise HTTPException(
            status_code=404,
            detail=(
                f"Trial {nct_id} not found in local cache and API is currently rate-limited."
            ),
        )

    trial = _parse_trial(raw, nct_id)
    _cache.set(nct_id, trial)
    _log.info("Fetched and cached %s — '%s'", nct_id, trial.title[:60])
    return trial
