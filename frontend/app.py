"""Streamlit frontend for The Trial Oracle — Clinical Reasoning Engine."""
import json
import os
import re
import time

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="The Trial Oracle",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""<style>
html,body,[class*="css"]{font-family:'Inter','Segoe UI',system-ui,sans-serif;font-size:14px}
#MainMenu,footer,header{visibility:hidden}
.stApp{background-color:#F1F5F9}
[data-testid="stSidebar"]{background-color:#0B1929!important}
[data-testid="stSidebar"] *{color:#CBD5E1!important}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong{color:#F1F5F9!important}
[data-testid="stSidebar"] hr{border-color:#1E3A5F!important}
[data-testid="stSidebar"] code{background:#1E3A5F!important;color:#7DD3FC!important;border-radius:4px;padding:2px 6px}
.lab-header{background:linear-gradient(120deg,#0B1929 0%,#1E3A5F 60%,#0D4F8C 100%);border-radius:12px;padding:30px 40px;margin-bottom:24px;border:1px solid #1E3A5F}
.lab-header h1{color:#F8FAFC!important;font-size:1.9rem;font-weight:700;margin:0 0 6px 0}
.lab-header .subtitle{color:#94A3B8!important;font-size:.92rem;margin:0}
.badge-row{margin-top:14px;display:flex;gap:8px;flex-wrap:wrap}
.badge{display:inline-block;padding:3px 10px;border-radius:4px;font-size:.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.badge-k2{background:rgba(5,150,105,.2);color:#6EE7B7;border:1px solid rgba(5,150,105,.3)}
.badge-api{background:rgba(59,130,246,.2);color:#93C5FD;border:1px solid rgba(59,130,246,.3)}
.badge-v{background:rgba(139,92,246,.2);color:#C4B5FD;border:1px solid rgba(139,92,246,.3)}
.section-label{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748B;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #E2E8F0}
.field-hint{font-size:.72rem;color:#94A3B8;margin-top:-4px;margin-bottom:8px;font-style:italic}
.trial-card{background:#FFF;border:1px solid #CBD5E1;border-left:4px solid #0D4F8C;border-radius:8px;padding:16px 20px;margin-bottom:16px}
.trial-nct{font-family:monospace;font-size:.8rem;color:#0D4F8C;font-weight:700}
.trial-title{font-size:.97rem;font-weight:600;color:#0F172A;margin:4px 0 6px 0;line-height:1.4}
.verdict-panel{background:#FFF;border:1px solid #CBD5E1;border-radius:10px;padding:20px 24px}
.verdict-label{font-size:.68rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:8px}
.vbadge{display:inline-block;padding:7px 20px;border-radius:6px;font-size:.88rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase}
.vbadge-eligible{background:#ECFDF5;color:#065F46;border:1.5px solid #6EE7B7}
.vbadge-ineligible{background:#FEF2F2;color:#7F1D1D;border:1.5px solid #FCA5A5}
.vbadge-uncertain{background:#FFFBEB;color:#78350F;border:1.5px solid #FDE68A}
.score-ring{font-size:2.6rem;font-weight:800;line-height:1;text-align:center}
.score-sub{font-size:.7rem;color:#64748B;text-align:center;margin-top:4px;text-transform:uppercase}
.cpill{display:inline-block;padding:3px 12px;border-radius:4px;font-size:.73rem;font-weight:600;text-transform:uppercase}
.cpill-high{background:#EFF6FF;color:#1E40AF;border:1px solid #BFDBFE}
.cpill-medium{background:#FFFBEB;color:#92400E;border:1px solid #FDE68A}
.cpill-low{background:#FEF2F2;color:#991B1B;border:1px solid #FECACA}
.kw-eligible{background:#ECFDF5;color:#065F46;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.85em}
.kw-ineligible{background:#FEF2F2;color:#7F1D1D;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.85em}
.kw-uncertain{background:#FFFBEB;color:#78350F;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.85em}
.kw-conflict{background:#FEF2F2;color:#7F1D1D;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.85em}
.evidence-box{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:8px 12px;font-size:.82rem;color:#334155;margin:6px 0;font-family:monospace}
.summary-box{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:16px 20px;font-size:.9rem;color:#1E293B;line-height:1.65}
.patient-table{width:100%;border-collapse:collapse;font-size:.84rem}
.patient-table th{background:#F1F5F9;color:#475569;font-size:.7rem;font-weight:700;text-transform:uppercase;padding:7px 12px;text-align:left;border-bottom:1px solid #CBD5E1}
.patient-table td{padding:8px 12px;color:#1E293B;border-bottom:1px solid #F1F5F9;vertical-align:top}
.patient-table tr:last-child td{border-bottom:none}
.pt-key{font-weight:600;color:#334155;width:38%}
.sci-footer{margin-top:32px;padding:16px 20px;background:#0B1929;border-radius:8px;font-size:.78rem;color:#64748B;line-height:1.6}
.sci-footer strong{color:#94A3B8}
div[data-testid="stFormSubmitButton"]>button{border-radius:6px!important;font-weight:700!important}
</style>""", unsafe_allow_html=True)

# ── Sample data ────────────────────────────────────────────────────────────────
_SAMPLE = {
    "pf_age": 58,
    "pf_sex": "female",
    "pf_ecog_ps": "1",
    "pf_diagnoses": "Non-small cell lung cancer, stage IIIB\nHypertension",
    "pf_biomarkers": "EGFR: exon19del\nPD-L1: 45%\neGFR: 72\nALT: 28\nAST: 31",
    "pf_medications": "Amlodipine 5 mg\nAspirin 81 mg",
    "pf_history": "Never-smoker\nNo prior thoracic surgery\nNo history of autoimmune disease",
    "pf_prior_therapies": "Carboplatin/Paclitaxel x4 cycles (2022)",
    "pf_notes": "Patient is ambulatory and capable of all self-care. No active infections.",
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _lines(text: str) -> list:
    return [ln.strip() for ln in (text or "").strip().splitlines() if ln.strip()]


def _parse_kv(text: str) -> dict:
    result: dict = {}
    for line in _lines(text):
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if not k:
            continue
        try:
            result[k] = int(v)
        except ValueError:
            try:
                result[k] = float(v)
            except ValueError:
                result[k] = v
    return result


def _build_patient_dict() -> dict:
    ecog_raw = st.session_state.get("pf_ecog_ps", "Not specified")
    ecog_val = None if ecog_raw == "Not specified" else int(ecog_raw)
    return {
        "age":             int(st.session_state.get("pf_age", 0)),
        "sex":             st.session_state.get("pf_sex", "male"),
        "diagnoses":       _lines(st.session_state.get("pf_diagnoses", "")),
        "biomarkers":      _parse_kv(st.session_state.get("pf_biomarkers", "")),
        "medications":     _lines(st.session_state.get("pf_medications", "")),
        "history":         _lines(st.session_state.get("pf_history", "")),
        "ecog_ps":         ecog_val,
        "prior_therapies": _lines(st.session_state.get("pf_prior_therapies", "")),
        "notes":           st.session_state.get("pf_notes", "").strip() or None,
    }


def _patient_as_html_table(p: dict) -> str:
    def _fmt(v):
        if isinstance(v, list):
            return "<br>".join(f"• {i}" for i in v) if v else "<em>None listed</em>"
        if isinstance(v, dict):
            return "<br>".join(f"<code>{k}</code>: {val}" for k, val in v.items()) if v else "<em>None</em>"
        return str(v) if v is not None else "—"

    labels = {
        "age": "Age", "sex": "Sex", "ecog_ps": "ECOG PS",
        "diagnoses": "Diagnoses", "biomarkers": "Biomarkers",
        "medications": "Medications", "history": "Medical History",
        "prior_therapies": "Prior Therapies", "notes": "Clinical Notes",
    }
    rows = "".join(
        f'<tr><td class="pt-key">{lbl}</td><td>{_fmt(p.get(k))}</td></tr>'
        for k, lbl in labels.items()
        if k in p and p.get(k) not in (None, [], {}, "")
    )
    return (
        '<table class="patient-table">'
        "<thead><tr><th>Field</th><th>Value</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _highlight_keywords(text: str) -> str:
    rules = [
        (r"\b(ELIGIBLE|MET)\b",                    "kw-eligible"),
        (r"\b(INELIGIBLE|NOT MET)\b",              "kw-ineligible"),
        (r"\b(UNCERTAIN|MISSING|ABSENT)\b",        "kw-uncertain"),
        (r"\b(CONFLICT|DISQUALIF\w*|EXCLUDED?)\b", "kw-conflict"),
    ]
    for pattern, cls in rules:
        text = re.sub(
            pattern,
            lambda m, c=cls: f'<span class="{c}">{m.group()}</span>',
            text, flags=re.IGNORECASE,
        )
    return text


def _score_color(s: float) -> str:
    return "#059669" if s >= 0.75 else "#D97706" if s >= 0.40 else "#DC2626"


def _verdict_badge(label: str) -> str:
    cls  = {"ELIGIBLE": "vbadge-eligible", "INELIGIBLE": "vbadge-ineligible", "UNCERTAIN": "vbadge-uncertain"}.get(label, "vbadge-uncertain")
    icon = {"ELIGIBLE": "✔ ELIGIBLE", "INELIGIBLE": "✘ INELIGIBLE", "UNCERTAIN": "⚬ UNCERTAIN"}.get(label, label)
    return f'<span class="vbadge {cls}">{icon}</span>'


def _conf_pill(conf: str) -> str:
    return f'<span class="cpill cpill-{conf.lower()}">{conf} confidence</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚕ Trial Oracle")
    st.markdown("---")
    st.markdown("**Configuration**")
    backend_url = st.text_input(
        "Backend URL",
        value=os.getenv("BACKEND_URL", "http://localhost:8000"),
        help="FastAPI backend URL",
    )
    st.markdown("---")
    st.markdown("**Engine**")
    st.code("MBZUAI-IFM/K2-Think-v2", language=None)
    st.markdown("**Data Source**")
    st.code("ClinicalTrials.gov API v2", language=None)
    st.markdown("---")
    st.markdown("**Sample NCT IDs**")
    for nct, lbl in [
        ("NCT04280706", "Lung cancer / EGFR"),
        ("NCT03661788", "Breast cancer"),
        ("NCT04158791", "COVID-19"),
    ]:
        st.markdown(f"`{nct}` — {lbl}")
    st.markdown("---")
    st.caption("Build with K2 Think V2 Hackathon · 2025")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lab-header">
    <h1>⚕ The Trial Oracle</h1>
    <p class="subtitle">Clinical Reasoning Engine · Automated Eligibility Matching</p>
    <div class="badge-row">
        <span class="badge badge-k2">Powered by K2-Think-v2</span>
        <span class="badge badge-api">ClinicalTrials.gov API v2</span>
        <span class="badge badge-v">v1.0.0</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── NCT ID (outside form) ──────────────────────────────────────────────────────
st.markdown('<div class="section-label">Clinical Trial Identifier</div>', unsafe_allow_html=True)
nct_id = st.text_input(
    "NCT ID", placeholder="NCT04280706", label_visibility="collapsed",
    key="nct_id_input", help="NCT number — fetched live with 403-resilient retry.",
)
st.caption("Format: NCT + 8 digits  ·  Example: NCT04280706")
st.markdown("---")

# ── Session-state defaults (set once; never overwrite user edits) ──────────────
_DEFAULTS: dict = {
    "pf_age": 45,
    "pf_sex": "female",
    "pf_ecog_ps": "Not specified",
    "pf_diagnoses": "",
    "pf_biomarkers": "",
    "pf_medications": "",
    "pf_history": "",
    "pf_prior_therapies": "",
    "pf_notes": "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Two-column layout ──────────────────────────────────────────────────────────
col_form, col_preview = st.columns([3, 2], gap="large")

# ── LEFT: st.form ─────────────────────────────────────────────────────────────
with col_form:
    st.markdown('<div class="section-label">Patient Data Entry</div>', unsafe_allow_html=True)

    # Load Sample — pre-populates session_state keys before the form renders
    if st.button("Load Sample Patient  (NSCLC / EGFR)", help="Pre-fill with a demo NSCLC patient"):
        for k, v in _SAMPLE.items():
            st.session_state[k] = v
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("patient_form", clear_on_submit=False):

        # Demographics
        d1, d2, d3 = st.columns([2, 2, 2])
        with d1:
            st.number_input(
                "Age (years)", min_value=1, max_value=120, step=1, key="pf_age",
            )
        with d2:
            st.selectbox(
                "Biological Sex",
                options=["female", "male", "other"],
                key="pf_sex",
            )
        with d3:
            st.selectbox(
                "ECOG PS",
                options=["Not specified", "0", "1", "2", "3", "4", "5"],
                key="pf_ecog_ps",
                help="0 = Fully active  ·  5 = Dead",
            )

        st.markdown("---")

        # Diagnoses
        st.text_area(
            "Active Diagnoses",
            height=75, key="pf_diagnoses",
            placeholder="Non-small cell lung cancer, stage IIIB\nHypertension",
        )
        st.markdown('<div class="field-hint">One diagnosis per line — ICD labels or clinical terms</div>', unsafe_allow_html=True)

        # Biomarkers & Medications
        bm_col, med_col = st.columns(2, gap="medium")
        with bm_col:
            st.text_area(
                "Biomarkers / Lab Values",
                height=105, key="pf_biomarkers",
                placeholder="EGFR: exon19del\nPD-L1: 45%\neGFR: 72",
            )
            st.markdown('<div class="field-hint">Format: KEY: VALUE — one per line</div>', unsafe_allow_html=True)
        with med_col:
            st.text_area(
                "Current Medications",
                height=105, key="pf_medications",
                placeholder="Amlodipine 5 mg\nAspirin 81 mg",
            )
            st.markdown('<div class="field-hint">One medication per line</div>', unsafe_allow_html=True)

        # History & Prior therapies
        h_col, pt_col = st.columns(2, gap="medium")
        with h_col:
            st.text_area(
                "Medical History",
                height=85, key="pf_history",
                placeholder="Never-smoker\nNo autoimmune disease",
            )
        with pt_col:
            st.text_area(
                "Prior Therapies",
                height=85, key="pf_prior_therapies",
                placeholder="Carboplatin/Paclitaxel x4 cycles (2022)",
            )
        st.markdown('<div class="field-hint">One entry per line for both columns above</div>', unsafe_allow_html=True)

        # Notes
        st.text_area(
            "Clinical Notes",
            height=65, key="pf_notes",
            placeholder="Patient is ambulatory. No active infections.",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "⚡  Start Reasoning", type="primary", use_container_width=True,
        )

# ── RIGHT: Patient profile preview ────────────────────────────────────────────
with col_preview:
    st.markdown('<div class="section-label">Patient Profile Preview</div>', unsafe_allow_html=True)
    st.caption("Reflects current form values — exactly what K2 will receive.")

    preview = {
        "age":             st.session_state.get("pf_age"),
        "sex":             st.session_state.get("pf_sex"),
        "ecog_ps":         st.session_state.get("pf_ecog_ps"),
        "diagnoses":       _lines(st.session_state.get("pf_diagnoses", "")),
        "biomarkers":      _parse_kv(st.session_state.get("pf_biomarkers", "")),
        "medications":     _lines(st.session_state.get("pf_medications", "")),
        "history":         _lines(st.session_state.get("pf_history", "")),
        "prior_therapies": _lines(st.session_state.get("pf_prior_therapies", "")),
        "notes":           st.session_state.get("pf_notes") or None,
    }
    has_data = any(v for v in preview.values() if v not in (None, [], {}, ""))
    if has_data:
        st.markdown(_patient_as_html_table(preview), unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="text-align:center;padding:48px 0;color:#94A3B8">'
            '<div style="font-size:2.5rem">📋</div>'
            '<div style="margin-top:10px;font-size:0.85rem">Fill the form to see the preview</div>'
            '</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── Results ────────────────────────────────────────────────────────────────────
if submitted:
    nct_clean = (st.session_state.get("nct_id_input") or "").strip().upper()
    if not re.match(r"^NCT\d{8}$", nct_clean):
        st.error("Invalid NCT ID — expected NCT followed by exactly 8 digits (e.g. NCT04280706).")
        st.stop()

    patient_dict = _build_patient_dict()
    if patient_dict["age"] < 1:
        st.error("Age must be at least 1.")
        st.stop()
    if not patient_dict["diagnoses"]:
        st.error("Please enter at least one diagnosis before starting the analysis.")
        st.stop()

    with st.status("Running eligibility analysis…", expanded=True) as status:
        st.write(f"**[1/3]** Fetching trial `{nct_clean}`…")
        st.caption("_Checking local demo cache first; live API used as fallback (4 retry attempts with browser headers)._")

        payload = {"nct_id": nct_clean, "patient": patient_dict}
        try:
            response = requests.post(
                f"{backend_url.rstrip('/')}/api/match",
                json=payload,
                timeout=150,
            )
        except requests.exceptions.ConnectionError:
            status.update(label="Connection failed", state="error")
            st.error(f"Cannot reach the backend at **{backend_url}**. Is the FastAPI server running?")
            st.stop()
        except requests.exceptions.Timeout:
            status.update(label="Request timed out", state="error")
            st.error("Request timed out after 150 s. K2 may be under heavy load — please retry.")
            st.stop()

        if response.status_code == 403:
            status.update(label="API blocked (403)", state="error")
            st.warning(
                "**Demo Mode Active: Please use NCT04280706** — "
                "ClinicalTrials.gov blocked all fetch attempts (403 Forbidden). "
                "Only trials in the local demo cache are available right now.",
                icon="🚫",
            )
            st.stop()
        if response.status_code == 404:
            status.update(label="Not in demo cache", state="error")
            st.warning(
                "**Demo Mode Active: Please use NCT04280706** — "
                f"Trial **{nct_clean}** is not in the local demo cache and the live API is currently rate-limited. "
                "Enter **NCT04280706** to see a full analysis.",
                icon="⚠️",
            )
            st.stop()
        if response.status_code >= 500:
            status.update(label="Backend error", state="error")
            st.warning(
                "**Demo Mode Active: Please use NCT04280706** — "
                "The backend encountered an error fetching that trial. "
                "Only NCT04280706 is guaranteed to work in this demo environment.",
                icon="⚠️",
            )
            st.stop()
        if response.status_code != 200:
            status.update(label="Backend error", state="error")
            try:
                detail = response.json().get("detail", response.text[:300])
            except Exception:
                detail = response.text[:300]
            st.error(f"Backend returned HTTP **{response.status_code}**: {detail}")
            st.stop()

        st.write("**[2/3]** Trial data received — sending patient profile to K2-Think-v2…")
        st.caption("_K2 performs chain-of-thought analysis across every criterion. This takes 30–90 s._")
        data = response.json()

        st.write("**[3/3]** Structuring reasoning output…")
        time.sleep(0.2)
        status.update(
            label=f"Analysis complete — {data.get('eligibility_label', '?')}",
            state="complete",
        )

    trial_title     = data.get("trial_title", nct_clean)
    verdict_label   = data.get("eligibility_label", "UNCERTAIN")
    score           = data.get("eligibility_score", 0.0)
    confidence      = data.get("confidence", "LOW")
    summary         = data.get("summary", "")
    disqualifying   = data.get("disqualifying_criteria", [])
    reasoning_chain = data.get("reasoning_chain", [])
    disclaimer      = data.get("disclaimer", "")

    # Trial card
    st.markdown(
        f'<div class="trial-card">'
        f'<div class="trial-nct">{nct_clean}</div>'
        f'<div class="trial-title">{trial_title}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Verdict row
    st.markdown("#### Eligibility Assessment")
    vc1, vc2, vc3, vc4 = st.columns([3, 1, 1, 1], gap="medium")
    with vc1:
        st.markdown('<div class="verdict-label">Clinical Summary</div>', unsafe_allow_html=True)

        def _summary_words(text: str):
            """Yield words one at a time for a live-typewriter streaming effect."""
            words = text.split()
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                time.sleep(0.025)

        st.write_stream(_summary_words(summary))
    with vc2:
        c = _score_color(score)
        st.markdown(
            f'<div class="verdict-panel" style="text-align:center">'
            f'<div class="verdict-label">Score</div>'
            f'<div class="score-ring" style="color:{c}">{score:.0%}</div>'
            f'<div class="score-sub">Eligibility</div></div>',
            unsafe_allow_html=True,
        )
    with vc3:
        st.markdown(
            f'<div class="verdict-panel" style="text-align:center">'
            f'<div class="verdict-label">Verdict</div>'
            f'{_verdict_badge(verdict_label)}</div>',
            unsafe_allow_html=True,
        )
    with vc4:
        st.markdown(
            f'<div class="verdict-panel" style="text-align:center">'
            f'<div class="verdict-label">Confidence</div>'
            f'{_conf_pill(confidence)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if disqualifying:
        st.error(
            "**Disqualifying exclusion criteria:** " +
            "  ·  ".join(f"`{c}`" for c in disqualifying),
            icon="✘",
        )

    # Reasoning chain
    st.markdown("#### Step-by-Step Reasoning Chain")
    inclusion_items = [v for v in reasoning_chain if v.get("criterion_id", "").startswith("INC")]
    exclusion_items = [v for v in reasoning_chain if v.get("criterion_id", "").startswith("EXC")]

    VERDICT_ICON  = {"MET": "✔", "NOT_MET": "✘", "UNCERTAIN": "⚬"}
    VERDICT_COLOR = {"MET": "#059669", "NOT_MET": "#DC2626", "UNCERTAIN": "#D97706"}

    def _render_chain(items: list) -> None:
        if not items:
            st.caption("No criteria recorded in this section.")
            return
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Total",       len(items))
        mc2.metric("Met ✔",       sum(1 for v in items if v.get("verdict") == "MET"))
        mc3.metric("Not Met ✘",   sum(1 for v in items if v.get("verdict") == "NOT_MET"))
        mc4.metric("Uncertain ⚬", sum(1 for v in items if v.get("verdict") == "UNCERTAIN"))
        st.markdown("<br>", unsafe_allow_html=True)
        for item in items:
            cid       = item.get("criterion_id", "")
            verdict   = item.get("verdict", "UNCERTAIN")
            ctext     = item.get("criterion_text", "")
            reasoning = item.get("reasoning", "")
            evidence  = item.get("patient_evidence", "")
            icon  = VERDICT_ICON.get(verdict, "⚬")
            color = VERDICT_COLOR.get(verdict, "#D97706")
            label = verdict.replace("_", " ")
            with st.expander(
                f"{icon}  **{cid}** — {ctext[:95]}{'…' if len(ctext) > 95 else ''}",
                expanded=(verdict == "NOT_MET"),
            ):
                hdr, _ = st.columns([1, 4])
                with hdr:
                    st.markdown(
                        f'<span style="background:{color}22;color:{color};'
                        f'border:1px solid {color}55;padding:3px 10px;'
                        f'border-radius:4px;font-size:.78rem;font-weight:700">'
                        f'{label}</span>',
                        unsafe_allow_html=True,
                    )
                st.markdown("**Criterion text**")
                st.markdown(f"> {ctext}")
                if evidence:
                    st.markdown("**Patient evidence**")
                    st.markdown(f'<div class="evidence-box">{evidence}</div>', unsafe_allow_html=True)
                if reasoning:
                    st.markdown("**K2 reasoning**")
                    st.markdown(_highlight_keywords(reasoning), unsafe_allow_html=True)

    inc_tab, exc_tab = st.tabs([
        f"Inclusion Criteria  ({len(inclusion_items)})",
        f"Exclusion Criteria  ({len(exclusion_items)})",
    ])
    with inc_tab:
        _render_chain(inclusion_items)
    with exc_tab:
        _render_chain(exclusion_items)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Raw K2-Think-v2 Chain-of-Thought  (audit / regulatory review)", expanded=False):
        st.caption("Full unprocessed model output — use for audit trail or regulatory documentation.")
        st.text(data.get("raw_reasoning", ""))

    disc = disclaimer or (
        "This output is an automated eligibility pre-screen generated by an AI model. "
        "It does not constitute medical advice, a clinical diagnosis, or a treatment recommendation. "
        "All eligibility decisions must be reviewed and confirmed by a qualified investigator "
        "or clinical research coordinator before any patient action is taken."
    )
    st.markdown(
        f'<div class="sci-footer"><strong>Scientific Disclaimer</strong><br>{disc}<br><br>'
        f'<strong>Powered by</strong> MBZUAI-IFM/K2-Think-v2 &nbsp;·&nbsp; '
        f'<strong>Data</strong> ClinicalTrials.gov API v2 &nbsp;·&nbsp; '
        f'<strong>Build with K2 Think V2 Hackathon · 2025</strong></div>',
        unsafe_allow_html=True,
    )

# ── Empty state ────────────────────────────────────────────────────────────────
else:
    st.markdown(
        '<div style="text-align:center;padding:48px 0 36px;color:#94A3B8">'
        '<div style="font-size:3.2rem;margin-bottom:14px">⚕</div>'
        '<div style="font-size:1.1rem;font-weight:700;color:#475569;margin-bottom:8px">'
        'Complete the patient form and click <em>Start Reasoning</em></div>'
        '<div style="font-size:.87rem;max-width:460px;margin:0 auto;line-height:1.6">'
        'K2-Think-v2 audits every inclusion and exclusion criterion against the patient '
        'profile and returns a structured eligibility verdict with a full reasoning chain.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
