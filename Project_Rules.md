# Project Rules: The Trial Oracle

## 1. Project Overview
**The Trial Oracle** is a clinical reasoning engine built for the "Build with K2 Think V2" hackathon. It automates the matching process between patient data and clinical trials using the **ClinicalTrials.gov API v2** and **MBZUAI K2 Think V2**.

## 2. Technical Stack
- **Backend:** FastAPI (Python 3.10+).
- **Frontend:** Streamlit (for rapid web deployment).
- **AI Model:** `MBZUAI-IFM/K2-Think-v2`.
- **Data Source:** ClinicalTrials.gov API v2 (Direct Integration).

## 3. Engineering Standards
- **Modular Design:** Keep services, models, and routes in separate files to minimize token consumption during updates.
- **Validation:** Use `pydantic` for all data schemas to ensure strict contract adherence between APIs.
- **Connectivity:** Implement a minimum 60-second timeout for K2 API calls due to long reasoning outputs.
- **Error Handling:** Avoid generic error messages. Use HTTP-specific exceptions for trial API and AI service failures.

## 4. AI & Reasoning Guidelines
- **System Role:** K2 must act as a "Senior Clinical Trial Auditor.".
- **Logic Chain:** Always enforce a step-by-step reasoning process. The model must compare patient markers (e.g., age, biomarkers, history) against specific trial criteria IDs.
- **Avoid:** Generic medical advice or hallucinations. If data is missing for a criterion, the model must state the uncertainty.

## 5. Deployment Constraints
- **Platform:** Vercel (Backend) and Streamlit Cloud (Frontend).
- **Environment:** Use a `.env` file for all credentials. Do not hardcode the API key: `IFM-QqUWAxlZRQPPklux`.