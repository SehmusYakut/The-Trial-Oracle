# The Trial Oracle 🔮

A clinical reasoning engine built for the **Build with K2 Think V2 Hackathon · 2026**. Automates the matching process between patient data and clinical trials using the **ClinicalTrials.gov API v2** and **MBZUAI K2 Think V2**.

## 🏗️ Project Structure

```
.
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── models/         # Pydantic data schemas
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── __init__.py
│   ├── main.py             # FastAPI entry point
│   └── requirements.txt
├── frontend/                # Streamlit frontend
│   ├── app.py              # Main Streamlit app
│   └── requirements.txt
├── Project_Rules.md        # Project guidelines
├── README.md
├── .env.example            # Environment template
└── .gitignore
```

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** Streamlit
- **AI Model:** MBZUAI-IFM/K2-Think-v2
- **Data Source:** ClinicalTrials.gov API v2

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

The UI will be available at `http://localhost:8501`

## 📋 Configuration

1. Copy `.env.example` to `.env`
2. Add your API keys:
   ```
   K2_API_KEY=your_k2_api_key_here
   CLINICALTRIALS_API_KEY=your_clinicaltrials_api_key_here
   ```

## 📚 Engineering Standards

- **Modular Design:** Separate services, models, and routes to minimize token consumption
- **Validation:** Pydantic for strict schema validation
- **Connectivity:** 60-second timeout for K2 API calls
- **Error Handling:** HTTP-specific exceptions for API failures

## 🔐 Security

- Never commit `.env` files (included in `.gitignore`)
- Use environment variables for all credentials
- API keys should never be hardcoded

## 📖 Additional Resources

See `Project_Rules.md` for detailed engineering guidelines and requirements.
