"""Service for calling the MBZUAI K2-Think-v2 model to match patients against trials."""
import json
import logging
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

_log = logging.getLogger(__name__)

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

_AUDIT_SYSTEM_PROMPT = """You are a Skeptical Clinical Trial Auditor — a Devil's Advocate whose sole purpose is to challenge eligibility decisions.

You will be given a patient profile, trial criteria, and the verdict from a primary eligibility audit. Your task is to find the single strongest reason this patient might NOT be eligible, even if the primary verdict was ELIGIBLE.

Search aggressively for:
1. Ambiguous inclusion criteria that could be interpreted against the patient under strict reading
2. Borderline lab values or biomarkers that might fail under rigorous clinical review
3. Prior therapies that may implicitly conflict with inclusion or exclusion requirements
4. Missing patient data whose absence, if filled, would likely disqualify the patient
5. Edge cases in exclusion criteria that the primary audit did not fully explore

Respond using this EXACT format — no other text before or after:

AUDIT VERDICT: CONFLICT_FOUND | HIGH_INTEGRITY_MATCH
CRITERION CHALLENGED: <criterion ID (e.g. EXC-2) and full criterion text, or "None">
CHALLENGE: <One specific, evidence-based argument for why this patient might be disqualified. Reference exact patient data values. Be precise and clinically rigorous. Maximum 4 sentences. If HIGH_INTEGRITY_MATCH, write exactly: No exploitable conflict identified after exhaustive review.>
AUDITOR CONFIDENCE: HIGH | MEDIUM | LOW

Rules:
- HIGH_INTEGRITY_MATCH means you genuinely cannot find a plausible disqualifier after careful review.
- CONFLICT_FOUND must cite a specific criterion ID and specific patient data — no vague concerns.
- You must NOT fabricate patient data. You may flag missing data as a potential concern.
- Never provide medical advice or treatment recommendations.
- Begin your response with "AUDIT VERDICT:" — do not add preamble."""


def _build_audit_message(
    patient: PatientData,
    trial: TrialData,
    pass1_verdict: str,
    pass1_summary: str,
) -> str:
    """Render the user turn for Pass 2 — Devil's Advocate audit."""
    inclusion_numbered = "\n".join(
        f"  INC-{i + 1}: {c}" for i, c in enumerate(trial.eligibility.inclusion)
    )
    exclusion_numbered = "\n".join(
        f"  EXC-{i + 1}: {c}" for i, c in enumerate(trial.eligibility.exclusion)
    )
    return f"""You are auditing the following eligibility decision. Find the strongest potential disqualifier.

## PRIMARY AUDIT RESULT
Overall Verdict : {pass1_verdict}
Primary Summary : {pass1_summary}

## PATIENT JSON
{patient.model_dump_json(indent=2)}

## TRIAL
NCT ID   : {trial.nct_id}
Title    : {trial.title}

### Inclusion Criteria
{inclusion_numbered or '  (none listed)'}

### Exclusion Criteria
{exclusion_numbered or '  (none listed)'}

Now perform your Devil's Advocate audit. Follow the required format exactly."""


def _parse_audit_response(text: str) -> tuple[str, str, str, str]:
    """Return (verdict, criterion_challenged, challenge, confidence) from Pass 2 output."""
    verdict = "HIGH_INTEGRITY_MATCH"
    if re.search(r"AUDIT VERDICT:\s*CONFLICT_FOUND", text, re.IGNORECASE):
        verdict = "CONFLICT_FOUND"

    criterion = ""
    m = re.search(r"CRITERION CHALLENGED:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    if m:
        criterion = m.group(1).strip()

    challenge = ""
    m = re.search(
        r"CHALLENGE:\s*(.+?)(?=AUDITOR CONFIDENCE|$)", text, re.IGNORECASE | re.DOTALL
    )
    if m:
        challenge = m.group(1).strip()

    confidence = "MEDIUM"
    for c in ("HIGH", "MEDIUM", "LOW"):
        if re.search(rf"AUDITOR CONFIDENCE:\s*{c}", text, re.IGNORECASE):
            confidence = c
            break

    return verdict, criterion, challenge, confidence


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


async def _collect_sse_stream(response: httpx.Response) -> str:
    """
    Consume a Server-Sent Events stream from K2 and return the full text.

    Each SSE line has the form:
        data: {"choices":[{"delta":{"content":"..."}}]}
    The final sentinel is:
        data: [DONE]
    """
    chunks: list[str] = []
    async for line in response.aiter_lines():
        if not line.startswith("data: "):
            continue
        sse_data = line[6:].strip()
        if sse_data == "[DONE]":
            break
        try:
            obj = json.loads(sse_data)
            content = obj["choices"][0]["delta"].get("content", "")
            if content:
                chunks.append(content)
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
    return "".join(chunks)


async def _call_k2(
    messages: list,
    headers: dict,
    timeout: httpx.Timeout,
    max_tokens: int = 4096,
    temperature: float = 0.1,
) -> str:
    """Make one streaming call to K2 and return the concatenated response text."""
    payload = {
        "model": _K2_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST", _K2_ENDPOINT, json=payload, headers=headers
            ) as response:
                if response.status_code == 401:
                    raise HTTPException(401, "K2 API rejected the Bearer token. Check K2_API_KEY.")
                if response.status_code == 429:
                    raise HTTPException(429, "K2 API rate limit exceeded. Please retry shortly.")
                if response.status_code != 200:
                    body = await response.aread()
                    raise HTTPException(
                        502, f"K2 API returned HTTP {response.status_code}: {body[:300]}"
                    )
                return await _collect_sse_stream(response)
    except httpx.TimeoutException:
        raise HTTPException(504, "K2 API timed out.")
    except httpx.RequestError as exc:
        raise HTTPException(503, f"K2 API unreachable: {exc}")


async def match_patient_to_trial(patient: PatientData, trial: TrialData) -> MatchResult:
    """
    Dual-pass K2 reasoning:
      Pass 1 — Primary Eligibility Audit (structured 5-step protocol)
      Pass 2 — Devil's Advocate Safety Audit (skeptical auditor seeks disqualifiers)
    Pass 2 failure is non-fatal; the result is returned with audit fields set to None.
    """
    api_key = os.getenv("K2_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="K2_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(connect=10.0, read=_TIMEOUT, write=10.0, pool=5.0)

    # ── Pass 1: Primary Eligibility Audit ─────────────────────────────────────
    raw_reasoning = await _call_k2(
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(patient, trial)},
        ],
        headers=headers,
        timeout=timeout,
        max_tokens=4096,
        temperature=0.1,
    )

    if not raw_reasoning:
        raise HTTPException(
            status_code=502,
            detail="K2 returned an empty response. The stream may have closed prematurely.",
        )

    overall = _parse_overall_eligibility(raw_reasoning)
    confidence = _parse_confidence(raw_reasoning)
    criteria_verdicts, disqualifying = _parse_criteria_verdicts(
        raw_reasoning,
        trial.eligibility.inclusion,
        trial.eligibility.exclusion,
    )
    summary = _extract_summary(raw_reasoning)
    _log.info("Pass 1 complete — %s  confidence=%s", overall, confidence)

    # ── Pass 2: Devil's Advocate Safety Audit ─────────────────────────────────
    audit_verdict = audit_criterion = audit_challenge = audit_confidence = audit_raw = None
    try:
        audit_raw = await _call_k2(
            messages=[
                {"role": "system", "content": _AUDIT_SYSTEM_PROMPT},
                {"role": "user", "content": _build_audit_message(patient, trial, overall, summary)},
            ],
            headers=headers,
            timeout=timeout,
            max_tokens=1024,
            temperature=0.3,
        )
        audit_verdict, audit_criterion, audit_challenge, audit_confidence = _parse_audit_response(
            audit_raw
        )
        _log.info("Pass 2 (Safety Audit) complete — %s", audit_verdict)
    except Exception as exc:
        _log.warning("Pass 2 (Devil's Advocate) failed — skipping: %s", exc)

    return MatchResult(
        nct_id=trial.nct_id,
        overall_eligibility=overall,
        confidence=confidence,
        summary=summary,
        criteria_verdicts=criteria_verdicts,
        disqualifying_criteria=disqualifying,
        raw_reasoning=raw_reasoning,
        audit_verdict=audit_verdict,
        audit_criterion=audit_criterion,
        audit_challenge=audit_challenge,
        audit_confidence=audit_confidence,
        audit_raw=audit_raw,
    )
