from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.core.security import get_current_user, require_admin
from app.services.admin_service import AdminService


router = APIRouter()


def get_admin_service() -> AdminService:
    """Dependency provider for AdminService."""
    return AdminService()


@router.get("/users")
def list_users(current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """List all users (admin only)."""
    require_admin(current_user)
    return service.list_users()


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """Delete a user (admin only)."""
    require_admin(current_user)
    service.delete_user(user_id)
    return


@router.get("/claims/pending")
def list_pending(current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """List pending claims (admin only)."""
    require_admin(current_user)
    return service.list_pending_claims()


@router.post("/claims/{claim_id}/approve")
def approve_claim(claim_id: str, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """Approve a claim (admin only)."""
    require_admin(current_user)
    return service.update_claim_status(claim_id, "APPROVED")


@router.post("/claims/{claim_id}/reject")
def reject_claim(claim_id: str, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """Reject a claim (admin only)."""
    require_admin(current_user)
    return service.update_claim_status(claim_id, "REJECTED")


@router.get("/claims")
def list_claims(status: Optional[str] = None, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """List all claims or filter by status (admin only)."""
    require_admin(current_user)
    return service.list_claims(status)


@router.get("/claims/by-patient/{patient_id}")
def list_claims_by_patient(patient_id: str, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """List all claims for a specific patient (admin only)."""
    require_admin(current_user)
    return service.list_claims_by_patient(patient_id)
