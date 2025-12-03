from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Dict
from app.schemas.claim import ClaimCreate, ClaimResponse
from app.services.claim_service import ClaimService
from app.core.security import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

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
    user_id = current_user.get("sub")
    patient_id = current_user.get("patient_id")
    
    logger.info(
        "Claim submission initiated",
        extra={
            "event": "claim_submission_started",
            "user_id": user_id,
            "patient_id": patient_id,
            "amount": claim.amount,
            "policy_number": claim.policy_number
        }
    )
    
    try:
        result = service.create_claim(claim, current_user)
        
        logger.info(
            f"Claim submitted successfully",
            extra={
                "event": "claim_submission_success",
                "claim_id": result.claim_id,
                "user_id": user_id,
                "patient_id": patient_id,
                "amount": claim.amount,
                "policy_number": claim.policy_number,
                "status": result.claim_status,
                "has_upload_url": result.s3_upload_url is not None
            }
        )
        return result
    except Exception as e:
        logger.error(
            f"Claim submission failed: {type(e).__name__}",
            extra={
                "event": "claim_submission_failed",
                "user_id": user_id,
                "patient_id": patient_id,
                "amount": claim.amount,
                "policy_number": claim.policy_number,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my", response_model=List)
def list_my_claims(
    service: ClaimService = Depends(get_claim_service),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    
    logger.info(
        "Fetching user claims",
        extra={
            "event": "list_claims_started",
            "user_id": user_id
        }
    )
    
    try:
        claims = service.get_claims_by_user(user_id)
        
        logger.info(
            f"Claims retrieved successfully",
            extra={
                "event": "list_claims_success",
                "user_id": user_id,
                "claim_count": len(claims)
            }
        )
        return claims
    except Exception as e:
        logger.error(
            f"Failed to retrieve claims: {type(e).__name__}",
            extra={
                "event": "list_claims_failed",
                "user_id": user_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise


@router.post("/{claim_id}/document")
def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    service: ClaimService = Depends(get_claim_service),
    current_user: dict = Depends(get_current_user)
):
    """Upload a PDF document for a claim to S3 and return a view URL."""
    user_id = current_user.get("sub")
    
    logger.info(
        "Document upload initiated",
        extra={
            "event": "document_upload_started",
            "claim_id": claim_id,
            "user_id": user_id,
            "filename": file.filename,
            "content_type": file.content_type
        }
    )
    
    try:
        # Ownership enforcement: patient can only upload to their claims would be enforced via service/repo in future
        result = service.upload_document(claim_id, file)
        
        logger.info(
            "Document uploaded successfully",
            extra={
                "event": "document_upload_success",
                "claim_id": claim_id,
                "user_id": user_id,
                "filename": file.filename
            }
        )
        return result
    except Exception as e:
        logger.error(
            f"Document upload failed: {type(e).__name__}",
            extra={
                "event": "document_upload_failed",
                "claim_id": claim_id,
                "user_id": user_id,
                "filename": file.filename,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{claim_id}/document/confirm")
def confirm_document(
    claim_id: str,
    service: ClaimService = Depends(get_claim_service),
    current_user: dict = Depends(get_current_user)
):
    """Confirm document upload for a claim (compatibility endpoint)."""
    user_id = current_user.get("sub")
    
    logger.info(
        "Document confirmation initiated",
        extra={
            "event": "document_confirm_started",
            "claim_id": claim_id,
            "user_id": user_id
        }
    )
    
    try:
        result = service.confirm_document(claim_id)
        
        logger.info(
            "Document confirmed successfully",
            extra={
                "event": "document_confirm_success",
                "claim_id": claim_id,
                "user_id": user_id
            }
        )
        return result
    except Exception as e:
        logger.error(
            f"Document confirmation failed: {type(e).__name__}",
            extra={
                "event": "document_confirm_failed",
                "claim_id": claim_id,
                "user_id": user_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
