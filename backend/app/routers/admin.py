from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.core.security import get_current_user, require_admin
from app.services.admin_service import AdminService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_admin_service() -> AdminService:
    """Dependency provider for AdminService."""
    return AdminService()


@router.get("/users")
def list_users(current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """List all users (admin only)."""
    admin_id = current_user.get("sub")
    
    logger.info(
        "Admin listing all users",
        extra={
            "event": "admin_list_users_started",
            "admin_id": admin_id
        }
    )
    
    require_admin(current_user)
    
    try:
        users = service.list_users()
        
        logger.info(
            "Users listed successfully",
            extra={
                "event": "admin_list_users_success",
                "admin_id": admin_id,
                "user_count": len(users)
            }
        )
        return users
    except Exception as e:
        logger.error(
            f"Failed to list users: {type(e).__name__}",
            extra={
                "event": "admin_list_users_failed",
                "admin_id": admin_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """Delete a user (admin only)."""
    admin_id = current_user.get("sub")
    
    logger.info(
        "Admin deleting user",
        extra={
            "event": "admin_delete_user_started",
            "admin_id": admin_id,
            "target_user_id": user_id
        }
    )
    
    require_admin(current_user)
    
    try:
        service.delete_user(user_id)
        
        logger.info(
            "User deleted successfully",
            extra={
                "event": "admin_delete_user_success",
                "admin_id": admin_id,
                "target_user_id": user_id
            }
        )
        return
    except Exception as e:
        logger.error(
            f"Failed to delete user: {type(e).__name__}",
            extra={
                "event": "admin_delete_user_failed",
                "admin_id": admin_id,
                "target_user_id": user_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise


@router.get("/claims/pending")
def list_pending(current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """List pending claims (admin only)."""
    admin_id = current_user.get("sub")
    
    logger.info(
        "Admin listing pending claims",
        extra={
            "event": "admin_list_pending_started",
            "admin_id": admin_id
        }
    )
    
    require_admin(current_user)
    
    try:
        claims = service.list_pending_claims()
        
        logger.info(
            "Pending claims listed successfully",
            extra={
                "event": "admin_list_pending_success",
                "admin_id": admin_id,
                "pending_count": len(claims)
            }
        )
        return claims
    except Exception as e:
        logger.error(
            f"Failed to list pending claims: {type(e).__name__}",
            extra={
                "event": "admin_list_pending_failed",
                "admin_id": admin_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise


@router.post("/claims/{claim_id}/approve")
def approve_claim(claim_id: str, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """Approve a claim (admin only)."""
    admin_id = current_user.get("sub")
    
    logger.info(
        "Admin approving claim",
        extra={
            "event": "admin_approve_claim_started",
            "admin_id": admin_id,
            "claim_id": claim_id
        }
    )
    
    require_admin(current_user)
    
    try:
        result = service.update_claim_status(claim_id, "APPROVED")
        
        logger.info(
            "Claim approved successfully",
            extra={
                "event": "admin_approve_claim_success",
                "admin_id": admin_id,
                "claim_id": claim_id,
                "new_status": "APPROVED"
            }
        )
        return result
    except Exception as e:
        logger.error(
            f"Failed to approve claim: {type(e).__name__}",
            extra={
                "event": "admin_approve_claim_failed",
                "admin_id": admin_id,
                "claim_id": claim_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise


@router.post("/claims/{claim_id}/reject")
def reject_claim(claim_id: str, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """Reject a claim (admin only)."""
    admin_id = current_user.get("sub")
    
    logger.info(
        "Admin rejecting claim",
        extra={
            "event": "admin_reject_claim_started",
            "admin_id": admin_id,
            "claim_id": claim_id
        }
    )
    
    require_admin(current_user)
    
    try:
        result = service.update_claim_status(claim_id, "REJECTED")
        
        logger.info(
            "Claim rejected successfully",
            extra={
                "event": "admin_reject_claim_success",
                "admin_id": admin_id,
                "claim_id": claim_id,
                "new_status": "REJECTED"
            }
        )
        return result
    except Exception as e:
        logger.error(
            f"Failed to reject claim: {type(e).__name__}",
            extra={
                "event": "admin_reject_claim_failed",
                "admin_id": admin_id,
                "claim_id": claim_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise


@router.get("/claims")
def list_claims(status: Optional[str] = None, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """List all claims or filter by status (admin only)."""
    admin_id = current_user.get("sub")
    
    logger.info(
        "Admin listing claims",
        extra={
            "event": "admin_list_claims_started",
            "admin_id": admin_id,
            "status_filter": status
        }
    )
    
    require_admin(current_user)
    
    try:
        claims = service.list_claims(status)
        
        logger.info(
            "Claims listed successfully",
            extra={
                "event": "admin_list_claims_success",
                "admin_id": admin_id,
                "status_filter": status,
                "claim_count": len(claims)
            }
        )
        return claims
    except Exception as e:
        logger.error(
            f"Failed to list claims: {type(e).__name__}",
            extra={
                "event": "admin_list_claims_failed",
                "admin_id": admin_id,
                "status_filter": status,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise


@router.get("/claims/by-patient/{patient_id}")
def list_claims_by_patient(patient_id: str, current_user: dict = Depends(get_current_user), service: AdminService = Depends(get_admin_service)):
    """List all claims for a specific patient (admin only)."""
    admin_id = current_user.get("sub")
    
    logger.info(
        "Admin listing claims for patient",
        extra={
            "event": "admin_list_patient_claims_started",
            "admin_id": admin_id,
            "patient_id": patient_id
        }
    )
    
    require_admin(current_user)
    
    try:
        claims = service.list_claims_by_patient(patient_id)
        
        logger.info(
            "Patient claims listed successfully",
            extra={
                "event": "admin_list_patient_claims_success",
                "admin_id": admin_id,
                "patient_id": patient_id,
                "claim_count": len(claims)
            }
        )
        return claims
    except Exception as e:
        logger.error(
            f"Failed to list patient claims: {type(e).__name__}",
            extra={
                "event": "admin_list_patient_claims_failed",
                "admin_id": admin_id,
                "patient_id": patient_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise
