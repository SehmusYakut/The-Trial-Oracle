"""Streamlit frontend for The Trial Oracle — Clinical AI Division."""
import html as _html
import os
import re
import time

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="The Trial Oracle",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: High-Contrast Clinical Theme 2026 ────────────────────────────────────
st.markdown("""<style>
html,body,[class*="css"]{font-family:'Inter','Segoe UI',system-ui,sans-serif;font-size:15px}
#MainMenu,footer,header{visibility:hidden}
.stApp{background-color:#060D1A!important}
.main .block-container{padding-top:1.5rem;max-width:100%}
label,.stMarkdown p,.stText p{color:#CBD5E1!important;font-size:.93rem}
h1,h2,h3,h4,h5,h6{color:#F1F5F9!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea{
  background-color:#0D1F35!important;color:#E2E8F0!important;font-size:.93rem!important;
  border-color:#2D4F7A!important;caret-color:#10B981!important}
.stSelectbox [data-baseweb="select"]>div{
  background-color:#0D1F35!important;border-color:#2D4F7A!important;color:#E2E8F0!important}
.stSelectbox [data-baseweb="select"] svg{fill:#94A3B8!important}
[data-testid="stForm"]{background:#0B1929;border:1px solid #1E3A5F;border-radius:12px;padding:20px}
.stButton>button{background:#0D2A45!important;color:#93C5FD!important;border:1px solid #1E4F8C!important;border-radius:6px!important;transition:box-shadow .2s}
.stButton>button:hover{background:#0D3660!important;box-shadow:0 0 14px rgba(16,185,129,.25)!important}
div[data-testid="stFormSubmitButton"]>button{
  background:linear-gradient(135deg,#059669 0%,#0D9488 100%)!important;color:#F0FDF4!important;
  border:none!important;font-weight:700!important;font-size:1rem!important;
  box-shadow:0 0 22px rgba(16,185,129,.45)!important;border-radius:6px!important}
div[data-testid="stFormSubmitButton"]>button:hover{box-shadow:0 0 32px rgba(16,185,129,.65)!important}
[data-testid="stSidebar"]{background-color:#040B16!important;border-right:1px solid #0D2040!important}
[data-testid="stSidebar"] *{color:#CBD5E1!important}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong{color:#F1F5F9!important}
[data-testid="stSidebar"] hr{border-color:#0D2040!important}
[data-testid="stSidebar"] code{background:#0D2040!important;color:#6EE7B7!important;border-radius:4px;padding:2px 6px}
.stTabs [data-baseweb="tab-list"]{background:#060D1A!important;border-bottom:1px solid #1E3A5F!important;gap:4px}
.stTabs [data-baseweb="tab"]{color:#64748B!important;background:transparent!important;padding:8px 16px!important;font-size:.88rem!important}
.stTabs [aria-selected="true"]{color:#10B981!important;border-bottom:2px solid #10B981!important}
[data-testid="stMetric"]{background:#0B1929!important;border:1px solid #1E3A5F!important;border-radius:8px!important;padding:12px 16px!important}
[data-testid="stMetricLabel"] p{color:#94A3B8!important;font-size:.68rem!important;text-transform:uppercase!important;letter-spacing:.09em!important}
[data-testid="stMetricValue"]{color:#10B981!important;font-size:1.4rem!important}
.streamlit-expanderHeader{background:#0B1929!important;border:1px solid #1E3A5F!important;border-radius:6px!important;color:#CBD5E1!important}
.streamlit-expanderContent{background:#08111E!important;border:1px solid #1E3A5F!important;border-top:none!important}
[data-testid="stStatusWidget"]{background:#0B1929!important;border:1px solid #1E3A5F!important}
hr{border-color:#0D2040!important}
/* ─── AUDIT COMPONENTS ─── */
.audit-card{border-radius:10px;padding:18px 20px;margin-bottom:4px}
.audit-conflict{background:rgba(239,68,68,.07);border:2px solid rgba(239,68,68,.4)}
.audit-clean{background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.3)}
.audit-badge{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border-radius:7px;font-size:.95rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase;margin-bottom:14px}
.audit-badge-conflict{background:rgba(239,68,68,.18);color:#FCA5A5;border:2px solid rgba(239,68,68,.55);box-shadow:0 0 18px rgba(239,68,68,.2)}
.audit-badge-clean{background:rgba(16,185,129,.14);color:#6EE7B7;border:1.5px solid rgba(16,185,129,.35);box-shadow:0 0 16px rgba(16,185,129,.18)}
.audit-badge-pending{background:rgba(100,116,139,.14);color:#94A3B8;border:1.5px solid rgba(100,116,139,.3)}
.audit-conflict-banner{background:rgba(239,68,68,.1);border:2px solid rgba(239,68,68,.5);border-radius:10px;padding:16px 20px;margin-bottom:16px}
.audit-conflict-title{font-size:1.05rem;font-weight:800;color:#EF4444;margin-bottom:6px;display:block}
.audit-conflict-body{color:#FCA5A5;font-size:.9rem;line-height:1.6}
.audit-criterion{font-family:monospace;font-size:.84rem;color:#94A3B8;background:#060D1A;padding:6px 12px;border-radius:4px;margin-bottom:10px;display:block;word-break:break-word}
.audit-challenge-label{font-size:.65rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:rgba(245,158,11,.85);display:block;margin-bottom:5px}
.audit-challenge-label-clean{color:rgba(16,185,129,.85)}
.audit-challenge-text{font-size:.9rem;color:#CBD5E1;line-height:1.65}
.audit-conf-pill{display:inline-block;padding:4px 12px;border-radius:4px;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-top:10px}
.audit-conf-high{background:rgba(239,68,68,.14);color:#FCA5A5;border:1px solid rgba(239,68,68,.27)}
.audit-conf-medium{background:rgba(245,158,11,.14);color:#FDE68A;border:1px solid rgba(245,158,11,.27)}
.audit-conf-low{background:rgba(100,116,139,.14);color:#94A3B8;border:1px solid rgba(100,116,139,.27)}
.advocate-header{font-size:.7rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#94A3B8;margin-bottom:10px;display:flex;align-items:center;gap:10px}
.advocate-header::after{content:'';flex:1;height:1px;background:#1E3A5F}
/* ─── HEADER ─── */
.lab-header{background:linear-gradient(120deg,#040B16 0%,#07121F 55%,#04130A 100%);border-radius:12px;padding:28px 36px;margin-bottom:20px;border:1px solid #0D2040;box-shadow:0 0 45px rgba(16,185,129,.07)}
.lab-header h1{color:#F8FAFC!important;font-size:1.95rem;font-weight:700;margin:0 0 5px 0}
.lab-header .subtitle{color:#94A3B8!important;font-size:.95rem;margin:0}
.badge-row{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.badge{display:inline-block;padding:3px 10px;border-radius:4px;font-size:.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.badge-k2{background:rgba(16,185,129,.13);color:#6EE7B7;border:1px solid rgba(16,185,129,.27)}
.badge-api{background:rgba(59,130,246,.13);color:#93C5FD;border:1px solid rgba(59,130,246,.27)}
.badge-v{background:rgba(139,92,246,.13);color:#C4B5FD;border:1px solid rgba(139,92,246,.27)}
.badge-demo{background:rgba(245,158,11,.13);color:#FDE68A;border:1px solid rgba(245,158,11,.27)}
/* ─── SECTION LABELS ─── */
.section-label{font-size:.7rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#94A3B8;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #1E3A5F}
.field-hint{font-size:.73rem;color:#64748B;margin-top:-4px;margin-bottom:8px;font-style:italic}
/* ─── TRIAL CARD ─── */
.trial-card{background:#0B1929;border:1px solid #2D4F7A;border-left:4px solid #10B981;border-radius:8px;padding:14px 18px;margin-bottom:14px;box-shadow:0 0 20px rgba(16,185,129,.08)}
.trial-nct{font-family:monospace;font-size:.82rem;color:#10B981;font-weight:700}
.trial-title{font-size:.98rem;font-weight:600;color:#F1F5F9;margin:4px 0 0 0;line-height:1.5}
/* ─── VERDICT ─── */
.verdict-panel{background:#0B1929;border:1px solid #1E3A5F;border-radius:10px;padding:16px 18px}
.verdict-label{font-size:.65rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#94A3B8;margin-bottom:8px}
.vbadge{display:inline-block;padding:6px 16px;border-radius:6px;font-size:.88rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase}
.vbadge-eligible{background:rgba(16,185,129,.14);color:#6EE7B7;border:1.5px solid rgba(16,185,129,.35)}
.vbadge-ineligible{background:rgba(239,68,68,.14);color:#FCA5A5;border:1.5px solid rgba(239,68,68,.35)}
.vbadge-uncertain{background:rgba(245,158,11,.14);color:#FDE68A;border:1.5px solid rgba(245,158,11,.35)}
.score-ring{font-size:2.3rem;font-weight:800;line-height:1;text-align:center}
.score-sub{font-size:.63rem;color:#64748B;text-align:center;margin-top:4px;text-transform:uppercase;letter-spacing:.07em}
.cpill{display:inline-block;padding:4px 12px;border-radius:4px;font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.cpill-high{background:rgba(16,185,129,.14);color:#6EE7B7;border:1px solid rgba(16,185,129,.27)}
.cpill-medium{background:rgba(245,158,11,.14);color:#FDE68A;border:1px solid rgba(245,158,11,.27)}
.cpill-low{background:rgba(239,68,68,.14);color:#FCA5A5;border:1px solid rgba(239,68,68,.27)}
/* ─── LOGIC TREE (K2 Reasoning Pathway) ─── */
.logic-tree{display:flex;flex-direction:column;gap:7px;padding:2px 0 6px}
.logic-step{border-radius:8px;padding:12px 14px;border:1px solid transparent}
.logic-step-met{background:rgba(16,185,129,.055);border-color:rgba(16,185,129,.2)}
.logic-step-notmet{background:rgba(239,68,68,.055);border-color:rgba(239,68,68,.2)}
.logic-step-uncertain{background:rgba(245,158,11,.055);border-color:rgba(245,158,11,.18)}
.ls-row{display:flex;align-items:flex-start;gap:10px}
.ls-icon{font-size:1.05rem;flex-shrink:0;padding-top:1px}
.ls-body{flex:1;min-width:0;overflow-wrap:break-word}
.ls-top{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:4px}
.ls-id{font-family:monospace;font-size:.7rem;font-weight:700;color:#94A3B8;background:#0D1F35;padding:2px 8px;border-radius:3px;border:1px solid #2D4F7A}
.ls-vbadge{font-size:.64rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:2px 8px;border-radius:3px}
.ls-vbadge-met{background:rgba(16,185,129,.18);color:#6EE7B7}
.ls-vbadge-notmet{background:rgba(239,68,68,.18);color:#FCA5A5}
.ls-vbadge-uncertain{background:rgba(245,158,11,.18);color:#FDE68A}
.ls-criterion{font-size:.88rem;color:#CBD5E1;line-height:1.55;overflow-wrap:break-word}
.ls-evidence{margin-top:7px;padding:6px 12px;background:#040B14;border-left:2px solid #2D4F7A;border-radius:0 4px 4px 0}
.ls-elabel{font-size:.62rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:#64748B;display:block;margin-bottom:2px}
.ls-etext{font-family:monospace;font-size:.81rem;color:#93C5FD;line-height:1.4;display:block;overflow-wrap:break-word}
.ls-reasoning{margin-top:6px;padding:7px 10px;background:rgba(16,185,129,.03);border-left:2px solid rgba(16,185,129,.3);border-radius:0 4px 4px 0}
.ls-rlabel{font-size:.62rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:rgba(16,185,129,.75);display:block;margin-bottom:3px}
.ls-rtext{font-size:.84rem;color:#94A3B8;line-height:1.6;margin:0;padding:0;overflow-wrap:break-word}
/* ─── KEY EVIDENCE GRID ─── */
.ke-header{font-size:.7rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#94A3B8;margin-bottom:10px;display:flex;align-items:center;gap:10px}
.ke-header::after{content:'';flex:1;height:1px;background:#1E3A5F}
.ke-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:8px;margin-bottom:8px}
.ke-card{background:#0B1929;border:1px solid #1E3A5F;border-radius:8px;padding:11px 13px}
.ke-card-disq{border-left:3px solid rgba(239,68,68,.7)}
.ke-card-pass{border-left:3px solid rgba(16,185,129,.7)}
.ke-cid{font-family:monospace;font-size:.7rem;font-weight:700;color:#94A3B8;margin-bottom:4px}
.ke-ctext{font-size:.84rem;color:#CBD5E1;line-height:1.45;margin-bottom:6px;overflow-wrap:break-word}
.ke-ev{font-family:monospace;font-size:.79rem;color:#93C5FD;background:#060D1A;padding:3px 8px;border-radius:4px;display:block;overflow-wrap:break-word}
/* ─── KEYWORD HIGHLIGHTS ─── */
.kw-eligible{background:rgba(16,185,129,.18);color:#6EE7B7;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.85em}
.kw-ineligible{background:rgba(239,68,68,.18);color:#FCA5A5;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.85em}
.kw-uncertain{background:rgba(245,158,11,.18);color:#FDE68A;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.85em}
.kw-conflict{background:rgba(239,68,68,.18);color:#FCA5A5;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.85em}
/* ─── PATIENT TABLE ─── */
.pt-wrapper{overflow-x:auto;-webkit-overflow-scrolling:touch}
.patient-table{width:100%;border-collapse:collapse;font-size:.85rem;min-width:320px}
.patient-table th{background:#0D1F35;color:#94A3B8;font-size:.7rem;font-weight:700;text-transform:uppercase;padding:8px 12px;text-align:left;border-bottom:1px solid #2D4F7A}
.patient-table td{padding:9px 12px;color:#CBD5E1;border-bottom:1px solid #0D1F35;vertical-align:top;overflow-wrap:break-word}
.patient-table tr:last-child td{border-bottom:none}
.pt-key{font-weight:600;color:#94A3B8;width:38%}
/* ─── FOOTER ─── */
.sci-footer{margin-top:28px;padding:14px 18px;background:#040B16;border:1px solid #0D2040;border-radius:8px;font-size:.76rem;color:#64748B;line-height:1.7}
.sci-footer strong{color:#94A3B8}
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
        '<div class="pt-wrapper"><table class="patient-table">'
        "<thead><tr><th>Field</th><th>Value</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
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
    return "#10B981" if s >= 0.75 else "#F59E0B" if s >= 0.40 else "#EF4444"


def _verdict_badge(label: str) -> str:
    cls  = {"ELIGIBLE": "vbadge-eligible", "INELIGIBLE": "vbadge-ineligible", "UNCERTAIN": "vbadge-uncertain"}.get(label, "vbadge-uncertain")
    icon = {"ELIGIBLE": "✔ ELIGIBLE", "INELIGIBLE": "✘ INELIGIBLE", "UNCERTAIN": "⚬ UNCERTAIN"}.get(label, label)
    return f'<span class="vbadge {cls}">{icon}</span>'


def _conf_pill(conf: str) -> str:
    return f'<span class="cpill cpill-{conf.lower()}">{conf} confidence</span>'


# ── Logic Tree renderer ────────────────────────────────────────────────────────
_VERDICT_META = {
    "MET":       ("✅", "logic-step-met",       "ls-vbadge-met",       "MET"),
    "NOT_MET":   ("❌", "logic-step-notmet",    "ls-vbadge-notmet",    "NOT MET"),
    "UNCERTAIN": ("⚬",  "logic-step-uncertain", "ls-vbadge-uncertain", "UNCERTAIN"),
}


def _render_logic_tree(items: list) -> None:
    if not items:
        st.markdown(
            '<p style="color:#334155;font-style:italic;padding:12px 0">No criteria recorded.</p>',
            unsafe_allow_html=True,
        )
        return

    n_met       = sum(1 for v in items if v.get("verdict") == "MET")
    n_notmet    = sum(1 for v in items if v.get("verdict") == "NOT_MET")
    n_uncertain = sum(1 for v in items if v.get("verdict") == "UNCERTAIN")

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Total",        len(items))
    mc2.metric("✅ Met",        n_met)
    mc3.metric("❌ Not Met",    n_notmet)
    mc4.metric("⚬ Uncertain",  n_uncertain)

    st.markdown("<br>", unsafe_allow_html=True)

    cards = ['<div class="logic-tree">']
    for item in items:
        cid      = _html.escape(item.get("criterion_id", ""))
        verdict  = item.get("verdict", "UNCERTAIN")
        ctext    = _html.escape(item.get("criterion_text", ""))
        evidence = _html.escape(item.get("patient_evidence", "") or "")
        reasoning = _html.escape(item.get("reasoning", "") or "")

        icon, step_cls, badge_cls, vlabel = _VERDICT_META.get(
            verdict, ("⚬", "logic-step-uncertain", "ls-vbadge-uncertain", "UNCERTAIN")
        )

        ev_html = (
            f'<div class="ls-evidence">'
            f'<span class="ls-elabel">Patient Data</span>'
            f'<span class="ls-etext">{evidence}</span>'
            f'</div>'
        ) if evidence else ""

        re_html = (
            f'<div class="ls-reasoning">'
            f'<span class="ls-rlabel">K2 Analysis</span>'
            f'<p class="ls-rtext">{reasoning}</p>'
            f'</div>'
        ) if reasoning else ""

        cards.append(
            f'<div class="logic-step {step_cls}">'
            f'<div class="ls-row">'
            f'<span class="ls-icon">{icon}</span>'
            f'<div class="ls-body">'
            f'<div class="ls-top">'
            f'<span class="ls-id">{cid}</span>'
            f'<span class="ls-vbadge {badge_cls}">{vlabel}</span>'
            f'</div>'
            f'<div class="ls-criterion">{ctext}</div>'
            f'</div></div>'
            f'{ev_html}{re_html}'
            f'</div>'
        )
    cards.append('</div>')
    st.markdown("\n".join(cards), unsafe_allow_html=True)


# ── Key Evidence renderer ──────────────────────────────────────────────────────
def _render_key_evidence(reasoning_chain: list) -> None:
    disq    = [v for v in reasoning_chain if v.get("verdict") == "NOT_MET"][:4]
    passing = [v for v in reasoning_chain if v.get("verdict") == "MET"][:4]
    if not disq and not passing:
        return

    st.markdown('<div class="ke-header">Key Evidence</div>', unsafe_allow_html=True)
    cards = []
    for item in disq:
        cid   = _html.escape(item.get("criterion_id", ""))
        ctext = _html.escape(item.get("criterion_text", ""))
        ev    = _html.escape(item.get("patient_evidence", "") or "")
        ev_html = f'<span class="ke-ev">{ev}</span>' if ev else ""
        cards.append(
            f'<div class="ke-card ke-card-disq">'
            f'<div class="ke-cid">❌ {cid} · CONFLICT</div>'
            f'<div class="ke-ctext">{ctext[:130]}{"…" if len(ctext) > 130 else ""}</div>'
            f'{ev_html}</div>'
        )
    for item in passing:
        cid   = _html.escape(item.get("criterion_id", ""))
        ctext = _html.escape(item.get("criterion_text", ""))
        ev    = _html.escape(item.get("patient_evidence", "") or "")
        ev_html = f'<span class="ke-ev">{ev}</span>' if ev else ""
        cards.append(
            f'<div class="ke-card ke-card-pass">'
            f'<div class="ke-cid">✅ {cid} · CONFIRMED</div>'
            f'<div class="ke-ctext">{ctext[:130]}{"…" if len(ctext) > 130 else ""}</div>'
            f'{ev_html}</div>'
        )
    st.markdown(f'<div class="ke-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


# ── Safety Audit renderer ─────────────────────────────────────────────────────
def _render_safety_audit(
    verdict: str | None,
    criterion: str,
    challenge: str,
    confidence: str,
    raw: str,
    pass1_verdict: str = "",
    pass1_summary: str = "",
) -> None:
    if verdict is None:
        st.markdown(
            '<div class="audit-card" style="background:rgba(100,116,139,.06);border:1px solid rgba(100,116,139,.25)">'
            '<span class="audit-badge audit-badge-pending">⏳ Safety Audit Unavailable</span>'
            '<p style="color:#94A3B8;font-size:.88rem;margin:0">Pass 2 did not complete — '
            'the K2 API may be under load. Re-run the analysis to attempt the safety audit.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    is_conflict = verdict == "CONFLICT_FOUND"
    card_cls    = "audit-conflict" if is_conflict else "audit-clean"
    badge_cls   = "audit-badge-conflict" if is_conflict else "audit-badge-clean"
    badge_icon  = "⚠️ SAFETY CONFLICT DETECTED" if is_conflict else "✔ HIGH INTEGRITY MATCH"
    label_cls   = "audit-challenge-label" if is_conflict else "audit-challenge-label audit-challenge-label-clean"

    conf_cls = {"HIGH": "audit-conf-high", "MEDIUM": "audit-conf-medium", "LOW": "audit-conf-low"}.get(
        (confidence or "").upper(), "audit-conf-low"
    )

    criterion_html = (
        f'<span class="audit-criterion">⚠ Criterion challenged: {_html.escape(criterion)}</span>'
        if criterion and criterion.lower() != "none" else ""
    )
    challenge_text = _html.escape(challenge) if challenge else (
        "No exploitable conflict identified after exhaustive review."
    )

    # Prominent full-width red banner when auditor finds a conflict
    conflict_banner = ""
    if is_conflict:
        conflict_banner = (
            '<div class="audit-conflict-banner">'
            '<span class="audit-conflict-title">⚠️ SAFETY CONFLICT DETECTED — CLINICAL REVIEW REQUIRED</span>'
            '<div class="audit-conflict-body">'
            '<strong>The skeptical auditor has flagged a potential disqualifying issue. '
            'Do not enroll this patient without thorough clinical re-evaluation.</strong>'
            f'<br><br>{criterion_html}'
            '</div></div>'
        )

    with st.container(border=True):
        st.markdown(
            f'{conflict_banner}'
            f'<div class="audit-card {card_cls}">'
            f'<span class="audit-badge {badge_cls}">{badge_icon}</span>'
            f'{"" if is_conflict else criterion_html}'
            f'<span class="{label_cls}">{"Devil\'s Advocate Argument" if is_conflict else "Auditor Assessment"}</span>'
            f'<p class="audit-challenge-text">{challenge_text}</p>'
            f'<span class="audit-conf-pill {conf_cls}">Auditor confidence: {confidence or "—"}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="advocate-header">Pass 1 Advocate vs Pass 2 Skeptical Auditor</div>', unsafe_allow_html=True)

        adv_col, aud_col = st.columns(2, gap="medium")
        with adv_col:
            verdict_color = "#10B981" if pass1_verdict == "ELIGIBLE" else "#EF4444" if pass1_verdict == "INELIGIBLE" else "#F59E0B"
            # Soft green background for Advocate
            st.markdown(
                f'<div style="background:rgba(16,185,129,0.07);border:1.5px solid rgba(16,185,129,0.3);'
                f'border-left:4px solid {verdict_color};border-radius:10px;padding:16px 18px">'
                f'<div style="font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;'
                f'color:#6EE7B7;margin-bottom:10px">⚕ Advocate — Pass 1 (Primary Audit)</div>'
                f'<div style="font-size:.88rem;color:#CBD5E1;line-height:1.6">{_html.escape(pass1_summary)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with aud_col:
            # Soft amber background for Auditor (conflict) or soft green (clean)
            aud_border = "rgba(245,158,11,0.45)" if is_conflict else "rgba(16,185,129,0.3)"
            aud_bg     = "rgba(245,158,11,0.07)" if is_conflict else "rgba(16,185,129,0.04)"
            aud_lcolor = "#FDE68A" if is_conflict else "#6EE7B7"
            aud_left   = "#F59E0B" if is_conflict else "#10B981"
            st.markdown(
                f'<div style="background:{aud_bg};border:1.5px solid {aud_border};'
                f'border-left:4px solid {aud_left};border-radius:10px;padding:16px 18px">'
                f'<div style="font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;'
                f'color:{aud_lcolor};margin-bottom:10px">⚖ Skeptical Auditor — Pass 2 (Safety Audit)</div>'
                f'<div style="font-size:.88rem;color:#CBD5E1;line-height:1.6">{challenge_text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if raw:
            with st.expander("Raw Pass 2 Auditor Output", expanded=False):
                st.text(raw)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚕ The Trial Oracle")
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
    st.markdown("**Demo NCT IDs**")
    for nct, lbl in [
        ("NCT04280706", "Lung cancer / EGFR ✅"),
        ("NCT03661788", "Breast cancer / TNBC ✅"),
        ("NCT04158791", "COVID-19"),
    ]:
        st.markdown(f"`{nct}` — {lbl}")
    st.markdown("---")
    st.caption("Build with K2 Think V2 Hackathon · 2026")
    st.caption("The Trial Oracle — Clinical AI Division")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lab-header">
    <h1>⚕ The Trial Oracle</h1>
    <p class="subtitle">Clinical AI Division · Automated Eligibility Matching · Dual-Pass K2 Reasoning</p>
    <div class="badge-row">
        <span class="badge badge-k2">Powered by K2-Think-v2</span>
        <span class="badge badge-api">ClinicalTrials.gov API v2</span>
        <span class="badge badge-demo">Devil's Advocate Audit</span>
        <span class="badge badge-v">v2.0.0 · 2026</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── NCT ID input ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Clinical Trial Identifier</div>', unsafe_allow_html=True)
nct_id = st.text_input(
    "NCT ID", placeholder="NCT04280706", label_visibility="collapsed",
    key="nct_id_input", help="NCT number — NCT04280706 (lung) and NCT03661788 (breast) load instantly from local cache.",
)
st.caption("Format: NCT + 8 digits  ·  NCT04280706 (NSCLC/EGFR) · NCT03661788 (TNBC) · Both served instantly from local cache")
st.markdown("---")

# ── Session-state defaults ─────────────────────────────────────────────────────
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

# ── LEFT: patient form ────────────────────────────────────────────────────────
with col_form:
    st.markdown('<div class="section-label">Patient Data Entry</div>', unsafe_allow_html=True)

    if st.button("Load Sample Patient  (NSCLC / EGFR)", help="Pre-fill with a demo NSCLC patient"):
        for k, v in _SAMPLE.items():
            st.session_state[k] = v
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("patient_form", clear_on_submit=False):
        d1, d2, d3 = st.columns([2, 2, 2])
        with d1:
            st.number_input("Age (years)", min_value=1, max_value=120, step=1, key="pf_age")
        with d2:
            st.selectbox("Biological Sex", options=["female", "male", "other"], key="pf_sex")
        with d3:
            st.selectbox(
                "ECOG PS",
                options=["Not specified", "0", "1", "2", "3", "4", "5"],
                key="pf_ecog_ps",
                help="0 = Fully active  ·  5 = Dead",
            )

        st.markdown("---")

        st.text_area(
            "Active Diagnoses", height=75, key="pf_diagnoses",
            placeholder="Non-small cell lung cancer, stage IIIB\nHypertension",
        )
        st.markdown('<div class="field-hint">One diagnosis per line — ICD labels or clinical terms</div>', unsafe_allow_html=True)

        bm_col, med_col = st.columns(2, gap="medium")
        with bm_col:
            st.text_area(
                "Biomarkers / Lab Values", height=105, key="pf_biomarkers",
                placeholder="EGFR: exon19del\nPD-L1: 45%\neGFR: 72",
            )
            st.markdown('<div class="field-hint">Format: KEY: VALUE — one per line</div>', unsafe_allow_html=True)
        with med_col:
            st.text_area(
                "Current Medications", height=105, key="pf_medications",
                placeholder="Amlodipine 5 mg\nAspirin 81 mg",
            )
            st.markdown('<div class="field-hint">One medication per line</div>', unsafe_allow_html=True)

        h_col, pt_col = st.columns(2, gap="medium")
        with h_col:
            st.text_area(
                "Medical History", height=85, key="pf_history",
                placeholder="Never-smoker\nNo autoimmune disease",
            )
        with pt_col:
            st.text_area(
                "Prior Therapies", height=85, key="pf_prior_therapies",
                placeholder="Carboplatin/Paclitaxel x4 cycles (2022)",
            )
        st.markdown('<div class="field-hint">One entry per line for both columns above</div>', unsafe_allow_html=True)

        st.text_area(
            "Clinical Notes", height=65, key="pf_notes",
            placeholder="Patient is ambulatory. No active infections.",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "⚡  Start Reasoning", type="primary", use_container_width=True,
        )

# ── RIGHT: patient profile preview ────────────────────────────────────────────
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
            '<div style="text-align:center;padding:48px 0">'
            '<div style="font-size:2.5rem;color:#1E3A5F">⬡</div>'
            '<div style="margin-top:10px;font-size:0.85rem;color:#64748B">Fill the form to see the preview</div>'
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
        st.caption("_Checking local demo cache first — live API used as fallback (4 retry attempts with browser headers)._")

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
                f"Trial **{nct_clean}** is not in the local demo cache and the live API is "
                "currently rate-limited. Enter **NCT04280706** to see a full analysis.",
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

        st.write("**[2/4]** Trial data received — Pass 1: K2 eligibility audit running…")
        st.caption("_K2 performs chain-of-thought analysis across every criterion. This takes 30–90 s._")
        data = response.json()

        st.write("**[3/4]** Pass 2: Devil's Advocate safety audit running…")
        st.caption("_A second K2 instance plays skeptical auditor — searching for any disqualifying edge case._")

        st.write("**[4/4]** Structuring dual-pass reasoning output…")
        time.sleep(0.2)
        status.update(
            label=f"Analysis complete — {data.get('eligibility_label', '?')}",
            state="complete",
        )

    trial_title      = data.get("trial_title", nct_clean)
    verdict_label    = data.get("eligibility_label", "UNCERTAIN")
    score            = data.get("eligibility_score", 0.0)
    confidence       = data.get("confidence", "LOW")
    summary          = data.get("summary", "")
    disqualifying    = data.get("disqualifying_criteria", [])
    reasoning_chain  = data.get("reasoning_chain", [])
    disclaimer       = data.get("disclaimer", "")
    audit_verdict    = data.get("audit_verdict")       # CONFLICT_FOUND | HIGH_INTEGRITY_MATCH | None
    audit_criterion  = data.get("audit_criterion", "")
    audit_challenge  = data.get("audit_challenge", "")
    audit_confidence = data.get("audit_confidence", "")
    audit_raw        = data.get("audit_raw", "")

    # ── Trial card ────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="trial-card">'
        f'<div class="trial-nct">{_html.escape(nct_clean)}</div>'
        f'<div class="trial-title">{_html.escape(trial_title)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Verdict row ───────────────────────────────────────────────────────────
    st.markdown("#### Eligibility Assessment")
    vc1, vc2, vc3, vc4 = st.columns([3, 1, 1, 1], gap="medium")
    with vc1:
        st.markdown('<div class="verdict-label">Clinical Summary</div>', unsafe_allow_html=True)

        def _summary_words(text: str):
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
            f'<div class="score-ring" style="color:{c};text-shadow:0 0 14px {c}55">'
            f'{score:.0%}</div>'
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

    # ── Eligibility Confidence Score metric ───────────────────────────────────
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric("Eligibility Score", f"{score:.0%}", help="0–100 % composite from per-criterion verdicts")
    sm2.metric("Inclusion Criteria", sum(1 for v in reasoning_chain if v.get("criterion_id", "").startswith("INC")))
    sm3.metric("Exclusion Criteria", sum(1 for v in reasoning_chain if v.get("criterion_id", "").startswith("EXC")))
    sm4.metric("Conflicts Found", len(disqualifying))

    if disqualifying:
        st.error(
            "**Disqualifying exclusion criteria:** " +
            "  ·  ".join(f"`{c}`" for c in disqualifying),
            icon="✘",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Key Evidence section ──────────────────────────────────────────────────
    _render_key_evidence(reasoning_chain)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Logic Tree (K2 Reasoning Pathway) ────────────────────────────────────
    st.markdown("#### K2 Reasoning Pathway")
    st.caption("Each card shows one criterion, K2's analysis, and the matching patient evidence.")

    inclusion_items = [v for v in reasoning_chain if v.get("criterion_id", "").startswith("INC")]
    exclusion_items = [v for v in reasoning_chain if v.get("criterion_id", "").startswith("EXC")]

    inc_tab, exc_tab, audit_tab, raw_tab = st.tabs([
        f"Inclusion Criteria  ({len(inclusion_items)})",
        f"Exclusion Criteria  ({len(exclusion_items)})",
        "⚖ Safety Audit",
        "Raw K2 Chain-of-Thought",
    ])
    with inc_tab:
        _render_logic_tree(inclusion_items)
    with exc_tab:
        _render_logic_tree(exclusion_items)
    with audit_tab:
        _render_safety_audit(
            audit_verdict, audit_criterion, audit_challenge, audit_confidence, audit_raw,
            pass1_verdict=verdict_label, pass1_summary=summary,
        )
    with raw_tab:
        st.caption("Full unprocessed K2 chain-of-thought — for audit trail or regulatory review.")
        raw_text = data.get("raw_reasoning", "")
        if raw_text:
            with st.expander("View Raw K2 Chain-of-Thought Output", expanded=False):
                st.text(raw_text)
        else:
            st.markdown('<p style="color:#64748B;font-style:italic">No raw output captured.</p>', unsafe_allow_html=True)

    disc = disclaimer or (
        "This output is an automated eligibility pre-screen generated by an AI model. "
        "It does not constitute medical advice, a clinical diagnosis, or a treatment recommendation. "
        "All eligibility decisions must be reviewed and confirmed by a qualified investigator "
        "or clinical research coordinator before any patient action is taken."
    )
    st.markdown(
        f'<div class="sci-footer"><strong>Scientific Disclaimer</strong><br>{_html.escape(disc)}<br><br>'
        f'<strong>Powered by</strong> MBZUAI-IFM/K2-Think-v2 &nbsp;·&nbsp; '
        f'<strong>Data</strong> ClinicalTrials.gov API v2 &nbsp;·&nbsp; '
        f'<strong>The Trial Oracle — Clinical AI Division &nbsp;·&nbsp; Build with K2 Think V2 Hackathon · 2026</strong></div>',
        unsafe_allow_html=True,
    )

# ── Empty state ────────────────────────────────────────────────────────────────
else:
    st.markdown(
        '<div style="text-align:center;padding:48px 0 36px">'
        '<div style="font-size:3.2rem;margin-bottom:14px;color:#10B981;'
        'text-shadow:0 0 20px rgba(16,185,129,.45)">⬡</div>'
        '<div style="font-size:1.05rem;font-weight:700;color:#94A3B8;margin-bottom:8px">'
        'Complete the patient form and click <em>Start Reasoning</em></div>'
        '<div style="font-size:.88rem;max-width:480px;margin:0 auto;line-height:1.65;color:#64748B">'
        'K2-Think-v2 audits every inclusion and exclusion criterion against the patient '
        'profile and returns a structured eligibility verdict with a full visual reasoning pathway.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
