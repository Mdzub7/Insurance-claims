from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.services.user_service import UserService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_user_service() -> UserService:
    """Dependency provider for UserService."""
    return UserService()


@router.get("/me")
def me(current_user: dict = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    """Return current user profile."""
    user_id = current_user.get("sub")
    
    logger.info(
        "Fetching user profile",
        extra={
            "event": "get_profile_started",
            "user_id": user_id
        }
    )
    
    try:
        profile = service.get_profile(user_id)
        
        if not profile:
            logger.warning(
                "User profile not found",
                extra={
                    "event": "get_profile_not_found",
                    "user_id": user_id
                }
            )
            raise HTTPException(status_code=404, detail="Profile not found")
        
        logger.info(
            "User profile retrieved successfully",
            extra={
                "event": "get_profile_success",
                "user_id": user_id,
                "role": profile.get("role"),
                "patient_id": profile.get("patient_id")
            }
        )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve user profile: {type(e).__name__}",
            extra={
                "event": "get_profile_failed",
                "user_id": user_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise
