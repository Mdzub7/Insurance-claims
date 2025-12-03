from fastapi import APIRouter, HTTPException, Depends
from botocore.exceptions import ClientError
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.services.auth_service import AuthService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_auth_service() -> AuthService:
    """Dependency provider for AuthService.

    Returns:
    - AuthService instance
    """

    return AuthService()


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, service: AuthService = Depends(get_auth_service)) -> LoginResponse:
    """Authenticate user credentials and return a JWT bearer token."""

    # Mask sensitive data for logging
    login_identifier = req.email if req.email else f"patient_id:{req.patient_id}"
    
    logger.info(
        f"Login attempt initiated",
        extra={
            "event": "login_attempt_started",
            "login_method": "email" if req.email else "patient_id",
            "identifier": login_identifier
        }
    )

    try:
        result = service.login(req)
        
        logger.info(
            f"Login successful",
            extra={
                "event": "login_success",
                "user_id": result.user_id,
                "role": result.role,
                "patient_id": result.patient_id,
                "login_method": "email" if req.email else "patient_id"
            }
        )
        return result
    except ValueError as e:
        logger.warning(
            f"Login failed - invalid credentials",
            extra={
                "event": "login_failed",
                "reason": "invalid_credentials",
                "login_method": "email" if req.email else "patient_id",
                "identifier": login_identifier,
                "error_message": str(e)
            }
        )
        raise HTTPException(status_code=401, detail=str(e))
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(
            f"Login failed - AWS service error: {error_code}",
            extra={
                "event": "login_failed",
                "reason": "aws_service_error",
                "error_code": error_code,
                "identifier": login_identifier
            },
            exc_info=True
        )
        raise HTTPException(status_code=503, detail="AWS service error")
    except Exception as e:
        logger.error(
            f"Login failed - unexpected error: {type(e).__name__}",
            extra={
                "event": "login_failed",
                "reason": "unexpected_error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "identifier": login_identifier
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(req: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> RegisterResponse:
    """Register a new user and return identifiers."""

    logger.info(
        f"Registration attempt initiated",
        extra={
            "event": "registration_attempt_started",
            "email": req.email,
            "role": req.role,
            "name": req.name
        }
    )

    try:
        result = service.register(req)
        
        logger.info(
            f"Registration successful",
            extra={
                "event": "registration_success",
                "user_id": result.user_id,
                "patient_id": result.patient_id,
                "email": req.email,
                "role": req.role
            }
        )
        return result
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(
            f"Registration failed - AWS service error: {error_code}",
            extra={
                "event": "registration_failed",
                "reason": "aws_service_error",
                "error_code": error_code,
                "email": req.email
            },
            exc_info=True
        )
        raise HTTPException(status_code=503, detail="AWS service error")
    except Exception as e:
        logger.error(
            f"Registration failed - unexpected error: {type(e).__name__}",
            extra={
                "event": "registration_failed",
                "reason": "unexpected_error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "email": req.email
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
