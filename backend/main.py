"""
Main FastAPI application for The Trial Oracle
Clinical Reasoning Engine for Clinical Trial Matching
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from backend.app.routes.trial import router as trial_router
from backend.app.routes.match import router as match_router

load_dotenv()

app = FastAPI(
    title="The Trial Oracle",
    description="Clinical Reasoning Engine for Clinical Trial Matching",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trial_router)
app.include_router(match_router)


@app.get("/")
async def root():
    return {"message": "The Trial Oracle API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
