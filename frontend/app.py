"""Streamlit frontend for The Trial Oracle — Clinical Reasoning Engine."""
import json
import os
import re
import time

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Trial Oracle",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens (Clinical Laboratory palette) ────────────────────────────────
# Navy #0B1929 · Slate #334155 · Emerald #059669 · Amber #D97706 · Crimson #DC2626
# Surface #F1F5F9 · Panel #FFFFFF · Border #CBD5E1

st.markdown("""
<style>
/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 14px;
}
#MainMenu, footer, header { visibility: hidden; }
.stApp { background-color: #F1F5F9; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background-color: #0B1929 !important; }
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong { color: #F1F5F9 !important; }
[data-testid="stSidebar"] hr { border-color: #1E3A5F !important; }
[data-testid="stSidebar"] code {
    background: #1E3A5F !important;
    color: #7DD3FC !important;
    border-radius: 4px;
    padding: 2px 6px;
}

/* ── Header ── */
.lab-header {
    background: linear-gradient(120deg, #0B1929 0%, #1E3A5F 60%, #0D4F8C 100%);
    border-radius: 12px;
    padding: 30px 40px;
    margin-bottom: 24px;
    border: 1px solid #1E3A5F;
    position: relative;
    overflow: hidden;
}
.lab-header::before {
    content: '';
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 40%;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    opacity: 0.4;
}
.lab-header h1 {
    color: #F8FAFC !important;
    font-size: 1.9rem;
    font-weight: 700;
    margin: 0 0 6px 0;
    letter-spacing: -0.4px;
}
.lab-header .subtitle {
    color: #94A3B8 !important;
    font-size: 0.92rem;
    margin: 0;
    letter-spacing: 0.01em;
}
.badge-row { margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; }
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.badge-k2  { background: rgba(5,150,105,0.2); color: #6EE7B7; border: 1px solid rgba(5,150,105,0.3); }
.badge-api { background: rgba(59,130,246,0.2); color: #93C5FD; border: 1px solid rgba(59,130,246,0.3); }
.badge-v   { background: rgba(139,92,246,0.2); color: #C4B5FD; border: 1px solid rgba(139,92,246,0.3); }

/* ── Section labels ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #64748B;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #E2E8F0;
}

/* ── Trial info card ── */
.trial-card {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #0D4F8C;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 16px;
}
.trial-nct {
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 0.8rem;
    color: #0D4F8C;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.trial-title {
    font-size: 0.97rem;
    font-weight: 600;
    color: #0F172A;
    margin: 4px 0 10px 0;
    line-height: 1.4;
}
.trial-meta { display: flex; gap: 16px; flex-wrap: wrap; }
.meta-chip {
    font-size: 0.75rem;
    color: #475569;
    background: #F1F5F9;
    padding: 2px 10px;
    border-radius: 4px;
    border: 1px solid #E2E8F0;
}

/* ── Verdict cards ── */
.verdict-panel {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 20px 24px;
    height: 100%;
}
.verdict-label { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #64748B; margin-bottom: 8px; }

.vbadge {
    display: inline-block;
    padding: 7px 20px;
    border-radius: 6px;
    font-size: 0.88rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.vbadge-eligible   { background: #ECFDF5; color: #065F46; border: 1.5px solid #6EE7B7; }
.vbadge-ineligible { background: #FEF2F2; color: #7F1D1D; border: 1.5px solid #FCA5A5; }
.vbadge-uncertain  { background: #FFFBEB; color: #78350F; border: 1.5px solid #FDE68A; }

.score-ring {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1;
    text-align: center;
}
.score-sub { font-size: 0.7rem; color: #64748B; text-align: center; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }

.cpill {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 4px;
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.cpill-high   { background: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }
.cpill-medium { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
.cpill-low    { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }

/* ── Criterion rows ── */
.crit-expander-met      { border-left: 3px solid #059669; }
.crit-expander-not_met  { border-left: 3px solid #DC2626; }
.crit-expander-uncertain{ border-left: 3px solid #D97706; }

.kw-eligible   { background:#ECFDF5; color:#065F46; padding:1px 5px; border-radius:3px; font-weight:600; font-size:0.85em; }
.kw-ineligible { background:#FEF2F2; color:#7F1D1D; padding:1px 5px; border-radius:3px; font-weight:600; font-size:0.85em; }
.kw-uncertain  { background:#FFFBEB; color:#78350F; padding:1px 5px; border-radius:3px; font-weight:600; font-size:0.85em; }
.kw-conflict   { background:#FEF2F2; color:#7F1D1D; padding:1px 5px; border-radius:3px; font-weight:600; font-size:0.85em; }

.evidence-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.82rem;
    color: #334155;
    margin: 6px 0;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* ── Summary panel ── */
.summary-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 16px 20px;
    font-size: 0.9rem;
    color: #1E293B;
    line-height: 1.65;
}

/* ── Patient profile table ── */
.patient-table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
.patient-table th {
    background: #F1F5F9;
    color: #475569;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 7px 12px;
    text-align: left;
    border-bottom: 1px solid #CBD5E1;
}
.patient-table td {
    padding: 8px 12px;
    color: #1E293B;
    border-bottom: 1px solid #F1F5F9;
    vertical-align: top;
}
.patient-table tr:last-child td { border-bottom: none; }
.pt-key { font-weight: 600; color: #334155; width: 36%; }

/* ── Footer ── */
.sci-footer {
    margin-top: 32px;
    padding: 16px 20px;
    background: #0B1929;
    border-radius: 8px;
    font-size: 0.78rem;
    color: #64748B;
    line-height: 1.6;
}
.sci-footer strong { color: #94A3B8; }

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
}

/* ── Progress bar color ── */
.stProgress > div > div > div > div { background-color: #059669 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
SAMPLE_PATIENT = {
    "age": 58,
    "sex": "female",
    "diagnoses": ["Non-small cell lung cancer, stage IIIB", "Hypertension"],
    "biomarkers": {"EGFR": "exon19del", "PD-L1": "45%", "eGFR": 72, "ALT": 28, "AST": 31},
    "medications": ["Amlodipine 5 mg", "Aspirin 81 mg"],
    "history": ["Never-smoker", "No prior thoracic surgery", "No history of autoimmune disease"],
    "ecog_ps": 1,
    "prior_therapies": ["Carboplatin/Paclitaxel × 4 cycles (2022)"],
    "notes": "Patient is ambulatory and capable of all self-care. No active infections.",
}

_STATUS_COLOR = {"RECRUITING": "#059669", "COMPLETED": "#64748B", "TERMINATED": "#DC2626",
                 "WITHDRAWN": "#DC2626", "SUSPENDED": "#D97706", "ACTIVE, NOT RECRUITING": "#D97706"}

# ── Helper functions ───────────────────────────────────────────────────────────
def _highlight_keywords(text: str) -> str:
    """Wrap clinical verdict keywords with color-coded HTML spans."""
    rules = [
        (r"\b(ELIGIBLE|MET)\b",          "kw-eligible"),
        (r"\b(INELIGIBLE|NOT MET)\b",     "kw-ineligible"),
        (r"\b(UNCERTAIN|MISSING|ABSENT)\b","kw-uncertain"),
        (r"\b(CONFLICT|DISQUALIF\w*|EXCLUDED?)\b", "kw-conflict"),
    ]
    for pattern, cls in rules:
        text = re.sub(pattern, lambda m: f'<span class="{cls}">{m.group()}</span>', text, flags=re.IGNORECASE)
    return text


def _parse_patient_json(raw: str) -> dict | None:
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _patient_as_html_table(p: dict) -> str:
    """Render patient dict as a clean HTML table — no raw JSON shown to user."""
    def _fmt(v) -> str:
        if isinstance(v, list):
            return "<br>".join(f"• {i}" for i in v) if v else "<em style='color:#94A3B8'>None listed</em>"
        if isinstance(v, dict):
            return "<br>".join(f"<code>{k}</code>: {val}" for k, val in v.items()) if v else "<em style='color:#94A3B8'>None</em>"
        return str(v) if v is not None else "<em style='color:#94A3B8'>—</em>"

    labels = {
        "age": "Age", "sex": "Sex", "diagnoses": "Diagnoses",
        "biomarkers": "Biomarkers / Lab Values", "medications": "Current Medications",
        "history": "Medical History", "ecog_ps": "ECOG Performance Status",
        "prior_therapies": "Prior Therapies", "notes": "Clinical Notes",
    }
    rows = ""
    for key, label in labels.items():
        val = p.get(key)
        if val is None and key not in p:
            continue
        rows += f'<tr><td class="pt-key">{label}</td><td>{_fmt(val)}</td></tr>'

    return f'<table class="patient-table"><thead><tr><th>Field</th><th>Value</th></tr></thead><tbody>{rows}</tbody></table>'


def _score_color(score: float) -> str:
    if score >= 0.75: return "#059669"
    if score >= 0.40: return "#D97706"
    return "#DC2626"


def _verdict_badge(label: str) -> str:
    cls_map = {"ELIGIBLE": "vbadge-eligible", "INELIGIBLE": "vbadge-ineligible", "UNCERTAIN": "vbadge-uncertain"}
    icon_map = {"ELIGIBLE": "✔ ELIGIBLE", "INELIGIBLE": "✘ INELIGIBLE", "UNCERTAIN": "⚬ UNCERTAIN"}
    cls = cls_map.get(label, "vbadge-uncertain")
    txt = icon_map.get(label, label)
    return f'<span class="vbadge {cls}">{txt}</span>'


def _conf_pill(conf: str) -> str:
    cls = f"cpill cpill-{conf.lower()}"
    return f'<span class="{cls}">{conf} confidence</span>'


def _status_chip(status: str | None) -> str:
    if not status:
        return '<span class="meta-chip">Status unknown</span>'
    color = _STATUS_COLOR.get(status.upper(), "#475569")
    return f'<span class="meta-chip" style="color:{color};border-color:{color}33;">{status}</span>'

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
    for nct, label in [("NCT04280706", "Lung cancer / EGFR"), ("NCT03661788", "Breast cancer"), ("NCT04158791", "COVID-19")]:
        st.markdown(f"`{nct}` — {label}")
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

# ── Input grid ─────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-label">Clinical Trial Identifier</div>', unsafe_allow_html=True)
    nct_id = st.text_input(
        "NCT ID",
        placeholder="NCT04280706",
        label_visibility="collapsed",
        help="ClinicalTrials.gov NCT number. Data is fetched live.",
    )
    st.caption("Enter a valid NCT ID — trial data is fetched live from ClinicalTrials.gov")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Patient Profile Preview</div>', unsafe_allow_html=True)
    if "patient_json" in st.session_state:
        pd = _parse_patient_json(st.session_state["patient_json"])
        if pd:
            st.markdown(_patient_as_html_table(pd), unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-label">Patient Clinical Profile (JSON)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    with c2:
        if st.button("Sample", use_container_width=True, help="Load a sample NSCLC patient"):
            st.session_state["patient_json"] = json.dumps(SAMPLE_PATIENT, indent=2)
            st.rerun()

    default_json = st.session_state.get("patient_json", json.dumps(SAMPLE_PATIENT, indent=2))
    patient_input = st.text_area(
        "Patient JSON",
        value=default_json,
        height=320,
        label_visibility="collapsed",
        help="PatientData JSON. Required: age, sex.",
    )
    st.session_state["patient_json"] = patient_input

# ── Action button ──────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
btn_col, _ = st.columns([1, 4])
with btn_col:
    run = st.button("⚡  Start Reasoning", type="primary", use_container_width=True)

st.markdown("---")

# ── Results ────────────────────────────────────────────────────────────────────
if run:
    # Local validation
    nct_clean = nct_id.strip().upper()
    if not re.match(r"^NCT\d{8}$", nct_clean):
        st.error("Invalid NCT ID — expected format: `NCT` followed by exactly 8 digits (e.g. `NCT04280706`).")
        st.stop()

    patient_dict = _parse_patient_json(patient_input)
    if patient_dict is None:
        st.error("Patient profile is not valid JSON. Check for missing commas or mismatched brackets.")
        st.stop()

    missing = {"age", "sex"} - patient_dict.keys()
    if missing:
        st.error(f"Patient JSON is missing required field(s): **{', '.join(sorted(missing))}**")
        st.stop()

    # st.status — real-time progress feedback
    with st.status("Running eligibility analysis…", expanded=True) as status:
        st.write(f"**[1/3]** Fetching trial `{nct_clean}` from ClinicalTrials.gov…")

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

        # Surface specific error types before falling through to generic handler
        if response.status_code == 403:
            status.update(label="API blocked (403)", state="error")
            st.warning(
                "**ClinicalTrials.gov blocked the request (403 Forbidden).** "
                "The server is rate-limiting this IP. Wait 60 seconds and try again.",
                icon="🚫",
            )
            st.stop()

        if response.status_code == 404:
            status.update(label="Trial not found", state="error")
            st.error(f"Trial **{nct_clean}** was not found on ClinicalTrials.gov. Verify the NCT ID.")
            st.stop()

        if response.status_code != 200:
            status.update(label="Backend error", state="error")
            try:
                detail = response.json().get("detail", response.text[:300])
            except Exception:
                detail = response.text[:300]
            st.error(f"Backend returned HTTP **{response.status_code}**: {detail}")
            st.stop()

        st.write(f"**[2/3]** Trial data received — sending to K2-Think-v2 for reasoning…")
        st.caption("_K2 performs chain-of-thought analysis across every criterion. This takes 30–90 s._")

        data = response.json()

        st.write("**[3/3]** Structuring reasoning output…")
        time.sleep(0.2)
        status.update(label=f"Analysis complete — {data.get('eligibility_label', '?')}", state="complete")

    # ── Trial info card ───────────────────────────────────────────────────────
    trial_title  = data.get("trial_title", nct_clean)
    verdict_label = data.get("eligibility_label", "UNCERTAIN")
    score        = data.get("eligibility_score", 0.0)
    confidence   = data.get("confidence", "LOW")
    summary      = data.get("summary", "")
    disqualifying = data.get("disqualifying_criteria", [])
    reasoning_chain = data.get("reasoning_chain", [])
    disclaimer   = data.get("disclaimer", "")

    st.markdown(f"""
    <div class="trial-card">
        <div class="trial-nct">{nct_clean}</div>
        <div class="trial-title">{trial_title}</div>
        <div class="trial-meta">
            {_status_chip(None)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Verdict row ───────────────────────────────────────────────────────────
    st.markdown("#### Eligibility Assessment")
    vc1, vc2, vc3, vc4 = st.columns([3, 1, 1, 1], gap="medium")

    with vc1:
        st.markdown('<div class="verdict-label">Clinical Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-box">{_highlight_keywords(summary)}</div>', unsafe_allow_html=True)

    with vc2:
        color = _score_color(score)
        st.markdown(f"""
        <div class="verdict-panel" style="text-align:center;">
            <div class="verdict-label">Score</div>
            <div class="score-ring" style="color:{color};">{score:.0%}</div>
            <div class="score-sub">Eligibility</div>
        </div>""", unsafe_allow_html=True)

    with vc3:
        st.markdown(f"""
        <div class="verdict-panel" style="text-align:center;">
            <div class="verdict-label">Verdict</div>
            {_verdict_badge(verdict_label)}
        </div>""", unsafe_allow_html=True)

    with vc4:
        st.markdown(f"""
        <div class="verdict-panel" style="text-align:center;">
            <div class="verdict-label">Confidence</div>
            {_conf_pill(confidence)}
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Disqualification alert ────────────────────────────────────────────────
    if disqualifying:
        ids_fmt = "  ·  ".join(f"`{c}`" for c in disqualifying)
        st.error(f"**Disqualifying exclusion criteria:** {ids_fmt}", icon="✘")

    # ── Reasoning panel ───────────────────────────────────────────────────────
    st.markdown("#### Step-by-Step Reasoning Chain")

    inclusion_items = [v for v in reasoning_chain if v.get("criterion_id", "").startswith("INC")]
    exclusion_items = [v for v in reasoning_chain if v.get("criterion_id", "").startswith("EXC")]

    VERDICT_ICON  = {"MET": "✔", "NOT_MET": "✘", "UNCERTAIN": "⚬"}
    VERDICT_BCLS  = {"MET": "crit-expander-met", "NOT_MET": "crit-expander-not_met", "UNCERTAIN": "crit-expander-uncertain"}
    VERDICT_COLOR = {"MET": "#059669", "NOT_MET": "#DC2626", "UNCERTAIN": "#D97706"}

    def _render_chain(items: list[dict]) -> None:
        if not items:
            st.caption("No criteria recorded in this section.")
            return

        # Summary progress bar
        met_n  = sum(1 for v in items if v.get("verdict") == "MET")
        fail_n = sum(1 for v in items if v.get("verdict") == "NOT_MET")
        unc_n  = sum(1 for v in items if v.get("verdict") == "UNCERTAIN")
        total  = len(items)

        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
        pcol1.metric("Total", total)
        pcol2.metric("Met ✔", met_n,  delta=None)
        pcol3.metric("Not Met ✘", fail_n, delta=None)
        pcol4.metric("Uncertain ⚬", unc_n, delta=None)

        st.markdown("<br>", unsafe_allow_html=True)

        for item in items:
            cid      = item.get("criterion_id", "")
            verdict  = item.get("verdict", "UNCERTAIN")
            ctext    = item.get("criterion_text", "")
            reasoning = item.get("reasoning", "")
            evidence = item.get("patient_evidence", "")

            icon  = VERDICT_ICON.get(verdict, "⚬")
            color = VERDICT_COLOR.get(verdict, "#D97706")
            label = verdict.replace("_", " ")

            title = f"{icon}  **{cid}** — {ctext[:95]}{'…' if len(ctext) > 95 else ''}"
            expanded = verdict == "NOT_MET"

            with st.expander(title, expanded=expanded):
                hdr_col, _ = st.columns([1, 4])
                with hdr_col:
                    st.markdown(
                        f'<span style="background:{color}22;color:{color};border:1px solid {color}55;'
                        f'padding:3px 10px;border-radius:4px;font-size:0.78rem;font-weight:700;'
                        f'letter-spacing:0.04em;">{label}</span>',
                        unsafe_allow_html=True,
                    )

                st.markdown(f"**Criterion text**")
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

    # ── Raw K2 output ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Raw K2-Think-v2 Chain-of-Thought  (audit / regulatory review)", expanded=False):
        st.caption("Full unprocessed model output. Use for debugging or regulatory documentation.")
        st.text(data.get("raw_reasoning", ""))

    # ── Scientific disclaimer footer ──────────────────────────────────────────
    st.markdown(f"""
    <div class="sci-footer">
        <strong>Scientific Disclaimer</strong><br>
        {disclaimer or
         "This output is an automated eligibility pre-screen generated by an AI model. "
         "It does not constitute medical advice, a clinical diagnosis, or a treatment recommendation. "
         "All eligibility decisions must be reviewed and confirmed by a qualified investigator "
         "or clinical research coordinator before any patient action is taken."}<br><br>
        <strong>Powered by</strong> MBZUAI-IFM/K2-Think-v2 &nbsp;·&nbsp;
        <strong>Data</strong> ClinicalTrials.gov API v2 &nbsp;·&nbsp;
        <strong>Build with K2 Think V2 Hackathon · 2025</strong>
    </div>
    """, unsafe_allow_html=True)

# ── Empty state ────────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="text-align:center; padding:56px 0 48px; color:#94A3B8;">
        <div style="font-size:3.5rem; margin-bottom:16px;">⚕</div>
        <div style="font-size:1.15rem; font-weight:700; color:#475569; margin-bottom:8px;">
            Enter an NCT ID and a patient profile, then click <em>Start Reasoning</em>
        </div>
        <div style="font-size:0.88rem; max-width:480px; margin:0 auto; line-height:1.6;">
            K2-Think-v2 will audit every inclusion and exclusion criterion against the patient
            profile, returning a structured eligibility verdict with a full reasoning chain.
        </div>
        <div style="margin-top:28px; display:flex; gap:24px; justify-content:center; flex-wrap:wrap;">
            <div style="background:white;border:1px solid #E2E8F0;border-radius:8px;padding:14px 22px;font-size:0.82rem;color:#334155;">
                <strong style="color:#0D4F8C;">Step 1</strong><br>Enter NCT ID
            </div>
            <div style="background:white;border:1px solid #E2E8F0;border-radius:8px;padding:14px 22px;font-size:0.82rem;color:#334155;">
                <strong style="color:#0D4F8C;">Step 2</strong><br>Paste patient profile
            </div>
            <div style="background:white;border:1px solid #E2E8F0;border-radius:8px;padding:14px 22px;font-size:0.82rem;color:#334155;">
                <strong style="color:#059669;">Step 3</strong><br>Start Reasoning ⚡
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
