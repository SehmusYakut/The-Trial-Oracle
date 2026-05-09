"""Service for calling the MBZUAI K2-Think-v2 model to match patients against trials."""
import os
import re

import httpx
from fastapi import HTTPException

from backend.app.models.patient import (
    CriterionVerdict,
    MatchResult,
    PatientData,
)
from backend.app.models.trial import TrialData

_K2_ENDPOINT = "https://api.k2think.ai/v1/chat/completions"
_K2_MODEL = "MBZUAI-IFM/K2-Think-v2"
_TIMEOUT = 120.0  # K2 produces long reasoning chains; 60 s minimum per project rules

_SYSTEM_PROMPT = """You are a Senior Clinical Trial Auditor with deep expertise in oncology, internal medicine, and regulatory affairs. Your sole task is to determine whether a specific patient is eligible for a specific clinical trial.

You MUST follow this exact reasoning protocol — do not skip any step:

STEP 1 — LABEL EVERY CRITERION
  • Assign each inclusion criterion a unique ID: INC-1, INC-2, INC-3 …
  • Assign each exclusion criterion a unique ID: EXC-1, EXC-2, EXC-3 …

STEP 2 — AUDIT EACH CRITERION INDIVIDUALLY
  For every criterion ID, output a block in this format:
    [ID] CRITERION: <full criterion text>
    [ID] PATIENT EVIDENCE: <exact patient field(s) and value(s) you are using>
    [ID] VERDICT: MET | NOT_MET | UNCERTAIN
    [ID] REASONING: <one or two sentences explaining the verdict>

  Rules for verdicts:
  • MET     — patient data clearly satisfies the criterion.
  • NOT_MET — patient data clearly violates the criterion.
  • UNCERTAIN — required data is absent or ambiguous; you must explicitly state what is missing.
  Never infer, guess, or hallucinate patient data. If a value is not present in the Patient JSON, mark UNCERTAIN and name the missing field.

STEP 3 — DISQUALIFICATION CHECK
  List every EXC-* criterion the patient does NOT meet (i.e., the exclusion applies).
  If any exclusion criterion is NOT_MET, the patient is INELIGIBLE regardless of inclusion results.

STEP 4 — OVERALL VERDICT
  State one of: ELIGIBLE | INELIGIBLE | UNCERTAIN
  • ELIGIBLE   — all inclusion criteria are MET and no exclusion criteria are NOT_MET.
  • INELIGIBLE — at least one inclusion criterion is NOT_MET, or at least one exclusion criterion is NOT_MET.
  • UNCERTAIN  — no hard disqualifiers, but one or more criteria are UNCERTAIN.

STEP 5 — CONFIDENCE & SUMMARY
  State confidence: HIGH | MEDIUM | LOW
  Write a 2–4 sentence plain-language summary for a clinical coordinator.

BEGIN your response with "## STEP 1" and end with "## STEP 5". Do not add any text outside this structure.

STRICT PROHIBITION: You must NOT provide treatment recommendations, drug dosages, clinical advice, prognoses, or any guidance that could be construed as practising medicine. Your output is a regulatory eligibility audit, not medical advice. If asked anything beyond criterion matching, respond only with "Outside scope of eligibility audit." """


def _build_user_message(patient: PatientData, trial: TrialData) -> str:
    """Render the user turn that contains both data payloads."""
    inclusion_numbered = "\n".join(
        f"  INC-{i + 1}: {c}" for i, c in enumerate(trial.eligibility.inclusion)
    )
    exclusion_numbered = "\n".join(
        f"  EXC-{i + 1}: {c}" for i, c in enumerate(trial.eligibility.exclusion)
    )

    return f"""Please audit the following patient against the clinical trial below.

## PATIENT JSON
{patient.model_dump_json(indent=2)}

## TRIAL
NCT ID   : {trial.nct_id}
Title    : {trial.title}
Status   : {trial.status or 'Unknown'}
Phase    : {trial.phase or 'Unknown'}
Conditions: {', '.join(trial.conditions) or 'Not specified'}

### Inclusion Criteria
{inclusion_numbered or '  (none listed)'}

### Exclusion Criteria
{exclusion_numbered or '  (none listed)'}

Follow the five-step protocol from your system instructions exactly."""


def _parse_overall_eligibility(text: str) -> str:
    for token in ("INELIGIBLE", "ELIGIBLE", "UNCERTAIN"):
        if token in text:
            return token
    return "UNCERTAIN"


def _parse_confidence(text: str) -> str:
    for token in ("HIGH", "MEDIUM", "LOW"):
        if re.search(rf"\bconfidence[:\s]+{token}\b", text, re.IGNORECASE):
            return token
    for token in ("HIGH", "MEDIUM", "LOW"):
        if token in text:
            return token
    return "LOW"


def _parse_criteria_verdicts(
    raw: str,
    inclusion: list[str],
    exclusion: list[str],
) -> tuple[list[CriterionVerdict], list[str]]:
    """Extract per-criterion blocks from the K2 response text."""
    verdicts: list[CriterionVerdict] = []
    disqualifying: list[str] = []

    # Build lookup: criterion_id → text
    criteria_map: dict[str, str] = {}
    for i, text in enumerate(inclusion):
        criteria_map[f"INC-{i + 1}"] = text
    for i, text in enumerate(exclusion):
        criteria_map[f"EXC-{i + 1}"] = text

    # Regex: capture each [ID] VERDICT block
    pattern = re.compile(
        r"\[(?P<id>(?:INC|EXC)-\d+)\]\s+VERDICT:\s*(?P<verdict>MET|NOT_MET|UNCERTAIN)",
        re.IGNORECASE,
    )
    evidence_pattern = re.compile(
        r"\[(?P<id>(?:INC|EXC)-\d+)\]\s+PATIENT EVIDENCE:\s*(?P<evidence>[^\n]+)",
        re.IGNORECASE,
    )
    reasoning_pattern = re.compile(
        r"\[(?P<id>(?:INC|EXC)-\d+)\]\s+REASONING:\s*(?P<reasoning>[^\n]+)",
        re.IGNORECASE,
    )

    evidence_map = {m.group("id").upper(): m.group("evidence").strip() for m in evidence_pattern.finditer(raw)}
    reasoning_map = {m.group("id").upper(): m.group("reasoning").strip() for m in reasoning_pattern.finditer(raw)}

    seen: set[str] = set()
    for match in pattern.finditer(raw):
        cid = match.group("id").upper()
        if cid in seen:
            continue
        seen.add(cid)

        raw_verdict = match.group("verdict").upper()
        criterion_text = criteria_map.get(cid, "")

        verdicts.append(
            CriterionVerdict(
                criterion_id=cid,
                criterion_text=criterion_text,
                verdict=raw_verdict,
                reasoning=reasoning_map.get(cid, ""),
                patient_evidence=evidence_map.get(cid, ""),
            )
        )

        # An exclusion that is NOT_MET means the patient triggers the exclusion
        if cid.startswith("EXC") and raw_verdict == "NOT_MET":
            disqualifying.append(cid)

    return verdicts, disqualifying


def _extract_summary(raw: str) -> str:
    """Pull the Step 5 summary block; fall back to the last paragraph."""
    match = re.search(r"##\s*STEP 5.*?(?:\n\n|$)(.*?)(?=##|\Z)", raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    return paragraphs[-1] if paragraphs else raw[:500]


async def match_patient_to_trial(patient: PatientData, trial: TrialData) -> MatchResult:
    """Send patient + trial data to K2-Think-v2 and return a structured MatchResult."""
    api_key = os.getenv("K2_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="K2_API_KEY is not configured.")

    payload = {
        "model": _K2_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(patient, trial)},
        ],
        "temperature": 0.1,  # low temperature for deterministic clinical reasoning
        "max_tokens": 4096,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            response = await client.post(_K2_ENDPOINT, json=payload, headers=headers)
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="K2 API timed out. The model may be producing a long reasoning chain — try again.",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"K2 API unreachable: {exc}",
            )

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="K2 API rejected the Bearer token. Check K2_API_KEY.")
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="K2 API rate limit exceeded. Please retry shortly.")
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"K2 API returned HTTP {response.status_code}: {response.text[:300]}",
        )

    try:
        body = response.json()
        raw_reasoning = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected K2 API response shape: {exc}",
        )

    overall = _parse_overall_eligibility(raw_reasoning)
    confidence = _parse_confidence(raw_reasoning)
    criteria_verdicts, disqualifying = _parse_criteria_verdicts(
        raw_reasoning,
        trial.eligibility.inclusion,
        trial.eligibility.exclusion,
    )
    summary = _extract_summary(raw_reasoning)

    return MatchResult(
        nct_id=trial.nct_id,
        overall_eligibility=overall,
        confidence=confidence,
        summary=summary,
        criteria_verdicts=criteria_verdicts,
        disqualifying_criteria=disqualifying,
        raw_reasoning=raw_reasoning,
    )
