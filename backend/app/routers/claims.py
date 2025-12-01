from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.claim import ClaimCreate, ClaimResponse
from app.services.claim_service import ClaimService
from app.core.security import get_current_user

router = APIRouter()

# Dependency Injection: We inject the service. 
# This makes unit testing easier (we can mock the service later).
def get_claim_service():
    return ClaimService()

@router.post("/", response_model=ClaimResponse, status_code=201)
def submit_claim(
    claim: ClaimCreate,
    service: ClaimService = Depends(get_claim_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a new insurance claim.
    Returns the claim details and a Presigned URL to upload documents.
    """
    try:
        return service.create_claim(claim, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my", response_model=List)
def list_my_claims(
    service: ClaimService = Depends(get_claim_service),
    current_user: dict = Depends(get_current_user)
):
    return service.get_claims_by_user(current_user.get("sub"))
