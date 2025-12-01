from typing import Dict, Optional
from fastapi import Header, HTTPException
import jwt
from app.core.auth import get_jwt_secret
from app.core.config import settings


def decode_token(token: str) -> Dict:
    """Decode a JWT token.

    Parameters:
    - token: bearer token without prefix

    Returns:
    - dict of token claims
    """

    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict:
    """FastAPI dependency to extract current user from Authorization header.

    Parameters:
    - authorization: header value in format 'Bearer <token>'

    Returns:
    - dict of user claims
    """

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split(" ", 1)[1]
    return decode_token(token)


def require_admin(current_user: Dict) -> Dict:
    """Ensure current user has admin role.

    Parameters:
    - current_user: decoded token claims

    Returns:
    - current_user claims if role is admin
    """

    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


def require_patient(current_user: Dict) -> Dict:
    """Ensure current user has patient role.

    Parameters:
    - current_user: decoded token claims

    Returns:
    - current_user claims if role is patient
    """

    if current_user.get("role") != "patient":
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user
