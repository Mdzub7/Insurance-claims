from typing import Dict, Optional
from fastapi import Header, HTTPException
import jwt
from app.core.auth import get_jwt_secret
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def decode_token(token: str) -> Dict:
    """Decode a JWT token.

    Parameters:
    - token: bearer token without prefix

    Returns:
    - dict of token claims
    """

    logger.debug(
        "Attempting to decode JWT token",
        extra={"event": "token_decode_started"}
    )

    try:
        decoded = jwt.decode(token, get_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
        
        logger.info(
            "JWT token decoded successfully",
            extra={
                "event": "token_decode_success",
                "user_id": decoded.get("sub"),
                "role": decoded.get("role"),
                "patient_id": decoded.get("patient_id")
            }
        )
        return decoded
    except jwt.ExpiredSignatureError:
        logger.warning(
            "JWT token has expired",
            extra={
                "event": "token_decode_failed",
                "reason": "token_expired"
            }
        )
        raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError as e:
        logger.warning(
            f"JWT token is invalid: {type(e).__name__}",
            extra={
                "event": "token_decode_failed",
                "reason": "invalid_token",
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(
            f"Unexpected error during token decode: {type(e).__name__}",
            extra={
                "event": "token_decode_failed",
                "reason": "unexpected_error",
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict:
    """FastAPI dependency to extract current user from Authorization header.

    Parameters:
    - authorization: header value in format 'Bearer <token>'

    Returns:
    - dict of user claims
    """

    if not authorization:
        logger.warning(
            "Authorization header missing",
            extra={
                "event": "auth_failed",
                "reason": "missing_header"
            }
        )
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not authorization.startswith("Bearer "):
        logger.warning(
            "Authorization header has invalid format",
            extra={
                "event": "auth_failed",
                "reason": "invalid_header_format"
            }
        )
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = authorization.split(" ", 1)[1]
    
    logger.debug(
        "Extracting user from Authorization header",
        extra={"event": "user_extraction_started"}
    )
    
    return decode_token(token)


def require_admin(current_user: Dict) -> Dict:
    """Ensure current user has admin role.

    Parameters:
    - current_user: decoded token claims

    Returns:
    - current_user claims if role is admin
    """

    user_role = current_user.get("role")
    user_id = current_user.get("sub")
    
    if user_role != "admin":
        logger.warning(
            f"Admin access denied - user has role '{user_role}'",
            extra={
                "event": "authorization_failed",
                "reason": "insufficient_role",
                "required_role": "admin",
                "actual_role": user_role,
                "user_id": user_id
            }
        )
        raise HTTPException(status_code=403, detail="Forbidden")
    
    logger.info(
        "Admin access granted",
        extra={
            "event": "authorization_success",
            "required_role": "admin",
            "user_id": user_id
        }
    )
    return current_user


def require_patient(current_user: Dict) -> Dict:
    """Ensure current user has patient role.

    Parameters:
    - current_user: decoded token claims

    Returns:
    - current_user claims if role is patient
    """

    user_role = current_user.get("role")
    user_id = current_user.get("sub")
    
    if user_role != "patient":
        logger.warning(
            f"Patient access denied - user has role '{user_role}'",
            extra={
                "event": "authorization_failed",
                "reason": "insufficient_role",
                "required_role": "patient",
                "actual_role": user_role,
                "user_id": user_id
            }
        )
        raise HTTPException(status_code=403, detail="Forbidden")
    
    logger.info(
        "Patient access granted",
        extra={
            "event": "authorization_success",
            "required_role": "patient",
            "user_id": user_id
        }
    )
    return current_user
