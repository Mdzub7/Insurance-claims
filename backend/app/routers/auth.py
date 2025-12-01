from fastapi import APIRouter, HTTPException, Depends
from botocore.exceptions import ClientError
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.services.auth_service import AuthService


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

    try:
        return service.login(req)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ClientError as e:
        raise HTTPException(status_code=503, detail="AWS service error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(req: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> RegisterResponse:
    """Register a new user and return identifiers."""

    try:
        return service.register(req)
    except ClientError:
        raise HTTPException(status_code=503, detail="AWS service error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
