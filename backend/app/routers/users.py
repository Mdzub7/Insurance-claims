from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.services.user_service import UserService


router = APIRouter()


def get_user_service() -> UserService:
    """Dependency provider for UserService."""
    return UserService()


@router.get("/me")
def me(current_user: dict = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    """Return current user profile."""
    profile = service.get_profile(current_user.get("sub"))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
