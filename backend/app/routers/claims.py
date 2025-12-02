from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Dict
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


@router.post("/{claim_id}/document")
def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    service: ClaimService = Depends(get_claim_service),
    current_user: dict = Depends(get_current_user)
):
    """Upload a PDF document for a claim to S3 and return a view URL."""
    try:
        # Ownership enforcement: patient can only upload to their claims would be enforced via service/repo in future
        return service.upload_document(claim_id, file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{claim_id}/document/confirm")
def confirm_document(
    claim_id: str,
    service: ClaimService = Depends(get_claim_service),
    current_user: dict = Depends(get_current_user)
):
    """Confirm document upload for a claim (compatibility endpoint)."""
    try:
        return service.confirm_document(claim_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
