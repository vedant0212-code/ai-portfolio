"""FastAPI service for StayShield AI.   uvicorn api.main:app --reload   (docs at /docs)"""
from fastapi import FastAPI
from pydantic import BaseModel, Field

from projects.stayshield import service

app = FastAPI(title="StayShield AI", version="1.0")


@app.get("/health")
def health():
    return {"ok": True, "project": "stayshield"}


class ClaimItem(BaseModel):
    item: str
    amount: float = 0


class Claim(BaseModel):
    claim_id: str | None = None
    description: str
    photos: int = 0
    documents: list[str] = Field(default_factory=list)
    items: list[ClaimItem]


class In(BaseModel):
    claim: Claim
    policy_text: str | None = None


@app.post("/stayshield/draft")
def draft(body: In):
    return service.draft_claim(body.claim.model_dump(), body.policy_text)
